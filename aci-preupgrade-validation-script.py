# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2021 Cisco Systems, Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division
from __future__ import print_function
from six import iteritems
from six.moves import input
from textwrap import TextWrapper
from getpass import getpass
from collections import defaultdict
from datetime import datetime
import warnings
import time
import pexpect
import logging
import subprocess
import json
import sys
import os
import re

SCRIPT_VERSION = "v2.1.0"
DONE = 'DONE'
PASS = 'PASS'
FAIL_O = 'FAIL - OUTAGE WARNING!!'
FAIL_UF = 'FAIL - UPGRADE FAILURE!!'
ERROR = 'ERROR !!'
MANUAL = 'MANUAL CHECK REQUIRED'
POST = 'POST UPGRADE CHECK REQUIRED'
NA = 'N/A'
node_regex = r'topology/pod-(?P<pod>\d+)/node-(?P<node>\d+)'
ver_regex = r'(?:dk9\.)?[1]?(?P<major1>\d)\.(?P<major2>\d)(?:\.|\()(?P<maint>\d+)\.?(?P<patch>(?:[a-b]|[0-9a-z]+))\)?'

tz = time.strftime('%z')
ts = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
DIR = 'preupgrade_validator_logs/'
BUNDLE_NAME = 'preupgrade_validator_%s%s.tgz' % (ts, tz)
RESULT_FILE = DIR + 'preupgrade_validator_%s%s.txt' % (ts, tz)
JSON_FILE = DIR + 'preupgrade_validator_%s%s.json' % (ts, tz)
LOG_FILE = DIR + 'preupgrade_validator_debug.log'
fmt = '[%(asctime)s.%(msecs)03d{} %(levelname)-8s %(funcName)20s:%(lineno)-4d] %(message)s'.format(tz)
subprocess.check_output(['mkdir', '-p', DIR])
logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, format=fmt, datefmt='%Y-%m-%d %H:%M:%S')
warnings.simplefilter(action='ignore', category=FutureWarning)


class OldVerClassNotFound(Exception):
    """ Later versions of ACI can have class properties not found in older versions """
    pass


class OldVerPropNotFound(Exception):
    """ Later versions of ACI can have class properties not found in older versions """
    pass


class Connection(object):
    """
    Object built primarily for executing commands on Cisco IOS/NXOS devices.  The following
    methods and variables are available for use in this class:

        username         (opt) username credential (default 'admin')
        password         (opt) password credential (default 'cisco')
        enable_password  (opt) enable password credential (IOS only) (default 'cisco')
        protocol         (opt) telnet/ssh option (default 'ssh')
        port             (opt) port to connect on (if different from telnet/ssh default)
        timeout          (opt) wait in seconds between each command (default 30)
        prompt           (opt) prompt to expect after each command (default for IOS/NXOS)
        log              (opt) logfile (default None)
        verify           (opt) verify/enforce strictHostKey values for SSL (disabled by default)
        searchwindowsize (opt) maximum amount of data used in matching expressions
                               extremely important to set to a low value for large outputs
                               pexpect default = None, setting this class default=256
        force_wait       (opt) some OS ignore searchwindowsize and therefore still experience high
                               CPU and long wait time for commands with large outputs to complete.
                               A workaround is to sleep the script instead of running regex checking
                               for prompt character.
                               This should only be used in those unique scenarios...
                               Default is 0 seconds (disabled).  If needed, set to 8 (seconds)

        functions:
        connect()        (opt) connect to device with provided protocol/port/hostname
        login()          (opt) log into device with provided credentials
        close()          (opt) close current connection
        cmd()            execute a command on the device (provide matches and timeout)

    Example using all defaults
        c = Connection("10.122.140.89")
        c.cmd("terminal length 0")
        c.cmd("show version")
        print "version of code: %s" % c.output

    @author agossett@cisco.com
    @version 07/28/2014
    """

    def __init__(self, hostname):
        self.hostname = hostname
        self.log = None
        self.username = 'admin'
        self.password = 'cisco'
        self.enable_password = 'cisco'
        self.protocol = "ssh"
        self.port = None
        self.timeout = 30
        self.prompt = "[^#]#[ ]*(\x1b[\x5b-\x5f][\x40-\x7e])*[ ]*$"
        self.verify = False
        self.searchwindowsize = 256
        self.force_wait = 0
        self.child = None
        self.output = ""  # output from last command
        self._term_len = 0  # terminal length for cisco devices
        self._login = False  # set to true at first successful login
        self._log = None  # private variable for tracking logfile state

    def __connected(self):
        # determine if a connection is already open
        connected = (self.child is not None and self.child.isatty())
        logging.debug("check for valid connection: %r" % connected)
        return connected

    @property
    def term_len(self):
        return self._term_len

    @term_len.setter
    def term_len(self, term_len):
        self._term_len = int(term_len)
        if (not self.__connected()) or (not self._login):
            # login function will set the terminal length
            self.login()
        else:
            # user changing terminal length during operation, need to explicitly
            self.cmd("terminal length %s" % self._term_len)

    def start_log(self):
        """ start or restart sending output to logfile """
        if self.log is not None and self._log is None:
            # if self.log is a string, then attempt to open file pointer (do not catch exception, we want it
            # to die if there's an error opening the logfile)
            if isinstance(self.log, str) or isinstance(self.log, unicode):
                self._log = open(self.log, "ab")
            else:
                self._log = self.log
            logging.debug("setting logfile to %s" % self._log.name)
            if self.child is not None:
                self.child.logfile = self._log

    def stop_log(self):
        """ stop sending output to logfile """
        self.child.logfile = None
        self._log = None
        return

    def connect(self):
        # close any currently open connections
        self.close()

        # determine port if not explicitly set
        if self.port is None:
            if self.protocol == "ssh":
                self.port = 22
            if self.protocol == "telnet":
                self.port = 23
        # spawn new thread
        if self.protocol.lower() == "ssh":
            logging.debug(
                "spawning new pexpect connection: ssh %s@%s -p %d" % (self.username, self.hostname, self.port))
            no_verify = " -o StrictHostKeyChecking=no -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null"
            no_verify += " -o HostKeyAlgorithms=+ssh-dss"
            if self.verify: no_verify = ""
            self.child = pexpect.spawn("ssh %s %s@%s -p %d" % (no_verify, self.username, self.hostname, self.port),
                                       searchwindowsize=self.searchwindowsize)
        elif self.protocol.lower() == "telnet":
            logging.info("spawning new pexpect connection: telnet %s %d" % (self.hostname, self.port))
            self.child = pexpect.spawn("telnet %s %d" % (self.hostname, self.port),
                                       searchwindowsize=self.searchwindowsize)
        else:
            logging.error("unknown protocol %s" % self.protocol)
            raise Exception("Unsupported protocol: %s" % self.protocol)

        # start logging
        self.start_log()

    def close(self):
        # try to gracefully close the connection if opened
        if self.__connected():
            logging.info("closing current connection")
            self.child.close()
        self.child = None
        self._login = False

    def __expect(self, matches, timeout=None):
        """
        receives a dictionary 'matches' and returns the name of the matched item
        instead of relying on the index into a list of matches.  Automatically
        adds following options if not already present
            "eof"       : pexpect.EOF
            "timeout"   : pexpect.TIMEOUT
        """

        if "eof" not in matches:
            matches["eof"] = pexpect.EOF
        if "timeout" not in matches:
            matches["timeout"] = pexpect.TIMEOUT

        if timeout is None: timeout = self.timeout
        indexed = []
        mapping = []
        for i in matches:
            indexed.append(matches[i])
            mapping.append(i)
        result = self.child.expect(indexed, timeout)
        logging.debug("timeout: %d, matched: '%s'\npexpect output: '%s%s'" % (
            timeout, self.child.after, self.child.before, self.child.after))
        if result <= len(mapping) and result >= 0:
            logging.debug("expect matched result[%d] = %s" % (result, mapping[result]))
            return mapping[result]
        ds = ''
        logging.error("unexpected pexpect return index: %s" % result)
        for i in range(0, len(mapping)):
            ds += '[%d] %s\n' % (i, mapping[i])
        logging.debug("mapping:\n%s" % ds)
        raise Exception("Unexpected pexpect return index: %s" % result)

    def login(self, max_attempts=7, timeout=17):
        """
        returns true on successful login, else returns false
        """

        logging.debug("Logging into host")

        # successfully logged in at a different time
        if not self.__connected(): self.connect()
        # check for user provided 'prompt' which indicates successful login
        # else provide approriate username/password/enable_password
        matches = {
            "console": "(?i)press return to get started",
            "refuse": "(?i)connection refused",
            "yes/no": "(?i)yes/no",
            "username": "(?i)(user(name)*|login)[ as]*[ \t]*:[ \t]*$",
            "password": "(?i)password[ \t]*:[ \t]*$",
            "enable": ">[ \t]*$",
            "prompt": self.prompt
        }

        last_match = None
        while max_attempts > 0:
            max_attempts -= 1
            match = self.__expect(matches, timeout)
            if match == "console":  # press return to get started
                logging.debug("matched console, send enter")
                self.child.sendline("\r\n")
            elif match == "refuse":  # connection refused
                logging.error("connection refused by host")
                return False
            elif match == "yes/no":  # yes/no for SSH key acceptance
                logging.debug("received yes/no prompt, send yes")
                self.child.sendline("yes")
            elif match == "username":  # username/login prompt
                logging.debug("received username prompt, send username")
                self.child.sendline(self.username)
            elif match == "password":
                # don't log passwords to the logfile
                self.stop_log()
                if last_match == "enable":
                    # if last match was enable prompt, then send enable password
                    logging.debug("matched password prompt, send enable password")
                    self.child.sendline(self.enable_password)
                else:
                    logging.debug("matched password prompt, send password")
                    self.child.sendline(self.password)
                # restart logging
                self.start_log()
            elif match == "enable":
                logging.debug("matched enable prompt, send enable")
                self.child.sendline("enable")
            elif match == "prompt":
                logging.debug("successful login")
                self._login = True
                # force terminal length at login
                self.term_len = self._term_len
                return True
            elif match == "timeout":
                logging.debug("timeout received but connection still opened, send enter")
                self.child.sendline("\r\n")
            last_match = match
        # did not find prompt within max attempts, failed login
        logging.error("failed to login after multiple attempts")
        return False

    def cmd(self, command, **kargs):
        """
        execute a command on a device and wait for one of the provided matches to return.
        Required argument string command
        Optional arguments:
            timeout - seconds to wait for command to completed (default to self.timeout)
            sendline - boolean flag to use send or sendline fuction (default to true)
            matches - dictionary of key/regex to match against.  Key corresponding to matched
                regex will be returned.  By default, the following three keys/regex are applied:
                    'eof'       : pexpect.EOF
                    'timeout'   : pexpect.TIMEOUT
                    'prompt'    : self.prompt
            echo_cmd - boolean flag to echo commands sent (default to false)
                note most terminals (i.e., Cisco devices) will echo back all typed characters
                by default.  Therefore, enabling echo_cmd may cause duplicate cmd characters
        Return:
        returns the key from the matched regex.  For most scenarios, this will be 'prompt'.  The output
        from the command can be collected from self.output variable
        """

        sendline = True
        timeout = self.timeout
        matches = {}
        echo_cmd = False
        if "timeout" in kargs:
            timeout = kargs["timeout"]
        if "matches" in kargs:
            matches = kargs["matches"]
        if "sendline" in kargs:
            sendline = kargs["sendline"]
        if "echo_cmd" in kargs:
            echo_cmd = kargs["echo_cmd"]

        # ensure prompt is in the matches list
        if "prompt" not in matches:
            matches["prompt"] = self.prompt

        self.output = ""
        # check if we've ever logged into device or currently connected
        if (not self.__connected()) or (not self._login):
            logging.debug("no active connection, attempt to login")
            if not self.login():
                raise Exception("failed to login to host")

        # if echo_cmd is disabled, then need to disable logging before
        # executing commands
        if not echo_cmd: self.stop_log()

        # execute command
        logging.debug("cmd command: %s" % command)
        if sendline:
            self.child.sendline(command)
        else:
            self.child.send(command)

        # remember to re-enable logging
        if not echo_cmd: self.start_log()

        # force wait option
        if self.force_wait != 0:
            time.sleep(self.force_wait)

        result = self.__expect(matches, timeout)
        self.output = "%s%s" % (self.child.before, self.child.after)
        if result == "eof" or result == "timeout":
            logging.warning("unexpected %s occurred" % result)
        return result


class IPAddress:
    """Custom IP handling class since old APICs do not have `ipaddress` module.
    """
    @classmethod
    def ip_to_binary(cls, ip):
        if ':' in ip:
            return cls.ipv6_to_binary(ip)
        else:
            return cls.ipv4_to_binary(ip)

    @staticmethod
    def ipv4_to_binary(ipv4):
        octets = ipv4.split(".")
        octets_bin = [format(int(octet), "08b") for octet in octets]
        return "".join(octets_bin)

    @staticmethod
    def ipv6_to_binary(ipv6):
        HEXTET_COUNT = 8
        _hextets = ipv6.split(":")
        dbl_colon_index = None
        if '' in _hextets:
            # leading/trailing '::' results in additional '' at the beginning/end.
            if _hextets[0] == '':
                _hextets = _hextets[1:]
            if _hextets[-1] == '':
                _hextets = _hextets[:-1]
            # Uncompress all zero hextets represented by '::'
            dbl_colon_index = _hextets.index('')
            skipped_hextets = HEXTET_COUNT - len(_hextets) + 1
            hextets = _hextets[:dbl_colon_index]
            hextets += ['0'] * skipped_hextets
            hextets += _hextets[dbl_colon_index+1:]
        else:
            hextets = _hextets
        hextets_bin = [format(int(hextet, 16), "016b") for hextet in hextets]
        return "".join(hextets_bin)

    @classmethod
    def get_network_binary(cls, ip, pfxlen):
        maxlen = 128 if ':' in ip else 32
        ip_bin = cls.ip_to_binary(ip)
        return ip_bin[0:maxlen-(maxlen-int(pfxlen))]

    @classmethod
    def ip_in_subnet(cls, ip, subnet):
        subnet_ip, subnet_pfxlen = subnet.split("/")
        subnet_network = cls.get_network_binary(subnet_ip, subnet_pfxlen)
        ip_network = cls.get_network_binary(ip, subnet_pfxlen)
        return ip_network == subnet_network


class AciVersion():
    v_regex = r'(?:dk9\.)?[1]?(?P<major1>\d)\.(?P<major2>\d)(?:\.|\()(?P<maint>\d+)\.?(?P<patch>(?:[a-b]|[0-9a-z]+))\)?'

    def __init__(self, version):
        self.original = version
        v = re.search(self.v_regex, version)
        self.version = ('{major1}.{major2}({maint}{patch})'
                        .format(**v.groupdict()) if v else None)
        self.dot_version = ("{major1}.{major2}.{maint}{patch}"
                            .format(**v.groupdict()) if v else None)
        self.simple_version = ("{major1}.{major2}({maint})"
                               .format(**v.groupdict()) if v else None)
        self.major1 = v.group('major1') if v else None
        self.major2 = v.group('major2') if v else None
        self.maint = v.group('maint') if v else None
        self.patch = v.group('patch') if v else None
        self.regex = v
        if not v:
            raise RuntimeError("Parsing failure of ACI version `%s`", version)

    def __str__(self):
        return self.version

    def older_than(self, version):
        v = re.search(self.v_regex, version)
        if not v: return None
        for i in range(1, len(v.groups())+1):
            if i < 4:
                if int(self.regex.group(i)) > int(v.group(i)): return False
                elif int(self.regex.group(i)) < int(v.group(i)): return True
            if i == 4:
                if self.regex.group(i) > v.group(i): return False
                elif self.regex.group(i) < v.group(i): return True
        return False

    def newer_than(self, version):
        return not self.older_than(version) and not self.same_as(version)

    def same_as(self, version):
        v = re.search(self.v_regex, version)
        ver = ('{major1}.{major2}({maint}{patch})'
               .format(**v.groupdict()) if v else None)
        return self.version == ver


def is_firstver_gt_secondver(first_ver, second_ver):
    """ Used for CIMC version comparison """
    result = False
    if first_ver[0] > second_ver[0]:
        return True
    elif first_ver[0] == second_ver[0]:
        if first_ver[2] > second_ver[2]:
            return True
        elif first_ver[2] == second_ver[2]:
            if first_ver[4] > second_ver[4]:
                return True
            elif first_ver[4] == second_ver[4]:
                if first_ver[5] >= second_ver[5]:
                    result = True
    return result


def format_table(headers, data,
                 min_width=5, left_padding=2, hdr_sp='-', col_sp='  '):
    """ get string results in table format
    Args:
        header (list): list of column headers (optional)
                each header can either be a string representing the name or a
                dictionary with following attributes:
                {
                    name (str): column name
                    width (int or str): integer width of column. can also be a string 'auto'
                                        which is based on the longest string in column
                    max_width (int): integer value of max width when combined with
                }
        data (list): list of rows, where each row is a list of values
                     corresponding to the appropriate header. If length of row
                     exceeds length of headers, it is is ignored.
        min_width (int, optional): minimum width enforced on any auto-calculated column. Defaults to 5.
        left_padding (int, optional): number of spaces to 'pad' left most column. Defaults to 2.
        hdr_sp (str, optional): print a separator string between hdr and data row. Defaults to '-'.
        col_sp (str, optional): print a separator string between data columns. Defaults to '  '.
    Returns:
        str: table with columns aligned with spacing
    """
    if type(data) is not list or len(data) == 0:
        return ""
    cl = 800
    col_widths = []
    rows = []

    def update_col_widths(idx, new_width):
        if len(col_widths) < idx + 1:
            col_widths.append(new_width)
        elif col_widths[idx] < new_width:
            col_widths[idx] = new_width

    for row in data:
        if type(row) is not list:
            return ""
        for idx, col in enumerate(row):
            update_col_widths(idx, len(str(col)))
        rows.append([str(col) for col in row])
    h_cols = []
    for idx, col in enumerate(headers):
        if isinstance(col, str):
            update_col_widths(idx, len(col))
            h_cols.append({'name': col, 'width': 'auto'})
        elif isinstance(col, dict):
            name = col.get('name', '')
            width = col.get('width', '')
            max_w = col.get('max_width', 0)
            update_col_widths(idx, len(name))
            if width == 'auto' and max_w:
                try:
                    if int(max_w) < col_widths[idx]:
                        col_widths[idx] = int(max_w)
                except ValueError:
                    max_w = 0
            else:
                try:
                    col_widths[idx] = int(width)
                except ValueError:
                    width = 'auto'
            h_cols.append({'name': name, 'width': width})

    # Adjust column width to fit the table with
    recovery_width = 3 * min_width
    total_width = sum(col_widths) + len(col_sp) * len(col_widths) + left_padding
    for idx, h in enumerate(h_cols):
        if total_width <= cl: break
        if h['width'] == 'auto' and col_widths[idx] > recovery_width:
            total_width -= col_widths[idx] - recovery_width
            col_widths[idx] = recovery_width

    pad = ' ' * left_padding
    output = []
    if headers:
        output.append(
            get_row(col_widths, [c['name'] for c in h_cols], col_sp, pad)
        )
        if isinstance(hdr_sp, str):
            if len(hdr_sp) > 0:
                hsp_sp = hdr_sp[0]  # only single char for hdr_sp
            values = [hsp_sp * len(c['name']) for c in h_cols]
            output.append(
                get_row(col_widths, values, col_sp, pad)
            )
    for row in rows:
        output.append(get_row(col_widths, row, col_sp, pad))
    return '\n'.join(output)


def get_row(widths, values, spad="  ", lpad=""):
    cols = []
    row_maxnum = 0
    for i, value in enumerate(values):
        w = widths[i] if widths[i] > 0 else 1
        tw = TextWrapper(width=w)
        lines = []
        for v in value.split('\n'):
            lines += tw.wrap(v)
        cols.append({'width': w, 'lines': lines})
        if row_maxnum < len(lines): row_maxnum = len(lines)
    spad2 = ' ' * len(spad)  # space separators except for the 1st line
    output = []
    for i in range(row_maxnum):
        row = []
        for c in cols:
            if len(c['lines']) > i:
                row.append('{:{}}'.format(c['lines'][i], c['width']))
            else:
                row.append('{:{}}'.format('', c['width']))
        if not output:
            output.append("%s%s" % (lpad, spad.join(row).rstrip()))
        else:
            output.append("%s%s" % (lpad, spad2.join(row).rstrip()))
    return ('\n'.join(output).rstrip())


def prints(objects, sep=' ', end='\n'):
    with open(RESULT_FILE, 'a') as f:
        print(objects, sep=sep, end=end, file=sys.stdout)
        print(objects, sep=sep, end=end, file=f)
        sys.stdout.flush()
        f.flush()


def print_title(title, index=None, total=None):
    if index and total:
        prints('[Check{:3}/{}] {}... '.format(index, total, title), end='')
    else:
        prints('{:14}{}... '.format('', title), end='')


def print_result(title, result, msg='',
                 headers=None, data=None,
                 unformatted_headers=None, unformatted_data=None,
                 recommended_action='',
                 doc_url='',
                 adjust_title=False):
    padding = 120 - len(title) - len(msg)
    if adjust_title: padding += len(title) + 18
    output = '{}{:>{}}'.format(msg, result, padding)
    if data:
        data.sort()
        output += '\n' + format_table(headers, data)
    if unformatted_data:
        unformatted_data.sort()
        output += '\n' + format_table(unformatted_headers, unformatted_data)
    if data or unformatted_data:
        output += '\n'
        if recommended_action:
            output += '\n  Recommended Action: %s' % recommended_action
        if doc_url:
            output += '\n  Reference Document: %s' % doc_url
        output += '\n' * 2
    prints(output)


def icurl(apitype, query):
    if apitype not in ['class', 'mo']:
        print('invalid API type - %s' % apitype)
        return []
    uri = 'http://127.0.0.1:7777/api/{}/{}'.format(apitype, query)
    cmd = ['icurl', '-gs', uri]
    logging.info('cmd = ' + ' '.join(cmd))
    response = subprocess.check_output(cmd)
    logging.debug('response: ' + str(response))
    imdata = json.loads(response)['imdata']
    if imdata and "error" in imdata[0]:
        if "not found in class" in imdata[0]['error']['attributes']['text']:
            raise OldVerPropNotFound('cversion does not have requested property')
        elif "unresolved class for" in imdata[0]['error']['attributes']['text']:
            raise OldVerClassNotFound('cversion does not have requested class')
        elif "not found" in imdata[0]['error']['attributes']['text']:
            raise OldVerClassNotFound('cversion does not have requested class')
        else:
            raise Exception('API call failed! Check debug log')
    else:
        return imdata


def get_credentials():
    while True:
        usr = input('Enter username for APIC login          : ')
        if usr: break
    while True:
        pwd = getpass('Enter password for corresponding User  : ')
        if pwd: break
    print('')
    return usr, pwd


def get_current_version():
    """ Returns: AciVersion instance """
    prints("Checking current APIC version...", end='')
    firmwares = icurl('class', 'firmwareCtrlrRunning.json')
    for firmware in firmwares:
        if 'node-1' in firmware['firmwareCtrlrRunning']['attributes']['dn']:
            apic1_version = firmware['firmwareCtrlrRunning']['attributes']['version']
            break
    current_version = AciVersion(apic1_version)
    prints('%s\n' % current_version)
    return current_version


def get_target_version():
    """ Returns: AciVersion instance """
    prints("Gathering APIC Versions from Firmware Repository...\n")
    repo_list = []
    response_json = icurl('class',
                          'firmwareFirmware.json?query-target-filter=and(wcard(firmwareFirmware.isoname,"aci-apic"),eq(firmwareFirmware.type,"controller"))')
    if response_json:
        for version in response_json:
            repo_list.append(version['firmwareFirmware']['attributes']['isoname'])
        repo_list.sort()
        # Display version info to User
        for i, value in enumerate(repo_list):
            prints("[%s]: %s" % (i + 1, value))
        prints('')

        version_choice = None
        while version_choice is None:
            version_choice = input("What is the Target Version?     : ")
            try:
                version_choice = int(version_choice)
                if version_choice < 1 or version_choice > len(repo_list): raise ValueError("")
            except ValueError:
                prints("Please select a value between 1 and %s" % len(repo_list))
                version_choice = None

        version = repo_list[version_choice - 1]
        target_version = AciVersion(version)
        prints('\nYou have chosen version "%s"\n' % target_version)
        return target_version
    else:
        prints("No Firmware Detected!  Please Upload APIC Firmware and re-run the script.\n")
        return None


def get_vpc_nodes(**kwargs):
    """ Returns list of VPC Node IDs; ['101', '102', etc...] """
    prints("Collecting VPC Node IDs...\n")
    vpc_nodes = []

    prot_pols = kwargs.get("fabricNodePEp.json", None)
    if not prot_pols:
        prot_pols = icurl('class', 'fabricNodePEp.json')

    if prot_pols:
        for vpc_node in prot_pols:
            vpc_nodes.append(vpc_node['fabricNodePEp']['attributes']['id'])

    return vpc_nodes


def get_switch_version(**kwargs):
    """ Returns lowest switch version as AciVersion instance """
    prints("Gathering Lowest Switch Version from Firmware Repository...", end='')
    firmwares = icurl('class', 'firmwareRunning.json')
    lowest_sw_ver = None
    versions = set()

    for firmware in firmwares:
        versions.add(firmware['firmwareRunning']['attributes']['peVer'])

    if versions:
        lowest_sw_ver = AciVersion(versions.pop())
        for version in versions:
            version = AciVersion(version)
            if lowest_sw_ver.newer_than(str(version)):
                lowest_sw_ver = version

    return lowest_sw_ver


def apic_cluster_health_check(index, total_checks, cversion, **kwargs):
    title = 'APIC Cluster is Fully-Fit'
    result = FAIL_UF
    msg = ''
    headers = ['APIC-ID\n(Seen By)', 'APIC-ID\n(Affected)', 'Admin State', 'Operational State', 'Health State']
    unformatted_headers = ['Affected DN', 'Admin State', 'Operational State', 'Health State']
    data = []
    unformatted_data = []
    doc_url = 'ACI Troubleshooting Guide 2nd Edition - http://cs.co/9003ybZ1d'
    print_title(title, index, total_checks)
    if cversion.older_than("4.2"):
        recommended_action = 'Follow "Initial Fabric Setup" in ACI Troubleshooting Guide 2nd Edition'
    else:
        recommended_action = 'Troubleshoot by running "acidiag cluster" on APIC CLI'

    dn_regex = node_regex + r'/av/node-(?P<winode>\d)'
    infraWiNodes = icurl('class', 'infraWiNode.json')
    for av in infraWiNodes:
        av_attr = av['infraWiNode']['attributes']
        if av_attr['health'] == 'fully-fit':
            continue
        dn = re.search(dn_regex, av_attr['dn'])
        if dn:
            data.append([dn.group('node'), dn.group('winode'),
                         av_attr['adminSt'], av_attr['operSt'], av_attr['health']])
        else:
            unformatted_data.append([av_attr['dn'], av_attr['adminSt'],
                                     av_attr['operSt'], av_attr['health']])
    if not infraWiNodes:
        result = ERROR
        msg = 'infraWiNode (Appliance Vector) not found!'
    elif not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data,
                 recommended_action, doc_url)
    return result


def switch_status_check(index, total_checks, **kwargs):
    title = 'Switches are all in Active state'
    result = FAIL_UF
    msg = ''
    headers = ['Pod-ID', 'Node-ID', 'State', 'Recommended Action']
    data = []
    recommended_action = 'Bring this node back to "active"'
    print_title(title, index, total_checks)
    # fabricNode.fabricSt shows `disabled` for both Decommissioned and Maintenance (GIR).
    # fabricRsDecommissionNode.debug==yes is required to show `disabled (Maintenance)`.
    fabricNodes = icurl('class', 'fabricNode.json?&query-target-filter=ne(fabricNode.role,"controller")')
    girNodes = icurl('class',
                     'fabricRsDecommissionNode.json?&query-target-filter=eq(fabricRsDecommissionNode.debug,"yes")')
    for fabricNode in fabricNodes:
        state = fabricNode['fabricNode']['attributes']['fabricSt']
        if state == 'active':
            continue
        dn = re.search(node_regex, fabricNode['fabricNode']['attributes']['dn'])
        pod_id = dn.group("pod")
        node_id = dn.group("node")
        for gir in girNodes:
            if node_id == gir['fabricRsDecommissionNode']['attributes']['targetId']:
                state = state + ' (Maintenance)'
        data.append([pod_id, node_id, state, recommended_action])
    if not fabricNodes:
        result = MANUAL
        msg = 'Switch fabricNode not found!'
    elif not data:
        result = PASS
    print_result(title, result, msg, headers, data)
    return result


def maintp_grp_crossing_4_0_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Firmware/Maintenance Groups when crossing 4.0 Release'
    result = PASS
    msg = ''
    headers = ["Group Name", "Group Type", "Recommended Action"]
    data = []
    recommended_action = 'Remove the group prior to APIC upgrade. Create a new switch group once APICs are upgraded to post-4.0.'
    print_title(title, index, total_checks)

    if (int(cversion.major1) >= 4) or (tversion and (int(tversion.major1) <= 3)):
        result = NA
        msg = 'Versions not applicable'
    elif (int(cversion.major1) < 4) and not tversion:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'
    else:
        groups = icurl('mo', '/uni/fabric.json?query-target=children&target-subtree-class=maintMaintP,firmwareFwP')
        for g in groups:
            result = FAIL_O
            if g.get('maintMaintP'):
                data.append([g['maintMaintP']['attributes']['name'], 'Maintenance Group', recommended_action])
            else:
                data.append([g['firmwareFwP']['attributes']['name'], 'Firmware Group', recommended_action])
    print_result(title, result, msg, headers, data)
    return result


def ntp_status_check(index, total_checks, **kargs):
    title = 'NTP Status'
    result = FAIL_UF
    msg = ''
    headers = ["Pod-ID", "Node-ID", "Recommended Action"]
    data = []
    recommended_action = 'Not Synchronized. Check NTP config and NTP server reachability.'
    print_title(title, index, total_checks)

    fabricNodes = icurl('class', 'fabricNode.json')
    nodes = [fn['fabricNode']['attributes']['id'] for fn in fabricNodes]

    apicNTPs = icurl('class', 'datetimeNtpq.json')
    switchNTPs = icurl('class', 'datetimeClkPol.json')
    for apicNTP in apicNTPs:
        if '*' == apicNTP['datetimeNtpq']['attributes']['tally']:
            dn = re.search(node_regex, apicNTP['datetimeNtpq']['attributes']['dn'])
            if dn and dn.group('node') in nodes:
                nodes.remove(dn.group('node'))
    for switchNTP in switchNTPs:
        if 'synced' in switchNTP['datetimeClkPol']['attributes']['srvStatus']:
            dn = re.search(node_regex, switchNTP['datetimeClkPol']['attributes']['dn'])
            if dn and dn.group('node') in nodes:
                nodes.remove(dn.group('node'))
    for fn in fabricNodes:
        if fn['fabricNode']['attributes']['id'] in nodes:
            dn = re.search(node_regex, fn['fabricNode']['attributes']['dn'])
            data.append([dn.group('pod'), dn.group('node'), recommended_action])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data)
    return result


def features_to_disable_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Features that need to be Disabled prior to Upgrade'
    result = FAIL_O
    msg = ''
    headers = ["Feature", "Name", "Status", "Recommended Action"]
    data = []
    print_title(title, index, total_checks)

    apPlugins = icurl('class', 'apPlugin.json?&query-target-filter=ne(apPlugin.pluginSt,"inactive")')
    infraMOs = icurl('mo', 'uni/infra.json?query-target=subtree&target-subtree-class=infrazoneZone,epControlP')

    default_apps = ['IntersightDC', 'NIALite', 'NIBASE', 'ApicVision']
    default_appDNs = ['pluginContr/plugin-Cisco_' + app for app in default_apps]
    if apPlugins:
        for apPlugin in apPlugins:
            if apPlugin['apPlugin']['attributes']['dn'] not in default_appDNs:
                name = apPlugin['apPlugin']['attributes']['name']
                pluginSt = apPlugin['apPlugin']['attributes']['pluginSt']
                data.append(['App Center', name, pluginSt, 'Disable the app'])
    for mo in infraMOs:
        if mo.get('infrazoneZone') and mo['infrazoneZone']['attributes']['deplMode'] == 'disabled':
            name = mo['infrazoneZone']['attributes']['name']
            data.append(['Config Zone', name, 'Locked',
                         'Change the status to "Open" or remove the zone'])
        elif mo.get('epControlP') and mo['epControlP']['attributes']['adminSt'] == 'enabled':
            ra = ''
            if not tversion:
                ra = 'Disable Rogue EP during the upgrade if your current version is 4.1 or your target version is 4.1'
            else:
                cv_is_4_1 = cversion.major1 == '4' and cversion.major2 == '1'
                tv_is_4_1 = tversion.major1 == '4' and tversion.major2 == '1'
                if cv_is_4_1 and not tv_is_4_1:
                    ra = 'Disable Rogue EP during the upgrade because your current version is 4.1'
                elif not cv_is_4_1 and tv_is_4_1:
                    ra = 'Disable Rogue EP during the upgrade because your target version is 4.1'
            if ra:
                name = mo['epControlP']['attributes']['name']
                data.append(['Rogue Endpoint', name, 'Enabled', ra])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data)
    return result


def switch_group_guideline_check(index, total_checks, **kwargs):
    title = 'Switch Upgrade Group Guidelines'
    result = FAIL_O
    msg = ''
    headers = ['Group Name', 'Pod-ID', 'Node-IDs', 'Failure Reason']
    data = []
    recommended_action = 'Upgrade nodes in each line above separately in another group.'
    doc_url = 'Guidelines for Switch Upgrades in ACI Firmware Upgrade Overview'
    print_title(title, index, total_checks)

    maints = icurl('class', 'maintMaintGrp.json?rsp-subtree=children')
    if not maints:
        result = MANUAL
        msg = 'No upgrade groups found!'
        print_result(title, result, msg, headers, data,
                     recommended_action=recommended_action, doc_url=doc_url)
        return result

    spine_type = ['', 'RR ', 'IPN/ISN ']
    f_spines = [defaultdict(list) for t in spine_type]
    reason = 'All {}spine nodes in this pod are in the same group.'
    reasons = [reason.format(t) for t in spine_type]
    reason_apicleaf = 'All leaf nodes connected to APIC {} are in the same group.'
    reason_vpc = 'Both leaf nodes in the same vPC pair are in the same group.'

    nodes = {}
    fabricNodes = icurl('class', 'fabricNode.json')
    for fn in fabricNodes:
        attr = fn['fabricNode']['attributes']
        nodes[attr['dn']] = {'role': attr['role'], 'nodeType': attr['nodeType']}

    for key in nodes:
        if nodes[key]['role'] == 'spine':
            dn = re.search(node_regex, key)
            if not dn:
                logging.error('Failed to parse - %s', key)
                continue
            f_spines[0][dn.group('pod')].append(int(dn.group('node')))

    bgpRRs = icurl('class', 'bgpRRNodePEp.json')
    for bgpRR in bgpRRs:
        pod = bgpRR['bgpRRNodePEp']['attributes']['podId']
        node = bgpRR['bgpRRNodePEp']['attributes']['id']
        f_spines[1][pod].append(int(node))

    infraL3Outs = icurl('class',
                        'l3extRsNodeL3OutAtt.json?query-target-filter=wcard(l3extRsNodeL3OutAtt.dn,"tn-infra/")')
    for infraL3Out in infraL3Outs:
        tDn = infraL3Out['l3extRsNodeL3OutAtt']['attributes']['tDn']
        if nodes.get(tDn, {}).get('role') == 'spine':
            dn = re.search(node_regex, tDn)
            if not dn:
                logging.error('Failed to parse - %s', tDn)
                continue
            f_spines[2][dn.group('pod')].append(int(dn.group('node')))

    apic_leafs = defaultdict(set)
    lldps = icurl('class', 'lldpCtrlrAdjEp.json')
    for lldp in lldps:
        dn = re.search(node_regex, lldp['lldpCtrlrAdjEp']['attributes']['dn'])
        if not dn:
            logging.error('Failed to parse - %s', lldp['lldpCtrlrAdjEp']['attributes']['dn'])
            continue
        apic_id_pod = '-'.join([lldp['lldpCtrlrAdjEp']['attributes']['id'], dn.group('pod')])
        apic_leafs[apic_id_pod].add(int(dn.group('node')))

    vpcs = icurl('class', 'fabricExplicitGEp.json?rsp-subtree=children&rsp-subtree-class=fabricNodePEp')

    for m in maints:
        m_nodes = []
        m_name = ''
        for mc in m['maintMaintGrp']['children']:
            if mc.get('maintRsMgrpp'):
                m_name = mc['maintRsMgrpp']['attributes']['tnMaintMaintPName']
            elif mc.get('fabricNodeBlk'):
                m_nodes += range(int(mc['fabricNodeBlk']['attributes']['from_']),
                                 int(mc['fabricNodeBlk']['attributes']['to_']) + 1)

        m_spines = [defaultdict(list) for t in spine_type]
        for m_node in m_nodes:
            for idx, fabric in enumerate(f_spines):
                for pod in fabric:
                    if m_node in fabric[pod]:
                        m_spines[idx][pod].append(m_node)
                        break
        for m, f, r in zip(m_spines, f_spines, reasons):
            for pod in m:
                if len(m[pod]) == len(f[pod]):
                    data.append([m_name, pod, ','.join(str(x) for x in m[pod]), r])

        for apic_id_pod in apic_leafs:
            if apic_leafs[apic_id_pod] == apic_leafs[apic_id_pod].intersection(m_nodes):
                pod = apic_id_pod.split('-')[1]
                apic_id = apic_id_pod.split('-')[0]
                data.append([m_name, pod, ','.join(str(x) for x in apic_leafs[apic_id_pod]),
                             reason_apicleaf.format(apic_id)])

        for vpc in vpcs:
            m_vpc_peers = []
            for vpc_peer in vpc['fabricExplicitGEp']['children']:
                if int(vpc_peer['fabricNodePEp']['attributes']['id']) in m_nodes:
                    m_vpc_peers.append({
                        'node': vpc_peer['fabricNodePEp']['attributes']['id'],
                        'pod': vpc_peer['fabricNodePEp']['attributes']['podId']
                    })
            if len(m_vpc_peers) > 1:
                data.append([m_name, m_vpc_peers[0]['pod'],
                             ','.join(x['node'] for x in m_vpc_peers),
                             reason_vpc])
    if not data and not msg:
        result = PASS
    print_result(title, result, msg, headers, data,
                 recommended_action=recommended_action, doc_url=doc_url)
    return result


def switch_bootflash_usage_check(index, total_checks, tversion, **kwargs):
    title = 'Switch Node /bootflash usage'
    result = FAIL_UF
    msg = ''
    headers = ["Pod-ID", "Node-ID", "Utilization", "Alert"]
    data = []
    print_title(title, index, total_checks)

    partitions_api =  'eqptcapacityFSPartition.json'
    partitions_api += '?query-target-filter=eq(eqptcapacityFSPartition.path,"/bootflash")'

    download_sts_api =  'maintUpgJob.json'
    download_sts_api += '?query-target-filter=and(eq(maintUpgJob.dnldStatus,"downloaded")' 
    download_sts_api += ',eq(maintUpgJob.desiredVersion,"n9000-1{}"))'.format(tversion)

    partitions = icurl('class', partitions_api)
    if not partitions:
        result = ERROR
        msg = 'bootflash objects not found'

    predownloaded_nodes = []
    try:
        download_sts = icurl('class', download_sts_api)
    except OldVerPropNotFound:
        # Older versions don't have 'dnldStatus' param
        download_sts = []

    for maintUpgJob in download_sts:
        dn = re.search(node_regex, maintUpgJob['maintUpgJob']['attributes']['dn'])
        node = dn.group("node")
        predownloaded_nodes.append(node)

    for eqptcapacityFSPartition in partitions:
        dn = re.search(node_regex, eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['dn'])
        pod = dn.group("pod")
        node = dn.group("node")
        avail = int(eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['avail'])
        used = int(eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['used'])

        usage = (used / (avail + used)) * 100
        if (usage >= 50) and (node not in predownloaded_nodes):
            data.append([pod, node, usage, "Over 50% usage! Contact Cisco TAC for Support"])

    if not data:
        result = PASS
        msg = 'All below 50% or pre-downloaded'
    print_result(title, result, msg, headers, data)
    return result


def l3out_mtu_check(index, total_checks, **kwargs):
    title = 'L3Out MTU'
    result = MANUAL
    msg = 'Verify that these MTUs match with connected devices'
    headers = ["Tenant", "L3Out", "Node Profile", "Logical Interface Profile",
               "Pod", "Node", "Interface", "Type", "IP Address", "MTU"]
    data = []
    unformatted_headers = ['L3 DN', "Type", "IP Address", "MTU"]
    unformatted_data = []
    print_title(title, index, total_checks)

    dn_regex = r'tn-(?P<tenant>[^/]+)/out-(?P<l3out>[^/]+)/lnodep-(?P<lnodep>[^/]+)/lifp-(?P<lifp>[^/]+)/rspathL3OutAtt-\[topology/pod-(?P<pod>[^/]+)/.*paths-(?P<nodes>\d{3,4}|\d{3,4}-\d{3,4})/pathep-\[(?P<int>.+)\]\]'
    response_json = icurl('class', 'l3extRsPathL3OutAtt.json')
    if response_json:
        l2Pols = icurl('mo', 'uni/fabric/l2pol-default.json')
        fabricMtu = l2Pols[0]['l2InstPol']['attributes']['fabricMtu']
        for l3extRsPathL3OutAtt in response_json:
            mtu = l3extRsPathL3OutAtt['l3extRsPathL3OutAtt']['attributes']['mtu']
            iftype = l3extRsPathL3OutAtt['l3extRsPathL3OutAtt']['attributes']['ifInstT']
            addr = l3extRsPathL3OutAtt['l3extRsPathL3OutAtt']['attributes']['addr']

            if mtu == 'inherit':
                mtu += " (%s)" % fabricMtu

            dn = re.search(dn_regex, l3extRsPathL3OutAtt['l3extRsPathL3OutAtt']['attributes']['dn'])

            if dn:
                data.append([dn.group("tenant"), dn.group("l3out"), dn.group("lnodep"),
                             dn.group("lifp"), dn.group("pod"), dn.group("nodes"),
                             dn.group("int"), iftype, addr, mtu])
            else:
                unformatted_data.append(
                    [l3extRsPathL3OutAtt['l3extRsPathL3OutAtt']['attributes']['dn'], iftype, addr, mtu])

    if not data and not unformatted_data:
        result = NA
        msg = 'No L3Out Interfaces found'
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def port_configured_as_l2_check(index, total_checks, **kwargs):
    title = 'L3 Port Config (F0467 port-configured-as-l2)'
    result = FAIL_O
    msg = ''
    headers = ['Fault', 'Tenant', 'L3Out', 'Node', 'Path', 'Recommended Action']
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Recommended Action']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing this config or other configs using this port as L2'
    print_title(title, index, total_checks)

    l2dn_regex = r'uni/tn-(?P<tenant>[^/]+)/out-(?P<l3out>[^/]+)/fd-\[.+rtdOutDef-.+/node-(?P<node>\d{3,4})/(?P<path>.+)/nwissues'
    l2response_json = icurl('class',
                            'faultDelegate.json?&query-target-filter=wcard(faultInst.changeSet,"port-configured-as-l2")')
    for faultDelegate in l2response_json:
        fc = faultDelegate['faultDelegate']['attributes']['code']
        dn = re.search(l2dn_regex, faultDelegate['faultDelegate']['attributes']['dn'])
        if dn:
            data.append([fc, dn.group('tenant'), dn.group('l3out'),
                         dn.group('node'), dn.group('path'),
                         recommended_action])
        else:
            unformatted_data.append(
                [fc, faultDelegate['faultDelegate']['attributes']['dn'], recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def port_configured_as_l3_check(index, total_checks, **kwargs):
    title = 'L2 Port Config (F0467 port-configured-as-l3)'
    result = FAIL_O
    msg = ''
    headers = ['Fault', 'Pod', 'Node', 'Tenant', 'AP', 'EPG', 'Port', 'Recommended Action']
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Recommended Action']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing this config or other configs using this port as L3'
    print_title(title, index, total_checks)

    l3affected_regex = r'topology/(?P<pod>[^/]+)/(?P<node>[^/]+)/.+uni/tn-(?P<tenant>[^/]+)/ap-(?P<ap>[^/]+)/epg-(?P<epg>\w+).+(?P<port>eth\d+/\d+)'
    l3response_json = icurl('class',
                            'faultDelegate.json?&query-target-filter=wcard(faultInst.changeSet,"port-configured-as-l3")')
    for faultDelegate in l3response_json:
        fc = faultDelegate['faultDelegate']['attributes']['code']
        affected_array = re.search(l3affected_regex, faultDelegate['faultDelegate']['attributes']['dn'])

        if affected_array:
            data.append(
                [fc, affected_array.group("pod"), affected_array.group("node"), affected_array.group("tenant"),
                 affected_array.group("ap"), affected_array.group("epg"), affected_array.group("port"),
                 recommended_action])
        else:
            unformatted_data.append(
                [fc, faultDelegate['faultDelegate']['attributes']['dn'], recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def prefix_already_in_use_check(index, total_checks, **kwargs):
    title = 'L3Out Subnets (F0467 prefix-entry-already-in-use)'
    result = FAIL_O
    msg = ''
    headers = ["Fault", "Failed L3Out EPG", "VRF VNID", "VRF Name", "Prefix already in use", 'Recommended Action']
    data = []
    unformatted_headers = ['Fault', 'Fault Description', 'Recommended Action']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing the faulted configuration for the overlapping prefix'
    print_title(title, index, total_checks)

    desc_regex = r'Configuration failed for (?P<failedEpg>.+) due to Prefix Entry Already Used in Another EPG'
    desc_regex += r'(.+Prefix entry sys/ctx-\[vxlan-(?P<vrfvnid>\d+)\]/pfx-\[(?P<prefixInUse>.+)\] is in use)?'

    filter = '?query-target-filter=and(wcard(faultInst.changeSet,"prefix-entry-already-in-use"),wcard(faultInst.dn,"uni/epp/rtd"))'
    faultInsts = icurl('class', 'faultInst.json' + filter)
    if faultInsts:
        vrf_dict = {}
        fv_ctx_response_json = icurl('class', 'fvCtx.json')

        for fvCtx in fv_ctx_response_json:
            vrf_name = fvCtx['fvCtx']['attributes']['name']
            vnid = fvCtx['fvCtx']['attributes']['scope']
            vrf_dict[vnid] = vrf_name

        for faultInst in faultInsts:
            fc = faultInst['faultInst']['attributes']['code']
            desc_array = re.search(desc_regex, faultInst['faultInst']['attributes']['descr'])
            if desc_array:
                if desc_array.group("prefixInUse") is not None:
                    vrf_vnid = desc_array.group("vrfvnid")
                    vrf_name = vrf_dict.get(vrf_vnid, '??')
                    prefix = desc_array.group("prefixInUse")
                else:
                    vrf_vnid = "--"
                    vrf_name = "--"
                    prefix = "Not described in the fault (version too old)"
                data.append([fc, desc_array.group("failedEpg"), vrf_vnid, vrf_name, prefix, recommended_action])
            else:
                unformatted_data.append(
                    [fc, faultInst['faultInst']['attributes']['descr'], recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def encap_already_in_use_check(index, total_checks, **kwargs):
    title = 'Encap Already In Use (F0467 encap-already-in-use)'
    result = FAIL_O
    msg = ''
    headers = ["Faulted EPG/L3Out", "Node", "Port", "In Use Encap(s)", "In Use by EPG/L3Out"]
    data = []
    unformatted_headers = ['Fault Description']
    unformatted_data = []
    recommended_action = 'Resolve the overlapping encap configuration prior to upgrade'
    print_title(title, index, total_checks)

    # <port> can be `ethX/X` or the name of I/F policy group
    # <vlan> is not there for older versions
    desc_regex = r'Configuration failed for (?P<failed>.+) node (?P<node>\d+) (?P<port>.+) due to .* Encap (\(vlan-(?P<vlan>\d+)\) )?is already in use by (?P<inuse>.+);'

    faultInsts = icurl('class',
                       'faultInst.json?query-target-filter=wcard(faultInst.descr,"encap-already-in-use")')
    fvIfConns = []
    for faultInst in faultInsts:
        desc = re.search(desc_regex, faultInst['faultInst']['attributes']['descr'])
        if desc:
            failed_dn = desc.group("failed")
            node_id = desc.group("node")
            port_id = desc.group("port")
            vlan_id = desc.group("vlan")
            inuse_list = desc.group("inuse").split(":")
            if len(inuse_list) == 3:
                inuse_dn = "uni/tn-{0}/ap-{1}/epg-{2}".format(*inuse_list)
            elif len(inuse_list) == 4:
                inuse_dn = "uni/tn-{0}/out-{2}".format(*inuse_list)

            # Get already-in-use encap(s) from fvIfConn when a fault doesn't include encap
            if vlan_id is None:
                faulted_epg_encaps = []
                in_use_epg_encaps = []
                if not fvIfConns:
                    fvIfConns = icurl('class', 'fvIfConn.json')
                for fvIfConn in fvIfConns:
                    dn = fvIfConn['fvIfConn']['attributes']['dn']
                    encap = fvIfConn['fvIfConn']['attributes']['encap']
                    if (failed_dn in dn) and ("node-"+node_id in dn):
                        if encap not in faulted_epg_encaps:
                            faulted_epg_encaps.append(encap)

                    if (inuse_dn in dn) and ("node-"+node_id in dn):
                        if encap not in in_use_epg_encaps:
                            in_use_epg_encaps.append(encap)

                overlapping_encaps = [x for x in in_use_epg_encaps if x in faulted_epg_encaps]
                vlan_id = ",".join(overlapping_encaps)

            data.append([failed_dn, node_id, port_id, vlan_id, inuse_dn])
        else:
            unformatted_data.append([faultInst['faultInst']['attributes']['descr']])

    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data,
                 unformatted_headers, unformatted_data, recommended_action=recommended_action)
    return result


def bd_subnet_overlap_check(index, total_checks, **kwargs):
    title = 'BD Subnets (F1425 subnet-overlap)'
    result = FAIL_O
    msg = ''
    headers = ["Fault", "Pod", "Node", "VRF", "Interface", "Address", "Recommended Action"]
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Recommended Action']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing BD subnets causing the overlap'
    print_title(title, index, total_checks)

    dn_regex = node_regex + r'/.+dom-(?P<vrf>[^/]+)/if-(?P<int>[^/]+)/addr-\[(?P<addr>[^/]+/\d{2})'
    faultInsts = icurl('class', 'faultInst.json?query-target-filter=wcard(faultInst.changeSet,"subnet-overlap")')
    if faultInsts:
        for faultInst in faultInsts:
            fc = faultInst['faultInst']['attributes']['code']
            if fc == "F1425":
                dn_array = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
                if dn_array:
                    data.append([fc, dn_array.group("pod"), dn_array.group("node"), dn_array.group("vrf"),
                                 dn_array.group("int"), dn_array.group("addr"), recommended_action])
                else:
                    unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn'], recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def bd_duplicate_subnet_check(index, total_checks, **kwargs):
    title = 'BD Subnets (F0469 duplicate-subnets-within-ctx)'
    result = FAIL_O
    msg = ''
    headers = ["Fault", "Pod", "Node", "Bridge Domain 1", "Bridge Domain 2", "Recommended Action"]
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Fault Description', 'Recommended Action']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing BD subnets causing the duplicate'
    print_title(title, index, total_checks)

    descr_regex = r'duplicate-subnets-within-ctx: (?P<bd1>.+)\s,(?P<bd2>.+)'
    faultInsts = icurl('class',
                       'faultInst.json?query-target-filter=wcard(faultInst.changeSet,"duplicate-subnets-within-ctx")')
    for faultInst in faultInsts:
        fc = faultInst['faultInst']['attributes']['code']
        dn = re.search(node_regex, faultInst['faultInst']['attributes']['dn'])
        descr = re.search(descr_regex, faultInst['faultInst']['attributes']['descr'])
        if dn and descr:
            data.append([fc, dn.group("pod"), dn.group("node"),
                         descr.group("bd1"), descr.group("bd2"), recommended_action])
        else:
            unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn'],
                                     faultInst['faultInst']['attributes']['descr'],
                                     recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def hw_program_fail_check(index, total_checks, cversion, **kwargs):
    title = 'HW Programming Failure (F3544 L3Out Prefixes, F3545 Contracts, actrl-resource-unavailable)'
    result = FAIL_O
    msg = ''
    headers = ["Fault", "Pod", "Node", "Fault Description", "Recommended Action"]
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Fault Description', 'Recommended Action']
    unformatted_data = []
    recommended_action = {
        'actrlRule': 'Check that "operSt" are set to "enabled". F3545 does not exist on this version.',
        'actrlPfxEntry': 'Check that "operSt" are set to "enabled". F3544 does not exist on this version.',
        'F3544': 'Ensure that LPM and host routes usage are below the capacity and resolve the fault',
        'F3545': 'Ensure that Policy CAM usage is below the capacity and resolve the fault'
    }
    print_title(title, index, total_checks)

    # Faults F3544 and F3545 don't exist until 4.1(1a)+
    if cversion.older_than("4.1(1a)"):
        headers = ["Object Class", "Recommended Action"]
        classes = ["actrlRule", "actrlPfxEntry"]
        result = MANUAL

        for entry in classes:
            data.append([entry, recommended_action.get(entry, "")])
    else:
        faultInsts = icurl('class',
                           'faultInst.json?query-target-filter=or(eq(faultInst.code,"F3544"),eq(faultInst.code,"F3545"))')
        for faultInst in faultInsts:
            fc = faultInst['faultInst']['attributes']['code']
            dn = re.search(node_regex, faultInst['faultInst']['attributes']['dn'])
            if dn:
                data.append([fc, dn.group('pod'), dn.group('node'),
                             faultInst['faultInst']['attributes']['descr'],
                             recommended_action.get(fc, 'Resolve the fault')])
            else:
                unformatted_data.append([
                    fc, faultInst['faultInst']['attributes']['dn'],
                    faultInst['faultInst']['attributes']['descr'],
                    recommended_action.get(fc, 'Resolve the fault')])

        if not data and not unformatted_data:
            result = PASS

    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def switch_ssd_check(index, total_checks, **kwargs):
    title = 'Switch SSD Health (F3073, F3074 equipment-flash-warning)'
    result = FAIL_O
    msg = ''
    headers = ["Fault", "Pod", "Node", "SSD Model", "% Threshold Crossed", "Recommended Action"]
    data = []
    unformatted_headers = ["Fault", "Fault DN", "% Threshold Crossed", "Recommended Action"]
    unformatted_data = []
    thresh = {'F3073': '90%', 'F3074': '80%'}
    recommended_action = {
        'F3073': 'Contact Cisco TAC for replacement procedure',
        'F3074': 'Monitor (no impact to upgrades)'
    }
    print_title(title, index, total_checks)

    cs_regex = r'model \(New: (?P<model>\w+)\),'
    faultInsts = icurl('class',
                       'faultInst.json?query-target-filter=or(eq(faultInst.code,"F3073"),eq(faultInst.code,"F3074"))')
    for faultInst in faultInsts:
        fc = faultInst['faultInst']['attributes']['code']
        dn_array = re.search(node_regex, faultInst['faultInst']['attributes']['dn'])
        cs_array = re.search(cs_regex, faultInst['faultInst']['attributes']['changeSet'])
        if dn_array and cs_array:
            data.append([fc, dn_array.group("pod"), dn_array.group("node"),
                         cs_array.group("model"),
                         thresh.get(fc, ''),
                         recommended_action.get(fc, 'Resolve the fault')])
        else:
            unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn'],
                                     thresh.get(fc, ''),
                                     recommended_action.get(fc, 'Resolve the fault')])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def apic_ssd_check(index, total_checks, cversion, **kwargs):
    title = 'APIC SSD Health'
    result = FAIL_UF
    msg = ''
    headers = ["Pod", "Node", "Storage Unit", "% lifetime remaining", "Recommended Action"]
    data = []
    unformatted_headers = ["Pod", "Node", "Storage Unit", "% lifetime remaining", "Recommended Action"]
    unformatted_data = []
    recommended_action = "Contact TAC for replacement"
    print_title(title, index, total_checks)

    dn_regex = node_regex + r'/.+p-\[(?P<storage>.+)\]-f'
    faultInsts = icurl('class', 'faultInst.json?query-target-filter=eq(faultInst.code,"F2731")')
    adjust_title = False
    if len(faultInsts) == 0 and (cversion.older_than("4.2(7f)") or cversion.older_than("5.2(1g)")):
        print('')
        adjust_title = True
        controller = icurl('class', 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")')
        report_other = False
        if not controller:
            print_result(title, ERROR, 'topSystem response empty. Is the cluster healthy?')
            return ERROR
        else:
            checked_apics = {}
            for apic in controller:
                attr = apic['topSystem']['attributes']
                if attr['address'] in checked_apics: continue
                checked_apics[attr['address']] = 1
                pod_id = attr['podId']
                node_id = attr['id']
                node_title = 'Checking %s...' % attr['name']
                print_title(node_title)
                try:
                    c = Connection(attr['address'])
                    c.username = username
                    c.password = password
                    c.log = LOG_FILE
                    c.connect()
                except Exception as e:
                    data.append([attr['id'], attr['name'], '-', '-', '-', e])
                    print_result(node_title, ERROR)
                    continue
                try:
                    c.cmd(
                        'grep -oE "SSD Wearout Indicator is [0-9]+"  /var/log/dme/log/svc_ifc_ae.bin.log | tail -1')
                except Exception as e:
                    data.append([attr['id'], attr['name'], '-', '-', '-', e])
                    print_result(node_title, ERROR)
                    continue

                wearout_ind = re.search(r'SSD Wearout Indicator is (?P<wearout>[0-9]+)', c.output)
                if wearout_ind is not None:
                    wearout = wearout_ind.group('wearout')
                    if int(wearout) < 5:
                        data.append([pod_id, node_id, "Solid State Disk",
                                     wearout, recommended_action])
                        report_other = True

                        print_result(node_title, DONE)
                        continue
                    if report_other:
                        data.append([pod_id, node_id, "Solid State Disk",
                                     wearout, "No Action Required"])
                print_result(node_title, DONE)
    else:
        headers = ["Fault", "Pod", "Node", "Storage Unit", "% lifetime remaining", "Recommended Action"]
        unformatted_headers = ["Fault", "Fault DN", "% lifetime remaining", "Recommended Action"]
        for faultInst in faultInsts:
            dn_array = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
            lifetime_remaining = "<5%"
            if dn_array:
                data.append(['F2731', dn_array.group("pod"), dn_array.group("node"), dn_array.group("storage"),
                             lifetime_remaining, recommended_action])
            else:
                unformatted_data.append(
                    ['F2731', faultInst['faultInst']['attributes']['dn'], lifetime_remaining, recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data, adjust_title=adjust_title)
    return result


def port_configured_for_apic_check(index, total_checks, **kwargs):
    title = 'Config On APIC Connected Port (F0467 port-configured-for-apic)'
    result = FAIL_UF
    msg = ''
    headers = ["Fault", "Pod", "Node", "Port", "EPG", "Recommended Action"]
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Recommended Action']
    unformatted_data = []
    recommended_action = 'Remove config overlapping with APIC Connected Interfaces'
    print_title(title, index, total_checks)

    dn_regex = node_regex + r'/.+fv-\[(?P<epg>.+)\]/node-\d{3,4}/.+\[(?P<port>eth\d{1,2}/\d{1,2}).+/nwissues'
    faultInsts = icurl('class',
                       'faultInst.json?&query-target-filter=wcard(faultInst.changeSet,"port-configured-for-apic")')
    for faultInst in faultInsts:
        fc = faultInst['faultInst']['attributes']['code']
        dn = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
        if dn:
            data.append([fc, dn.group("pod"), dn.group("node"), dn.group("port"),
                         dn.group("epg"), recommended_action])
        else:
            unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn'], recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def overlapping_vlan_pools_check(index, total_checks, **kwargs):
    title = 'Overlapping VLAN Pools'
    result = FAIL_O
    msg = ''
    headers = ["Tenant", "AP", "EPG", "VLAN Pool (Domain) 1", "VLAN Pool (Domain) 2", "Recommended Action"]
    data = []
    recommended_action = 'Resolve overlapping VLANs between these two VLAN pools'
    doc_url = '"Overlapping VLAN Pool" from from Pre-Upgrade Check Lists'
    print_title(title, index, total_checks)

    infraSetPols = icurl('mo', 'uni/infra/settings.json')
    if infraSetPols[0]['infraSetPol']['attributes'].get('validateOverlappingVlans') == 'true':
        result = PASS
        msg = '`Enforce EPG VLAN Validation` is enabled. No need to check overlapping VLANs'
        print_result(title, result, msg)
        return result

    fvAEPgs_with_fvRsDomAtt = icurl('class',
                                    'fvAEPg.json?rsp-subtree=children&rsp-subtree-class=fvRsDomAtt&rsp-subtree-include=required')
    fvnsVlanInstPs = icurl('class',
                           'fvnsVlanInstP.json?rsp-subtree=children&rsp-subtree-class=fvnsRtVlanNs,fvnsEncapBlk&rsp-subtree-include=required')
    # get VLAN pools per domain
    vpools = {}
    for vlanInstP in fvnsVlanInstPs:
        vpool = {'name': vlanInstP['fvnsVlanInstP']['attributes']['name'], 'encap': []}
        dom_dns = []
        for vlan_child in vlanInstP['fvnsVlanInstP']['children']:
            if vlan_child.get('fvnsRtVlanNs'):
                dom_dns.append(vlan_child['fvnsRtVlanNs']['attributes']['tDn'])
            elif vlan_child.get('fvnsEncapBlk'):
                encap_blk = range(int(vlan_child['fvnsEncapBlk']['attributes']['from'].split('-')[1]),
                                  int(vlan_child['fvnsEncapBlk']['attributes']['to'].split('-')[1]) + 1)
                vpool['encap'] += encap_blk
        for dom_dn in dom_dns:
            dom_regex = r'uni/(vmmp-[^/]+/)?(phys|l2dom|l3dom|dom)-(?P<dom>[^/]+)'
            dom_match = re.search(dom_regex, dom_dn)
            dom_name = '...' if not dom_match else dom_match.group('dom')
            vpools[dom_dn] = dict(vpool, **{'dom_name': dom_name})

    # check VLAN pools if an EPG has multiple domains attached
    for fvAEPg in fvAEPgs_with_fvRsDomAtt:
        overlap_vpools = []
        rsDoms = fvAEPg['fvAEPg']['children']
        for i in range(len(rsDoms)):
            for j in range(i + 1, len(rsDoms)):
                i_dn = rsDoms[i]['fvRsDomAtt']['attributes']['tDn']
                j_dn = rsDoms[j]['fvRsDomAtt']['attributes']['tDn']
                # domains that do not have VLAN pools attached
                if not vpools.get(i_dn) or not vpools.get(j_dn):
                    continue
                if vpools[i_dn]['name'] != vpools[j_dn]['name'] \
                        and set(vpools[i_dn]['encap']).intersection(vpools[j_dn]['encap']):
                    overlap_vpools.append([vpools[i_dn], vpools[j_dn]])

        for overlap in overlap_vpools:
            epg_regex = r'uni/tn-(?P<tenant>[^/]+)/ap-(?P<ap>[^/]+)/epg-(?P<epg>[^/]+)'
            dn = re.search(epg_regex, fvAEPg['fvAEPg']['attributes']['dn'])
            data.append([dn.group('tenant'), dn.group('ap'), dn.group('epg'),
                         '{} ({})'.format(overlap[0]['name'], overlap[0]['dom_name']),
                         '{} ({})'.format(overlap[1]['name'], overlap[1]['dom_name']),
                         recommended_action])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, doc_url=doc_url)
    return result


def vnid_mismatch_check(index, total_checks, **kwargs):
    title = 'VNID Mismatch'
    result = FAIL_O
    msg = ''
    headers = ["EPG", "Access Encap", "Node ID", "Fabric Encap"]
    data = []
    mismatch_hits = []
    recommended_action = 'Remove any domains with overlapping VLAN Pools from above EPGs, then redeploy VLAN'
    doc_url = '"Overlapping VLAN Pool" from Pre-Upgrade Check Lists'
    print_title(title, index, total_checks)

    vlanCktEps = icurl('class', 'vlanCktEp.json?query-target-filter=ne(vlanCktEp.name,"")')
    if not vlanCktEps:
        result = ERROR
        msg = 'Deployed VLANs (vlanCktEp) not found'

    epg_encap_dict = {}
    for vlanCktEp in vlanCktEps:
        dn = re.search(node_regex, vlanCktEp['vlanCktEp']['attributes']['dn'])
        node = dn.group("node")
        access_encap = vlanCktEp['vlanCktEp']['attributes']['encap']
        epg_dn = vlanCktEp['vlanCktEp']['attributes']['epgDn']
        fab_encap = vlanCktEp['vlanCktEp']['attributes']['fabEncap']

        if epg_dn not in epg_encap_dict:
            epg_encap_dict[epg_dn] = {}

        if access_encap not in epg_encap_dict[epg_dn]:
            epg_encap_dict[epg_dn][access_encap] = []

        epg_encap_dict[epg_dn][access_encap].append({'node': node, 'fabEncap': fab_encap})

    # Iterate through, check for overlaps, and print
    for key, epg in iteritems(epg_encap_dict):
        for vlanKey, vlan in iteritems(epg):
            fab_encap_to_check = ""
            for deployment in vlan:
                if fab_encap_to_check == "" or deployment["fabEncap"] == fab_encap_to_check:
                    fab_encap_to_check = deployment["fabEncap"]
                else:  # something is wrong
                    tmp_hit = {}
                    tmp_hit["epgDn"] = key
                    tmp_hit["epgDeployment"] = epg
                    if tmp_hit not in mismatch_hits:  # some epg has more than one access encap.
                        mismatch_hits.append(tmp_hit)
                    break

    if not mismatch_hits:
        result = PASS

    mismatch_hits.sort(key=lambda d: d.get("epgDn", ""))
    for epg in mismatch_hits:
        for access_encap, nodeFabEncaps in iteritems(epg["epgDeployment"]):
            for nodeFabEncap in nodeFabEncaps:
                node_id = nodeFabEncap['node']
                fabric_encap = nodeFabEncap['fabEncap']
                data.append([epg["epgDn"], access_encap, node_id, fabric_encap])

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def scalability_faults_check(index, total_checks, **kwargs):
    title = 'Scalability (faults related to Capacity Dashboard)'
    result = FAIL_O
    msg = ''
    headers = ["Fault", "Pod", "Node", "Description", "Recommended Action"]
    data = []
    unformatted_headers = ["Fault", "Fault DN", "Description", "Recommended Action"]
    unformatted_data = []
    recommended_action = 'Review config and reduce the usage'
    print_title(title, index, total_checks)

    faultInsts = icurl('class', 'eqptcapacityEntity.json?rsp-subtree-include=faults,no-scoped')
    for fault in faultInsts:
        if not fault.get('faultInst'):
            continue
        f = fault['faultInst']['attributes']
        dn = re.search(node_regex, f['dn'])
        if dn:
            data.append([f['code'], dn.group('pod'), dn.group('node'), f['descr'], recommended_action])
        else:
            unformatted_data.append([f['code'], f['dn'], f['descr'], recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def apic_disk_space_faults_check(index, total_checks, cversion, **kwargs):
    title = 'APIC Disk Space Usage (F1527, F1528, F1529 equipment-full)'
    result = FAIL_UF
    msg = ''
    headers = ['Fault', 'Pod', 'Node', 'Mount Point', 'Current Usage %', 'Recommended Action']
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Recommended Action']
    unformatted_data = []
    recommended_action = {
        '/firmware': 'Remove unneeded images',
        '/techsupport': 'Remove unneeded techsupports/cores'
    }
    default_action = 'Contact Cisco TAC.'
    if cversion.same_as('4.0(1h)') or cversion.older_than('3.2(6i)'):
        default_action += ' A typical issue is CSCvn13119.'
    print_title(title, index, total_checks)

    dn_regex = node_regex + r'/.+p-\[(?P<mountpoint>.+)\]-f'
    desc_regex = r'is (?P<usage>\d{2}%) full'

    faultInsts = icurl('class',
                       'faultInst.json?query-target-filter=or(eq(faultInst.code,"F1527"),eq(faultInst.code,"F1528"),eq(faultInst.code,"F1529"))')
    for faultInst in faultInsts:
        fc = faultInst['faultInst']['attributes']['code']
        dn = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
        desc = re.search(desc_regex, faultInst['faultInst']['attributes']['descr'])
        if dn and desc:
            data.append([fc, dn.group('pod'), dn.group('node'), dn.group('mountpoint'),
                         desc.group('usage'),
                         recommended_action.get(dn.group('mountpoint'), default_action)])
        else:
            unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn'], default_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def l3out_route_map_direction_check(index, total_checks, **kwargs):
    """ Implementation change due to CSCvm75395 - 4.1(1) """
    title = 'L3Out Route Map import/export direction'
    result = FAIL_O
    msg = ''
    headers = ["Tenant", "L3Out", "External EPG", "Subnet", "Subnet Scope",
               "Route Map", "Direction", "Recommended Action", ]
    data = []
    recommended_action = 'The subnet scope must have {}-rtctrl'
    print_title(title, index, total_checks)

    dn_regex = r'uni/tn-(?P<tenant>[^/]+)/out-(?P<l3out>[^/]+)/instP-(?P<epg>[^/]+)/extsubnet-\[(?P<subnet>[^\]]+)\]'
    l3extSubnets = icurl('class',
                         'l3extSubnet.json?rsp-subtree=children&rsp-subtree-class=l3extRsSubnetToProfile&rsp-subtree-include=required')
    for l3extSubnet in l3extSubnets:
        dn = re.search(dn_regex, l3extSubnet['l3extSubnet']['attributes']['dn'])
        subnet_scope = l3extSubnet['l3extSubnet']['attributes']['scope']
        basic = [dn.group('tenant'), dn.group('l3out'), dn.group('epg'), dn.group('subnet'), subnet_scope]
        for child in l3extSubnet['l3extSubnet']['children']:
            dir = child['l3extRsSubnetToProfile']['attributes']['direction']
            rmap = child['l3extRsSubnetToProfile']['attributes']['tnRtctrlProfileName']
            if ((dir == 'export' and 'export-rtctrl' not in subnet_scope) or
                    (dir == 'import' and 'import-rtctrl' not in subnet_scope)):
                data.append(basic + [rmap, dir, recommended_action.format(dir)])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data)
    return result


def l3out_route_map_missing_target_check(index, total_checks, cversion, tversion, **kwargs):
    """ Implementation change due to CSCwc11570 - 5.2.8/6.0.2 """
    title = 'L3Out Route Map Match Rule with missing-target'
    result = FAIL_O
    msg = ''
    headers = ['Tenant', 'L3Out', 'Route Map', 'Context', 'Action', 'Match Rule']
    data = []
    recommended_action = 'The configured match rules do not exist. Update the route maps with existing match rules.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l3out-route-map-match-rule-with-missing-target'
    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, "Target version not supplied. Skipping.")
        return MANUAL

    def is_old(v):
        return True if v.older_than("5.2(8a)") or v.simple_version == "6.0(1)" else False

    c_is_old = is_old(cversion)
    t_is_old = is_old(tversion)
    if (c_is_old and t_is_old) or (not c_is_old and not t_is_old):
        print_result(title, NA)
        return NA

    dn_regex = r'uni/tn-(?P<tenant>[^/]+)/out-(?P<l3out>[^/]+)/'
    # Get a missing-target match rule in a route map with type `combinable`
    api = 'rtctrlProfile.json'
    api += '?query-target-filter=eq(rtctrlProfile.type,"combinable")'
    api += '&rsp-subtree=full&rsp-subtree-filter=eq(rtctrlRsCtxPToSubjP.state,"missing-target")'
    profiles = icurl('class', api)
    for profile in profiles:
        dn = re.search(dn_regex, profile['rtctrlProfile']['attributes']['dn'])
        for ctxP in profile['rtctrlProfile'].get('children', []):
            if not ctxP.get('rtctrlCtxP'):
                continue
            for rsCtxPToSubjP in ctxP['rtctrlCtxP'].get('children', []):
                if (
                    rsCtxPToSubjP.get('rtctrlRsCtxPToSubjP')
                    and rsCtxPToSubjP['rtctrlRsCtxPToSubjP']['attributes']['state'] == 'missing-target'
                ):
                    data.append([
                        dn.group('tenant'),
                        dn.group('l3out'),
                        profile['rtctrlProfile']['attributes']['name'],
                        ctxP['rtctrlCtxP']['attributes']['name'],
                        ctxP['rtctrlCtxP']['attributes']['action'],
                        rsCtxPToSubjP['rtctrlRsCtxPToSubjP']['attributes']['tnRtctrlSubjPName'],
                    ])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def l3out_overlapping_loopback_check(index, total_checks, **kwargs):
    title = 'L3Out Loopback IP Overlap With L3Out Interfaces'
    result = FAIL_O
    msg = ''
    headers = ['Tenant:VRF', 'Node ID', 'Loopback IP (Tenant:L3Out:NodeP)', 'Interface IP (Tenant:L3Out:NodeP:IFP)']
    data = []
    recommended_action = 'Change either the loopback or L3Out interface IP subnet to avoid overlap.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l3out-loopback-ip-overlap-with-l3out-interfaces'
    print_title(title, index, total_checks)

    tn_regex = r'uni/tn-(?P<tenant>[^/]+)/'
    path_regex = r'topology/pod-(?P<pod>\d+)/(?:prot)?paths-(?P<node1>\d+)(?:-(?P<node2>\d+))?'

    vrfs = defaultdict(dict)
    api = 'l3extOut.json'
    api += '?rsp-subtree=full'
    api += '&rsp-subtree-class=l3extRsEctx,l3extRsNodeL3OutAtt,l3extLoopBackIfP,l3extRsPathL3OutAtt,l3extMember'
    l3outs = icurl('class', api)
    for l3out in l3outs:
        vrf = ""
        loopback_ips = defaultdict(dict)
        interface_ips = defaultdict(list)
        for child in l3out['l3extOut'].get('children', []):
            dn = re.search(tn_regex, l3out['l3extOut']['attributes']['dn'])
            tenant_name = dn.group('tenant') if dn else ""
            l3out_name = l3out['l3extOut']['attributes']['name']
            # Get VRF
            if child.get('l3extRsEctx'):
                vrf_tdn = re.search(tn_regex, child['l3extRsEctx']['attributes']['tDn'])
                if vrf_tdn:
                    vrf = ':'.join([vrf_tdn.group('tenant'), child['l3extRsEctx']['attributes']['tnFvCtxName']])
                else:
                    vrf = child['l3extRsEctx']['attributes']['tDn']
            # Get loopback and interface IPs
            elif child.get('l3extLNodeP'):
                nodep_name = child['l3extLNodeP']['attributes']['name']
                for np_child in child['l3extLNodeP'].get('children', []):
                    # Get the loopback IP for each node
                    if np_child.get('l3extRsNodeL3OutAtt'):
                        node = np_child['l3extRsNodeL3OutAtt']
                        m = re.search(node_regex, node['attributes']['tDn'])
                        if not m:
                            logging.error('Failed to parse tDn - %s', node['attributes']['tDn'])
                            continue
                        node_id = m.group('node')

                        loopback_ip = ''
                        if node['attributes']['rtrIdLoopBack'] == 'yes':
                            loopback_ip = node['attributes']['rtrId']
                        else:
                            for lb in node.get('children', []):
                                # There should be only one l3extLoopBackIfP per node
                                if lb.get('l3extLoopBackIfP'):
                                    loopback_ip = lb['l3extLoopBackIfP']['attributes']['addr']
                                    break
                        if loopback_ip:
                            loopback_ips[node_id] = {
                                'addr': loopback_ip,
                                'config': ':'.join([tenant_name, l3out_name, nodep_name]),
                            }
                    # Get interface IPs for each node
                    elif np_child.get('l3extLIfP'):
                        ifp_name = np_child['l3extLIfP']['attributes']['name']
                        for ifp_child in np_child['l3extLIfP'].get('children', []):
                            if not ifp_child.get('l3extRsPathL3OutAtt'):
                                continue
                            port = ifp_child['l3extRsPathL3OutAtt']
                            m = re.search(path_regex, port['attributes']['tDn'])
                            if not m:
                                logging.error('Failed to parse tDn - %s', port['attributes']['tDn'])
                                continue
                            node1_id = m.group('node1')
                            node2_id = m.group('node2')
                            config = ':'.join([tenant_name, l3out_name, nodep_name, ifp_name])
                            # non-vPC port
                            if not node2_id:
                                interface_ips[node1_id].append({
                                    'addr': port['attributes']['addr'],
                                    'config': config,
                                })
                            # vPC port
                            else:
                                for member in port.get('children', []):
                                    if not member.get('l3extMember'):
                                        continue
                                    node_id = node1_id
                                    if member['l3extMember']['attributes']['side'] == 'B':
                                        node_id = node2_id
                                    interface_ips[node_id].append({
                                        'addr': member['l3extMember']['attributes']['addr'],
                                        'config': config,
                                    })
        for node in loopback_ips:
            if not vrfs[vrf].get(node):
                vrfs[vrf][node] = {}
            vrfs[vrf][node]['loopback'] = loopback_ips[node]
        for node in interface_ips:
            if not vrfs[vrf].get(node):
                vrfs[vrf][node] = {}
            vrfs[vrf][node]['interfaces'] = vrfs[vrf][node].get('interfaces', []) + interface_ips[node]

    # Check overlaps
    for vrf in vrfs:
        for node in vrfs[vrf]:
            loopback = vrfs[vrf][node].get('loopback')
            interfaces = vrfs[vrf][node].get('interfaces')
            if not loopback or not interfaces:
                continue
            for interface in interfaces:
                if IPAddress.ip_in_subnet(loopback['addr'], interface['addr']):
                    data.append([
                        vrf,
                        node,
                        '{} ({})'.format(loopback['addr'], loopback['config']),
                        '{} ({})'.format(interface['addr'], interface['config']),
                    ])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def bgp_peer_loopback_check(index, total_checks, **kwargs):
    """ Implementation change due to CSCvm28482 - 4.1(2) """
    title = 'BGP Peer Profile at node level without Loopback'
    result = FAIL_O
    msg = ''
    headers = ["Tenant", "L3Out", "Node Profile", "Pod", "Node", "Recommended Action"]
    data = []
    recommended_action = 'Configure a loopback or configure bgpPeerP under interfaces instead of nodes'
    print_title(title, index, total_checks)

    name_regex = r'uni/tn-(?P<tenant>[^/]+)/out-(?P<l3out>[^/]+)/lnodep-(?P<nodep>[^/]+)'
    l3extLNodePs = icurl('class',
                         'l3extLNodeP.json?rsp-subtree=full&rsp-subtree-class=bgpPeerP,l3extRsNodeL3OutAtt,l3extLoopBackIfP')
    for l3extLNodeP in l3extLNodePs:
        if not l3extLNodeP['l3extLNodeP'].get('children'):
            continue
        # if the node profile has no bgpPeerP, no need to check loopbacks
        bgpPeerPs = [x for x in l3extLNodeP['l3extLNodeP']['children'] if x.get('bgpPeerP')]
        if not bgpPeerPs:
            continue
        for l3extLNodeP_child in l3extLNodeP['l3extLNodeP']['children']:
            if not l3extLNodeP_child.get('l3extRsNodeL3OutAtt'):
                continue
            if l3extLNodeP_child['l3extRsNodeL3OutAtt']['attributes']['rtrIdLoopBack'] == 'yes':
                continue
            if l3extLNodeP_child['l3extRsNodeL3OutAtt'].get('children'):
                for rsnode_child in l3extLNodeP_child['l3extRsNodeL3OutAtt']['children']:
                    if rsnode_child.get('l3extLoopBackIfP'):
                        break
                else:
                    # No loopbacks are configured for this node even though it has bgpPeerP
                    name = re.search(name_regex, l3extLNodeP['l3extLNodeP']['attributes']['dn'])
                    dn = re.search(node_regex, l3extLNodeP_child['l3extRsNodeL3OutAtt']['attributes']['tDn'])
                    data.append([
                        name.group('tenant'), name.group('l3out'), name.group('nodep'),
                        dn.group('pod'), dn.group('node'), recommended_action])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data)
    return result


def lldp_with_infra_vlan_mismatch_check(index, total_checks, **kwargs):
    title = 'Different infra VLAN via LLDP (F0454 infra-vlan-mismatch)'
    result = FAIL_O
    msg = ''
    headers = ["Fault", "Pod", "Node", "Port", "Recommended Action"]
    data = []
    unformatted_headers = ["Fault", "Fault DN", "Failure Reason"]
    unformatted_data = []
    recommended_action = 'Disable LLDP on this port if it is expected to receive LLDP with a mismatched infra VLAN'
    print_title(title, index, total_checks)

    dn_regex = node_regex + r'/sys/lldp/inst/if-\[(?P<port>eth\d{1,2}/\d{1,2})\]/fault-F0454'
    faultInsts = icurl('class',
                       'faultInst.json?query-target-filter=and(eq(faultInst.code,"F0454"),wcard(faultInst.changeSet,"infra-vlan-mismatch"))')
    for faultInst in faultInsts:
        fc = faultInst['faultInst']['attributes']['code']
        dn = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
        if dn:
            data.append([fc, dn.group("pod"), dn.group("node"), dn.group("port"), recommended_action])
        else:
            unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn'], recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def apic_version_md5_check(index, total_checks, tversion, username, password, **kwargs):
    title = 'APIC Target version image and MD5 hash'
    result = FAIL_UF
    msg = ''
    headers = ['APIC', 'Firmware', 'md5sum', 'Failure', 'Recommended Action']
    data = []
    recommended_action = 'Delete the firmware from APIC and re-download'
    print_title(title, index, total_checks)
    if not tversion:
        print_result(title, MANUAL, 'Target version not supplied. Skipping.')
        return MANUAL
    prints('')

    image_validaton = True
    mo = icurl('mo', 'fwrepo/fw-aci-apic-dk9.%s.json' % tversion.dot_version)
    for fm_mo in mo:
        if fm_mo.get("firmwareFirmware"):
            desc = fm_mo["firmwareFirmware"]['attributes']["description"]
            md5 = fm_mo["firmwareFirmware"]['attributes']["checksum"]
            if "Image signing verification failed" in desc:
                data.append(["All", tversion, md5,
                             'Target image is corrupted', 'Delete and Upload Again'])
                image_validaton = False

    md5s = []
    md5_names = []

    if image_validaton:
        nodes_response_json = icurl('class', 'topSystem.json')
        for node in nodes_response_json:
            if node['topSystem']['attributes']['role'] != "controller":
                continue
            apic_name = node['topSystem']['attributes']['name']
            node_title = 'Checking %s...' % apic_name
            print_title(node_title)
            try:
                c = Connection(node['topSystem']['attributes']['address'])
                c.username = username
                c.password = password
                c.log = LOG_FILE
                c.connect()
            except Exception as e:
                data.append([apic_name, '-', '-', e, '-'])
                print_result(node_title, ERROR)
                continue

            try:
                c.cmd("ls -aslh /firmware/fwrepos/fwrepo/aci-apic-dk9.%s.bin" %
                      tversion.dot_version)
            except Exception as e:
                data.append([apic_name, '-', '-',
                             'ls command via ssh failed due to:{}'.format(e), '-'])
                print_result(node_title, ERROR)
                continue
            if "No such file or directory" in c.output:
                data.append([apic_name, str(tversion), '-', 'image not found', recommended_action])
                print_result(node_title, FAIL_UF)
                continue

            try:
                c.cmd("cat /firmware/fwrepos/fwrepo/md5sum/aci-apic-dk9.%s.bin" %
                      tversion.dot_version)
            except Exception as e:
                data.append([apic_name, str(tversion), '-',
                             'failed to check md5sum via ssh due to:{}'.format(e), '-'])
                print_result(node_title, ERROR)
                continue
            for line in c.output.split("\n"):
                if "md5sum" not in line and "fwrepo" in line:
                    md5_regex = r'([^\s]+)'
                    md5 = re.search(md5_regex, line)
                    if md5 is not None:
                        md5s.append(md5.group(0))
                        md5_names.append(c.hostname)
            print_result(node_title, DONE)
    if len(set(md5s)) > 1:
        for name, md5 in zip(md5_names, md5s):
            data.append([name, str(tversion), md5, 'md5sum do not match on all APICs', recommended_action])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, adjust_title=True)
    return result


def standby_apic_disk_space_check(index, total_checks, **kwargs):
    title = 'Standby APIC Disk Space Usage'
    result = FAIL_UF
    msg = ''
    headers = ['SN', 'OOB', 'Mount Point', 'Current Usage %', 'Recommended Action']
    data = []
    recommended_action = 'Contact Cisco TAC'
    threshold = 75  # usage (%)
    print_title(title, index, total_checks)

    checked_stby = []
    infraSnNodes = icurl('class', 'infraSnNode.json?query-target-filter=eq(infraSnNode.cntrlSbstState,"approved")')
    for stby_apic in infraSnNodes:
        stb = stby_apic['infraSnNode']['attributes']
        if stb['addr'] in checked_stby:
            continue
        checked_stby.append(stb['addr'])
        try:
            c = Connection(stb['addr'])
            c.username = "rescue-user"
            c.log = LOG_FILE
            c.connect()
        except Exception as e:
            data.append([stb['mbSn'], stb['oobIpAddr'], '-', '-', e])
            continue

        try:
            c.cmd("df -h")
        except Exception as e:
            data.append([stb['mbSn'], stb['oobIpAddr'], '-', '-', e])
            continue

        for line in c.output.split("\n"):
            if "Filesystem" not in line and "df" not in line:
                fs_regex = r'([^\s]+) +([^\s]+) +([^\s]+) +([^\s]+) +([^\s]+)%'
                fs = re.search(fs_regex, line)
                if fs is not None:
                    directory = fs.group(1)
                    usage = fs.group(5)
                    if int(usage) >= threshold:
                        data.append([stb['mbSn'], stb['oobIpAddr'], directory, usage, recommended_action])
    if not infraSnNodes:
        result = NA
        msg = 'No standby APIC found'
    elif not data:
        result = PASS
        msg = 'all below {}%'.format(threshold)
    print_result(title, result, msg, headers, data)
    return result


def r_leaf_compatibility_check(index, total_checks, tversion, **kwargs):
    title = 'Remote Leaf Compatibility'
    result = PASS
    msg = ''
    headers = ['Target Version', 'Remote Leaf', 'Direct Traffic Forwarding', 'Recommended Action']
    data = []
    recommended_action_4_2_2 = 'Upgrade remote leaf nodes before spine nodes or\ndisable Direct Traffic Forwarding (CSCvs16767)'
    recommended_action_5a = 'Direct Traffic Forwarding is required on 5.0 or later. Enable the feature before the upgrade'
    recommended_action_5b = ('Direct Traffic Forwarding is required on 5.0 or later.\n'
                             'Upgrade to 4.1(2)-4.2(x) first to enable the feature before upgrading to 5.0 or later.')
    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, 'Target version not supplied. Skipping.')
        return MANUAL

    remote_leafs = icurl('class', 'fabricNode.json?&query-target-filter=eq(fabricNode.nodeType,"remote-leaf-wan")')
    if not remote_leafs:
        result = NA
        msg = 'No Remote Leaf Found'
    else:
        infraSetPols = icurl('mo', 'uni/infra/settings.json')
        direct = infraSetPols[0]['infraSetPol']['attributes'].get('enableRemoteLeafDirect')
        direct_enabled = 'Not Supported'
        if direct:
            direct_enabled = direct == 'yes'

        ra = ''
        if tversion.simple_version == "4.2(2)" and direct_enabled is True:
            ra = recommended_action_4_2_2
        elif int(tversion.major1) >= 5 and direct_enabled is False:
            ra = recommended_action_5a
        elif int(tversion.major1) >= 5 and direct_enabled == 'Not Supported':
            ra = recommended_action_5b
        if ra:
            result = FAIL_O
            data.append([str(tversion), "Present", direct_enabled, ra])
    print_result(title, result, msg, headers, data)
    return result


def ep_announce_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'EP Announce Compatibility'
    result = PASS
    msg = ''
    headers = ['Susceptible Defect', 'Recommended Action']
    data = []
    recommended_action = ('For fabrics running a pre-12.2(4p) ACI switch release, '
                          'upgrade to 12.2(4r) and then upgrade to the desired destination release.\n'
                          'For fabrics running a 12.3(1) ACI switch release, '
                          'upgrade to 13.1(2v) and then upgrade to the desired destination release.')
    print_title(title, index, total_checks)

    fixed_versions = ["2.2(4p)", "2.2(4q)", "2.2(4r)"]
    current_version_affected = False
    target_version_affected = False

    if not tversion:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'
    else:
        if cversion.version not in fixed_versions and int(cversion.major1) < 3:
            current_version_affected = True

        if tversion.major1 == "3":
            if int(tversion.major2) >= 2 and int(tversion.maint) >= 2:
                target_version_affected = True
        elif int(tversion.major1) >= 4:
            target_version_affected = True

        if current_version_affected and target_version_affected:
            result = FAIL_O
            data.append(['CSCvi76161', recommended_action])
    print_result(title, result, msg, headers, data)
    return result


def vmm_controller_status_check(index, total_checks, **kwargs):
    title = 'VMM Domain Controller Status'
    result = PASS
    msg = ''
    headers = ['VMM Domain', 'vCenter IP or Hostname', 'Current State', 'Recommended Action']
    data = []
    recommended_action = 'Check network connectivity to the vCenter.'
    print_title(title, index, total_checks)

    vmmDoms = icurl('class', 'compCtrlr.json')
    if not vmmDoms:
        result = NA
        msg = 'No VMM Domains Found'
    else:
        for dom in vmmDoms:
            if dom['compCtrlr']['attributes']['operSt'] == "offline":
                domName = dom['compCtrlr']['attributes']['domName']
                hostOrIp = dom['compCtrlr']['attributes']['hostOrIp']
                result = FAIL_O
                data.append([domName, hostOrIp, "offline", recommended_action])

    print_result(title, result, msg, headers, data)
    return result


def vmm_controller_adj_check(index, total_checks, **kwargs):
    title = 'VMM Domain LLDP/CDP Adjacency Status'
    result = PASS
    msg = ''
    headers = ['VMM Domain', 'Host IP or Hostname', 'Recommended Action']
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Recommended Action']
    unformatted_data = []

    recommended_action = 'Ensure consistent use of expected Discovery Protocol from Hypervisor to ACI Leaf.'
    print_title(title, index, total_checks)

    adjFaults = icurl('class', 'faultInst.json?query-target-filter=eq(faultInst.code,"F606391")')
    adj_regex = r'adapters on the host: (?P<host>[^\(]+)'
    dom_reg = r'comp\/prov-VMware\/ctrlr-\[(?P<dom>.+)\]'
    if not adjFaults:
        msg = 'No LLDP/CDP Adjacency Failed Faults Found'
    else:
        for adj in adjFaults:
            if adj['faultInst']['attributes']['severity'] != "cleared":
                if "prov-VMware" in adj['faultInst']['attributes']['dn']:
                    r1 = re.search(adj_regex, adj['faultInst']['attributes']['descr'])
                    r2 = re.search(dom_reg, adj['faultInst']['attributes']['dn'])
                    if r1 and r2:
                        host = r1.group("host")
                        dom = r2.group("dom")
                        result = FAIL_O
                        data.append([dom, host, recommended_action])
                    else:
                        unformatted_data.append(
                            [adj['faultInst']['attributes']['code'], adj['faultInst']['attributes']['dn'],
                             recommended_action])

    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
    return result


def vpc_paired_switches_check(index, total_checks, vpc_node_ids=None, **kwargs):
    title = 'VPC-paired Leaf switches'
    result = FAIL_O
    msg = ''
    headers = ["Node ID", "Node Name", "Recommended Action"]
    data = []
    recommended_action = 'Determine if dataplane redundancy is available if this node goes down'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#vpc-paired-leaf-switches'
    print_title(title, index, total_checks)

    if not vpc_node_ids:
        msg = 'No VPC definitions found!'
        vpc_node_ids = []

    top_system = icurl('class', 'topSystem.json')

    for node in top_system:
        node_id = node['topSystem']['attributes']['id']
        role = node['topSystem']['attributes']['role']
        if role == 'leaf' and (node_id not in vpc_node_ids):
            result = MANUAL
            name = node['topSystem']['attributes']['name']
            data.append([node_id, name, recommended_action])

    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, doc_url=doc_url)
    return result


def cimc_compatibilty_check(index, total_checks, tversion, **kwargs):
    title = 'APIC CIMC Compatibility'
    result = FAIL_UF
    msg = ''
    headers = ["Node ID", "Model", "Current CIMC version", "Catalog Recommended CIMC Version", "Warning"]
    data = []
    recommended_action = 'Check Release note of APIC Model/version for latest recommendations.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#compatibility-cimc-version'
    print_title(title, index, total_checks)
    apic_obj = icurl('class', 'eqptCh.json?query-target-filter=wcard(eqptCh.descr,"APIC")')
    if apic_obj and tversion:
        try:
            for eqptCh in apic_obj:
                if eqptCh['eqptCh']['attributes']['cimcVersion']:
                    apic_model = eqptCh['eqptCh']['attributes']['descr']
                    model = "apic" + apic_model.split('-')[2].lower()
                    current_cimc = eqptCh['eqptCh']['attributes']['cimcVersion']
                    compat_lookup_dn = "uni/fabric/compcat-default/ctlrfw-apic-" + tversion.simple_version + \
                                       "/rssuppHw-[uni/fabric/compcat-default/ctlrhw-" + model + "].json"
                    compatMo = icurl('mo', compat_lookup_dn)
                    recommended_cimc = compatMo[0]['compatRsSuppHw']['attributes']['cimcVersion']
                    warning = ""
                    if compatMo and recommended_cimc:
                        if not is_firstver_gt_secondver(current_cimc, "3.0(3a)"):
                            warning = "Multi-step Upgrade may be required, check UCS CIMC Matrix."
                        if not is_firstver_gt_secondver(current_cimc, recommended_cimc):
                            nodeid = eqptCh['eqptCh']['attributes']['dn'].split('/')[2]
                            data.append([nodeid, apic_model, current_cimc, recommended_cimc, warning])

            if not data:
                result = PASS

        except KeyError:
            result = MANUAL
            msg = 'eqptCh does not have cimcVersion parameter on this version'
    else:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def intersight_upgrade_status_check(index, total_checks, **kwargs):
    title = 'Intersight Device Connector upgrade status'
    result = FAIL_UF
    msg = ''
    headers = ["Connector Status", "Recommended Action"]
    data = []
    recommended_action = 'Wait a few minutes for the upgrade to complete'
    doc_url = '"Intersight Device Connector is upgrading" in Pre-Upgrade Check Lists'
    print_title(title, index, total_checks)

    cmd = ['icurl', '-gks', 'https://127.0.0.1/connector/UpgradeStatus']

    logging.info('cmd = ' + ' '.join(cmd))
    response = subprocess.check_output(cmd)
    try:
        resp_json = json.loads(response)

        try:
            if resp_json[0]['Status'] != 'Idle':
                data.append([resp_json[0]['UpgradeNotification'], recommended_action])
        except KeyError:
            if resp_json['code'] == 'InternalServerError':
                msg = 'Connector reporting InternalServerError, Non-Upgrade issue'

        if not data:
            result = PASS

    except ValueError:
        result = NA
        msg = 'Intersight Device Connector not responding'

    print_result(title, result, msg, headers, data, doc_url=doc_url)
    return result


def isis_redis_metric_mpod_msite_check(index, total_checks, **kwargs):
    title = 'ISIS Redistribution metric for MPod/MSite'
    result = FAIL_O
    msg = ''
    headers = ["ISIS Redistribution Metric", "MPod Deployment", "MSite Deployment", "Recommendation"]
    data = []
    recommended_action = None
    doc_url = '"ISIS Redistribution Metric" from ACI Best Practices Quick Summary - http://cs.co/9001zNNr7'
    print_title(title, index, total_checks)

    isis_mo = icurl('mo', 'uni/fabric/isisDomP-default.json')
    redistribMetric = isis_mo[0]['isisDomPol']['attributes'].get('redistribMetric')

    msite = False
    mpod = False

    if not redistribMetric:
        recommended_action = 'Upgrade to 2.2(4f)+ or 3.0(1k)+ to support configurable ISIS Redistribution Metric'
    else:
        if int(redistribMetric) >= 63:
            recommended_action = 'Change ISIS Redistribution Metric to less than 63'

    if recommended_action:
        mpod_msite_mo = icurl('class', 'fvFabricExtConnP.json?query-target=children')
        if mpod_msite_mo:
            pods_list = []

            for mo in mpod_msite_mo:
                if mo.get('fvSiteConnP'):
                    msite = True
                elif mo.get('fvPodConnP'):
                    podid = mo['fvPodConnP']['attributes'].get('id')
                    if podid and podid not in pods_list:
                        pods_list.append(podid)
            mpod = (len(pods_list) > 1)
    if mpod or msite:
        data.append([redistribMetric, mpod, msite, recommended_action])
    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, doc_url=doc_url)
    return result


def bgp_golf_route_target_type_check(index, total_checks, cversion=None, tversion=None, **kwargs):
    title = 'BGP route target type for GOLF over L2EVPN'
    result = FAIL_O
    msg = ''
    headers = ["VRF DN", "Global Name", "Route Target", "Recommendation"]
    data = []
    recommended_action = "Reconfigure extended: RT with prefix route-target: "
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvm23100'
    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, 'Target version not supplied. Skipping.')
        return MANUAL

    if cversion.older_than("4.2(1a)") and tversion.newer_than("4.2(1a)"):
        fvctx_mo = icurl('class', 'fvCtx.json?rsp-subtree=full&rsp-subtree-class=l3extGlobalCtxName,bgpRtTarget&rsp-subtree-include=required')

        if fvctx_mo:
            for vrf in fvctx_mo:
                globalname = ''
                vrfdn = vrf['fvCtx']['attributes']['dn']
                for child in vrf['fvCtx']['children']:
                    if child.get('l3extGlobalCtxName'):
                        globalname = child['l3extGlobalCtxName']['attributes'].get('name')
                if globalname != '':
                    for child in vrf['fvCtx']['children']:
                        if child.get('bgpRtTargetP'):
                            for bgprt in child['bgpRtTargetP']['children']:
                                if bgprt.get('bgpRtTarget') and not bgprt['bgpRtTarget']['attributes']['rt'].startswith('route-target:'):
                                    data.append([vrfdn, globalname, bgprt['bgpRtTarget']['attributes']['rt'], recommended_action])

    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, doc_url=doc_url)
    return result


def docker0_subnet_overlap_check(index, total_checks, **kwargs):
    title = 'APIC Container Bridge IP Overlap with APIC TEP'
    result = PASS
    msg = ''
    headers = ["Container Bridge IP", "APIC TEP", "Recommended Action"]
    data = []
    recommended_action = 'Change the container bridge IP via "Apps > Settings" on the APIC GUI'
    print_title(title, index, total_checks)

    containerPols = icurl('mo', 'pluginPolContr/ContainerPol.json')
    if not containerPols:
        bip = "172.17.0.1/16"
    else:
        bip = containerPols[0]["apContainerPol"]["attributes"]["containerBip"]

    teps = []
    infraWiNodes = icurl('class', 'infraWiNode.json')
    for infraWiNode in infraWiNodes:
        if infraWiNode["infraWiNode"]["attributes"]["addr"] not in teps:
            teps.append(infraWiNode["infraWiNode"]["attributes"]["addr"])

    for tep in teps:
        if IPAddress.ip_in_subnet(tep, bip):
            result = FAIL_UF
            data.append([tep, bip, recommended_action])

    print_result(title, result, msg, headers, data)
    return result


def eventmgr_db_defect_check(index, total_checks, cversion, **kwargs):
    title = 'Eventmgr DB size defect susceptibility'
    result = PASS
    msg = ''
    headers = ["Potential Defect", "Doc URL"]
    data = []
    recommended_action = 'Contact Cisco TAC to check the DB size via root'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#eventmgr-db-size-defect-susceptibility'
    print_title(title, index, total_checks)

    if cversion.older_than('3.2(5d)') or (cversion.major1 == '4' and cversion.older_than('4.1(1i)')): 
        data.append(['CSCvn20175', 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvn20175'])
    if cversion.older_than('4.2(4i)') or (cversion.major1 == '5' and cversion.older_than('5.0(1k)')):  
        data.append(['CSCvt07565', 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvt07565'])

    if data:
        result = FAIL_UF

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def target_version_compatibility_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Target version compatibility'
    result = FAIL_UF
    msg = ''
    headers = ["Current version", "Target Version", "Warning"]
    data = []
    recommended_action = ''
    doc_url = 'APIC Upgrade/Downgrade Support Matrix - http://cs.co/9005ydMQP'
    print_title(title, index, total_checks)
    if not tversion:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'
    else:
        if cversion.simple_version != tversion.simple_version:
            compatRsUpgRelString = "uni/fabric/compcat-default/ctlrfw-apic-" + cversion.simple_version + \
                                   "/rsupgRel-[uni/fabric/compcat-default/ctlrfw-apic-" + tversion.simple_version + "].json"
            compatRsUpgRel = icurl('mo', compatRsUpgRelString)
            if not compatRsUpgRel:
                compatRtUpgRelString = "uni/fabric/compcat-default/ctlrfw-apic-" + cversion.simple_version + \
                                       "/rtupgRel-[uni/fabric/compcat-default/ctlrfw-apic-" + tversion.simple_version + "].json"
                compatRtUpgRel = icurl('mo', compatRtUpgRelString)
                if not compatRtUpgRel:
                    data.append([str(cversion), str(tversion), 'Target version not a supported hop'])

        if not data:
            result = PASS

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def gen1_switch_compatibility_check(index, total_checks, tversion, **kwargs):
    title = 'Gen 1 switch compatibility'
    result = FAIL_UF
    msg = ''
    headers = ["Target Version", "Node ID", "Model", "Warning"]
    gen1_models = ["N9K-C9336PQ", "N9K-X9736PQ", "N9K-C9504-FM", "N9K-C9508-FM", "N9K-C9516-FM", "N9K-C9372PX-E",
                   "N9K-C9372TX-E", "N9K-C9332PQ", "N9K-C9372PX", "N9K-C9372TX", "N9K-C9396PX", "N9K-C9396TX",
                   "N9K-C93128TX"]
    data = []
    recommended_action = 'Select supported target version or upgrade hardware'
    doc_url = 'ACI 5.0(1) Switch Release Notes - http://cs.co/9001ydKCV'
    print_title(title, index, total_checks)
    if not tversion:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'
    else:
        if tversion.newer_than("5.0(1a)"):
            fabric_node = icurl('class', 'fabricNode.json')
            for node in fabric_node:
                if node['fabricNode']['attributes']['model'] in gen1_models:
                    data.append([str(tversion), node['fabricNode']['attributes']['id'],
                                 node['fabricNode']['attributes']['model'], 'Not supported on 5.x+'])

        if not data:
            result = PASS

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def contract_22_defect_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Contract Port 22 Defect'
    result = PASS
    msg = ''
    headers = ["Potential Defect", "Reason"]
    data = []
    recommended_action = 'Review Software Advisory for details'
    doc_url = 'Cisco Software Advisory Notices for CSCvz65560 - http://cs.co/9007yh22H'
    print_title(title, index, total_checks)

    if not tversion:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'
    else:
        if cversion.older_than("5.0(1a)") and (tversion.newer_than("5.0(1a)") and
                                               tversion.older_than("5.2(2g)")):
            result = FAIL_O
            data.append(["CSCvz65560", "Target Version susceptible to Defect"])

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def llfc_susceptibility_check(index, total_checks, cversion=None, tversion=None,  vpc_node_ids=None, **kwargs):
    title = 'Link Level Flow Control'
    result = PASS
    msg = ''
    headers = ["Pod", "NodeId", "Int", "Type", "BugId", "Warning"]
    data = []
    sx_affected = t_affected = False
    recommended_action = 'Manually change Peer devices Transmit(send) Flow Control to off prior to switch Upgrade'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvo27498'
    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, 'Target version not supplied. Skipping.')
        return MANUAL

    if not vpc_node_ids:
        print_result(title, result, 'No VPC Nodes found. Not susceptible.')
        return result

    # Check for Fiber 1000base-SX, CSCvv33100
    if cversion.older_than("4.2(6d)") and tversion.newer_than("4.2(6c)"):
        sx_affected = True

    # Check for Copper 1000base-T, CSCvj67507 fixed by CSCwd37387
    if cversion.older_than("4.1(1i)") and tversion.newer_than("4.1(1h)") and tversion.older_than("5.2(7f)"):
        t_affected = True

    if sx_affected or t_affected:
        ethpmFcot = icurl('class', 'ethpmFcot.json?query-target-filter=and(eq(ethpmFcot.type,"sfp"),eq(ethpmFcot.state,"inserted"))')

        for fcot in ethpmFcot:
            typeName = fcot['ethpmFcot']['attributes']['typeName']
            dn = fcot['ethpmFcot']['attributes']['dn']

            m = re.match(r'topology/pod-(?P<podid>\d+)/node-(?P<nodeid>\d+)/.+/phys-\[(?P<int>eth\d/\d+)\]', dn)
            podid = m.group('podid')
            nodeid = m.group('nodeid')
            int = m.group('int')

            if sx_affected and typeName == "1000base-SX":
                data.append([podid, nodeid, int, typeName, 'CSCvv33100', 'Check Peer Device LLFC behavior'])

            if t_affected and typeName == "1000base-T":
                data.append([podid, nodeid, int, typeName, 'CSCwd37387', 'Check Peer Device LLFC behavior'])

    if data:
        result = MANUAL

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def telemetryStatsServerP_object_check(index, total_checks, sw_cversion=None, tversion=None, **kwargs):
    title = 'telemetryStatsServerP Object'
    result = PASS
    msg = ''
    headers = ["Current version", "Target Version", "Warning"]
    data = []
    recommended_action = 'Change telemetryStatsServerP.collectorLocation to "none" prior to upgrade'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvt47850'
    print_title(title, index, total_checks)

    if not sw_cversion or not tversion:
        print_result(title, MANUAL, 'Current and target Switch version not supplied. Skipping.')
        return MANUAL

    if sw_cversion.older_than("4.2(4d)") and tversion.newer_than("5.2(2d)"):
        telemetryStatsServerP_json = icurl('class', 'telemetryStatsServerP.json')
        for serverp in telemetryStatsServerP_json:
            if serverp["telemetryStatsServerP"]["attributes"].get("collectorLocation") == "apic":
                result = FAIL_O
                data.append([str(sw_cversion), str(tversion), 'telemetryStatsServerP.collectorLocation = "apic" Found'])

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def internal_vlanpool_check(index, total_checks, tversion=None, **kwargs):
    title = 'Internal VLAN Pool'
    result = PASS
    msg = ''
    headers = ["VLAN Pool", "Internal VLAN Block(s)", "Non-AVE Domain", "Warning"]
    data = []
    recommended_action = 'Ensure Leaf Front-Panel VLAN Blocks are explicitly set to "external (on the wire)"'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvw33061'
    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, 'Target version not supplied. Skipping.')
        return MANUAL

    if tversion.newer_than("4.2(6a)"):
        fvnsVlanInstP_json = icurl('class', 'fvnsVlanInstP.json?rsp-subtree=children&rsp-subtree-class=fvnsRtVlanNs,fvnsEncapBlk&rsp-subtree-include=required')
        # Dict with key = vlan pool name, values = list of associated domains
        dom_rel = {}
        # List of vlanInstP which contain fvnsEncapBlk.role = "internal"
        encap_list = []
        encap_blk_dict = {}
        for vlanInstP in fvnsVlanInstP_json:
            encap_blk_list = []
            vlanInstP_name = vlanInstP['fvnsVlanInstP']["attributes"]["name"]
            dom_list = []
            for vlan_child in vlanInstP['fvnsVlanInstP']['children']:
                if vlan_child.get('fvnsRtVlanNs'):
                    dom_list.append({"dn": vlan_child['fvnsRtVlanNs']['attributes']['tDn'], "tCl": vlan_child['fvnsRtVlanNs']['attributes']['tCl']})
                elif vlan_child.get('fvnsEncapBlk'):
                    if vlan_child['fvnsEncapBlk']['attributes']['role'] == "internal":
                        encap_list.append(vlanInstP_name)
                        encap_blk_list.append(vlan_child['fvnsEncapBlk']['attributes']['rn'])
            dom_rel[vlanInstP_name] = dom_list
            if encap_blk_list != []:
                encap_blk_dict[vlanInstP_name] = encap_blk_list
        if len(encap_list) > 0:
            # Check if internal vlan pool is associated to a domain which isnt AVE
            # List of domains which are associated to a vlan pool that contains an encap block with role "internal"
            assoc_doms = []
            for vlanInstP_name in encap_list:
                for dom in dom_rel[vlanInstP_name]:
                    if dom["tCl"] != "vmmDomP":
                        result = FAIL_O
                        # Deduplicate results for multiple encap blks and/or multiple domains
                        if [vlanInstP_name, ', '.join(encap_blk_dict[vlanInstP_name]), dom["dn"], 'VLANs in this Block will be removed from switch Front-Panel if not corrected'] not in data:
                            data.append([vlanInstP_name, ', '.join(encap_blk_dict[vlanInstP_name]), dom["dn"], 'VLANs in this Block will be removed from switch Front-Panel if not corrected'])
                    assoc_doms.append(dom["dn"])
            vmmDomP_json = icurl('class', 'vmmDomP.json')
            for vmmDomP in vmmDomP_json:
                if vmmDomP["vmmDomP"]["attributes"]["dn"] in assoc_doms:
                    if vmmDomP["vmmDomP"]["attributes"]["enableAVE"] != "yes":
                        result = FAIL_O
                        # For each non-AVE vmm domain, check if vmm dom is associated to an internal pool
                        for vlanInstP_name in encap_list:
                            for dom in dom_rel[vlanInstP_name]:
                                if vmmDomP["vmmDomP"]["attributes"]["dn"] == dom["dn"]:
                                    # Deduplicate results for multiple encap blks and/or multiple domains
                                    if [vlanInstP_name, ', '.join(encap_blk_dict[vlanInstP_name]), vmmDomP["vmmDomP"]["attributes"]["dn"], 'VLANs in this Block will be removed from switch Front-Panel if not corrected'] not in data:
                                        data.append([vlanInstP_name, ', '.join(encap_blk_dict[vlanInstP_name]), vmmDomP["vmmDomP"]["attributes"]["dn"], 'VLANs in this Block will be removed from switch Front-Panel if not corrected'])

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def apic_ca_cert_validation(index, total_checks, **kwargs):
    title = 'APIC CA Cert Validation'
    result = FAIL_O
    msg = ''
    headers = ["Certreq Response"]
    data = []
    recommended_action = "Contact Cisco TAC to fix APIC CA Certs"
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvy35257'
    print_title(title, index, total_checks)

    certreq_out = kwargs.get("certreq_out")
    if not certreq_out:
        pki_fabric_ca_mo = icurl('class', 'pkiFabricSelfCAEp.json')
        if pki_fabric_ca_mo:
            # Prep csr
            passphrase = pki_fabric_ca_mo[0]['pkiFabricSelfCAEp']['attributes']['currCertReqPassphrase']
            cert_gen_filename = "gen.cnf"
            key_pem = 'temp.key.pem'
            csr_pem = 'temp.csr.pem'
            sign = 'temp.sign'
            cert_gen_cnf = '''
            [ req ]
            default_bits        = 2048
            distinguished_name  = req_distinguished_name
            string_mask         = utf8only
            default_md          = sha512
            prompt              = no

            [ req_distinguished_name ]
            commonName                      = aci_pre_upgrade
            '''
            with open(cert_gen_filename, 'w') as f:
                f.write(cert_gen_cnf)

            # Generate csr for certreq
            cmd = '/bin/openssl genrsa -out ' + key_pem + ' 2048'
            cmd = cmd + ' && /bin/openssl req -config ' + cert_gen_filename + ' -new -key ' + key_pem + ' -out ' + csr_pem
            cmd = cmd + ' && /bin/openssl dgst -sha256 -hmac ' + passphrase + ' -out ' + sign + ' ' + csr_pem
            logging.debug('cmd = '+''.join(cmd))
            genrsa_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            genrsa_proc.communicate()[0].strip()
            if genrsa_proc.returncode != 0:
                print_result(title, ERROR, 'openssl cmd issue, send logs to TAC')
                return ERROR

            # Prep certreq
            with open(sign) as f:
                hmac = f.read().strip().split(' ')[-1]
            with open(csr_pem) as f:
                certreq = f.read().strip()

            # file cleanup
            subprocess.check_output(['rm', '-rf', sign, csr_pem, key_pem, cert_gen_filename])

            # Perform test certreq
            url = 'https://127.0.0.1/raca/certreq.json'
            payload = '{"aaaCertGenReq":{"attributes":{"type":"csvc","hmac":"%s", "certreq": "%s", ' \
                      '"podip": "None", "podmac": "None", "podname": "None"}}}' % (hmac, certreq)
            cmd = 'icurl -kX POST %s -d \' %s \'' % (url, payload)
            logging.debug('cmd = ' + ''.join(cmd))
            certreq_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            certreq_out = certreq_proc.communicate()[0].strip()

    logging.debug(certreq_out)
    if '"error":{"attributes"' in str(certreq_out):
        # Spines can crash on 5.2(6e)+, but APIC CA Certs should be fixed regardless of tver
        data.append([certreq_out])

    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def fabricdomain_name_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'FabricDomain Name'
    result = FAIL_O
    msg = ''
    headers = ["FabricDomain", "Reason"]
    data = []
    recommended_action = "Do not upgrade to 6.0(2)"
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwf80352'

    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, 'Target version not supplied. Skipping.')
        return MANUAL

    if tversion.same_as("6.0(2h)"):
        controller = icurl('class', 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")')
        if not controller:
            print_result(title, ERROR, 'topSystem response empty. Is the cluster healthy?')
            return ERROR

        fabricDomain = controller[0]['topSystem']['attributes']['fabricDomain']
        if re.search(r'#|;', fabricDomain):
            data.append([fabricDomain, "Contains a special character"])

    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


# TODO: Add tversion handling when CSCwb86706 is fixed.
def sup_hwrev_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Spine SUP HW Revision'
    result = FAIL_O
    msg = ''
    headers = ["Pod", "Node", "Sup Slot", "Part Number"]
    data = []
    recommended_action = "Do not upgrade yet. Contact TAC and share these results."
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwb86706'

    print_title(title, index, total_checks)

    if cversion.newer_than("5.2(1a)") and cversion.older_than("6.0(1a)"):
        sup_re = r'/.+(?P<supslot>supslot-\d+)'
        sups = icurl('class', 'eqptSpCmnBlk.json?&query-target-filter=wcard(eqptSpromSupBlk.dn,"sup")')
        if not sups:
            print_result(title, ERROR, 'No sups found. This is unlikely.')
            return ERROR

        for sup in sups:
            prtNum = sup['eqptSpCmnBlk']['attributes']['prtNum']
            if prtNum in ['73-18562-02', '73-18570-02']:
                dn = re.search(node_regex+sup_re, sup['eqptSpCmnBlk']['attributes']['dn'])
                pod_id = dn.group("pod")
                node_id = dn.group("node")
                supslot = dn.group("supslot")
                data.append([pod_id, node_id, supslot, prtNum])

    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def uplink_limit_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Per-Leaf Fabric Uplink Limit Validation'
    result = PASS
    msg = ''
    headers = ["Node", "Uplink Count"]
    data = []
    recommended_action = "Reduce Per-Leaf Port Profile Uplinks to supported scale; 56 or less."
    doc_url = 'http://cs.co/ACI_Access_Interfaces_Config_Guide'

    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, 'Target version not supplied. Skipping.')
        return MANUAL

    if cversion.older_than("6.0(1a)") and tversion.newer_than("6.0(1a)"):
        port_profiles = icurl('class', 'eqptPortP.json?query-target-filter=eq(eqptPortP.ctrl,"uplink")')
        if not port_profiles or (len(port_profiles) < 57):
            return result

        node_count = {}
        for pp in port_profiles:
            dn = re.search(node_regex, pp['eqptPortP']['attributes']['dn'])
            node_id = dn.group("node")
            node_count.setdefault(node_id, 0)
            node_count[node_id] += 1

        for node, count in node_count.items():
            if count > 56:
                data.append([node, count])

    if data:
        result = FAIL_O
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def oob_mgmt_security_check(index, total_checks, cversion, tversion, **kwargs):
    """Implementation change due to CSCvx29282/CSCvz96117"""
    title = "OoB Mgmt Security"
    result = PASS
    msg = ""
    headers = ["ACI Node EPG", "External Instance (Subnets)", "OoB Contracts"]
    data = []
    recommended_action = (
        "\n\tEnsure that ICMP, SSH and HTTPS access are allowed for the required subnets with the above config."
        "\n\tOtherwise, APIC access will be limited to the above subnets and the same subnet as APIC OoB after the upgrade."
    )
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#oob-mgmt-security"

    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, "Target version not supplied. Skipping.")
        return MANUAL

    affected_versions = ["4.2(7)", "5.2(1)", "5.2(2)"]
    if cversion.simple_version not in affected_versions or (
        cversion.simple_version in affected_versions
        and tversion.simple_version in affected_versions
    ):
        print_result(title, NA)
        return NA

    # ACI Node EPGs (providers)
    mgmtOoBs = icurl("class", "mgmtOoB.json?rsp-subtree=children")
    # External Instant Profiles (consumers)
    mgmtInstPs = icurl("class", "mgmtInstP.json?rsp-subtree=children")

    contract_to_providers = defaultdict(list)
    for mgmtOoB in mgmtOoBs:
        for child in mgmtOoB["mgmtOoB"].get("children", []):
            if child.get("mgmtRsOoBProv"):
                epg_name = mgmtOoB["mgmtOoB"]["attributes"]["name"]
                contract_name = child["mgmtRsOoBProv"]["attributes"]["tnVzOOBBrCPName"]
                contract_to_providers[contract_name].append(epg_name)

    for mgmtInstP in mgmtInstPs:
        consumer = mgmtInstP["mgmtInstP"]["attributes"]["name"]
        providers = defaultdict(list)
        subnets = []
        for child in mgmtInstP["mgmtInstP"].get("children", []):
            if child.get("mgmtRsOoBCons"):
                contract = child["mgmtRsOoBCons"]["attributes"]["tnVzOOBBrCPName"]
                for prov in contract_to_providers.get(contract, []):
                    providers[prov].append(contract)
            elif child.get("mgmtSubnet"):
                subnets.append(child["mgmtSubnet"]["attributes"]["ip"])

        if not subnets or not providers:
            continue

        for provider, contracts in providers.items():
            data.append([
                provider,
                "{} ({})".format(consumer, ", ".join(subnets)),
                ", ".join(contracts)
            ])

    if data:
        result = MANUAL
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def mini_aci_6_0_2_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Mini ACI Upgrade to 6.0(2)+'
    result = FAIL_UF
    msg = ''
    headers = ["Pod ID","Node ID", "APIC Type", "Failure Reason"]
    data = []
    recommended_action = "All virtual APICs must be removed from the cluster prior to upgrading to 6.0(2)+."
    doc_url = 'Upgrading Mini ACI - http://cs.co/9009bBTQB'

    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, 'Target version not supplied. Skipping.')
        return MANUAL

    if cversion.older_than("6.0(2a)") and tversion.newer_than("6.0(2a)"):
        topSystem = icurl('class', 'topSystem.json?query-target-filter=wcard(topSystem.role,"controller")')
        if not topSystem:
            print_result(title, ERROR, 'topSystem response empty. Is the cluster healthy?')
            return ERROR
        for controller in topSystem:
            if controller['topSystem']['attributes']['nodeType'] == "virtual":
                pod_id = controller["topSystem"]["attributes"]["podId"]
                node_id = controller['topSystem']['attributes']['id']
                data.append([pod_id, node_id, "virtual", "Virtual APIC must be removed prior to upgrade to 6.0(2)+"])

    if not data:
        result = PASS
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def sup_a_high_memory_check(index, total_checks, tversion, **kwargs):
    title = "SUP-A/A+ High Memory Usage"
    result = PASS
    msg = ""
    headers = ["Pod ID", "Node ID", "SUP Model", "Active/Standby"]
    data = []
    recommended_action = "Change the target version to the one with memory optimization in a near-future 6.0 release."
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#sup-aa-high-memory-usage"

    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, "Target version not supplied. Skipping.")
        return MANUAL

    affected_versions = ["6.0(3)", "6.0(4)", "6.0(5)"]
    if tversion.simple_version in affected_versions:
        eqptSupCs = icurl("class", "eqptSupC.json")
        for eqptSupC in eqptSupCs:
            model = eqptSupC["eqptSupC"]["attributes"]["model"]
            if model in ["N9K-SUP-A", "N9K-SUP-A+"]:
                dn = re.search(node_regex, eqptSupC["eqptSupC"]["attributes"]["dn"])
                pod_id = dn.group("pod")
                node_id = dn.group("node")
                act_stb = eqptSupC["eqptSupC"]["attributes"]["rdSt"]
                data.append([pod_id, node_id, model, act_stb])

    if data:
        result = FAIL_O
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def access_untagged_check(index, total_checks, **kwargs):
    title = 'Access (Untagged) Port Config (F0467 native-or-untagged-encap-failure)'
    result = FAIL_O
    msg = ''
    headers = ["Fault", "POD ID","Node ID","Port","Tenant", "Application Profile", "Application EPG", "Recommended Action"]
    unformatted_headers = ['Fault', 'Fault Description', 'Recommended Action']
    unformatted_data = []
    data = []
    recommended_action = 'Resolve the conflict by removing this config or other configs using this port in Access(untagged) or native mode.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#access-untagged-port-config'
    print_title(title, index, total_checks)
    
    faultInsts = icurl('class','faultInst.json?&query-target-filter=wcard(faultInst.changeSet,"native-or-untagged-encap-failure")')
    fault_dn_regex=r"topology/pod-(?P<podid>\d+)/node-(?P<nodeid>[^/]+)/[^/]+/[^/]+/uni/epp/fv-\[uni/tn-(?P<tenant>[^/]+)/ap-(?P<app_profile>[^/]+)/epg-(?P<epg_name>[^/]+)\]/[^/]+/stpathatt-\[(?P<port>.+)\]/nwissues/fault-F0467"
    
    if faultInsts:
        fc = faultInsts[0]['faultInst']['attributes']['code']
        for faultInst in faultInsts:
            m = re.search(fault_dn_regex, faultInst['faultInst']['attributes']['dn'])
            if m:
                podid = m.group('podid')
                nodeid = m.group('nodeid')
                port = m.group('port')
                tenant = m.group('tenant')
                app_profile = m.group('app_profile')
                epg_name = m.group('epg_name')
                data.append([fc,podid, nodeid, port, tenant, app_profile, epg_name, recommended_action])
            else:
                unformatted_data.append(fc,faultInst['faultInst']['attributes']['descr'],recommended_action)

    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data, recommended_action="", doc_url=doc_url)
    return result


def post_upgrade_cb_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Post Upgrade Callback Integrity'
    result = PASS
    msg = ''
    headers = ["Missed Objects", "Impact"]
    data = []
    recommended_action = 'Contact Cisco TAC with Output'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#post-upgrade-callback-integrity'
    print_title(title, index, total_checks)

    new_mo_dict = {
        "infraImplicitSetPol": {
            "CreatedBy": "",
            "SinceVersion": "3.2(10e)",
            "Impact": "Infra implicit settings will not be deployed",
        },
        "infraRsToImplicitSetPol": {
            "CreatedBy": "infraImplicitSetPol",
            "SinceVersion": "3.2(10e)",
            "Impact": "Infra implicit settings will not be deployed",
        },
        "fvSlaDef": {
            "CreatedBy": "fvIPSLAMonitoringPol",
            "SinceVersion": "4.1(1i)",
            "Impact": "IPSLA monitor policy will not be deployed",
        },
        "infraRsConnectivityProfileOpt": {
            "CreatedBy": "infraRsConnectivityProfile",
            "SinceVersion": "5.2(4d)",
            "Impact": "VPC for missing Mo will not be deployed to leaf",
        },
        "infraAssocEncapInstDef": {
            "CreatedBy": "infraRsToEncapInstDef",
            "SinceVersion": "5.2(4d)",
            "Impact": "VLAN for missing Mo will not be deployed to leaf",
        },
        "compatSwitchHw": {
            "CreatedBy": "",  # suppBit attribute is available from 6.0(2h)
            "SinceVersion": "6.0(2h)",
            "Impact": "Unexpected 64/32 bit image can deploy to switches",
        },
    }
    if not tversion or (tversion and cversion.older_than(str(tversion))):
        print_result(title, POST, 'Re-run script after APICs are upgraded and back to Fully-Fit')
        return POST

    for new_mo in new_mo_dict:
        since_version = AciVersion(new_mo_dict[new_mo]['SinceVersion'])
        created_by_mo = new_mo_dict[new_mo]['CreatedBy']

        if since_version.newer_than(str(cversion)):
            continue

        api = "{}.json?rsp-subtree-include=count"
        if new_mo == "compatSwitchHw":
            # Expected to see suppBit in 32 or 64. Zero 32 means a failed postUpgradeCb.
            api += '&query-target-filter=eq(compatSwitchHw.suppBit,"32")'

        temp_new_mo_count = icurl("class", api.format(new_mo))
        new_mo_count = int(temp_new_mo_count[0]['moCount']['attributes']['count'])
        if created_by_mo == "":
            if new_mo_count == 0:
                data.append([new_mo, new_mo_dict[new_mo]["Impact"]])
        else:
            temp_createdby_mo_count = icurl('class', api.format(created_by_mo))
            created_by_mo_count = int(temp_createdby_mo_count[0]['moCount']['attributes']['count'])
            if created_by_mo_count != new_mo_count:
                data.append([new_mo, new_mo_dict[new_mo]["Impact"]])

    if data:
        result = FAIL_O
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def eecdh_cipher_check(index, total_checks, cversion, **kwargs):
    title = 'EECDH SSL Cipher'
    result = FAIL_UF
    msg = ''
    headers = ["DN", "Cipher", "State", "Failure Reason"]
    data = []
    recommended_action = "Re-enable EECDH key exchange prior to APIC upgrade."
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#eecdh-ssl-cipher'

    print_title(title, index, total_checks)
    
    if cversion.newer_than("4.2(1a)"):
        commCipher = icurl('class', 'commCipher.json')
        if not commCipher:
            print_result(title, ERROR, 'commCipher response empty. Is the cluster healthy?')
            return ERROR
        for cipher in commCipher:
            if cipher['commCipher']['attributes']['id'] == "EECDH" and cipher['commCipher']['attributes']['state'] == "disabled":
                data.append([cipher['commCipher']['attributes']['dn'], "EECDH", "disabled", "Secure key exchange is disabled which may cause APIC GUI to be down after upgrade."])

    if not data:
        result = PASS

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def vmm_active_uplinks_check(index, total_checks, **kwargs):
    title = 'fvUplinkOrderCont with blank active uplinks definition'
    result = PASS
    msg = ''
    headers = ["Tenant", "Application Profile", "Application EPG", "VMM Domain"]
    data = []
    recommended_action = 'Identify Active Uplinks and apply this to the VMM domain association of each EPG'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#vmm-uplink-container-with-empty-actives'
    print_title(title, index, total_checks)

    uplink_api =  'fvUplinkOrderCont.json' 
    uplink_api += '?query-target-filter=eq(fvUplinkOrderCont.active,"")'
    vmm_epg_regex=r"uni/tn-(?P<tenant>[^/]+)/ap-(?P<ap>[^/]+)/epg-(?P<epg>[^/]+)/rsdomAtt-\[uni/vmmp-.+/dom-(?P<dom>.+)\]"

    try:
        affected_uplinks = icurl('class', uplink_api)
    except OldVerClassNotFound:
        # Pre 4.x did not have this class
        msg = 'cversion does not have class fvUplinkOrderCont'
        result = NA
        print_result(title, result, msg)
        return result

    if affected_uplinks:
        result = FAIL_O
        for uplink in affected_uplinks:
            dn = re.search(vmm_epg_regex, uplink['fvUplinkOrderCont']['attributes']['dn'])
            data.append([dn.group("tenant"), dn.group("ap"), dn.group("epg"), dn.group("dom")])

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def fabric_port_down_check(index, total_checks, **kwargs):
    title = 'Fabric Port is Down (F1394 ethpm-if-port-down-fabric)'
    result = FAIL_O
    msg = ''
    headers = ["Pod", "Node", "Int", "Reason"]
    unformatted_headers = ['dn', 'Fault Description']
    unformatted_data = []
    data = []
    recommended_action = 'Identify if these ports are needed for redundancy and reason for being down'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#fabric-port-is-down'
    print_title(title, index, total_checks)
    
    fault_api =  'faultInst.json'
    fault_api += '?&query-target-filter=and(eq(faultInst.code,"F1394")'
    fault_api += ',eq(faultInst.rule,"ethpm-if-port-down-fabric"))'

    faultInsts = icurl('class',fault_api)
    dn_re = node_regex + r'/.+/phys-\[(?P<int>eth\d/\d+)\]'

    for faultInst in faultInsts:
        m = re.search(dn_re, faultInst['faultInst']['attributes']['dn'])
        if m:
            podid = m.group('pod')
            nodeid = m.group('node')
            port = m.group('int')
            reason = faultInst['faultInst']['attributes']['descr'].split("reason:")[1]
            data.append([podid, nodeid, port, reason])
        else:
            unformatted_data.append([faultInst['faultInst']['attributes']['dn'], faultInst['faultInst']['attributes']['descr']])

    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def fabric_dpp_check(index, total_checks, tversion, **kwargs):
    title = 'CoS 3 with Dynamic Packet Prioritization'
    result = PASS
    msg = ''
    headers = ["Potential Defect", "Reason"]
    data = []
    recommended_action = 'Change the target version to the fixed version of CSCwf05073'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwf05073'
    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, "Target version not supplied. Skipping.")
        return MANUAL
    
    lbpol_api =  'lbpPol.json'
    lbpol_api += '?query-target-filter=eq(lbpPol.pri,"on")'

    lbpPol = icurl('class', lbpol_api)
    if lbpPol:
        if ((tversion.newer_than("5.1(1h)") and tversion.older_than("5.2(8e)")) or 
            (tversion.major1 == "6" and tversion.older_than("6.0(3d)"))):
                result = FAIL_O
                data.append(["CSCwf05073", "Target Version susceptible to Defect"])

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def n9k_c93108tc_fx3p_interface_down_check(index, total_checks, tversion, **kwargs):
    title = 'N9K-C93108TC-FX3P/FX3H Interface Down'
    result = PASS
    msg = ''
    headers = ["Node ID", "Node Name", "Product ID"]
    data = []
    recommended_action = 'Change the target version to the fixed version of CSCwh81430'
    doc_url = 'https://www.cisco.com/c/en/us/support/docs/field-notices/740/fn74085.html'
    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, "Target version not supplied. Skipping.")
        return MANUAL

    if (
        tversion.older_than("5.2(8h)")
        or tversion.same_as("5.3(1d)")
        or (tversion.major1 == "6" and tversion.older_than("6.0(4a)"))
    ):
        api = 'fabricNode.json'
        api += '?query-target-filter=or('
        api += 'eq(fabricNode.model,"N9K-C93108TC-FX3P"),'
        api += 'eq(fabricNode.model,"N9K-C93108TC-FX3H"))'
        nodes = icurl('class', api)
        for node in nodes:
            nodeid = node["fabricNode"]["attributes"]["id"]
            name = node["fabricNode"]["attributes"]["name"]
            pid = node["fabricNode"]["attributes"]["model"]
            data.append([nodeid, name, pid])

    if data:
        result = FAIL_O
    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def subnet_scope_check(index, total_checks, cversion, **kwargs):
    title = 'BD and EPG Subnet Scope Check'
    result = PASS
    msg = ''
    headers = ["BD DN", "BD Scope", "EPG DN", "EPG Scope"]
    data = []
    recommended_action = 'Configure the same Scope for the identified subnet pairings'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#bd-and-epg-subnet-must-have-matching-scopes'
    print_title(title, index, total_checks)

    if cversion.older_than("4.2(6d)") or (cversion.major1 == "5" and cversion.older_than("5.1(1h)")):
        epg_api =  'fvAEPg.json?'
        epg_api += 'rsp-subtree=children&rsp-subtree-class=fvSubnet&rsp-subtree-include=required'

        fvAEPg = icurl('class', epg_api)
        if not fvAEPg:
            print_result(title, NA, "0 EPG Subnets found. Skipping.")
            return NA

        bd_api =  'fvBD.json'
        bd_api += '?rsp-subtree=children&rsp-subtree-class=fvSubnet&rsp-subtree-include=required'

        fvBD = icurl('class', bd_api)
        fvRsBd = icurl('class', 'fvRsBd.json')

        epg_to_subnets = {}
        # EPG subnets *tend* to be fewer, build out lookup dict by EPG first
        # {"epg_dn": {subnet1: scope, subnet2: scope},...}
        for epg in fvAEPg:
            subnet_scopes = {}
            for subnet in epg['fvAEPg']['children']:
                subnet_scopes[subnet["fvSubnet"]["attributes"]["ip"]] = subnet["fvSubnet"]["attributes"]["scope"]
            epg_to_subnets[epg['fvAEPg']['attributes']['dn']] = subnet_scopes

        bd_to_epg = {}
        # Build out BD to epg lookup, if EPG has a subnet (entry in epg_to_subnets)
        # {bd_tdn: [epg1, epg2, epg3...]}
        for reln in fvRsBd:
            epg_dn = reln["fvRsBd"]["attributes"]["dn"].replace('/rsbd', '')
            bd_tdn = reln["fvRsBd"]["attributes"]["tDn"]
            if epg_to_subnets.get(epg_dn):
                bd_to_epg.setdefault(bd_tdn, []).append(epg_dn)

        # walk through BDs and lookup EPG subnets to check scope
        for bd in fvBD:
            bd_dn = bd["fvBD"]["attributes"]["dn"]
            epgs_to_check = bd_to_epg.get(bd_dn)
            if epgs_to_check:
                for fvSubnet in bd['fvBD']['children']:
                    bd_subnet = fvSubnet["fvSubnet"]["attributes"]["ip"]
                    bd_scope = fvSubnet["fvSubnet"]["attributes"]["scope"]
                    for epg_dn in epgs_to_check:
                        epg_scope = epg_to_subnets[epg_dn].get(bd_subnet)
                        if bd_scope != epg_scope:
                            data.append([bd_dn, bd_scope, epg_dn, epg_scope])

    if data:
        result = FAIL_O

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def invalid_fex_rs_check(index, total_checks, **kwargs):
    title = 'Invalid FEX Relation Source'
    result = PASS
    msg = ''
    headers = ["FEX ID", "Invalid DN"]
    data = []
    recommended_action = 'Identify if FEX ID in use, then contact TAC for cleanup'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#invalid-fex-fabricpathep-dn-references'
    print_title(title, index, total_checks)


    hpath_api =  'infraRsHPathAtt.json?query-target-filter=wcard(infraRsHPathAtt.dn,"eth")'
    infraRsHPathAtt = icurl('class', hpath_api)

    for rs in infraRsHPathAtt:
        dn = rs["infraRsHPathAtt"]["attributes"]["dn"]
        m = re.search(r'eth(?P<fex>\d+)\/\d\/\d', dn)
        if m:
            fex_id = m.group('fex')
            data.append([fex_id, dn])

    if data:
        result = FAIL_UF

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def lldp_custom_int_description_defect_check(index, total_checks, tversion, **kwargs):
    title = 'LLDP Custom Interface Description Defect'
    result = PASS
    msg = ''
    headers = ["Potential Defect"]
    data = []
    recommended_action = 'Target version is not recommended; Custom interface descriptions and lazy VMM domain attachments found.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#lldp-custom-interface-description'
    print_title(title, index, total_checks)

    if not tversion:
        print_result(title, MANUAL, "Target version not supplied. Skipping.")
        return MANUAL

    if tversion.major1 == '6' and tversion.older_than('6.0(3a)'):
        custom_int_count = icurl('class', 'infraPortBlk.json?query-target-filter=ne(infraPortBlk.descr,"")&rsp-subtree-include=count')[0]['moCount']['attributes']['count']
        lazy_vmm_count = icurl('class','fvRsDomAtt.json?query-target-filter=and(eq(fvRsDomAtt.tCl,"vmmDomP"),eq(fvRsDomAtt.resImedcy,"lazy"))&rsp-subtree-include=count')[0]['moCount']['attributes']['count']

        if int(custom_int_count) > 0 and int(lazy_vmm_count) > 0:
            result = FAIL_O
            data.append(['CSCwf00416'])

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result

def sixty_four_and_thirty_two_memory_image_check(index, total_checks, cversion, tversion, **kwargs):
	title = '32 and 64-Bit Firmware Image for Switches'
	result = FAIL_O
	msg = ''
	headers = ["Node ID", "Node Name", "Recommended Action"]
	data = []
	recommended_action = 'Upload the 32 or 64 bit Switch Image missing to the Firmware repository'
	doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/'
	print_title(title, index, total_checks)
	switchVersion_regex = r'n9000-1(?P<version>[^$])'

	if tversion.newer_than("6.0(2a)"):
		is32BUp = False
		is64BUp = False
		firmwareFiles = icurl('class', 'firmwareFirmware.json')
		for firmwareFile in firmwareFiles:
			switchVersion = 'n9000-1' + tversion.version
			if (switchVersion == firmwareFile['firmwareFirmware']['attributes']['fullVersion'] and firmwareFile['firmwareFirmware']['attributes']['bitInfo'] == '32'):
				is32BUp = True
				
			elif (switchVersion == firmwareFile['firmwareFirmware']['attributes']['fullVersion'] and firmwareFile['firmwareFirmware']['attributes']['bitInfo'] == '64'):
				is64BUp = True
				
		if (is32BUp == True and is64BUp == True):
			result = PASS
		else:
			data.append[recommended_action]
			
	else: #Target Version prior to 6.0-2 
		result = NA
	
		
	print_result(title, result, msg, headers, data, doc_url=doc_url)
	return result

if __name__ == "__main__":
    prints('    ==== %s%s, Script Version %s  ====\n' % (ts, tz, SCRIPT_VERSION))
    prints('!!!! Check https://github.com/datacenter/ACI-Pre-Upgrade-Validation-Script for Latest Release !!!!\n')
    prints('To use a non-default Login Domain, enter apic#DOMAIN\\\\USERNAME')
    username, password = get_credentials()
    try:
        cversion = get_current_version()
        tversion = get_target_version()
        vpc_nodes = get_vpc_nodes()
        sw_cversion = get_switch_version()
    except Exception as e:
        prints('')
        err = 'Error: %s' % e
        print_title(err)
        print_result(err, ERROR)
        print_title("Initial query failed. Ensure APICs are healthy. Ending script run.")
        logging.exception(e)
        sys.exit()
    inputs = {'username': username, 'password': password,
              'cversion': cversion, 'tversion': tversion,
              'vpc_node_ids': vpc_nodes, 'sw_cversion':sw_cversion}
    json_log = {"name": "PreupgradeCheck", "method": "standalone script", "datetime": ts + tz,
                "script_version": str(SCRIPT_VERSION), "check_details": [], 
                'cversion': str(cversion), 'tversion': str(tversion)}
    checks = [
        # General Checks
        apic_version_md5_check,
        target_version_compatibility_check,
        gen1_switch_compatibility_check,
        r_leaf_compatibility_check,
        cimc_compatibilty_check,
        apic_cluster_health_check,
        switch_status_check,
        ntp_status_check,
        maintp_grp_crossing_4_0_check,
        features_to_disable_check,
        switch_group_guideline_check,
        mini_aci_6_0_2_check,
        post_upgrade_cb_check,

        # Faults
        apic_disk_space_faults_check,
        switch_bootflash_usage_check,
        standby_apic_disk_space_check,
        apic_ssd_check,
        switch_ssd_check,
        port_configured_for_apic_check,
        port_configured_as_l2_check,
        port_configured_as_l3_check,
        prefix_already_in_use_check,
        encap_already_in_use_check,
        access_untagged_check,
        bd_subnet_overlap_check,
        bd_duplicate_subnet_check,
        vmm_controller_status_check,
        vmm_controller_adj_check,
        lldp_with_infra_vlan_mismatch_check,
        hw_program_fail_check,
        scalability_faults_check,
        fabric_port_down_check,

        # Configurations
        vpc_paired_switches_check,
        overlapping_vlan_pools_check,
        vnid_mismatch_check,
        l3out_mtu_check,
        bgp_peer_loopback_check,
        l3out_route_map_direction_check,
        l3out_route_map_missing_target_check,
        l3out_overlapping_loopback_check,
        intersight_upgrade_status_check,
        isis_redis_metric_mpod_msite_check,
        bgp_golf_route_target_type_check,
        docker0_subnet_overlap_check,
        uplink_limit_check,
        oob_mgmt_security_check,
        eecdh_cipher_check,
        subnet_scope_check,

        # Bugs
        ep_announce_check,
        eventmgr_db_defect_check,
        contract_22_defect_check,
        telemetryStatsServerP_object_check,
        llfc_susceptibility_check,
        internal_vlanpool_check,
        apic_ca_cert_validation,
        fabricdomain_name_check,
        sup_hwrev_check,
        sup_a_high_memory_check,
        vmm_active_uplinks_check,
        fabric_dpp_check,
        n9k_c93108tc_fx3p_interface_down_check,
        invalid_fex_rs_check,
        lldp_custom_int_description_defect_check,

    ]
    summary = {PASS: 0, FAIL_O: 0, FAIL_UF: 0, ERROR: 0, MANUAL: 0, POST: 0, NA: 0, 'TOTAL': len(checks)}
    for idx, check in enumerate(checks):
        try:
            r = check(idx + 1, len(checks), **inputs)
            summary[r] += 1
            json_log["check_details"].append({"check_number": idx + 1, "name": check.__name__, "results": r})
        except KeyboardInterrupt:
            prints('\n\n!!! KeyboardInterrupt !!!\n')
            break
        except Exception as e:
            prints('')
            err = 'Error: %s' % e
            print_title(err)
            print_result(err, ERROR)
            summary[ERROR] += 1
            logging.exception(e)
    prints('\n=== Summary Result ===\n')

    jsonString = json.dumps(json_log)
    with open(JSON_FILE, 'w') as f:
        f.write(jsonString)

    subprocess.check_output(['tar', '-czf', BUNDLE_NAME, DIR])
    summary_headers = [PASS, FAIL_O, FAIL_UF, MANUAL, POST, NA, ERROR, 'TOTAL']
    res = max(summary_headers, key=len)
    max_header_len = len(res)
    for key in summary_headers:
        prints('{:{}} : {:2}'.format(key, max_header_len, summary[key]))

    bundle_loc = '/'.join([os.getcwd(), BUNDLE_NAME])

    prints("""
    Pre-Upgrade Check Complete.
    Next Steps: Address all checks flagged as FAIL, ERROR or MANUAL CHECK REQUIRED

    Result output and debug info saved to below bundle for later reference.
    Attach this bundle to Cisco TAC SRs opened to address the flagged checks.

      Result Bundle: {bundle}
    """.format(bundle=bundle_loc))
    prints('==== Script Version %s FIN ====' % (SCRIPT_VERSION))

    subprocess.check_output(['rm', '-rf', DIR])
