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
from six import iteritems, text_type
from six.moves import input
from textwrap import TextWrapper
from getpass import getpass
from collections import defaultdict
from datetime import datetime
from argparse import ArgumentParser
import functools
import shutil
import warnings
import time
import pexpect
import logging
import subprocess
import json
import sys
import os
import re

SCRIPT_VERSION = "v3.0.0"
# result constants
DONE = 'DONE'
PASS = 'PASS'
FAIL_O = 'FAIL - OUTAGE WARNING!!'
FAIL_UF = 'FAIL - UPGRADE FAILURE!!'
ERROR = 'ERROR !!'
MANUAL = 'MANUAL CHECK REQUIRED'
POST = 'POST UPGRADE CHECK REQUIRED'
NA = 'N/A'
# message constants
TVER_MISSING = "Target version not supplied. Skipping."
VER_NOT_AFFECTED = "Version not affected."
# regex constants
node_regex = r'topology/pod-(?P<pod>\d+)/node-(?P<node>\d+)'
port_regex = node_regex + r'/sys/phys-\[(?P<port>.+)\]'
path_regex = (
    r"topology/pod-(?P<pod>\d+)/"
    r"(?:prot)?paths-(?P<nodes>\d+|\d+-\d+)/"  # direct or PC/vPC
    r"(?:ext(?:prot)?paths-(?P<fex>\d+|\d+-\d+)/)?"  # FEX (optional)
    r"pathep-\[(?P<port>.+)\]"  # ethX/Y or PC/vPC IFPG name
)
dom_regex = r"uni/(?:vmmp-[^/]+/)?(?P<type>phys|l2dom|l3dom|dom)-(?P<dom>[^/]+)"

tz = time.strftime('%z')
ts = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
BUNDLE_NAME = 'preupgrade_validator_%s%s.tgz' % (ts, tz)
DIR = 'preupgrade_validator_logs/'
JSON_DIR = DIR + 'json_results/'
META_FILE = DIR + 'meta.json'
RESULT_FILE = DIR + 'preupgrade_validator_%s%s.txt' % (ts, tz)
SUMMARY_FILE = DIR + 'summary.json'
LOG_FILE = DIR + 'preupgrade_validator_debug.log'
warnings.simplefilter(action='ignore', category=FutureWarning)

log = logging.getLogger()


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
        self.protocol = "ssh"
        self.port = None
        self.timeout = 30
        self.prompt = r"#\s.*$"
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
        log.debug("check for valid connection: %r" % connected)
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
            if isinstance(self.log, str) or isinstance(self.log, text_type):
                self._log = open(self.log, "ab")
            else:
                self._log = self.log
            log.debug("setting logfile to %s" % self._log.name)
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
            log.debug(
                "spawning new pexpect connection: ssh %s@%s -p %d" % (self.username, self.hostname, self.port))
            no_verify = " -o StrictHostKeyChecking=no -o LogLevel=ERROR -o UserKnownHostsFile=/dev/null"
            if self.verify: no_verify = ""
            self.child = pexpect.spawn("ssh %s %s@%s -p %d" % (no_verify, self.username, self.hostname, self.port),
                                       searchwindowsize=self.searchwindowsize)
        elif self.protocol.lower() == "telnet":
            log.info("spawning new pexpect connection: telnet %s %d" % (self.hostname, self.port))
            self.child = pexpect.spawn("telnet %s %d" % (self.hostname, self.port),
                                       searchwindowsize=self.searchwindowsize)
        else:
            log.error("unknown protocol %s" % self.protocol)
            raise Exception("Unsupported protocol: %s" % self.protocol)

        # start logging
        self.start_log()

    def close(self):
        # try to gracefully close the connection if opened
        if self.__connected():
            log.info("closing current connection")
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
        log.debug("timeout: %d, matched: '%s'\npexpect output: '%s%s'" % (
            timeout, self.child.after, self.child.before, self.child.after))
        if result <= len(mapping) and result >= 0:
            log.debug("expect matched result[%d] = %s" % (result, mapping[result]))
            return mapping[result]
        ds = ''
        log.error("unexpected pexpect return index: %s" % result)
        for i in range(0, len(mapping)):
            ds += '[%d] %s\n' % (i, mapping[i])
        log.debug("mapping:\n%s" % ds)
        raise Exception("Unexpected pexpect return index: %s" % result)

    def login(self, max_attempts=7, timeout=17):
        """
        returns true on successful login, else returns false
        """

        log.debug("Logging into host")

        # successfully logged in at a different time
        if not self.__connected(): self.connect()
        # check for user provided 'prompt' which indicates successful login
        # else provide approriate username/password
        matches = {
            "console": "(?i)press return to get started",
            "refuse": "(?i)connection refused",
            "yes/no": "(?i)yes/no",
            "username": "(?i)(user(name)*|login)[ as]*[ \t]*:[ \t]*$",
            "password": "(?i)password[ \t]*:[ \t]*$",
            "prompt": self.prompt
        }

        while max_attempts > 0:
            max_attempts -= 1
            match = self.__expect(matches, timeout)
            if match == "console":  # press return to get started
                log.debug("matched console, send enter")
                self.child.sendline("\r\n")
            elif match == "refuse":  # connection refused
                log.error("connection refused by host")
                return False
            elif match == "yes/no":  # yes/no for SSH key acceptance
                log.debug("received yes/no prompt, send yes")
                self.child.sendline("yes")
            elif match == "username":  # username/login prompt
                log.debug("received username prompt, send username")
                self.child.sendline(self.username)
            elif match == "password":
                # don't log passwords to the logfile
                self.stop_log()
                log.debug("matched password prompt, send password")
                self.child.sendline(self.password)
                # restart logging
                self.start_log()
            elif match == "prompt":
                log.debug("successful login")
                self._login = True
                # force terminal length at login
                self.term_len = self._term_len
                return True
            elif match == "timeout":
                log.debug("timeout received but connection still opened, send enter")
                self.child.sendline("\r\n")
        # did not find prompt within max attempts, failed login
        log.error("failed to login after multiple attempts")
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
            log.debug("no active connection, attempt to login")
            if not self.login():
                raise Exception("failed to login to host")

        # if echo_cmd is disabled, then need to disable logging before
        # executing commands
        if not echo_cmd: self.stop_log()

        # execute command
        log.debug("cmd command: %s" % command)
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
        self.output = "%s%s" % (self.child.before.decode("utf-8"), self.child.after.decode("utf-8"))
        if result == "eof" or result == "timeout":
            log.warning("unexpected %s occurred" % result)
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
        if "/" in ip:
            raise ValueError(
                "IP address {} should not have a subnet mask".format(ip)
            )
        if "/" not in subnet:
            return False
        subnet_ip, subnet_pfxlen = subnet.split("/")
        subnet_network = cls.get_network_binary(subnet_ip, subnet_pfxlen)
        ip_network = cls.get_network_binary(ip, subnet_pfxlen)
        return ip_network == subnet_network


class AciVersion():
    """
    ACI Version parser class. Parses the version string and provides methods to compare versions.
    Supported version formats:
    - APIC: `5.2(7f)`, `5.2.7f`, `5.2(7.123a)`, `5.2.7.123a`, `5.2(7.123)`, `5.2.7.123`, `aci-apic-dk9.5.2.7f.iso/bin`
    - Switch: `15.2(7f)`, `15.2.7f`, `15.2(7.123a)`, `15.2.7.123a`, `15.2(7.123)`, `15.2.7.123`, `aci-n9000-dk9.15.2.7f.bin`
    """
    v_regex = r'(?:dk9\.)?[1]?(?P<major1>\d)\.(?P<major2>\d)(?:\.|\()(?P<maint>\d+)(?P<QAdot>\.?)(?P<patch1>(?:[a-z]|\d+))(?P<patch2>[a-z]?)\)?'

    def __init__(self, version):
        self.original = version
        v = re.search(self.v_regex, version)
        if not v:
            raise ValueError("Parsing failure of ACI version `%s`" % version)
        self.version = "{major1}.{major2}({maint}{QAdot}{patch1}{patch2})".format(**v.groupdict())
        self.dot_version = "{major1}.{major2}.{maint}{QAdot}{patch1}{patch2}".format(**v.groupdict())
        self.simple_version = "{major1}.{major2}({maint})".format(**v.groupdict())
        self.major_version = "{major1}.{major2}".format(**v.groupdict())
        self.major1 = v.group("major1")
        self.major2 = v.group("major2")
        self.maint = v.group("maint")
        self.patch1 = v.group("patch1")
        self.patch2 = v.group("patch2")
        self.regex = v

    def __str__(self):
        return self.version

    def older_than(self, version):
        v2 = version if isinstance(version, AciVersion) else AciVersion(version)
        for key in ["major1", "major2", "maint"]:
            if int(self.regex.group(key)) > int(v2.regex.group(key)): return False
            elif int(self.regex.group(key)) < int(v2.regex.group(key)): return True
        # Patch1 can be alphabet or number
        if self.patch1.isalpha() and v2.patch1.isdigit():
            return True  # e.g., 5.2(7f) is older than 5.2(7.123)
        elif self.patch1.isdigit() and v2.patch1.isalpha():
            return False
        elif self.patch1.isalpha() and v2.patch1.isalpha():
            if self.patch1 > v2.patch1: return False
            elif self.patch1 < v2.patch1: return True
        elif self.patch1.isdigit() and v2.patch1.isdigit():
            if int(self.patch1) > int(v2.patch1): return False
            elif int(self.patch1) < int(v2.patch1): return True
            # Patch2 (alphabet) is optional.
            if not self.patch2 and v2.patch2:
                return True  # one without Patch2 is older.
            elif self.patch2 and not v2.patch2:
                return False
            elif self.patch2 and v2.patch2:
                if self.patch2 > v2.patch2: return False
                elif self.patch2 < v2.patch2: return True
        return False

    def newer_than(self, version):
        return not self.older_than(version) and not self.same_as(version)

    def same_as(self, version):
        v2 = version if isinstance(version, AciVersion) else AciVersion(version)
        return self.version == v2.version


class AciObjectCrawler(object):
    """
    Args:
        mos (list of dict): MOs in the form of output from the function `icurl()` with
                            the filter `query-target` that returns a flat list.
    """

    def __init__(self, mos):
        self.mos = mos
        self.mos_per_class = defaultdict(list)

        self.init_mos_per_class()

    def init_mos_per_class(self):
        """
        Create `self.mos_per_class` (dict) which stores lists of MOs per class.
        """
        for mo in self.mos:
            classname = list(mo.keys())[0]
            _mo = {"classname": classname}
            _mo.update(mo[classname]["attributes"])
            self.mos_per_class[classname].append(_mo)

    def get_mos(self, classname):
        return self.mos_per_class.get(classname, [])

    def get_children(self, parent_dn, children_class):
        """
        Args:
            parent_dn (str): DN of the parent MO.
            children_class (str): Class name of the (grand) children under parent_dn.
        Returns:
            list of dict: The MOs of children_class under parent_dn.
        """
        mos = self.get_mos(children_class)
        return [mo for mo in mos if mo["dn"].startswith(parent_dn + "/")]

    def get_parent(self, child_dn, parent_class):
        """
        Args:
            child_dn (str): DN of the child MO.
            parent_class (str): Class name of the (grand) parent of child_dn.
        Returns:
            dict: The parent MO of child_dn.
        """
        mos = self.get_mos(parent_class)
        for mo in mos:
            if child_dn.startswith(mo["dn"] + "/"):
                return mo
        return {}

    def get_rel_targets(self, src_dn, rel_class):
        """
        Args:
            src_dn (str): DN of the source object.
            rel_class (str): Relation class with tDn/tCl. Children of src_dn
        Returns:
            list of dict: MOs that are pointed by tDn from src_dn
        """
        targets = []
        rel_mos = self.get_children(src_dn, rel_class)
        for rel_mo in rel_mos:
            mos = self.get_mos(rel_mo["tCl"])
            for mo in mos:
                if mo["dn"] == rel_mo["tDn"]:
                    targets.append(mo)
                    break
            else:
                # The target objects may not be in our self.mos_per_class.
                # In that case, just return the DN and class.
                targets.append({"dn": rel_mo["tDn"], "classname": rel_mo["tCl"]})
        return targets

    def get_src_from_tDn(self, tDn, rs_class, src_class):
        """
        Args:
            tDn (str): Target DN. Get all MOs with this DN as the target via rs_class.
            rs_class (str): Relation class.
            src_class (str): Class name of source MOs that may have tDn as the target
                             via rs_class.
        Returns:
            list of dict: MOs that point to tDn via rs_class.
        """
        src_mos = []
        rs_mos = self.get_mos(rs_class)
        for rs_mo in rs_mos:
            if rs_mo["tDn"] == tDn:
                src_mo = self.get_parent(rs_mo["dn"], src_class)
                if src_mo:
                    src_mos.append(src_mo)
        return src_mos


class AciAccessPolicyParser(AciObjectCrawler):
    """
    port_data:
        key: port_path in the format shown below:
            `<node_id>/eth<card_id>/<port_id>`
            `<node_id>/<fex_id>/eth<card_id>/<port_id>`
            `<node_id>/<IFPG name>`
            `<node_id>/<fex_id>/<IFPG name>`
        value: {
            "ifpg": Name of IFPG
            "override_ifpg": Name of override IFPG. Skipped if not override
            "pc_type": none|pc|vpc. From the IFPG
            "aep": Name of AEP
            "domain_dns": List of domain DNs associated to the AEP
            "vlan_scope": global or portlocal. From the IFPG
            "node": Node ID
            "fex": Fex ID or 0
            "port": ethX/Y, ethX/Y/Z, IFPG name
        }
    vpool_per_dom:
        key: domain DN
        value: {
            "name": Name of VLAN Pool
            "vlan_ids": List of VLAN IDs. ex) [1,2,3,100,101]
            "dom_name": Name of domain
            "dom_type": Type of domain (phys, l3dom, vmm)
        }
    """
    # VLAN Pool
    VLANPool = "fvnsVlanInstP"
    VLANBlk = "fvnsEncapBlk"
    # AEP
    AEP = "infraAttEntityP"
    # Leaf Interface Profile etc.
    IFP = "infraAccPortP"
    IFSel = "infraHPortS"
    PortBlk = "infraPortBlk"
    SubPortBlk = "infraSubPortBlk"  # breakout
    IFPath = "infraHPathS"  # override
    # Leaf Switch Profile etc.
    SWP = "infraNodeP"
    SWSel = "infraLeafS"
    NodeBlk = "infraNodeBlk"
    # FEX
    FEXP = "infraFexP"
    FEXPG = "infraFexBndlGrp"

    # Leaf Interface Policy Group etc.
    IFPG = "infraAccPortGrp"
    IFPG_PC = "infraAccBndlGrp"
    IFPG_PC_O = "infraAccBndlPolGrp"  # override (PC/VPC PG)

    # Leaf Interface Policy
    IFPol_L2 = "l2IfPol"

    # Relation objects (<src>_to_<tDn>)
    VLAN_to_Dom = "fvnsRtVlanNs"
    AEP_to_Dom = "infraRsDomP"
    IFPG_to_AEP = "infraRsAttEntP"
    IFSel_to_IFPG = "infraRsAccBaseGrp"
    IFPath_to_IFPG = "infraRsPathToAccBaseGrp"  # override
    IFPath_to_Path = "infraRsHPathAtt"  # override
    SWP_to_IFP = "infraRsAccPortP"
    IFPol_L2_to_IFPG = "l2RtL2IfPol"

    def __init__(self, mos):
        super(AciAccessPolicyParser, self).__init__(mos)
        self.nodes_per_ifp = defaultdict(list)
        self.port_data = defaultdict(dict)
        self.vpool_per_dom = defaultdict(dict)

        self.create_port_data()
        self.create_vlanpool_per_domain()

    @classmethod
    def get_classes(cls):
        """Get all ACI object classes used in this class"""
        classes = []
        for key, val in iteritems(AciAccessPolicyParser.__dict__):
            if key.startswith("__") or not isinstance(val, str):
                continue
            classes.append(val)
        return classes

    def get_node_ids_from_ifp(self, ifp_dn):
        if ifp_dn in self.nodes_per_ifp:
            return self.nodes_per_ifp[ifp_dn]
        node_ids = []
        swps = self.get_src_from_tDn(ifp_dn, self.SWP_to_IFP, self.SWP)
        for swp in swps:
            swsels = self.get_children(swp["dn"], self.SWSel)
            for swsel in swsels:
                node_blks = self.get_children(swsel["dn"], self.NodeBlk)
                for node_blk in node_blks:
                    _from = int(node_blk["from_"])
                    _to = int(node_blk["to_"])
                    node_ids += range(_from, _to + 1)
        self.nodes_per_ifp[ifp_dn] = node_ids
        return node_ids

    def get_node_ids_from_ifsel(self, ifsel_dn):
        ifp = self.get_parent(ifsel_dn, self.IFP)
        if not ifp:
            log.warning("No I/F Profile for Selector (%s)", ifsel_dn)
            return []
        node_ids = self.get_node_ids_from_ifp(ifp["dn"])
        return node_ids

    def get_fex_id_from_ifsel(self, ifsel_dn):
        """Get FEX ID if ifsel is FEX NIF"""
        fex_id = 0
        rs_ifpgs = self.get_children(ifsel_dn, self.IFSel_to_IFPG)
        if rs_ifpgs and rs_ifpgs[0]["tCl"] == "infraFexBndlGrp":
            fex_id = int(rs_ifpgs[0]["fexId"])
        return fex_id

    def get_fexnif_ifsels_from_fexhif(self, hif_ifsel_dn):
        """
        Get FEX NIF I/F selectors from a FEX HIF I/F Selector
        """
        # 1. Get FEXPG from FEX HIF IFSel via the parent (FEXP).
        #     FEXP -+- IFSel (FEX HIF)
        #           +- FEXPG
        fexp = self.get_parent(hif_ifsel_dn, self.FEXP)
        if not fexp:
            return []
        fexpgs = self.get_children(fexp["dn"], self.FEXPG)
        if not fexpgs:
            return []
        # There should be only one FEXPG for each FEXP
        fexpg = fexpgs[0]
        # 2. Get FEX NIF IFSels from FEXPG via the relation.
        #     IFSel (FEX NIF) <--[IFSel_to_IFPG]-- FEXPG
        fexnif_ifsels = self.get_src_from_tDn(
            fexpg["dn"], self.IFSel_to_IFPG, self.IFSel
        )
        return fexnif_ifsels

    def get_ports_from_ifsel(self, ifsel_dn):
        ports = []
        port_blks = self.get_children(ifsel_dn, self.PortBlk)
        subport_blks = self.get_children(ifsel_dn, self.SubPortBlk)
        for port_blk in port_blks + subport_blks:
            from_card = int(port_blk["fromCard"])
            from_port = int(port_blk["fromPort"])
            from_subport = int(port_blk["fromSubPort"]) if port_blk["classname"] == self.SubPortBlk else 0
            to_card = int(port_blk["toCard"])
            to_port = int(port_blk["toPort"])
            to_subport = int(port_blk["toSubPort"]) if port_blk["classname"] == self.SubPortBlk else 0
            for card in range(from_card, to_card + 1):
                for port in range(from_port, to_port + 1):
                    for subport in range(from_subport, to_subport + 1):
                        if subport:
                            ports.append("eth{}/{}/{}".format(card, port, subport))
                        else:
                            ports.append("eth{}/{}".format(card, port))
        return ports

    def create_port_data(self):
        ifsels = self.get_mos(self.IFSel)
        for ifsel in ifsels:
            # GET Node IDs and FEX IDs
            node2fexid = {}
            if ifsel["dn"].startswith("uni/infra/fexprof-"):
                # When ifsel is of FEX HIF, get node IDs and FEX IDs from FEX NIFs.
                # ACI supports only single-homed FEXes with or without vPC.
                # One FEX HIF can be tied to 2 nodes, one FEX for each, at maximum.
                nifs = self.get_fexnif_ifsels_from_fexhif(ifsel["dn"])
                for nif in nifs:
                    _node_ids = self.get_node_ids_from_ifsel(nif["dn"])
                    fex_id = self.get_fex_id_from_ifsel(nif["dn"])
                    for _node_id in _node_ids:
                        node2fexid[_node_id] = fex_id
                node_ids = node2fexid.keys()
                if len(node_ids) > 2:
                    log.error(
                        "FEX HIF handling failed as it shows more than 2 nodes."
                    )
                    break
            else:
                node_ids = self.get_node_ids_from_ifsel(ifsel["dn"])
            if not node_ids:
                continue

            # Get IFPG
            ifpgs = self.get_rel_targets(ifsel["dn"], self.IFSel_to_IFPG)
            if not ifpgs:
                continue
            ifpg = ifpgs[0]

            # Get ports or use IFPG Name for PC/VPC
            if ifpg.get("classname") == self.IFPG_PC and ifpg.get("name"):
                ports = [ifpg["name"]]
            else:
                ports = self.get_ports_from_ifsel(ifsel["dn"])
            if not ports:
                continue

            # Get settings from IFPG
            pc_type = self.get_pc_type(ifpg)

            l2if = self.get_ifpol_l2if_from_ifpg(ifpg["dn"])
            vlan_scope = l2if.get("vlanScope", "unknown")

            # Get AEP from IFPG
            aeps = self.get_rel_targets(ifpg.get("dn", ""), self.IFPG_to_AEP)
            aep = aeps[0] if aeps else {}
            # Get Domains from AEP
            doms = self.get_rel_targets(aep.get("dn", ""), self.AEP_to_Dom)

            for node_id in node_ids:
                fex_id = node2fexid.get(node_id, 0)
                for port in ports:
                    if fex_id:
                        path = "/".join([str(node_id), str(fex_id), port])
                    else:
                        path = "/".join([str(node_id), port])
                    self.port_data[path] = {
                        "node": str(node_id),
                        "fex": str(fex_id),
                        "port": port,
                        "ifpg_name": ifpg.get("name", ""),
                        "pc_type": pc_type,
                        "vlan_scope": vlan_scope,
                        "aep_name": aep.get("name", ""),
                        "domain_dns": [dom["dn"] for dom in doms],
                    }

        # Override
        ifpaths = self.get_mos(self.IFPath)
        for ifpath in ifpaths:
            # Get Node/FEX/Port ID
            override_paths = self.get_children(ifpath["dn"], self.IFPath_to_Path)
            if not override_paths:
                continue
            override_path = override_paths[0]
            p = re.search(path_regex, override_path["tDn"])
            nodes = p.group("nodes").split("-")
            fexes = p.group("fex").split("-") if p.group("fex") else []
            port = p.group("port")

            # Get IFPG
            ifpgs = self.get_rel_targets(ifpath["dn"], self.IFPath_to_IFPG)
            if not ifpgs:
                continue
            ifpg = ifpgs[0]

            # Get settings from IFPG
            l2if = self.get_ifpol_l2if_from_ifpg(ifpg["dn"])
            vlan_scope = l2if.get("vlanScope", "unknown")

            # Get AEP from IFPG
            aeps = self.get_rel_targets(ifpg.get("dn", ""), self.IFPG_to_AEP)
            aep = aeps[0] if aeps else {}
            # Get Domains from AEP
            doms = self.get_rel_targets(aep.get("dn", ""), self.AEP_to_Dom)

            for idx, node in enumerate(nodes):
                fex = "0"
                if fexes:
                    fex = fexes[0] if len(fexes) == 1 else fexes[idx]
                    path = "/".join([node, fex, port])
                else:
                    path = "/".join([node, port])
                self.port_data[path].update({
                    "node": node,
                    "fex": fex,
                    "port": port,
                    "override_ifpg_name": ifpg.get("name", ""),
                    "vlan_scope": vlan_scope,
                    "aep_name": aep.get("name", ""),
                    "domain_dns": [dom["dn"] for dom in doms],
                })

    def create_vlanpool_per_domain(self):
        vlan_pools = self.get_mos(self.VLANPool)
        for vlan_pool in vlan_pools:
            vlan_ids = []
            vlan_blks = self.get_children(vlan_pool["dn"], self.VLANBlk)
            for vlan_blk in vlan_blks:
                vlan_ids += range(
                    int(vlan_blk["from"].split("-")[1]),
                    int(vlan_blk["to"].split("-")[1]) + 1,
                )
            rs_domains = self.get_children(vlan_pool["dn"], self.VLAN_to_Dom)
            for rs_domain in rs_domains:
                dom_match = re.search(dom_regex, rs_domain["tDn"])
                dom_name = "..." if not dom_match else dom_match.group("dom")
                dom_type = "..." if not dom_match else dom_match.group("type")
                # No need to worry about overwrite because there can be
                # only one VLAN pool per domain.
                self.vpool_per_dom[rs_domain["tDn"]] = {
                    "name": vlan_pool["name"],
                    "vlan_ids": vlan_ids,
                    "dom_name": dom_name,
                    "dom_type": "vmm" if dom_type == "dom" else dom_type,
                }
        return self.vpool_per_dom

    def get_pc_type(self, ifpg):
        pc_type = "none"
        if ifpg.get("lagT") == "node":
            pc_type = "vpc"
        elif ifpg.get("lagT") in ["link", "fc-link"]:
            pc_type = "pc"
        return pc_type

    def get_ifpol_l2if_from_ifpg(self, ifpg_dn):
        ifpol_l2s = self.get_src_from_tDn(ifpg_dn, self.IFPol_L2_to_IFPG, self.IFPol_L2)
        return ifpol_l2s[0] if ifpol_l2s else {}


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


class AciResult:
    """
    APIC uses an object called `AciResult` to store the results of
    each rule/check in the pre-upgrade validation which is run during the upgrade
    workflow in the APIC GUI. When this script is invoked during the workflow, it
    is expected to write the results of each rule/check to a JSON file (one per rule)
    in a specific format.
    """
    # Expected keys in the JSON file
    __slots__ = (
        "ruleId", "name", "description", "reason", "sub_reason", "recommended_action",
        "docUrl", "severity", "ruleStatus", "showValidation", "failureDetails",
    )

    def __init__(self, func_name, name, description):
        self.ruleId = func_name
        self.name = name
        self.description = description
        self.reason = ""
        self.sub_reason = ""
        self.recommended_action = ""
        self.docUrl = ""
        self.severity = "informational"
        self.ruleStatus = "passed"  # passed|failed
        self.showValidation = True
        self.failureDetails = {
            "failType": "",
            "data": [],
            "unformatted_data": [],
        }

    @staticmethod
    def craftData(column, rows):
        if not (isinstance(rows, list) and isinstance(column, list)):
            raise TypeError("Rows and column must be lists.")
        data = []
        c_len = len(column)
        for row_entry in range(len(rows)):
            r_len = len(rows[row_entry])
            if r_len != c_len:
                raise ValueError("Row length ({}), data: {} does not match column length ({}).".format(r_len, rows[row_entry], c_len))
            entry = {}
            for col_pos in range(c_len):
                entry[column[col_pos]] = rows[row_entry][col_pos]
            data.append(entry)
        return data

    def updateWithResults(self, result, recommended_action, msg, doc_url, headers, data, unformatted_headers, unformatted_data):
        self.reason = msg
        self.recommended_action = recommended_action
        self.docUrl = doc_url

        # Show validation
        if result in [NA, POST]:
            self.showValidation = False

        # Severity
        if result in [FAIL_O, FAIL_UF]:
            self.severity = "critical"
        elif result in [ERROR]:
            self.severity = "major"
        elif result in [MANUAL]:
            self.severity = "warning"

        if result not in [NA, PASS]:
            self.ruleStatus = "failed"
            self.failureDetails["failType"] = result
            self.failureDetails["data"] = self.craftData(headers, data)
            if unformatted_headers and unformatted_data:
                self.failureDetails["unformatted_data"] = self.craftData(unformatted_headers, unformatted_data)
                if self.reason:
                    self.reason += "\n"
                self.reason += (
                    "Parse failure occurred, the provided data may not be complete. "
                    "Please contact Cisco TAC to identify the missing data."
                )

    def buildResult(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def writeResult(self, path=JSON_DIR):
        filename = re.sub(r'[^a-zA-Z0-9_]+|\s+', '_', self.ruleId) + '.json'
        if not os.path.isdir(path):
            os.mkdir(path)
        with open(os.path.join(path, filename), "w") as f:
            json.dump(self.buildResult(), f, indent=2)
        return "{}/{}".format(path, filename)


class Result:
    """Class to hold the result of a check."""
    __slots__ = ("result", "msg", "headers", "data", "unformatted_headers", "unformatted_data", "recommended_action", "doc_url", "adjust_title")

    def __init__(self, result=PASS, msg="", headers=None, data=None, unformatted_headers=None, unformatted_data=None, recommended_action="", doc_url="", adjust_title=False):
        self.result = result
        self.msg = msg
        self.headers = headers if headers is not None else []
        self.data = data if data is not None else []
        self.unformatted_headers = unformatted_headers if unformatted_headers is not None else []
        self.unformatted_data = unformatted_data if unformatted_data is not None else []
        self.recommended_action = recommended_action
        self.doc_url = doc_url
        self.adjust_title = adjust_title

    def as_dict(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def as_dict_for_json_result(self):
        return {slot: getattr(self, slot) for slot in self.__slots__ if slot != "adjust_title"}


def check_wrapper(check_title):
    """
    Decorator to wrap a check function to handle the printing of title and results,
    and to write the results in a file in a JSON format.
    """
    def decorator(check_func):
        @functools.wraps(check_func)
        def wrapper(index, total_checks, *args, **kwargs):
            # Print `[Check  1/81] <title>...`
            print_title(check_title, index, total_checks)

            try:
                # Run check, expecting it to return a `Result` object
                r = check_func(*args, **kwargs)
            except Exception as e:
                r = Result(result=ERROR, msg='Unexpected Error: {}'.format(e))
                log.exception(e)

            # Print `[Check  1/81] <title>... <result> + <failure details>`
            print_result(title=check_title, **r.as_dict())

            # Write results in JSON
            # Using `wrapper.__name__` instead of `check_func.__name` because
            # both show the original check func name and `wrapper.__name__` can
            # be dynamically changed inside each check func if needed. (mainly
            # for test or debugging)
            synth = AciResult(wrapper.__name__, check_title, "")
            synth.updateWithResults(**r.as_dict_for_json_result())
            synth.writeResult()
            return r.result
        return wrapper
    return decorator


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
        output += '\n\n' + format_table(unformatted_headers, unformatted_data)
    if data or unformatted_data:
        output += '\n'
        if recommended_action:
            output += '\n  Recommended Action: %s' % recommended_action
        if doc_url:
            output += '\n  Reference Document: %s' % doc_url
        output += '\n' * 2
    prints(output)


def _icurl_error_handler(imdata):
    if imdata and "error" in imdata[0]:
        if "not found in class" in imdata[0]['error']['attributes']['text']:
            raise OldVerPropNotFound('Your current ACI version does not have requested property')
        elif "unresolved class for" in imdata[0]['error']['attributes']['text']:
            raise OldVerClassNotFound('Your current ACI version does not have requested class')
        elif "not found" in imdata[0]['error']['attributes']['text']:
            raise OldVerClassNotFound('Your current ACI version does not have requested class')
        else:
            raise Exception('API call failed! Check debug log')


def _icurl(apitype, query, page=0, page_size=100000):
    if apitype not in ['class', 'mo']:
        print('invalid API type - %s' % apitype)
        return []
    pre = '&' if '?' in query else '?'
    query += '{}page={}&page-size={}'.format(pre, page, page_size)
    uri = 'http://127.0.0.1:7777/api/{}/{}'.format(apitype, query)
    cmd = ['icurl', '-gs', uri]
    log.info('cmd = ' + ' '.join(cmd))
    response = subprocess.check_output(cmd)
    log.debug('response: ' + str(response))
    data = json.loads(response)
    _icurl_error_handler(data['imdata'])
    return data


def icurl(apitype, query, page_size=100000):
    total_imdata = []
    total_cnt = 999999
    page = 0
    while total_cnt > len(total_imdata):
        data = _icurl(apitype, query, page, page_size)
        if not data['imdata']:
            break
        total_imdata += data['imdata']
        total_cnt = int(data['totalCount'])
        page += 1
    return total_imdata


def get_credentials():
    prints('To use a non-default Login Domain, enter apic#DOMAIN\\\\USERNAME')
    while True:
        usr = input('Enter username for APIC login          : ')
        if usr: break
    while True:
        pwd = getpass('Enter password for corresponding User  : ')
        if pwd: break
    print('')
    return usr, pwd


def get_current_version(arg_cversion):
    """ Returns: AciVersion instance """
    if arg_cversion:
        prints("Current APIC version is overridden to %s" % arg_cversion)
        try:
            current_version = AciVersion(arg_cversion)
        except ValueError as e:
            prints(e)
            sys.exit(1)
        return current_version
    prints("Checking current APIC version...", end='')
    firmwares = icurl('class', 'firmwareCtrlrRunning.json')
    for firmware in firmwares:
        if 'node-1' in firmware['firmwareCtrlrRunning']['attributes']['dn']:
            apic1_version = firmware['firmwareCtrlrRunning']['attributes']['version']
            break
    current_version = AciVersion(apic1_version)
    prints('%s\n' % current_version)
    return current_version


def get_target_version(arg_tversion):
    """ Returns: AciVersion instance """
    if arg_tversion:
        prints("Target APIC version is overridden to %s" % arg_tversion)
        try:
            target_version = AciVersion(arg_tversion)
        except ValueError as e:
            prints(e)
            sys.exit(1)
        return target_version
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


def get_vpc_nodes():
    """ Returns list of VPC Node IDs; ['101', '102', etc...] """
    prints("Collecting VPC Node IDs...", end='')
    vpc_nodes = []
    prot_pols = icurl('class', 'fabricNodePEp.json')
    for vpc_node in prot_pols:
        vpc_nodes.append(vpc_node['fabricNodePEp']['attributes']['id'])
    vpc_nodes.sort()
    # Display up to 4 node IDs
    max_display = 4
    if len(vpc_nodes) <= max_display:
        prints('%s\n' % ", ".join(vpc_nodes))
    else:
        omitted_count = len(vpc_nodes) - max_display
        prints('%s, ... (and %d more)\n' % (", ".join(vpc_nodes[:max_display]), omitted_count))
    return vpc_nodes


def get_switch_version():
    """ Returns lowest switch version as AciVersion instance """
    prints("Gathering Lowest Switch Version from Firmware Repository...", end='')
    firmwares = icurl('class', 'firmwareRunning.json')
    versions = set()

    for firmware in firmwares:
        versions.add(firmware['firmwareRunning']['attributes']['peVer'])

    if versions:
        lowest_sw_ver = AciVersion(versions.pop())
        for version in versions:
            version = AciVersion(version)
            if lowest_sw_ver.newer_than(str(version)):
                lowest_sw_ver = version
        prints('%s\n' % lowest_sw_ver)
        return lowest_sw_ver
    else:
        prints("No Switches Detected! Join switches to the fabric then re-run this script.\n")
        return None


@check_wrapper(check_title="APIC Cluster is Fully-Fit")
def apic_cluster_health_check(cversion, **kwargs):
    result = FAIL_UF
    msg = ''
    headers = ['APIC-ID\n(Seen By)', 'APIC-ID\n(Affected)', 'Admin State', 'Operational State', 'Health State']
    unformatted_headers = ['Affected DN', 'Admin State', 'Operational State', 'Health State']
    data = []
    unformatted_data = []
    doc_url = 'http://cs.co/9003ybZ1d'  # ACI Troubleshooting Guide 2nd Edition
    if cversion.older_than("4.2(1a)"):
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
    return Result(result=result, msg=msg, headers=headers, data=data, unformatted_headers=unformatted_headers, unformatted_data=unformatted_data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Switches are all in Active state")
def switch_status_check(**kwargs):
    result = FAIL_UF
    msg = ''
    headers = ['Pod-ID', 'Node-ID', 'State']
    data = []
    recommended_action = 'Bring this node back to "active"'
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
        data.append([pod_id, node_id, state])
    if not fabricNodes:
        result = MANUAL
        msg = 'Switch fabricNode not found!'
    elif not data:
        result = PASS
    return Result(result=result, msg=msg, headers=headers, data=data, recommended_action=recommended_action)


@check_wrapper(check_title="Firmware/Maintenance Groups when crossing 4.0 Release")
def maintp_grp_crossing_4_0_check(cversion, tversion, **kwargs):
    result = PASS
    msg = ''
    headers = ["Group Name", "Group Type"]
    data = []
    recommended_action = 'Remove the group prior to APIC upgrade. Create a new switch group once APICs are upgraded to post-4.0.'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#firmwaremaintenance-groups-when-crossing-40-release"
    if (int(cversion.major1) >= 4) or (tversion and (int(tversion.major1) <= 3)):
        result = NA
        msg = VER_NOT_AFFECTED
    elif (int(cversion.major1) < 4) and not tversion:
        result = MANUAL
        msg = TVER_MISSING
    else:
        groups = icurl('mo', '/uni/fabric.json?query-target=children&target-subtree-class=maintMaintP,firmwareFwP')
        for g in groups:
            result = FAIL_O
            if g.get('maintMaintP'):
                data.append([g['maintMaintP']['attributes']['name'], 'Maintenance Group'])
            else:
                data.append([g['firmwareFwP']['attributes']['name'], 'Firmware Group'])
    return Result(result=result, msg=msg, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="NTP Status")
def ntp_status_check(**kargs):
    result = FAIL_UF
    headers = ["Pod-ID", "Node-ID"]
    data = []
    recommended_action = 'Not Synchronized. Check NTP config and NTP server reachability.'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#ntp-status"
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
            data.append([dn.group('pod'), dn.group('node')])
    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Features that need to be Disabled prior to Upgrade")
def features_to_disable_check(cversion, tversion, **kwargs):
    result = FAIL_O
    headers = ["Feature", "Name", "Status", "Recommended Action"]
    data = []
    recommended_action = 'Disable the feature prior to upgrade'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#features-that-need-to-be-disabled-prior-to-upgrade"

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
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Switch Upgrade Group Guidelines")
def switch_group_guideline_check(**kwargs):
    result = FAIL_O
    headers = ['Group Name', 'Pod-ID', 'Node-IDs', 'Failure Reason']
    data = []
    recommended_action = 'Upgrade nodes in each line above separately in another group.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#switch-upgrade-group-guidelines'

    maints = icurl('class', 'maintMaintGrp.json?rsp-subtree=children')
    if not maints:
        return Result(result=MANUAL, msg='No upgrade groups found!', doc_url=doc_url)

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
                log.error('Failed to parse - %s', key)
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
                log.error('Failed to parse - %s', tDn)
                continue
            f_spines[2][dn.group('pod')].append(int(dn.group('node')))

    apic_leafs = defaultdict(set)
    lldps = icurl('class', 'lldpCtrlrAdjEp.json')
    for lldp in lldps:
        dn = re.search(node_regex, lldp['lldpCtrlrAdjEp']['attributes']['dn'])
        if not dn:
            log.error('Failed to parse - %s', lldp['lldpCtrlrAdjEp']['attributes']['dn'])
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
    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Switch Node /bootflash usage")
def switch_bootflash_usage_check(tversion, **kwargs):
    result = FAIL_UF
    msg = ''
    headers = ["Pod-ID", "Node-ID", "Utilization"]
    data = []
    recommended_action = "Over 50% usage! Contact Cisco TAC for Support"
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#switch-node-bootflash-usage"

    partitions_api = 'eqptcapacityFSPartition.json'
    partitions_api += '?query-target-filter=eq(eqptcapacityFSPartition.path,"/bootflash")'

    download_sts_api = 'maintUpgJob.json'
    download_sts_api += '?query-target-filter=and(eq(maintUpgJob.dnldStatus,"downloaded")'
    download_sts_api += ',eq(maintUpgJob.desiredVersion,"n9000-1{}"))'.format(tversion)

    partitions = icurl('class', partitions_api)
    if not partitions:
        return Result(result=ERROR, msg='bootflash objects not found', doc_url=doc_url)

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
            data.append([pod, node, usage])

    if not data:
        result = PASS
        msg = 'All below 50% or pre-downloaded'
    return Result(result=result, msg=msg, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="L3Out MTU")
def l3out_mtu_check(**kwargs):
    result = MANUAL
    msg = ""
    headers = ["Tenant", "L3Out", "Node Profile", "Logical Interface Profile",
               "Pod", "Node", "Interface", "Type", "IP Address", "MTU"]
    data = []
    unformatted_headers = ['L3 DN', "Type", "IP Address", "MTU"]
    unformatted_data = []
    recommended_action = 'Verify that these MTUs match with connected devices'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l3out-mtu"

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
    return Result(
        result=result,
        msg=msg,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="L3 Port Config (F0467 port-configured-as-l2)")
def port_configured_as_l2_check(**kwargs):
    result = FAIL_O
    headers = ['Fault', 'Tenant', 'L3Out', 'Node', 'Path']
    data = []
    unformatted_headers = ['Fault', 'Fault DN']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing this config or other configs using this port as L2'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l2l3-port-config"

    l2dn_regex = r'uni/tn-(?P<tenant>[^/]+)/out-(?P<l3out>[^/]+)/fd-\[.+rtdOutDef-.+/node-(?P<node>\d{3,4})/(?P<path>.+)/nwissues'
    l2response_json = icurl('class',
                            'faultDelegate.json?&query-target-filter=wcard(faultInst.changeSet,"port-configured-as-l2")')
    for faultDelegate in l2response_json:
        fc = faultDelegate['faultDelegate']['attributes']['code']
        dn = re.search(l2dn_regex, faultDelegate['faultDelegate']['attributes']['dn'])
        if dn:
            data.append([fc, dn.group('tenant'), dn.group('l3out'), dn.group('node'), dn.group('path')])
        else:
            unformatted_data.append([fc, faultDelegate['faultDelegate']['attributes']['dn']])
    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="L2 Port Config (F0467 port-configured-as-l3)")
def port_configured_as_l3_check(**kwargs):
    result = FAIL_O
    headers = ['Fault', 'Pod', 'Node', 'Tenant', 'AP', 'EPG', 'Port']
    data = []
    unformatted_headers = ['Fault', 'Fault DN']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing this config or other configs using this port as L3'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l2l3-port-config"

    l3affected_regex = r'topology/(?P<pod>[^/]+)/(?P<node>[^/]+)/.+uni/tn-(?P<tenant>[^/]+)/ap-(?P<ap>[^/]+)/epg-(?P<epg>\w+).+(?P<port>eth\d+/\d+)'
    l3response_json = icurl('class',
                            'faultDelegate.json?&query-target-filter=wcard(faultInst.changeSet,"port-configured-as-l3")')
    for faultDelegate in l3response_json:
        fc = faultDelegate['faultDelegate']['attributes']['code']
        affected_array = re.search(l3affected_regex, faultDelegate['faultDelegate']['attributes']['dn'])
        if affected_array:
            data.append([
                fc, affected_array.group("pod"), affected_array.group("node"), affected_array.group("tenant"),
                affected_array.group("ap"), affected_array.group("epg"), affected_array.group("port")
            ])
        else:
            unformatted_data.append([fc, faultDelegate['faultDelegate']['attributes']['dn']])
    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="L3Out Subnets (F0467 prefix-entry-already-in-use)")
def prefix_already_in_use_check(**kwargs):
    result = FAIL_O
    headers = ["VRF Name", "Prefix", "L3Out EPGs without F0467", "L3Out EPGs with F0467"]
    headers_old = ["Fault", "Failed L3Out EPG"]
    data = []
    unformatted_headers = ['Fault', 'Fault Description', 'Fault DN']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing the overlapping prefix from the faulted L3Out EPG.'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l3out-subnets"

    # Old versions (pre-CSCvq93592) do not show VRF VNID and prefix in use (2nd line)
    desc_regex = r'Configuration failed for (?P<failedEpg>.+) due to Prefix Entry Already Used in Another EPG'
    desc_regex += r'(.+Prefix entry sys/ctx-\[vxlan-(?P<vrfvnid>\d+)\]/pfx-\[(?P<prefixInUse>.+)\] is in use)?'

    filter = '?query-target-filter=and(wcard(faultInst.changeSet,"prefix-entry-already-in-use"),wcard(faultInst.dn,"uni/epp/rtd"))'
    faultInsts = icurl("class", "faultInst.json" + filter)
    if not faultInsts:
        return Result(result=PASS)

    vnid2vrf = {}
    fvCtxs = icurl("class", "fvCtx.json")
    for fvCtx in fvCtxs:
        vrf_vnid = fvCtx["fvCtx"]["attributes"]["scope"]
        vrf_dn = fvCtx["fvCtx"]["attributes"]["dn"]
        vnid2vrf[vrf_vnid] = vrf_dn

    conflicts = defaultdict(dict)  # vrf -> prefix -> extepgs, faulted_extepgs
    for faultInst in faultInsts:
        code = faultInst["faultInst"]["attributes"]["code"]
        desc = re.search(desc_regex, faultInst["faultInst"]["attributes"]["descr"])
        if not desc:
            unformatted_data.append([
                code,
                faultInst["faultInst"]["attributes"]["descr"],
                faultInst["faultInst"]["attributes"]["dn"],
            ])
            continue

        extepg_dn = desc.group("failedEpg")
        vrf_vnid = desc.group("vrfvnid") if desc.group("vrfvnid") else "_"
        vrf_dn = vnid2vrf.get(vrf_vnid, "_")
        prefix = desc.group("prefixInUse") if desc.group("prefixInUse") else "_"

        # When the L3Out is deployed on multiple switches, the same fault
        # is raised more than once. Skip dup.
        # Old ver: `vrf_dn`, `prefix` are always "_" -> keep one extepg, all in (_, _)
        # New ver: `vrf_dn`, `prefix` are real values -> keep one extepg per (vrf, prefix)
        if prefix not in conflicts[vrf_dn]:
            # Should be only one extepg without a fault per prefix.
            # But use `set()` just in case.
            conflicts[vrf_dn][prefix] = {"extepgs": set(), "faulted_extepgs": set()}
        conflicts[vrf_dn][prefix]["faulted_extepgs"].add(extepg_dn)

    # Old ver: print only the L3Out EPGs with faults
    if conflicts.get("_", {}).get("_", {}).get("faulted_extepgs"):
        data = [["F0467", epg] for epg in conflicts["_"]["_"]["faulted_extepgs"]]
        if not data and not unformatted_data:
            result = PASS
        return Result(
            result=result,
            headers=headers_old,
            data=data,
            unformatted_headers=unformatted_headers,
            unformatted_data=unformatted_data,
            recommended_action=recommended_action,
            doc_url=doc_url,
        )

    # Proceed further only for new versions with VRF/prefix data in faults
    # Get L3Out DNs in the VRFs mentioned by the faults
    l3out2vrf = {}
    l3extRsEctxes = icurl("class", "l3extRsEctx.json")
    for l3extRsEctx in l3extRsEctxes:
        vrf_dn = l3extRsEctx["l3extRsEctx"]["attributes"]["tDn"]
        if vrf_dn in conflicts:
            # l3extRsEctx.dn is always L3Out DN + "/rsectx"
            l3out_dn = l3extRsEctx["l3extRsEctx"]["attributes"]["dn"].split("/rsectx")[0]
            l3out2vrf[l3out_dn] = vrf_dn

    # Get conflicting l3extSubnets
    l3extSubnets = icurl("class", "l3extSubnet.json")
    for l3extSubnet in l3extSubnets:
        l3extSubnet_attr = l3extSubnet["l3extSubnet"]["attributes"]
        l3out_dn = l3extSubnet_attr["dn"].split("/instP-")[0]
        vrf_dn = l3out2vrf.get(l3out_dn)
        if not vrf_dn:
            continue
        # F0467 is only for import-security
        if "import-security" not in l3extSubnet_attr["scope"]:
            continue
        prefix = l3extSubnet_attr["ip"]
        if prefix not in conflicts[vrf_dn]:
            continue
        extepg_dn = l3extSubnet_attr["dn"].split("/extsubnet-")[0]
        if extepg_dn not in conflicts[vrf_dn][prefix]["faulted_extepgs"]:
            conflicts[vrf_dn][prefix]["extepgs"].add(extepg_dn)

    for vrf_dn in conflicts:
        for prefix in conflicts[vrf_dn]:
            for faulted_epg in sorted(conflicts[vrf_dn][prefix]["faulted_extepgs"]):
                data.append([
                    vrf_dn,
                    prefix,
                    ",".join(sorted(conflicts[vrf_dn][prefix]["extepgs"])),
                    faulted_epg,
                ])

    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="Encap Already In Use (F0467 encap-already-in-use)")
def encap_already_in_use_check(**kwargs):
    result = FAIL_O
    headers = ["Faulted EPG/L3Out", "Node", "Port", "In Use Encap(s)", "In Use by EPG/L3Out"]
    data = []
    unformatted_headers = ['Fault Description']
    unformatted_data = []
    recommended_action = 'Resolve the overlapping encap configuration prior to upgrade'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#encap-already-in-use"

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
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="BD Subnets (F1425 subnet-overlap)")
def bd_subnet_overlap_check(**kwargs):
    result = FAIL_O
    headers = ["Fault", "Pod", "Node", "VRF", "Interface", "Address"]
    data = []
    unformatted_headers = ['Fault', 'Fault DN']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing BD subnets causing the overlap'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#bd-subnets"

    dn_regex = node_regex + r'/.+dom-(?P<vrf>[^/]+)/if-(?P<int>[^/]+)/addr-\[(?P<addr>[^/]+/\d{2})'
    faultInsts = icurl('class', 'faultInst.json?query-target-filter=wcard(faultInst.changeSet,"subnet-overlap")')
    if faultInsts:
        for faultInst in faultInsts:
            fc = faultInst['faultInst']['attributes']['code']
            if fc == "F1425":
                dn_array = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
                if dn_array:
                    data.append([fc, dn_array.group("pod"), dn_array.group("node"), dn_array.group("vrf"),
                                 dn_array.group("int"), dn_array.group("addr")])
                else:
                    unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn']])
    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="BD Subnets (F0469 duplicate-subnets-within-ctx)")
def bd_duplicate_subnet_check(**kwargs):
    result = FAIL_O
    headers = ["Fault", "Pod", "Node", "Bridge Domain 1", "Bridge Domain 2"]
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Fault Description']
    unformatted_data = []
    recommended_action = 'Resolve the conflict by removing BD subnets causing the duplicate'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#bd-subnets"

    descr_regex = r'duplicate-subnets-within-ctx: (?P<bd1>.+)\s,(?P<bd2>.+)'
    faultInsts = icurl('class',
                       'faultInst.json?query-target-filter=wcard(faultInst.changeSet,"duplicate-subnets-within-ctx")')
    for faultInst in faultInsts:
        fc = faultInst['faultInst']['attributes']['code']
        dn = re.search(node_regex, faultInst['faultInst']['attributes']['dn'])
        descr = re.search(descr_regex, faultInst['faultInst']['attributes']['descr'])
        if dn and descr:
            data.append([fc, dn.group("pod"), dn.group("node"), descr.group("bd1"), descr.group("bd2")])
        else:
            unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn'], faultInst['faultInst']['attributes']['descr']])
    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="HW Programming Failure (F3544 L3Out Prefixes, F3545 Contracts, actrl-resource-unavailable)")
def hw_program_fail_check(cversion, **kwargs):
    result = FAIL_O
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
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#hw-programming-failure"

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
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        doc_url=doc_url,
    )


@check_wrapper(check_title="Switch SSD Health (F3073, F3074 equipment-flash-warning)")
def switch_ssd_check(**kwargs):
    result = FAIL_O
    headers = ["Fault", "Pod", "Node", "SSD Model", "% Threshold Crossed", "Recommended Action"]
    data = []
    unformatted_headers = ["Fault", "Fault DN", "% Threshold Crossed", "Recommended Action"]
    unformatted_data = []
    thresh = {'F3073': '90%', 'F3074': '80%'}
    recommended_action = {
        'F3073': 'Contact Cisco TAC for replacement procedure',
        'F3074': 'Monitor (no impact to upgrades)'
    }
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#switch-ssd-health"

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
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        doc_url=doc_url,
    )


# Connection Based Check
@check_wrapper(check_title="APIC SSD Health")
def apic_ssd_check(cversion, username, password, **kwargs):
    result = FAIL_UF
    headers = ["Pod", "Node", "Storage Unit", "% lifetime remaining", "Recommended Action"]
    data = []
    unformatted_headers = ["Fault", "Fault DN", "% lifetime remaining", "Recommended Action"]
    unformatted_data = []
    recommended_action = "Contact TAC for replacement"
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#apic-ssd-health"

    has_error = False
    dn_regex = node_regex + r'/.+p-\[(?P<storage>.+)\]-f'
    faultInsts = icurl('class', 'faultInst.json?query-target-filter=eq(faultInst.code,"F2731")')
    adjust_title = False
    if len(faultInsts) == 0 and (cversion.older_than("4.2(7f)") or cversion.older_than("5.2(1g)")):
        controller = icurl('class', 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")')
        if not controller:
            return Result(result=ERROR, msg="topSystem response empty. Is the cluster healthy?", doc_url=doc_url)

        print('')
        adjust_title = True
        report_other = False
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
                data.append([attr['id'], attr['name'], '-', '-', str(e)])
                print_result(node_title, ERROR)
                has_error = True
                continue
            try:
                c.cmd(
                    'grep -oE "SSD Wearout Indicator is [0-9]+"  /var/log/dme/log/svc_ifc_ae.bin.log | tail -1')
            except Exception as e:
                data.append([attr['id'], attr['name'], '-', '-', str(e)])
                print_result(node_title, ERROR)
                has_error = True
                continue

            wearout_ind = re.search(r'SSD Wearout Indicator is (?P<wearout>[0-9]+)', c.output)
            if wearout_ind is not None:
                wearout = wearout_ind.group('wearout')
                if int(wearout) < 5:
                    data.append([pod_id, node_id, "Solid State Disk", wearout, recommended_action])
                    report_other = True
                    print_result(node_title, DONE)
                    continue
                if report_other:
                    data.append([pod_id, node_id, "Solid State Disk", wearout, "No Action Required"])
            print_result(node_title, DONE)
    else:
        headers = ["Fault", "Pod", "Node", "Storage Unit", "% lifetime remaining", "Recommended Action"]
        for faultInst in faultInsts:
            dn_array = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
            lifetime_remaining = "<5%"
            if dn_array:
                data.append(['F2731', dn_array.group("pod"), dn_array.group("node"), dn_array.group("storage"),
                             lifetime_remaining, recommended_action])
            else:
                unformatted_data.append(
                    ['F2731', faultInst['faultInst']['attributes']['dn'], lifetime_remaining, recommended_action])
    if has_error:
        result = ERROR
    elif not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        doc_url=doc_url,
        adjust_title=adjust_title,
    )


@check_wrapper(check_title="Config On APIC Connected Port (F0467 port-configured-for-apic)")
def port_configured_for_apic_check(**kwargs):
    result = FAIL_UF
    headers = ["Fault", "Pod", "Node", "Port", "EPG"]
    data = []
    unformatted_headers = ['Fault', 'Fault DN']
    unformatted_data = []
    recommended_action = 'Remove config overlapping with APIC Connected Interfaces'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#config-on-apic-connected-port"

    dn_regex = node_regex + r'/.+fv-\[(?P<epg>.+)\]/node-\d{3,4}/.+\[(?P<port>eth\d{1,2}/\d{1,2}).+/nwissues'
    faultInsts = icurl('class',
                       'faultInst.json?&query-target-filter=wcard(faultInst.changeSet,"port-configured-for-apic")')
    for faultInst in faultInsts:
        fc = faultInst['faultInst']['attributes']['code']
        dn = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
        if dn:
            data.append([fc, dn.group("pod"), dn.group("node"), dn.group("port"), dn.group("epg")])
        else:
            unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn']])
    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="Overlapping VLAN Pools")
def overlapping_vlan_pools_check(**kwargs):
    result = PASS
    headers = ['Tenant', 'AP', 'EPG', 'Node', 'Port', 'VLAN Scope', 'VLAN ID', 'VLAN Pools (Domains)', 'Impact']
    data = []
    recommended_action = """
    Each node must have only one VLAN pool per VLAN ID across all the ports or across the ports with VLAN scope `portlocal` in the same EPG.'
    When `Impact` shows `Outage`, you must resolve the overlapping VLAN pools.
    When `Impact` shows `Flood Scope`, you should check whether it is ok that STP BPDUs, or any BUM traffic when using Flood-in-Encap, may not be flooded within the same VLAN ID across all the nodes/ports.
    Note that only the nodes causing the overlap are shown above."""
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#overlapping-vlan-pool'

    infraSetPols = icurl('mo', 'uni/infra/settings.json')
    if infraSetPols[0]['infraSetPol']['attributes'].get('validateOverlappingVlans') in ['true', 'yes']:
        return Result(result=PASS, msg="`Enforce EPG VLAN Validation` is enabled. No need to check overlapping VLANs")

    # Get VLAN pools and ports from access policy
    mo_classes = AciAccessPolicyParser.get_classes()
    filter = '?query-target=subtree&target-subtree-class=' + ','.join(mo_classes)
    infra_mos = icurl('class', 'infraInfra.json' + filter)
    mos = AciAccessPolicyParser(infra_mos)

    # Get EPG port deployments
    epg_regex = r'uni/tn-(?P<tenant>[^/]+)/ap-(?P<ap>[^/]+)/epg-(?P<epg>[^/]+)'
    conn_regex = (
        r"uni/epp/fv-\[" + epg_regex + r"]/"
        r"node-(?P<node>\d+)/"
        r"(?:"
        r"(?:ext)?stpathatt-\[(?P<stport>[^\]]+)\](:?-extchid-(?P<stfex>\d+))?|"  # static port binding
        r"dyatt-\[.+(?:ext(?:prot)?paths-(?P<dyfex>\d+)/)?pathep-\[(?P<dyport>[^\]]+)\]\]|"  # dynamic port binding
        r"attEntitypathatt-\[(?P<aep>.+)\]"  # AEP binding
        r")/"
        r".*\[vlan-(?P<vlan>\d+)"
    )
    # uni/epp/fv-[{epgPKey}]/node-{id}/stpathatt-[{pathName}]/conndef/conn-[{encap}]-[{addr}]
    # uni/epp/fv-[{epgPKey}]/node-{id}/extstpathatt-[{pathName}]-extchid-{extChId}/conndef/conn-[{encap}]-[{addr}]
    # uni/epp/fv-[{epgPKey}]/node-{id}/dyatt-[{targetDn}]/conndef/conn-[{encap}]-[{addr}]
    # uni/epp/fv-[{epgPKey}]/node-{id}/attEntitypathatt-[{pathName}]/conndef/conn-[{encap}]-[{addr}]
    ports_per_epg = defaultdict(list)
    fvIfConns = icurl('class', 'fvIfConn.json')
    for fvIfConn in fvIfConns:
        dn = re.search(conn_regex, fvIfConn['fvIfConn']['attributes']['dn'])
        if not dn:
            continue
        epg_key = ':'.join([dn.group('tenant'), dn.group('ap'), dn.group('epg')])
        port_keys = []
        if not dn.group('aep'):
            fex = dn.group('stfex') if dn.group('stfex') else dn.group('dyfex')
            port = dn.group('stport') if dn.group('stport') else dn.group('dyport')
            if fex:
                port_keys.append('/'.join([dn.group('node'), fex, port]))
            else:
                port_keys.append('/'.join([dn.group('node'), port]))
        else:
            for port_key, port_data in iteritems(mos.port_data):
                if port_data.get('aep_name') == dn.group('aep') and port_data.get('node') == dn.group('node'):
                    port_keys.append(port_key)
        for port_key in port_keys:
            port_data = mos.port_data.get(port_key)
            if not port_data:
                continue
            ports_per_epg[epg_key].append({
                'tenant': str(dn.group('tenant')),
                'ap': str(dn.group('ap')),
                'epg': str(dn.group('epg')),
                'node': str(port_data.get('node', '')),
                'fex': str(port_data.get('fex', '')),
                'port': str(port_data.get('port', '')),
                'vlan': str(dn.group('vlan')),
                'aep': str(port_data.get('aep_name', '')),
                'domain_dns': port_data.get('domain_dns', []),
                'pc_type': str(port_data.get('pc_type', '')),
                'vlan_scope': str(port_data.get('vlan_scope', '')),
            })

    # Check overlapping VLAN pools per EPG
    epg_filter = '?rsp-subtree-include=required&rsp-subtree=children&rsp-subtree-class=fvRsDomAtt'
    fvAEPgs_with_domains = icurl('class', 'fvAEPg.json' + epg_filter)
    for fvAEPg in fvAEPgs_with_domains:
        # `rsp-subtree-include=required` ensures that fvRsDomAtt are the only children
        rsDoms = fvAEPg['fvAEPg']['children']
        rsDom_dns = [rsDom['fvRsDomAtt']['attributes']['tDn'] for rsDom in rsDoms]

        overlap_vlan_ids = set()
        for i in range(len(rsDoms)):
            for j in range(i + 1, len(rsDoms)):
                i_dn = rsDoms[i]['fvRsDomAtt']['attributes']['tDn']
                j_dn = rsDoms[j]['fvRsDomAtt']['attributes']['tDn']
                i_vpool = mos.vpool_per_dom.get(i_dn)
                j_vpool = mos.vpool_per_dom.get(j_dn)
                # domains that do not have VLAN pools attached
                if not i_vpool or not j_vpool:
                    continue
                if i_vpool['name'] != j_vpool['name']:
                    overlap_vlan_ids.update(
                        set(i_vpool['vlan_ids']).intersection(j_vpool['vlan_ids'])
                    )

        if not overlap_vlan_ids:
            continue

        ports_per_node = defaultdict(dict)
        epg_dn = re.search(epg_regex, fvAEPg['fvAEPg']['attributes']['dn'])
        epg_key = ':'.join([epg_dn.group('tenant'), epg_dn.group('ap'), epg_dn.group('epg')])
        epg_ports = ports_per_epg.get(epg_key, [])
        for port in epg_ports:
            vlan_id = int(port['vlan'])
            if vlan_id not in overlap_vlan_ids:
                continue

            # Get domains that are attached to the port and the EPG
            common_domain_dns = set(port['domain_dns']).intersection(rsDom_dns)
            # Get VLAN pools for the VLAN ID of the port
            # Also store domains for each VLAN pool for the final output
            inuse_vpools = defaultdict(list)
            for dom_dn in common_domain_dns:
                vpool = mos.vpool_per_dom.get(dom_dn, {})
                if vlan_id not in vpool.get('vlan_ids', []):
                    continue
                inuse_vpools[vpool['name']].append(vpool['dom_name'])
            if not inuse_vpools:
                continue

            # len(inuse_vpools) == 1 at this point means that there is no
            # overlapping VLAN pool issue with this port alone.
            # But do not skip such a port yet because there may be another port
            # on the same node with the same VLAN ID with a different VLAN pool.
            port['inuse_vpools'] = inuse_vpools
            vlan_scope = port.get('vlan_scope', 'global')
            # handle all non-portlocal scope as global
            if vlan_scope not in ['global', 'portlocal']:
                vlan_scope = 'global'
            if vlan_id not in ports_per_node[port['node']]:
                ports_per_node[port['node']][vlan_id] = {}
            if vlan_scope not in ports_per_node[port['node']][vlan_id]:
                ports_per_node[port['node']][vlan_id][vlan_scope] = []
            ports_per_node[port['node']][vlan_id][vlan_scope].append(port)

        for ports_per_vlanid in ports_per_node.values():
            for ports_per_scope in ports_per_vlanid.values():
                for ports in ports_per_scope.values():
                    inuse_vpools_across_ports = set()
                    has_vpc = False
                    for port in ports:
                        inuse_vpools_across_ports.update(
                            port.get('inuse_vpools', {}).keys()
                        )
                        if port.get('pc_type') == 'vpc':
                            has_vpc = True

                    # All ports on the node with the same VLAN ID use the same VLAN pool
                    if len(inuse_vpools_across_ports) < 2:
                        continue

                    if has_vpc:
                        result = FAIL_O
                    elif result == PASS:
                        result = MANUAL
                    impact = 'Outage' if has_vpc else 'Flood Scope'
                    for port in ports:
                        node = port['node']
                        if port.get('fex') != "0":
                            node += '(FEX {})'.format(port['fex'])
                        vpool_domains = []
                        for v_name, d_names in iteritems(port.get('inuse_vpools', {})):
                            vpool_domains.append(
                                '{}({})'.format(v_name, ','.join(sorted(d_names)))
                            )
                        data.append([
                            port['tenant'],
                            port['ap'],
                            port['epg'],
                            node,
                            port['port'],
                            port['vlan_scope'],
                            port['vlan'],
                            ', '.join(vpool_domains),
                            impact,
                        ])
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Scalability (faults related to Capacity Dashboard)")
def scalability_faults_check(**kwargs):
    result = FAIL_O
    headers = ["Fault", "Pod", "Node", "Description"]
    data = []
    unformatted_headers = ["Fault", "Fault DN", "Description"]
    unformatted_data = []
    recommended_action = 'Review config and reduce the usage'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#scalability-faults-related-to-capacity-dashboard"

    faultInsts = icurl('class', 'eqptcapacityEntity.json?rsp-subtree-include=faults,no-scoped')
    for fault in faultInsts:
        if not fault.get('faultInst'):
            continue
        f = fault['faultInst']['attributes']
        dn = re.search(node_regex, f['dn'])
        if dn:
            data.append([f['code'], dn.group('pod'), dn.group('node'), f['descr']])
        else:
            unformatted_data.append([f['code'], f['dn'], f['descr']])
    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="APIC Disk Space Usage (F1527, F1528, F1529 equipment-full)")
def apic_disk_space_faults_check(cversion, **kwargs):
    result = FAIL_UF
    headers = ['Fault', 'Pod', 'Node', 'Mount Point', 'Current Usage %', 'Recommended Action']
    data = []
    unformatted_headers = ['Fault', 'Fault DN', 'Recommended Action']
    unformatted_data = []
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#apic-disk-space-usage"
    recommended_action = {
        '/firmware': 'Remove unneeded images',
        '/techsupport': 'Remove unneeded techsupports/cores'
    }
    default_action = 'Contact Cisco TAC.'
    if cversion.same_as('4.0(1h)') or cversion.older_than('3.2(6i)'):
        default_action += ' A typical issue is CSCvn13119.'

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
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        doc_url=doc_url,
    )


@check_wrapper(check_title="L3Out Route Map import/export direction")
def l3out_route_map_direction_check(**kwargs):
    """ Implementation change due to CSCvm75395 - 4.1(1) """
    result = FAIL_O
    headers = ["Tenant", "L3Out", "External EPG", "Subnet", "Subnet Scope",
               "Route Map", "Direction", "Recommended Action", ]
    data = []
    recommended_action = 'The subnet scope must have {}-rtctrl'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l3out-route-map-importexport-direction"

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
    return Result(result=result, headers=headers, data=data, doc_url=doc_url)


@check_wrapper(check_title="L3Out Route Map Match Rule with missing-target")
def l3out_route_map_missing_target_check(cversion, tversion, **kwargs):
    """ Implementation change due to CSCwc11570 - 5.2.8/6.0.2 """
    result = FAIL_O
    headers = ['Tenant', 'L3Out', 'Route Map', 'Context', 'Action', 'Match Rule']
    data = []
    recommended_action = 'The configured match rules do not exist. Update the route maps with existing match rules.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l3out-route-map-match-rule-with-missing-target'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    def is_old(v):
        return True if v.older_than("5.2(8a)") or v.simple_version == "6.0(1)" else False

    c_is_old = is_old(cversion)
    t_is_old = is_old(tversion)
    if (c_is_old and t_is_old) or (not c_is_old and not t_is_old):
        return Result(result=NA, msg=VER_NOT_AFFECTED)

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
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="L3Out Loopback IP Overlap With L3Out Interfaces")
def l3out_overlapping_loopback_check(**kwargs):
    result = FAIL_O
    headers = ['Tenant:VRF', 'Node ID', 'Loopback IP (Tenant:L3Out:NodeP)', 'Interface IP (Tenant:L3Out:NodeP:IFP)']
    data = []
    recommended_action = 'Change either the loopback or L3Out interface IP subnet to avoid overlap.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l3out-loopback-ip-overlap-with-l3out-interfaces'

    tn_regex = r'uni/tn-(?P<tenant>[^/]+)/'
    path_regex = r'topology/pod-(?P<pod>\d+)/(?:prot)?paths-(?P<node1>\d+)(?:-(?P<node2>\d+))?'

    vrfs = defaultdict(dict)
    api = 'l3extOut.json'
    api += '?rsp-subtree=full'
    api += '&rsp-subtree-class=l3extRsEctx,l3extRsNodeL3OutAtt,l3extLoopBackIfP,l3extRsPathL3OutAtt,l3extMember'
    l3outs = icurl('class', api)
    for l3out in l3outs:
        vrf = ""
        loopback_ips = defaultdict(list)
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
                            log.error('Failed to parse tDn - %s', node['attributes']['tDn'])
                            continue
                        node_id = m.group('node')

                        config = ':'.join([tenant_name, l3out_name, nodep_name])
                        if node['attributes']['rtrIdLoopBack'] == 'yes':
                            loopback_ips[node_id].append({
                                'addr': node['attributes']['rtrId'],
                                'config': config,
                            })
                        else:
                            for lb in node.get('children', []):
                                # One l3extLoopBackIfP per node for each IPv4/v6
                                if not lb.get('l3extLoopBackIfP'):
                                    continue
                                loopback_ip = lb['l3extLoopBackIfP']['attributes']['addr']
                                # Strip the subnet mask (/32, /128) if any
                                lo_addr = loopback_ip.split("/")[0]
                                loopback_ips[node_id].append({
                                    'addr': lo_addr,
                                    'config': config,
                                })
                    # Get interface IPs for each node
                    elif np_child.get('l3extLIfP'):
                        ifp_name = np_child['l3extLIfP']['attributes']['name']
                        for ifp_child in np_child['l3extLIfP'].get('children', []):
                            if not ifp_child.get('l3extRsPathL3OutAtt'):
                                continue
                            port = ifp_child['l3extRsPathL3OutAtt']
                            m = re.search(path_regex, port['attributes']['tDn'])
                            if not m:
                                log.error('Failed to parse tDn - %s', port['attributes']['tDn'])
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
            vrfs[vrf][node]['loopbacks'] = vrfs[vrf][node].get('loopbacks', []) + loopback_ips[node]
        for node in interface_ips:
            if not vrfs[vrf].get(node):
                vrfs[vrf][node] = {}
            vrfs[vrf][node]['interfaces'] = vrfs[vrf][node].get('interfaces', []) + interface_ips[node]

    # Check overlaps
    for vrf in vrfs:
        for node in vrfs[vrf]:
            loopbacks = vrfs[vrf][node].get('loopbacks')
            interfaces = vrfs[vrf][node].get('interfaces')
            if not loopbacks or not interfaces:
                continue
            for interface in interfaces:
                for loopback in loopbacks:
                    if IPAddress.ip_in_subnet(loopback['addr'], interface['addr']):
                        data.append([
                            vrf,
                            node,
                            '{} ({})'.format(loopback['addr'], loopback['config']),
                            '{} ({})'.format(interface['addr'], interface['config']),
                        ])
    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="BGP Peer Profile at node level without Loopback")
def bgp_peer_loopback_check(**kwargs):
    """ Implementation change due to CSCvm28482 - 4.1(2) """
    result = FAIL_O
    headers = ["Tenant", "L3Out", "Node Profile", "Pod", "Node"]
    data = []
    recommended_action = 'Configure a loopback or configure bgpPeerP under interfaces instead of nodes'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#bgp-peer-profile-at-node-level-without-loopback"

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
                        dn.group('pod'), dn.group('node')])
    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Different infra VLAN via LLDP (F0454 infra-vlan-mismatch)")
def lldp_with_infra_vlan_mismatch_check(**kwargs):
    result = FAIL_O
    headers = ["Fault", "Pod", "Node", "Port"]
    data = []
    unformatted_headers = ["Fault", "Fault DN", "Failure Reason"]
    unformatted_data = []
    recommended_action = 'Disable LLDP on this port if it is expected to receive LLDP with a mismatched infra VLAN'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#different-infra-vlan-via-lldp"

    dn_regex = node_regex + r'/sys/lldp/inst/if-\[(?P<port>eth\d{1,2}/\d{1,2})\]/fault-F0454'
    faultInsts = icurl('class',
                       'faultInst.json?query-target-filter=and(eq(faultInst.code,"F0454"),wcard(faultInst.changeSet,"infra-vlan-mismatch"))')
    for faultInst in faultInsts:
        fc = faultInst['faultInst']['attributes']['code']
        dn = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
        if dn:
            data.append([fc, dn.group("pod"), dn.group("node"), dn.group("port")])
        else:
            unformatted_data.append([fc, faultInst['faultInst']['attributes']['dn']])
    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


# Connection Based Check
@check_wrapper(check_title="APIC Target version image and MD5 hash")
def apic_version_md5_check(tversion, username, password, **kwargs):
    result = FAIL_UF
    headers = ['APIC', 'Firmware', 'md5sum', 'Failure']
    data = []
    recommended_action = 'Delete the firmware from APIC and re-download'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#apic-target-version-image-and-md5-hash"

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    image_validaton = True
    mo = icurl('mo', 'fwrepo/fw-aci-apic-dk9.%s.json' % tversion.dot_version)
    for fm_mo in mo:
        if fm_mo.get("firmwareFirmware"):
            desc = fm_mo["firmwareFirmware"]['attributes']["description"]
            md5 = fm_mo["firmwareFirmware"]['attributes']["checksum"]
            if "Image signing verification failed" in desc:
                data.append(["All", str(tversion), md5, 'Target image is corrupted'])
                image_validaton = False

    if not image_validaton:
        return Result(result=FAIL_UF, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)

    md5s = []
    md5_names = []

    has_error = False
    prints('')
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
            data.append([apic_name, '-', '-', str(e)])
            print_result(node_title, ERROR)
            has_error = True
            continue

        try:
            c.cmd("ls -aslh /firmware/fwrepos/fwrepo/aci-apic-dk9.%s.bin" %
                  tversion.dot_version)
        except Exception as e:
            data.append([apic_name, '-', '-',
                         'ls command via ssh failed due to:{}'.format(str(e))])
            print_result(node_title, ERROR)
            has_error = True
            continue
        if "No such file or directory" in c.output:
            data.append([apic_name, str(tversion), '-', 'image not found'])
            print_result(node_title, FAIL_UF)
            continue

        try:
            c.cmd("cat /firmware/fwrepos/fwrepo/md5sum/aci-apic-dk9.%s.bin" %
                  tversion.dot_version)
        except Exception as e:
            data.append([apic_name, str(tversion), '-',
                         'failed to check md5sum via ssh due to:{}'.format(str(e))])
            print_result(node_title, ERROR)
            has_error = True
            continue
        if "No such file or directory" in c.output:
            data.append([apic_name, str(tversion), '-', 'md5sum file not found'])
            print_result(node_title, FAIL_UF)
            continue
        for line in c.output.split("\n"):
            words = line.split()
            if (
                    len(words) == 2 and
                    words[1].startswith("/var/run/mgmt/fwrepos/fwrepo/aci-apic")
            ):
                md5s.append(words[0])
                md5_names.append(apic_name)
                break
        else:
            data.append([apic_name, str(tversion), '-', 'unexpected output when checking md5sum file'])
            print_result(node_title, ERROR)
            has_error = True
            continue

        print_result(node_title, DONE)
    if len(set(md5s)) > 1:
        for name, md5 in zip(md5_names, md5s):
            data.append([name, str(tversion), md5, 'md5sum do not match on all APICs'])
    if has_error:
        result = ERROR
    elif not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url, adjust_title=True)


# Connection Based Check
@check_wrapper(check_title="Standby APIC Disk Space Usage")
def standby_apic_disk_space_check(**kwargs):
    result = FAIL_UF
    msg = ''
    headers = ['SN', 'OOB', 'Mount Point', 'Current Usage %', 'Details']
    data = []
    recommended_action = 'Contact Cisco TAC'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#standby-apic-disk-space-usage"
    threshold = 75  # usage (%)

    has_error = False
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
            data.append([stb['mbSn'], stb['oobIpAddr'], '-', '-', str(e)])
            has_error = True
            continue

        try:
            c.cmd("df -h")
        except Exception as e:
            data.append([stb['mbSn'], stb['oobIpAddr'], '-', '-', str(e)])
            has_error = True
            continue

        for line in c.output.split("\n"):
            if "Filesystem" not in line and "df" not in line:
                fs_regex = r'([^\s]+) +([^\s]+) +([^\s]+) +([^\s]+) +([^\s]+)%'
                fs = re.search(fs_regex, line)
                if fs is not None:
                    directory = fs.group(1)
                    usage = fs.group(5)
                    if int(usage) >= threshold:
                        data.append([stb['mbSn'], stb['oobIpAddr'], directory, usage, '-'])
    if not infraSnNodes:
        result = NA
        msg = 'No standby APIC found'
    elif has_error:
        result = ERROR
    elif not data:
        result = PASS
        msg = 'all below {}%'.format(threshold)
    return Result(result=result, msg=msg, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Remote Leaf Compatibility")
def r_leaf_compatibility_check(tversion, **kwargs):
    result = PASS
    headers = ['Target Version', 'Remote Leaf', 'Direct Traffic Forwarding']
    data = []
    recommended_action_4_2_2 = 'Upgrade remote leaf nodes before spine nodes or\ndisable Direct Traffic Forwarding (CSCvs16767)'
    recommended_action_5a = 'Direct Traffic Forwarding is required on 5.0 or later. Enable the feature before the upgrade'
    recommended_action_5b = ('Direct Traffic Forwarding is required on 5.0 or later.\n'
                             'Upgrade to 4.1(2)-4.2(x) first to enable the feature before upgrading to 5.0 or later.')
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#compatibility-remote-leaf-switch"

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    remote_leafs = icurl('class', 'fabricNode.json?&query-target-filter=eq(fabricNode.nodeType,"remote-leaf-wan")')
    if not remote_leafs:
        return Result(result=NA, msg="No Remote Leaf Found")

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
        data.append([str(tversion), "Present", direct_enabled])
    return Result(result=result, headers=headers, data=data, recommended_action=ra, doc_url=doc_url)


@check_wrapper(check_title="EP Announce Compatibility")
def ep_announce_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ['Susceptible Defect', 'Recommended Action']
    data = []
    recommended_action = ('For fabrics running a pre-12.2(4p) ACI switch release, '
                          'upgrade to 12.2(4r) and then upgrade to the desired destination release.\n'
                          'For fabrics running a 12.3(1) ACI switch release, '
                          'upgrade to 13.1(2v) and then upgrade to the desired destination release.')

    fixed_versions = ["2.2(4p)", "2.2(4q)", "2.2(4r)"]
    current_version_affected = False
    target_version_affected = False

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

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
    return Result(result=result, headers=headers, data=data)


@check_wrapper(check_title="VMM Domain Controller Status")
def vmm_controller_status_check(**kwargs):
    result = PASS
    headers = ['VMM Domain', 'vCenter IP or Hostname', 'Current State']
    data = []
    recommended_action = 'Check network connectivity to the vCenter.'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#vmm-domain-controller-status"

    vmmDoms = icurl('class', 'compCtrlr.json')
    if not vmmDoms:
        return Result(result=NA, msg='No VMM Domains Found')
    for dom in vmmDoms:
        if dom['compCtrlr']['attributes']['operSt'] == "offline":
            domName = dom['compCtrlr']['attributes']['domName']
            hostOrIp = dom['compCtrlr']['attributes']['hostOrIp']
            result = FAIL_O
            data.append([domName, hostOrIp, "offline"])
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="VMM Domain LLDP/CDP Adjacency Status")
def vmm_controller_adj_check(**kwargs):
    result = PASS
    msg = ''
    headers = ['VMM Domain', 'Host IP or Hostname']
    data = []
    unformatted_headers = ['Fault', 'Fault DN']
    unformatted_data = []
    recommended_action = 'Ensure consistent use of expected Discovery Protocol from Hypervisor to ACI Leaf.'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#vmm-domain-lldpcdp-adjacency-status"

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
                    result = FAIL_O
                    if r1 and r2:
                        host = r1.group("host")
                        dom = r2.group("dom")
                        data.append([dom, host])
                    else:
                        unformatted_data.append([adj['faultInst']['attributes']['code'], adj['faultInst']['attributes']['dn']])
    return Result(
        result=result,
        msg=msg,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="VPC-paired Leaf switches")
def vpc_paired_switches_check(vpc_node_ids, **kwargs):
    result = PASS
    headers = ["Node ID", "Node Name"]
    data = []
    recommended_action = 'Determine if dataplane redundancy is available if these nodes go down.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#vpc-paired-leaf-switches'

    top_system = icurl('class', 'topSystem.json')
    for node in top_system:
        node_id = node['topSystem']['attributes']['id']
        role = node['topSystem']['attributes']['role']
        if role == 'leaf' and (node_id not in vpc_node_ids):
            result = MANUAL
            name = node['topSystem']['attributes']['name']
            data.append([node_id, name])

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="APIC CIMC Compatibility")
def cimc_compatibilty_check(tversion, **kwargs):
    result = FAIL_UF
    headers = ["Node ID", "Model", "Current CIMC version", "Catalog Recommended CIMC Version", "Warning"]
    data = []
    recommended_action = 'Check Release note of APIC Model/version for latest recommendations.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#compatibility-cimc-version'

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
                    if not compatMo:
                        msg = "No compatibility information found for {}/{}".format(model, tversion.simple_version)
                        return Result(result=MANUAL, msg=msg, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)
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
            return Result(result=MANUAL, msg="eqptCh does not have cimcVersion parameter on this version", headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)
    else:
        return Result(result=MANUAL, msg=TVER_MISSING)

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Intersight Device Connector upgrade status")
def intersight_upgrade_status_check(**kwargs):
    result = FAIL_UF
    msg = ''
    headers = ["Connector Status"]
    data = []
    recommended_action = 'Wait a few minutes for the upgrade to complete'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#intersight-device-connector-upgrade-status'

    cmd = ['icurl', '-gks', 'https://127.0.0.1/connector/UpgradeStatus']

    log.info('cmd = ' + ' '.join(cmd))
    response = subprocess.check_output(cmd)
    try:
        resp_json = json.loads(response)

        try:
            if resp_json[0]['Status'] != 'Idle':
                data.append([resp_json[0]['UpgradeNotification']])
        except KeyError:
            if resp_json['code'] == 'InternalServerError':
                msg = 'Connector reporting InternalServerError, Non-Upgrade issue'

        if not data:
            result = PASS

    except ValueError:
        result = NA
        msg = 'Intersight Device Connector not responding'

    return Result(result=result, msg=msg, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="ISIS Redistribution metric for MPod/MSite")
def isis_redis_metric_mpod_msite_check(**kwargs):
    result = FAIL_O
    headers = ["ISIS Redistribution Metric", "MPod Deployment", "MSite Deployment"]
    data = []
    recommended_action = ""
    doc_url = 'http://cs.co/9001zNNr7'  # "ISIS Redistribution Metric" from ACI Best Practices Quick Summary

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
        data.append([redistribMetric, mpod, msite])
    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="BGP route target type for GOLF over L2EVPN")
def bgp_golf_route_target_type_check(cversion, tversion, **kwargs):
    result = FAIL_O
    headers = ["VRF DN", "Global Name", "Route Target"]
    data = []
    recommended_action = "Reconfigure extended: RT with prefix route-target: "
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvm23100'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

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
                                    data.append([vrfdn, globalname, bgprt['bgpRtTarget']['attributes']['rt']])
    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="APIC Container Bridge IP Overlap with APIC TEP")
def docker0_subnet_overlap_check(**kwargs):
    result = PASS
    headers = ["Container Bridge IP", "APIC TEP"]
    data = []
    recommended_action = 'Change the container bridge IP via "Apps > Settings" on the APIC GUI'
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#apic-container-bridge-ip-overlap-with-apic-tep"

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
            data.append([tep, bip])

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Eventmgr DB size defect susceptibility")
def eventmgr_db_defect_check(cversion, **kwargs):
    result = PASS
    headers = ["Potential Defect", "Doc URL"]
    data = []
    recommended_action = 'Contact Cisco TAC to check the DB size via root'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#eventmgr-db-size-defect-susceptibility'

    if cversion.older_than('3.2(5d)') or (cversion.major1 == '4' and cversion.older_than('4.1(1i)')):
        data.append(['CSCvn20175', 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvn20175'])
    if cversion.older_than('4.2(4i)') or (cversion.major1 == '5' and cversion.older_than('5.0(1k)')):
        data.append(['CSCvt07565', 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvt07565'])

    if data:
        result = FAIL_UF

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Target version compatibility")
def target_version_compatibility_check(cversion, tversion, **kwargs):
    result = FAIL_UF
    headers = ["Current version", "Target Version", "Warning"]
    data = []
    recommended_action = ''
    doc_url = 'APIC Upgrade/Downgrade Support Matrix - http://cs.co/9005ydMQP'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)
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
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Gen 1 switch compatibility")
def gen1_switch_compatibility_check(tversion, **kwargs):
    result = FAIL_UF
    headers = ["Target Version", "Node ID", "Model", "Warning"]
    gen1_models = ["N9K-C9336PQ", "N9K-X9736PQ", "N9K-C9504-FM", "N9K-C9508-FM", "N9K-C9516-FM", "N9K-C9372PX-E",
                   "N9K-C9372TX-E", "N9K-C9332PQ", "N9K-C9372PX", "N9K-C9372TX", "N9K-C9396PX", "N9K-C9396TX",
                   "N9K-C93128TX"]
    data = []
    recommended_action = 'Select supported target version or upgrade hardware'
    doc_url = 'http://cs.co/9001ydKCV'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)
    if tversion.newer_than("5.0(1a)"):
        fabric_node = icurl('class', 'fabricNode.json')
        for node in fabric_node:
            if node['fabricNode']['attributes']['model'] in gen1_models:
                data.append([str(tversion), node['fabricNode']['attributes']['id'],
                            node['fabricNode']['attributes']['model'], 'Not supported on 5.x+'])
    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Contract Port 22 Defect")
def contract_22_defect_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["Potential Defect", "Reason"]
    data = []
    recommended_action = 'Review Cisco Software Advisory Notices for CSCvz65560'
    doc_url = 'http://cs.co/9007yh22H'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if cversion.older_than("5.0(1a)") and (tversion.newer_than("5.0(1a)") and
                                           tversion.older_than("5.2(2g)")):
        result = FAIL_O
        data.append(["CSCvz65560", "Target Version susceptible to Defect"])

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Link Level Flow Control")
def llfc_susceptibility_check(cversion, tversion, vpc_node_ids, **kwargs):
    result = PASS
    headers = ["Pod", "NodeId", "Int", "Type", "BugId", "Warning"]
    data = []
    sx_affected = t_affected = False
    recommended_action = 'Manually change Peer devices Transmit(send) Flow Control to off prior to switch Upgrade'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvo27498'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if not vpc_node_ids:
        return Result(result=PASS, msg="No VPC Nodes found. Not susceptible.")

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

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="telemetryStatsServerP Object")
def telemetryStatsServerP_object_check(sw_cversion, tversion, **kwargs):
    result = PASS
    headers = ["Current version", "Target Version", "Warning"]
    data = []
    recommended_action = 'Change telemetryStatsServerP.collectorLocation to "none" prior to upgrade'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#telemetrystatserverp-object'

    if not sw_cversion:
        return Result(result=MANUAL, msg="Current switch version not found. Check switch health.")

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if sw_cversion.older_than("4.2(4d)") and tversion.newer_than("5.2(2d)"):
        telemetryStatsServerP_json = icurl('class', 'telemetryStatsServerP.json')
        for serverp in telemetryStatsServerP_json:
            if serverp["telemetryStatsServerP"]["attributes"].get("collectorLocation") == "apic":
                result = FAIL_O
                data.append([str(sw_cversion), str(tversion), 'telemetryStatsServerP.collectorLocation = "apic" Found'])

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Internal VLAN Pool")
def internal_vlanpool_check(tversion, **kwargs):
    result = PASS
    headers = ["VLAN Pool", "Internal VLAN Block(s)", "Non-AVE Domain", "Warning"]
    data = []
    recommended_action = 'Ensure Leaf Front-Panel VLAN Blocks are explicitly set to "external (on the wire)"'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvw33061'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

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

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="APIC CA Cert Validation")
def apic_ca_cert_validation(**kwargs):
    result = FAIL_O
    headers = ["Certreq Response"]
    data = []
    recommended_action = "Contact Cisco TAC to fix APIC CA Certs"
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvy35257'

    certreq_out = kwargs.get("certreq_out")
    if not certreq_out:
        pki_fabric_ca_mo = icurl('class', 'pkiFabricSelfCAEp.json')
        if pki_fabric_ca_mo:
            # Prep csr
            passphrase = pki_fabric_ca_mo[0]['pkiFabricSelfCAEp']['attributes']['currCertReqPassphrase']
            cert_gen_filename = "preupgrade_gen.cnf"
            key_pem = 'preupgrade_temp.key.pem'
            csr_pem = 'preupgrade_temp.csr.pem'
            sign = 'preupgrade_temp.sign'
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
            # Re-run cleanup for Issue #120
            if os.path.exists(cert_gen_filename):
                log.debug('CA CHECK file found and removed: ' + ''.join(cert_gen_filename))
                os.remove(cert_gen_filename)
            if os.path.exists(key_pem):
                log.debug('CA CHECK file found and removed: ' + ''.join(key_pem))
                os.remove(key_pem)
            if os.path.exists(csr_pem):
                log.debug('CA CHECK file found and removed: ' + ''.join(csr_pem))
                os.remove(csr_pem)
            if os.path.exists(sign):
                log.debug('CA CHECK file found and removed: ' + ''.join(sign))
                os.remove(sign)

            with open(cert_gen_filename, 'w') as f:
                f.write(cert_gen_cnf)

            # Generate csr for certreq
            cmd = 'openssl genrsa -out ' + key_pem + ' 2048'
            cmd = cmd + ' && openssl req -config ' + cert_gen_filename + ' -new -key ' + key_pem + ' -out ' + csr_pem
            cmd = cmd + ' && openssl dgst -sha256 -hmac ' + passphrase + ' -out ' + sign + ' ' + csr_pem
            log.debug('cmd = '+''.join(cmd))
            genrsa_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            genrsa_proc.communicate()[0].strip()
            if genrsa_proc.returncode != 0:
                return Result(result=ERROR, msg="openssl cmd issue, send logs to TAC.")

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
            log.debug('cmd = ' + ''.join(cmd))
            certreq_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            certreq_out = certreq_proc.communicate()[0].strip()

    log.debug(certreq_out)
    if '"error":{"attributes"' in str(certreq_out):
        # Spines can crash on 5.2(6e)+, but APIC CA Certs should be fixed regardless of tver
        data.append([certreq_out])

    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="FabricDomain Name")
def fabricdomain_name_check(cversion, tversion, **kwargs):
    result = FAIL_O
    headers = ["FabricDomain", "Reason"]
    data = []
    recommended_action = "Do not upgrade to 6.0(2)"
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwf80352'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if tversion.same_as("6.0(2h)"):
        controller = icurl('class', 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")')
        if not controller:
            return Result(result=ERROR, msg='topSystem response empty. Is the cluster healthy?')

        fabricDomain = controller[0]['topSystem']['attributes']['fabricDomain']
        if re.search(r'#|;', fabricDomain):
            data.append([fabricDomain, "Contains a special character"])

    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Spine SUP HW Revision")
def sup_hwrev_check(cversion, tversion, **kwargs):
    result = FAIL_O
    headers = ["Pod", "Node", "Sup Slot", "Part Number", "VRM Concern", "FPGA Concern"]
    data = []
    recommended_action = "Review Field Notice FN74050 within Reference Document for all details."
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#spine-sup-hw-revision'
    vrm_concern = False
    fpga_concern = False

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if cversion.older_than("5.2(8f)"):
        vrm_concern = True
        recommended_action += "\n\tFor VRM Concern: Consider vrm_update script within FN74050"

    if (
            cversion.newer_than("5.2(1a)") and cversion.older_than("6.0(1a)")
            and tversion.older_than("5.2(8f)") or (tversion.major1 == "6" and tversion.older_than("6.0(3d)"))
       ):
        fpga_concern = True
        recommended_action += "\n\tFor FPGA Concern: Consider a target version with fix for CSCwb86706"

    if vrm_concern or fpga_concern:
        sup_re = r'/.+(?P<supslot>supslot-\d+)'
        sups = icurl('class', 'eqptSpCmnBlk.json?&query-target-filter=wcard(eqptSpromSupBlk.dn,"sup")')
        if not sups:
            return Result(result=ERROR, msg='No sups found. This is unlikely.')

        for sup in sups:
            prtNum = sup['eqptSpCmnBlk']['attributes']['prtNum']
            if prtNum in ['73-18562-02', '73-18562-03', '73-18570-02', '73-18570-03']:
                dn = re.search(node_regex+sup_re, sup['eqptSpCmnBlk']['attributes']['dn'])
                pod_id = dn.group("pod")
                node_id = dn.group("node")
                supslot = dn.group("supslot")
                data.append([pod_id, node_id, supslot, prtNum, vrm_concern, fpga_concern])

    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Per-Leaf Fabric Uplink Limit")
def uplink_limit_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["Node", "Uplink Count"]
    data = []
    recommended_action = "Reduce Per-Leaf Port Profile Uplinks to supported scale; 56 or less."
    doc_url = 'http://cs.co/ACI_Access_Interfaces_Config_Guide'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if cversion.older_than("6.0(1a)") and tversion.newer_than("6.0(1a)"):
        port_profiles = icurl('class', 'eqptPortP.json?query-target-filter=eq(eqptPortP.ctrl,"uplink")')
        if len(port_profiles) > 56:
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
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="OoB Mgmt Security")
def oob_mgmt_security_check(cversion, tversion, **kwargs):
    """Implementation change due to CSCvx29282/CSCvz96117"""
    result = PASS
    headers = ["ACI Node EPG", "External Instance (Subnets)", "OoB Contracts"]
    data = []
    recommended_action = (
        "\n\tEnsure that ICMP, SSH and HTTPS access are allowed for the required subnets with the above config."
        "\n\tOtherwise, APIC access will be limited to the above subnets and the same subnet as APIC OoB after the upgrade."
    )
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#oob-mgmt-security"

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    affected_versions = ["4.2(7)", "5.2(1)", "5.2(2)"]
    if cversion.simple_version not in affected_versions or (
        cversion.simple_version in affected_versions
        and tversion.simple_version in affected_versions
    ):
        return Result(result=NA, msg=VER_NOT_AFFECTED)

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
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Mini ACI Upgrade to 6.0(2)+")
def mini_aci_6_0_2_check(cversion, tversion, **kwargs):
    result = FAIL_UF
    headers = ["Pod ID", "Node ID", "APIC Type", "Failure Reason"]
    data = []
    recommended_action = "All virtual APICs must be removed from the cluster prior to upgrading to 6.0(2)+."
    doc_url = 'Upgrading Mini ACI - http://cs.co/9009bBTQB'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if cversion.older_than("6.0(2a)") and tversion.newer_than("6.0(2a)"):
        topSystem = icurl('class', 'topSystem.json?query-target-filter=wcard(topSystem.role,"controller")')
        if not topSystem:
            return Result(result=ERROR, msg='topSystem response empty. Is the cluster healthy?')
        for controller in topSystem:
            if controller['topSystem']['attributes']['nodeType'] == "virtual":
                pod_id = controller["topSystem"]["attributes"]["podId"]
                node_id = controller['topSystem']['attributes']['id']
                data.append([pod_id, node_id, "virtual", "Virtual APIC must be removed prior to upgrade to 6.0(2)+"])

    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="SUP-A/A+ High Memory Usage")
def sup_a_high_memory_check(tversion, **kwargs):
    result = PASS
    headers = ["Pod ID", "Node ID", "SUP Model", "Active/Standby"]
    data = []
    recommended_action = "Change the target version to the one with memory optimization in a near-future 6.0 release."
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#sup-aa-high-memory-usage"

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

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
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Access (Untagged) Port Config (F0467 native-or-untagged-encap-failure)")
def access_untagged_check(**kwargs):
    result = FAIL_O
    headers = ["Fault", "POD ID", "Node ID", "Port", "Tenant", "Application Profile", "Application EPG", "Recommended Action"]
    unformatted_headers = ['Fault', 'Fault Description', 'Recommended Action']
    unformatted_data = []
    data = []
    recommended_action = 'Resolve the conflict by removing this config or other configs using this port in Access(untagged) or native mode.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#access-untagged-port-config'

    faultInsts = icurl('class', 'faultInst.json?&query-target-filter=wcard(faultInst.changeSet,"native-or-untagged-encap-failure")')
    fault_dn_regex = r"topology/pod-(?P<podid>\d+)/node-(?P<nodeid>[^/]+)/[^/]+/[^/]+/uni/epp/fv-\[uni/tn-(?P<tenant>[^/]+)/ap-(?P<app_profile>[^/]+)/epg-(?P<epg_name>[^/]+)\]/[^/]+/stpathatt-\[(?P<port>.+)\]/nwissues/fault-F0467"

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
                data.append([fc, podid, nodeid, port, tenant, app_profile, epg_name, recommended_action])
            else:
                unformatted_data.append(fc, faultInst['faultInst']['attributes']['descr'], recommended_action)

    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title="Post Upgrade Callback Integrity")
def post_upgrade_cb_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["Missed Objects", "Impact"]
    data = []
    recommended_action = 'Contact Cisco TAC with Output'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#post-upgrade-callback-integrity'

    new_mo_dict = {
        "infraImplicitSetPol": {
            "CreatedBy": "",
            "SinceVersion": ["3.2(10e)"],
            "Impact": "Infra implicit settings will not be deployed",
        },
        "infraRsToImplicitSetPol": {
            "CreatedBy": "infraImplicitSetPol",
            "SinceVersion": ["3.2(10e)"],
            "Impact": "Infra implicit settings will not be deployed",
        },
        "fvSlaDef": {
            "CreatedBy": "fvIPSLAMonitoringPol",
            "SinceVersion": ["4.1(1i)"],
            "Impact": "IPSLA monitor policy will not be deployed",
        },
        "infraRsConnectivityProfileOpt": {
            "CreatedBy": "infraRsConnectivityProfile",
            "SinceVersion": ["5.2(4d)"],
            "Impact": "VPC for missing Mo will not be deployed to leaf",
        },
        "infraAssocEncapInstDef": {
            "CreatedBy": "infraRsToEncapInstDef",
            "SinceVersion": ["5.2(4d)"],
            "Impact": "VLAN for missing Mo will not be deployed to leaf",
        },
        "infraRsToInterfacePolProfileOpt": {
            "CreatedBy": "infraRsToInterfacePolProfile",
            "SinceVersion": ["5.2(8d)", "6.0(3d)"],
            "Impact": "VLAN for missing Mo will not be deployed to leaf",
        },
        "compatSwitchHw": {
            "CreatedBy": "",  # suppBit attribute is available from 6.0(2h)
            "SinceVersion": ["6.0(2h)"],
            "Impact": "Unexpected 64/32 bit image can deploy to switches",
        },
    }
    if not tversion or (tversion and cversion.older_than(str(tversion))):
        return Result(result=POST, msg="Re-run script after APICs are upgraded and back to Fully-Fit")

    for new_mo in new_mo_dict:
        skip_current_mo = False
        if cversion.older_than(new_mo_dict[new_mo]['SinceVersion'][0]):
            continue
        for version in new_mo_dict[new_mo]['SinceVersion']:
            if version[0] == str(cversion)[0]:
                if AciVersion(version).newer_than(str(cversion)):
                    skip_current_mo = True
        if skip_current_mo:
            continue
        created_by_mo = new_mo_dict[new_mo]['CreatedBy']
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
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="EECDH SSL Cipher")
def eecdh_cipher_check(cversion, **kwargs):
    result = FAIL_UF
    headers = ["DN", "Cipher", "State", "Failure Reason"]
    data = []
    recommended_action = "Re-enable EECDH key exchange prior to APIC upgrade."
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#eecdh-ssl-cipher'

    if cversion.newer_than("4.2(1a)"):
        commCipher = icurl('class', 'commCipher.json')
        for cipher in commCipher:
            if cipher['commCipher']['attributes']['id'] == "EECDH" and cipher['commCipher']['attributes']['state'] == "disabled":
                data.append([cipher['commCipher']['attributes']['dn'], "EECDH", "disabled", "Secure key exchange is disabled which may cause APIC GUI to be down after upgrade."])

    if not data:
        result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="fvUplinkOrderCont with blank active uplinks definition")
def vmm_active_uplinks_check(**kwargs):
    result = PASS
    headers = ["Tenant", "Application Profile", "Application EPG", "VMM Domain"]
    data = []
    recommended_action = 'Identify Active Uplinks and apply this to the VMM domain association of each EPG'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#vmm-uplink-container-with-empty-actives'

    uplink_api = 'fvUplinkOrderCont.json'
    uplink_api += '?query-target-filter=eq(fvUplinkOrderCont.active,"")'
    vmm_epg_regex = r"uni/tn-(?P<tenant>[^/]+)/ap-(?P<ap>[^/]+)/epg-(?P<epg>[^/]+)/rsdomAtt-\[uni/vmmp-.+/dom-(?P<dom>.+)\]"

    try:
        affected_uplinks = icurl('class', uplink_api)
    except OldVerClassNotFound:
        # Pre 4.x did not have this class
        return Result(result=NA, msg="cversion does not have class fvUplinkOrderCont")

    if affected_uplinks:
        result = FAIL_O
        for uplink in affected_uplinks:
            dn = re.search(vmm_epg_regex, uplink['fvUplinkOrderCont']['attributes']['dn'])
            data.append([dn.group("tenant"), dn.group("ap"), dn.group("epg"), dn.group("dom")])

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title="Fabric Port is Down (F1394 ethpm-if-port-down-fabric)")
def fabric_port_down_check(**kwargs):
    result = FAIL_O
    headers = ["Pod", "Node", "Int", "Reason", "Lifecycle"]
    unformatted_headers = ['dn', 'Fault Description', 'Lifecycle']
    unformatted_data = []
    data = []
    recommended_action = 'Identify if these ports are needed for redundancy and reason for being down'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#fabric-port-is-down'

    fault_api = 'faultInst.json'
    fault_api += '?&query-target-filter=and(eq(faultInst.code,"F1394")'
    fault_api += ',eq(faultInst.rule,"ethpm-if-port-down-fabric"))'

    faultInsts = icurl('class', fault_api)
    dn_re = node_regex + r'/.+/phys-\[(?P<int>eth\d/\d+)\]'

    for faultInst in faultInsts:
        m = re.search(dn_re, faultInst['faultInst']['attributes']['dn'])
        if m:
            podid = m.group('pod')
            nodeid = m.group('node')
            port = m.group('int')
            reason = faultInst['faultInst']['attributes']['descr'].split("reason:")[1]
            lc = faultInst['faultInst']['attributes']['lc']
            data.append([podid, nodeid, port, reason, lc])
        else:
            unformatted_data.append([faultInst['faultInst']['attributes']['dn'], faultInst['faultInst']['attributes']['descr'], faultInst['faultInst']['attributes']['lc']])

    if not data and not unformatted_data:
        result = PASS
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title='CoS 3 with Dynamic Packet Prioritization')
def fabric_dpp_check(tversion, **kwargs):
    result = PASS
    headers = ["Potential Defect", "Reason"]
    data = []
    recommended_action = 'Change the target version to the fixed version of CSCwf05073'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwf05073'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    lbpol_api = 'lbpPol.json'
    lbpol_api += '?query-target-filter=eq(lbpPol.pri,"on")'

    lbpPol = icurl('class', lbpol_api)
    if lbpPol:
        if (
            (tversion.newer_than("5.1(1h)") and tversion.older_than("5.2(8e)")) or
            (tversion.major1 == "6" and tversion.older_than("6.0(3d)"))
        ):
            result = FAIL_O
            data.append(["CSCwf05073", "Target Version susceptible to Defect"])

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='N9K-C93108TC-FX3P/FX3H Interface Down')
def n9k_c93108tc_fx3p_interface_down_check(tversion, **kwargs):
    result = PASS
    headers = ["Node ID", "Node Name", "Product ID"]
    data = []
    recommended_action = 'Change the target version to the fixed version of CSCwh81430'
    doc_url = 'https://www.cisco.com/c/en/us/support/docs/field-notices/740/fn74085.html'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

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
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='BD and EPG Subnet Scope Consistency')
def subnet_scope_check(cversion, **kwargs):
    result = PASS
    headers = ["BD DN", "BD Scope", "EPG DN", "EPG Scope"]
    data = []
    recommended_action = 'Configure the same Scope for the identified subnet pairings'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#bd-and-epg-subnet-scope-consistency'

    if cversion.older_than("4.2(6d)") or (cversion.major1 == "5" and cversion.older_than("5.1(1h)")):
        epg_api = 'fvAEPg.json?'
        epg_api += 'rsp-subtree=children&rsp-subtree-class=fvSubnet&rsp-subtree-include=required'

        fvAEPg = icurl('class', epg_api)
        if not fvAEPg:
            return Result(result=NA, msg="No EPG Subnets found. Skipping.")

        bd_api = 'fvBD.json'
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

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Route-map Community Match Defect')
def rtmap_comm_match_defect_check(tversion, **kwargs):
    result = PASS
    headers = ["Route-map DN", "Route-map Match DN", "Failure Reason"]
    data = []
    recommended_action = 'Add a prefix list match to each route-map prior to upgrading.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#route-map-community-match'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if (tversion.major1 == "5" and tversion.major2 == "2" and tversion.older_than("5.2(8a)")):
        rtctrlSubjPs = icurl('class', 'rtctrlSubjP.json?rsp-subtree=full&rsp-subtree-class=rtctrlMatchCommFactor,rtctrlMatchRtDest&rsp-subtree-include=required')
        if rtctrlSubjPs:
            subj_dn_list = []
            for rtctrlSubjP in rtctrlSubjPs:
                has_comm = False
                has_dest = False
                dn = rtctrlSubjP['rtctrlSubjP']['attributes']['dn']
                for child in rtctrlSubjP['rtctrlSubjP']['children']:
                    if child.get("rtctrlMatchCommTerm"):
                        has_comm = True
                    elif child.get("rtctrlMatchRtDest"):
                        has_dest = True
                if has_comm and not has_dest:
                    subj_dn_list.append(dn)

            # Now check if affected match statement is in use by any route-map
            if len(subj_dn_list) > 0:
                rtctrlCtxPs = icurl('class', 'rtctrlCtxP.json?rsp-subtree=full&rsp-subtree-class=rtctrlRsCtxPToSubjP,rtctrlRsScopeToAttrP&rsp-subtree-include=required')
                if rtctrlCtxPs:
                    for rtctrlCtxP in rtctrlCtxPs:
                        has_affected_subj = False
                        has_set = False
                        for child in rtctrlCtxP['rtctrlCtxP']['children']:
                            if child.get("rtctrlRsCtxPToSubjP") and child['rtctrlRsCtxPToSubjP']['attributes']['tDn'] in subj_dn_list:
                                has_affected_subj = True
                                subj_dn = child['rtctrlRsCtxPToSubjP']['attributes']['tDn']
                            if child.get("rtctrlScope"):
                                for subchild in child['rtctrlScope']['children']:
                                    if subchild.get("rtctrlRsScopeToAttrP"):
                                        has_set = True

                        if has_affected_subj and has_set:
                            dn = rtctrlCtxP['rtctrlCtxP']['attributes']['dn']
                            parent_dn = '/'.join(dn.rsplit('/', 1)[:-1])
                            data.append([parent_dn, subj_dn, "Route-map has community match statement but no prefix list."])

        if data:
            result = FAIL_O

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Invalid fabricPathEp Targets')
def fabricPathEp_target_check(**kwargs):
    result = PASS
    headers = ["Invalid DN", "Reason"]
    data = []
    recommended_action = 'Contact TAC for cleanup procedure'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#invalid-fex-fabricpathep-dn-references'
    fabricPathEp_regex = r"topology/pod-\d+/(?:\w+)?paths-\d+(?:-\d+)?(?:/ext(?:\w+)?paths-(?P<fexA>\d+)(?:-(?P<fexB>\d+))?)?/pathep-\[(?P<path>.+)\]"
    eth_regex = r'eth(?P<first>\d+)/(?P<second>\d+)(?:/(?P<third>\d+))?'

    hpath_api = 'infraRsHPathAtt.json'
    oosPorts_api = 'fabricRsOosPath.json'
    infraRsHPathAtt = icurl('class', hpath_api)
    fabricRsOosPath = icurl('class', oosPorts_api)

    all_objects = infraRsHPathAtt + fabricRsOosPath
    for obj in all_objects:
        dn = obj.get('infraRsHPathAtt', {}).get('attributes', {}).get('dn', '') or obj.get('fabricRsOosPath', {}).get('attributes', {}).get('dn', '')
        tDn = obj.get('infraRsHPathAtt', {}).get('attributes', {}).get('tDn', '') or obj.get('fabricRsOosPath', {}).get('attributes', {}).get('tDn', '')

        # CHECK ensure tDn looks like a valid fabricPathEp
        fabricPathep_match = re.search(fabricPathEp_regex, tDn)
        if fabricPathep_match:
            groups = fabricPathep_match.groupdict()
            fex_a = groups.get("fexA")
            fex_b = groups.get("fexB")
            path = groups.get("path")

            # CHECK FEX ID(s) of extpath(s) is 101 or greater
            if fex_a:
                if int(fex_a) < 101:
                    data.append([dn, "FEX ID A {} is invalid (101+ expected)".format(fex_a)])
            if fex_b:
                if int(fex_b) < 101:
                    data.append([dn, "FEX ID B {} is invalid (101+ expected)".format(fex_b)])

            # There should always be path... so will assume we always have it
            if 'eth' in path.lower():
                # CHECK path has proper ethx/y or ethx/y/z formatting
                eth_match = re.search(eth_regex, path)
                if eth_match:
                    groups = eth_match.groupdict()
                    first = groups.get("first")
                    second = groups.get("second")
                    third = groups.get("third")

                    # CHECK eth looks like FEX (FIRST is 101 or greater)
                    if first:
                        if int(first) > 100:
                            data.append([dn, "eth module {} like FEX ID".format(first)])
                    # CHECK eth is non-zero
                    if second:
                        if int(second) == 0:
                            data.append([dn, "eth port cannot be 0"])
                    # CHECK eth is non-0 or not greater than 16 for breakout
                    if third:
                        if int(third) == 0:
                            data.append([dn, "eth port cannot be 0 for breakout ports"])
                        elif int(third) > 16:
                            data.append([dn, "eth port {} is invalid (1-16 expected) for breakout ports".format(third)])
                else:
                    data.append([dn, "PathEp 'eth' syntax is invalid"])
        else:
            data.append([dn, "target is not a valid fabricPathEp DN"])

    if data:
        result = FAIL_UF

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='LLDP Custom Interface Description Defect')
def lldp_custom_int_description_defect_check(tversion, **kwargs):
    result = PASS
    headers = ["Potential Defect"]
    data = []
    recommended_action = 'Target version is not recommended; Custom interface descriptions and lazy VMM domain attachments found.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#lldp-custom-interface-description'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if tversion.major1 == '6' and tversion.older_than('6.0(3a)'):
        custom_int_count = icurl('class', 'infraPortBlk.json?query-target-filter=ne(infraPortBlk.descr,"")&rsp-subtree-include=count')[0]['moCount']['attributes']['count']
        lazy_vmm_count = icurl('class', 'fvRsDomAtt.json?query-target-filter=and(eq(fvRsDomAtt.tCl,"vmmDomP"),eq(fvRsDomAtt.resImedcy,"lazy"))&rsp-subtree-include=count')[0]['moCount']['attributes']['count']

        if int(custom_int_count) > 0 and int(lazy_vmm_count) > 0:
            result = FAIL_O
            data.append(['CSCwf00416'])

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Unsupported FEC Configuration For N9K-C93180YC-EX')
def unsupported_fec_configuration_ex_check(sw_cversion, tversion, **kwargs):
    result = PASS
    headers = ["Pod ID", "Node ID", "Switch Model", "Interface", "FEC Mode"]
    data = []
    recommended_action = 'Nexus C93180YC-EX switches do not support IEEE-RS-FEC or CONS16-RS-FEC mode. Misconfigured ports will be hardware disabled upon upgrade. Remove unsupported FEC configuration prior to upgrade.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#unsupported-fec-configuration-for-n9k-c93180yc-ex'

    if not sw_cversion:
        return Result(result=MANUAL, msg="Current switch version not found. Check switch health.")

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if sw_cversion.older_than('5.0(1a)') and tversion.newer_than("5.0(1a)"):
        api = 'topSystem.json'
        api += '?rsp-subtree=children&rsp-subtree-class=l1PhysIf,eqptCh'
        api += '&rsp-subtree-filter=or(eq(l1PhysIf.fecMode,"ieee-rs-fec"),eq(l1PhysIf.fecMode,"cons16-rs-fec"),eq(eqptCh.model,"N9K-C93180YC-EX"))'
        api += '&rsp-subtree-include=required'
        topSystems = icurl('class', api)
        for topSystem in topSystems:
            model = None
            l1PhysIfs = []
            for child in topSystem['topSystem']['children']:
                if child.get("eqptCh"):
                    model = child['eqptCh']['attributes']['model']
                elif child.get("l1PhysIf"):
                    interface = child['l1PhysIf']['attributes']['id']
                    fecMode = child['l1PhysIf']['attributes']['fecMode']
                    l1PhysIfs.append({"interface": interface, "fecMode": fecMode})
            if model and l1PhysIfs:
                pod_id = topSystem['topSystem']['attributes']['podId']
                node_id = topSystem['topSystem']['attributes']['id']
                for l1PhysIf in l1PhysIfs:
                    data.append([pod_id, node_id, model, l1PhysIf['interface'], l1PhysIf['fecMode']])
        if data:
            result = FAIL_O

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='L3out /32 Static Route and BD Subnet Overlap')
def static_route_overlap_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ['L3out', '/32 Static Route', 'BD', 'BD Subnet']
    data = []
    recommended_action = 'Change /32 static route design or target a fixed version'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#l3out-32-overlap-with-bd-subnet'
    iproute_regex = r'uni/tn-(?P<tenant>[^/]+)/out-(?P<l3out>[^/]+)/lnodep-(?P<nodeprofile>[^/]+)/rsnodeL3OutAtt-\[topology/pod-(?P<pod>[^/]+)/node-(?P<node>\d{3,4})\]/rt-\[(?P<addr>[^/]+)/(?P<netmask>\d{1,2})\]'
    bd_subnet_regex = r'uni/tn-(?P<tenant>[^/]+)/BD-(?P<bd>[^/]+)/subnet-\[(?P<subnet>[^/]+/\d{2})\]'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if (cversion.older_than("5.2(6e)") and tversion.newer_than("5.0(1a)") and tversion.older_than("5.2(6e)")):
        slash32filter = 'ipRouteP.json?query-target-filter=and(wcard(ipRouteP.dn,"/32"))'
        staticRoutes = icurl('class', slash32filter)
        if staticRoutes:
            staticroute_vrf = icurl('class', 'l3extRsEctx.json')
            staticR_to_vrf = {}
            for staticRoute in staticRoutes:
                staticroute_array = re.search(iproute_regex, staticRoute['ipRouteP']['attributes']['dn'])
                l3out_dn = 'uni/tn-' + staticroute_array.group("tenant") + '/out-' + staticroute_array.group("l3out") + '/rsectx'

                for l3outCtx in staticroute_vrf:
                    l3outCtx_Vrf = {}
                    if l3outCtx['l3extRsEctx']['attributes']['dn'] == l3out_dn:
                        l3outCtx_Vrf['vrf'] = l3outCtx['l3extRsEctx']['attributes']['tDn']
                        l3outCtx_Vrf['l3out'] = l3outCtx['l3extRsEctx']['attributes']['dn'].replace('/rsectx', '')
                        staticR_to_vrf[staticroute_array.group("addr")] = l3outCtx_Vrf

            bds_in_vrf = icurl('class', 'fvRsCtx.json')
            vrf_to_bd = {}
            for bd_ref in bds_in_vrf:
                vrf_name = bd_ref['fvRsCtx']['attributes']['tDn']
                bd_list = vrf_to_bd.get(vrf_name, [])
                bd_name = bd_ref['fvRsCtx']['attributes']['dn'].replace('/rsctx', '')
                bd_list.append(bd_name)
                vrf_to_bd[vrf_name] = bd_list

            subnets_in_bd = icurl('class', 'fvSubnet.json')
            bd_to_subnet = {}
            for subnet in subnets_in_bd:
                bd_subnet_re = re.search(bd_subnet_regex, subnet['fvSubnet']['attributes']['dn'])
                if bd_subnet_re:
                    bd_dn = 'uni/tn-' + bd_subnet_re.group("tenant") + '/BD-' + bd_subnet_re.group("bd")
                    subnet_list = bd_to_subnet.get(bd_dn, [])
                    subnet_list.append(bd_subnet_re.group("subnet"))
                    bd_to_subnet[bd_dn] = subnet_list

            for static_route, info in staticR_to_vrf.items():
                for bd in vrf_to_bd[info['vrf']]:
                    for subnet in bd_to_subnet[bd]:
                        if IPAddress.ip_in_subnet(static_route, subnet):
                            data.append([info['l3out'], static_route, bd, subnet])

        if data:
            result = FAIL_O

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='vzAny-to-vzAny Service Graph when crossing 5.0 release')
def vzany_vzany_service_epg_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["VRF (Tn:VRF)", "Contract (Tn:Contract)", "Service Graph (Tn:SG)"]
    data = []
    recommended_action = "Be aware of transient traffic disruption for vzAny-to-vzAny Service Graph during APIC upgrade."
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#vzany-to-vzany-service-graph-when-crossing-50-release"

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if not (cversion.older_than("5.0(1a)") and tversion.newer_than("5.0(1a)")):
        return Result(result=NA, msg=VER_NOT_AFFECTED)

    tn_regex = r"uni/tn-(?P<tn>[^/]+)"
    vrf_regex = tn_regex + r"/ctx-(?P<vrf>[^/]+)"
    brc_regex = tn_regex + r"/brc-(?P<brc>[^/]+)"
    sg_regex = tn_regex + r"/AbsGraph-(?P<sg>[^/]+)"

    # check if a SG is attached to a contract
    vzRsSubjGraphAtts = icurl("class", "vzRsSubjGraphAtt.json")
    for vzRsSubjGraphAtt in vzRsSubjGraphAtts:
        graphAtt_rns = vzRsSubjGraphAtt["vzRsSubjGraphAtt"]["attributes"]["dn"].split("/")
        if len(graphAtt_rns) < 3:
            return Result(result=ERROR, msg="Failed to get contract DN from vzRsSubjGraphAtt DN")

        # Get vzAny(VRF) relations of the contract. There can be multiple VRFs per contract.
        vrfs = defaultdict(set)  # key: VRF, value: vzRtAnyToCons, vzRtAnyToProv
        vzBrCP_dn = "/".join(graphAtt_rns[:3])  # Contract DN (uni/tn-xx/brc.xxx)
        vzBrCP_api = vzBrCP_dn + ".json"
        vzBrCP_api += "?query-target=children&target-subtree-class=vzRtAnyToCons,vzRtAnyToProv"
        vzRtAnys = icurl("mo", vzBrCP_api)
        for vzRtAny in vzRtAnys:
            if "vzRtAnyToCons" in vzRtAny:
                rel_class = "vzRtAnyToCons"
            elif "vzRtAnyToProv" in vzRtAny:
                rel_class = "vzRtAnyToProv"
            else:
                log.warning("Unexpected class - %s", vzRtAny.keys())
                continue
            vrf_tdn = vzRtAny[rel_class]["attributes"]["tDn"]
            vrf_match = re.search(vrf_regex, vrf_tdn)
            if vrf_match:
                vrf = vrf_match.group("tn") + ":" + vrf_match.group("vrf")
            else:
                vrf = vrf_tdn
            vrfs[vrf].add(rel_class)
        for vrf, relations in vrfs.items():
            if len(relations) == 2:  # both cons and prov mean vzAny-to-vzAny
                brc_match = re.search(brc_regex, vzBrCP_dn)
                if brc_match:
                    contract = brc_match.group("tn") + ":" + brc_match.group("brc")
                else:
                    contract = vzBrCP_dn
                sg_dn = vzRsSubjGraphAtt["vzRsSubjGraphAtt"]["attributes"]["tDn"]
                sg_match = re.search(sg_regex, sg_dn)
                if sg_match:
                    sg = sg_match.group("tn") + ":" + sg_match.group("sg")
                else:
                    sg = sg_dn
                data.append([vrf, contract, sg])
    if data:
        result = FAIL_O
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='32 and 64-Bit Firmware Image for Switches')
def validate_32_64_bit_image_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["Target Switch Version", "32-Bit Image Result", "64-Bit Image Result"]
    data = []
    recommended_action = 'Upload the missing 32 or 64 bit Switch Image to the Firmware repository'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#602-requires-32-and-64-bit-switch-images'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if cversion.older_than("6.0(2a)") and tversion.newer_than("6.0(2a)"):
        return Result(result=POST, msg="Re-run after APICs are upgraded to 6.0(2) or later")

    if cversion.newer_than("6.0(2a)") and tversion.newer_than("6.0(2a)"):
        result_32 = result_64 = "Not Found"
        target_sw_ver = 'n9000-1' + tversion.version
        firmware_api = 'firmwareFirmware.json'
        firmware_api += '?query-target-filter=eq(firmwareFirmware.fullVersion,"%s")' % (target_sw_ver)
        firmwares = icurl('class', firmware_api)

        for firmware in firmwares:
            name = firmware['firmwareFirmware']['attributes']['name']
            if firmware['firmwareFirmware']['attributes']['bitInfo'] == '32':
                result_32 = "Found"
            elif firmware['firmwareFirmware']['attributes']['bitInfo'] == '64':
                result_64 = "Found"
            elif firmware['firmwareFirmware']['attributes']['bitInfo'] == 'NA':
                if "cs_64" in name:
                    result_64 = "INVALID"
                    recommended_action += '\n\t\tInvalid 64-bit switch image found, remove and reupload to APIC fwrepo'
                else:
                    result_32 = "INVALID"
                    recommended_action += '\n\t\tInvalid 32-bit switch image found, remove and reupload to APIC fwrepo'

        if result_32 in ["Not Found", "INVALID"] or result_64 in ["Not Found", "INVALID"]:
            result = FAIL_UF
            data.append([target_sw_ver, result_32, result_64])
    else:
        return Result(result=NA, msg="Target version below 6.0(2)")

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Fabric Link Redundancy')
def fabric_link_redundancy_check(**kwargs):
    result = PASS
    headers = ["Leaf Name", "Fabric Link Adjacencies", "Problem"]
    data = []
    recommended_action = ""
    sp_recommended_action = "Connect the leaf switch(es) to multiple spine switches for redundancy"
    t1_recommended_action = "Connect the tier 2 leaf switch(es) to multiple tier1 leaf switches for redundancy"
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#fabric-link-redundancy"

    fabric_nodes_api = 'fabricNode.json'
    fabric_nodes_api += '?query-target-filter=and(or(eq(fabricNode.role,"leaf"),eq(fabricNode.role,"spine")),eq(fabricNode.fabricSt,"active"))'

    lldp_adj_api = 'lldpAdjEp.json'
    lldp_adj_api += '?query-target-filter=wcard(lldpAdjEp.sysDesc,"topology/pod")'

    fabricNodes = icurl("class", fabric_nodes_api)
    spines = {}
    leafs = {}
    t2leafs = {}
    for node in fabricNodes:
        dn = node["fabricNode"]["attributes"]["dn"]
        name = node["fabricNode"]["attributes"]["name"]
        if node["fabricNode"]["attributes"]["role"] == "spine":
            spines[dn] = name
        elif node["fabricNode"]["attributes"]["role"] == "leaf":
            leafs[dn] = name
            if node["fabricNode"]["attributes"]["nodeType"] == "tier-2-leaf":
                t2leafs[dn] = name

    t1_missing = sp_missing = False
    lldp_adjs = icurl("class", lldp_adj_api)
    for leaf_dn, leaf_name in iteritems(leafs):
        is_tier2 = True if leaf_dn in t2leafs else False
        neighbors = set()
        for lldp_adj in lldp_adjs:
            lldp_dn = lldp_adj["lldpAdjEp"]["attributes"]["dn"]
            if not lldp_dn.startswith(leaf_dn + "/"):
                continue
            adj_name = lldp_adj["lldpAdjEp"]["attributes"]["sysName"]
            adj_dn = lldp_adj["lldpAdjEp"]["attributes"]["sysDesc"].replace("\\", "")
            # t1leaf look for spines
            if not is_tier2 and adj_dn in spines:
                neighbors.add(adj_name)
            # t2leaf look for t1leafs
            elif is_tier2 and adj_dn in leafs and adj_dn not in t2leafs:
                neighbors.add(adj_name)
            if len(neighbors) > 1:
                break

        if len(neighbors) > 1:
            continue

        if is_tier2:
            adj_type = "tier 1 leaf"
            t1_missing = True
        else:
            adj_type = "spine"
            sp_missing = True
        if len(neighbors) == 1:
            data.append([leaf_name, "".join(neighbors), "Only one {} adjacency".format(adj_type)])
        elif not neighbors:
            data.append([leaf_name, "", "No {} adjacency".format(adj_type)])

    if data:
        result = FAIL_O
    if sp_missing and t1_missing:
        recommended_action = "\n\t" + sp_recommended_action + "\n\t" + t1_recommended_action
    elif sp_missing and not t1_missing:
        recommended_action = sp_recommended_action
    elif not sp_missing and t1_missing:
        recommended_action = t1_recommended_action

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='CloudSec Encryption Deprecated')
def cloudsec_encryption_depr_check(tversion, **kwargs):
    result = NA
    headers = ["Findings"]
    data = []
    recommended_action = 'Validate if CloudSec Encryption is enabled within Nexus Dashboard Orchestrator'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#cloudsec-encryption-deprecated'

    cloudsec_api = 'cloudsecPreSharedKey.json'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    try:
        cloudsecPreSharedKey = icurl('class', cloudsec_api)
    except OldVerClassNotFound:
        return Result(result=NA, msg="cversion does not have class cloudsecPreSharedKey")

    if tversion.newer_than("6.0(6a)"):
        if len(cloudsecPreSharedKey) > 1:
            data.append(['Multiple CloudSec Encryption Keys found'])
            result = MANUAL
        elif len(cloudsecPreSharedKey) == 1:
            data.append(['Single CloudSec Encryption Key found'])
            result = MANUAL
        else:
            result = PASS
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Out-of-Service Ports')
def out_of_service_ports_check(**kwargs):
    result = PASS
    headers = ["Pod ID", "Node ID", "Port ID", "Operational State", "Usage"]
    data = []
    recommended_action = 'Remove Out-of-service Policy on identified "up" ports or they will remain "down" after switch Upgrade'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#out-of-service-ports'

    ethpmPhysIf_api = 'ethpmPhysIf.json'
    ethpmPhysIf_api += '?query-target-filter=and(eq(ethpmPhysIf.operSt,"2"),bw(ethpmPhysIf.usage,"32","34"))'

    ethpmPhysIf = icurl('class', ethpmPhysIf_api)

    if ethpmPhysIf:
        for port in ethpmPhysIf:
            port_dn = port['ethpmPhysIf']['attributes']['dn']
            oper_st = port['ethpmPhysIf']['attributes']['operSt']
            usage = port['ethpmPhysIf']['attributes']['usage']
            node_data = re.search(port_regex, port_dn)
            data.append([node_data.group("pod"), node_data.group("node"), node_data.group("port"), oper_st, usage])

    if data:
        result = FAIL_O

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='FC/FCOE support removed for -EX platforms')
def fc_ex_model_check(tversion, **kwargs):
    result = PASS
    headers = ["FC/FCOE Node ID", "Model"]
    data = []
    recommended_action = 'Select a different target version. Refer to the doc for additional details.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#fcfcoe-support-for-ex-switches'

    fcEntity_api = "fcEntity.json"
    fabricNode_api = 'fabricNode.json'
    fabricNode_api += '?query-target-filter=wcard(fabricNode.model,".*EX")'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if (tversion.newer_than("6.0(7a)") and tversion.older_than("6.0(9c)")) or tversion.same_as("6.1(1f)"):
        fcEntitys = icurl('class', fcEntity_api)
        fc_nodes = []
        if fcEntitys:
            for fcEntity in fcEntitys:
                fc_nodes.append(fcEntity['fcEntity']['attributes']['dn'].split('/sys')[0])

        if fc_nodes:
            fabricNodes = icurl('class', fabricNode_api)
            for node in fabricNodes:
                node_dn = node['fabricNode']['attributes']['dn']
                if node_dn in fc_nodes:
                    model = node['fabricNode']['attributes']['model']
                    if model in ["N9K-C93180YC-EX", "N9K-C93108TC-EX", "N9K-C93108LC-EX"]:
                        data.append([node_dn, model])
    if data:
        result = FAIL_O
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='TEP-to-TEP Atomic Counter scalability')
def tep_to_tep_ac_counter_check(**kwargs):
    result = NA
    headers = ["dbgAcPath Count", "Supported Maximum"]
    data = []
    recommended_action = 'Assess and cleanup dbgAcPath policies to drop below the supported maximum'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#tep-to-tep-atomic-counters-scalability'

    ac_limit = 1600
    atomic_counter_api = 'dbgAcPath.json'
    atomic_counter_api += '?rsp-subtree-include=count'

    atomic_counter_number = icurl('class', atomic_counter_api)
    atomic_counter_number = int(atomic_counter_number[0]['moCount']['attributes']['count'])

    if atomic_counter_number >= ac_limit:
        data.append([atomic_counter_number, str(ac_limit)])
    elif atomic_counter_number > 0 and atomic_counter_number < ac_limit:
        result = PASS

    if data:
        result = FAIL_UF

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Nexus 950X FM or LC Might Fail to boot after reload')
def clock_signal_component_failure_check(**kwargs):
    result = PASS
    headers = ['Pod', "Node", "Slot", "Model", "Serial Number"]
    data = []
    recommended_action = 'Run the SN string through the Serial Number Validation tool (linked within doc url) to check for FN64251.\n\tSN String:\n\t'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#nexus-950x-fm-or-lc-might-fail-to-boot-after-reload'

    eqptFC_api = 'eqptFC.json'
    eqptFC_api += '?query-target-filter=or(eq(eqptFC.model,"N9K-C9504-FM-E"),eq(eqptFC.model,"N9K-C9508-FM-E"))'

    eqptLC_api = 'eqptLC.json'
    eqptLC_api += '?query-target-filter=eq(eqptLC.model,"N9K-X9732C-EX")'

    eqptFC = icurl('class', eqptFC_api)
    eqptLC = icurl('class', eqptLC_api)

    sn_string = ""
    if eqptFC or eqptLC:
        full = eqptFC + eqptLC
        for card in full:
            dn = card.get('eqptLC', {}).get('attributes', {}).get('dn', '') or card.get('eqptFC', {}).get('attributes', {}).get('dn', '')
            slot_regex = node_regex + r"/sys/ch/(?P<slot>.+)/"
            match = re.search(slot_regex, dn)
            if match:
                pod = match.group("pod")
                node = match.group("node")
                slot = match.group("slot")

            model = card.get('eqptLC', {}).get('attributes', {}).get('model', '') or card.get('eqptFC', {}).get('attributes', {}).get('model', '')
            sn = card.get('eqptLC', {}).get('attributes', {}).get('ser', '') or card.get('eqptFC', {}).get('attributes', {}).get('ser', '')
            data.append([pod, node, slot, model, sn])
            sn_string += "{},".format(sn)

    if data:
        result = MANUAL
        recommended_action += sn_string[:-1]

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Stale Decomissioned Spine')
def stale_decomissioned_spine_check(tversion, **kwargs):
    result = PASS
    headers = ["Susceptible Spine Node Id", "Spine Name", "Current Node State"]
    data = []
    recommended_action = 'Remove fabricRsDecommissionNode objects pointing to above Spine Nodes before APIC upgrade'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#stale-decommissioned-spine'

    decomissioned_api = 'fabricRsDecommissionNode.json'
    active_spine_api = 'topSystem.json'
    active_spine_api += '?query-target-filter=eq(topSystem.role,"spine")'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if tversion.newer_than("5.2(3d)") and tversion.older_than("6.0(3d)"):
        decomissioned_switches = icurl('class', decomissioned_api)
        if decomissioned_switches:
            decommissioned_node_ids = [node['fabricRsDecommissionNode']['attributes']['targetId'] for node in decomissioned_switches]

            active_spine_mo = icurl('class', active_spine_api)
            for spine in active_spine_mo:
                node_id = spine['topSystem']['attributes']['id']
                name = spine['topSystem']['attributes']['name']
                state = spine['topSystem']['attributes']['state']
                if node_id in decommissioned_node_ids:
                    data.append([node_id, name, state])
    if data:
        result = FAIL_O
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='N9K-C9408 Platform Model')
def n9408_model_check(tversion, **kwargs):
    result = PASS
    headers = ["Node ID", "Model"]
    data = []
    recommended_action = 'Identified N9K-C9408 must be decommissioned then recomissioned after upgrade to 6.1(3)'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#n9k-c9408-platform-model'

    eqptCh_api = 'eqptCh.json'
    eqptCh_api += '?query-target-filter=eq(eqptCh.model,"N9K-C9400-SW-GX2A")'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if tversion.newer_than("6.1(3a)"):
        eqptCh = icurl('class', eqptCh_api)
        for node in eqptCh:
            node_dn = node['eqptCh']['attributes']['dn']
            model = node['eqptCh']['attributes']['model']
            data.append([node_dn, model])
    if data:
        result = FAIL_O

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='PBR High Scale')
def pbr_high_scale_check(tversion, **kwargs):
    result = PASS
    headers = ["Fabric-Wide PBR Object Count"]
    data = []
    recommended_action = 'High PBR scale detected, target a fixed version for CSCwi66348'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#pbr-high-scale'

    # Not querying fvAdjDefCons as it fails from APIC
    vnsAdjacencyDefCont_api = 'vnsAdjacencyDefCont.json'
    vnsSvcRedirEcmpBucketCons_api = 'vnsSvcRedirEcmpBucketCons.json'
    count_filter = '?rsp-subtree-include=count'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if tversion.older_than("5.3(2c)"):
        vnsAdj = icurl('class', vnsAdjacencyDefCont_api+count_filter)
        vnsSvc = icurl('class', vnsSvcRedirEcmpBucketCons_api+count_filter)

        vnsAdj_count = int(vnsAdj[0]['moCount']['attributes']['count'])
        vnsSvc_count = int(vnsSvc[0]['moCount']['attributes']['count'])
        total = vnsAdj_count + vnsSvc_count
        if total > 100000:
            data.append([total])

    if data:
        result = FAIL_O

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='HTTPS Request Throttle Rate')
def https_throttle_rate_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["Mgmt Access Policy", "HTTPS Throttle Rate"]
    data = []
    recommended_action = "Reduce the throttle rate to 40 (req/sec), 2400 (req/min) or lower."
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#https-request-throttle-rate"

    # Applicable only when crossing 6.1(2) as upgrade instead of downgrade.
    if cversion.newer_than("6.1(2a)"):
        return Result(result=NA, msg=VER_NOT_AFFECTED)
    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    commHttpses = icurl("class", "commHttps.json")
    for commHttps in commHttpses:
        if commHttps["commHttps"]["attributes"].get("globalThrottleSt", "disabled") == "disabled":
            continue
        if ((
            commHttps["commHttps"]["attributes"]["globalThrottleUnit"] == "r/s" and
            int(commHttps["commHttps"]["attributes"]["globalThrottleRate"]) > 40
        ) or (
            commHttps["commHttps"]["attributes"]["globalThrottleUnit"] == "r/m" and
            int(commHttps["commHttps"]["attributes"]["globalThrottleRate"]) > 2400
        )):
            # Get `default` of `uni/fabric/comm-default/https`
            commPol_rn = commHttps["commHttps"]["attributes"]["dn"].split("/")[2]
            commPol_name = commPol_rn.split("-")[1]
            rate = "{} ({})".format(
                commHttps["commHttps"]["attributes"]["globalThrottleRate"],
                commHttps["commHttps"]["attributes"]["globalThrottleUnit"],
            )
            data.append([commPol_name, rate])

    if data:
        if tversion.older_than("6.1(2a)"):
            result = MANUAL
            recommended_action = "6.1(2)+ will reject this config. " + recommended_action
        else:
            result = FAIL_UF
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Standby SUP Image Sync')
def standby_sup_sync_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["Pod ID", "Node ID", "Standby SUP Slot"]
    data = []
    recommended_action = 'Target an interim image with fix for CSCwa44220 that is smaller than 2Gigs, such as 5.2(8i)'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#standby-sup-image-sync'

    sup_regex = node_regex + r'/sys/ch/supslot-(?P<slot>\d)'
    eqptSupC_api = 'eqptSupC.json'
    eqptSupC_api += '?query-target-filter=eq(eqptSupC.rdSt,"standby")'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if (
        (cversion.older_than("4.2(7t)") or (cversion.major_version == "5.2" and cversion.older_than("5.2(5d)")))
        and ((tversion.major_version == "5.2" and tversion.older_than("5.2(7f)")) or tversion.newer_than("6.0(2h)"))
    ):
        eqptSupC = icurl('class', eqptSupC_api)
        for node in eqptSupC:
            node_dn = node['eqptSupC']['attributes']['dn']
            match = re.search(sup_regex, node_dn)
            if match:
                pod = match.group("pod")
                node = match.group("node")
                slot = match.group("slot")
                data.append([pod, node, slot])

    if data:
        result = FAIL_UF

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Equipment Disk Limits Exceeded')
def equipment_disk_limits_exceeded(**kwargs):
    result = PASS
    headers = ['Pod', 'Node', 'Code', '%', 'Description']
    data = []
    unformatted_headers = ['Fault DN', '%', 'Recommended Action']
    unformatted_data = []
    recommended_action = 'Review the reference document for commands to validate disk usage'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/##equipment-disk-limits-exceeded'

    usage_regex = r"avail \(New: (?P<avail>\d+)\).+used \(New: (?P<used>\d+)\)"
    f182x_api = 'faultInst.json'
    f182x_api += '?query-target-filter=or(eq(faultInst.code,"F1820"),eq(faultInst.code,"F1821"),eq(faultInst.code,"F1822"))'
    faults = icurl('class', f182x_api)

    for faultInst in faults:
        percent = "NA"
        attributes = faultInst['faultInst']['attributes']

        usage_match = re.search(usage_regex, attributes['changeSet'])
        if usage_match:
            avail = int(usage_match.group('avail'))
            used = int(usage_match.group('used'))
            percent = round((used / (avail + used)) * 100)

        dn_match = re.search(node_regex, attributes['dn'])
        if dn_match:
            data.append([dn_match.group('pod'), dn_match.group('node'), attributes['code'], percent, attributes['descr']])
        else:
            unformatted_data.append([attributes['dn'], percent, attributes['descr']])

    if data or unformatted_data:
        result = FAIL_UF

    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


@check_wrapper(check_title='Global AES Encryption')
def aes_encryption_check(tversion, **kwargs):
    result = FAIL_UF
    headers = ["Target Version", "Global AES Encryption", "Impact"]
    data = []
    recommended_action = (
        "\n\tEnable Global AES Encryption before upgrading your APIC (and take a configuration backup)."
        "\n\tGlobal AES Encryption ensures that all configurations are included in the backup securely."
    )
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#global-aes-encryption"

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if tversion.newer_than("6.1(2a)"):
        impact = "Upgrade Failure"
        result = FAIL_UF
        recommended_action += "\n\tUpgrade to 6.1(2) or later will fail when it is not enabled."
    else:
        impact = "Your config backup may not contain all data"
        result = MANUAL

    cryptkeys = icurl("mo", "uni/exportcryptkey.json")
    if not cryptkeys:
        data = [[str(tversion), "Object Not Found", impact]]
    elif cryptkeys[0]["pkiExportEncryptionKey"]["attributes"]["strongEncryptionEnabled"] != "yes":
        data = [[str(tversion), "Disabled", impact]]
    else:
        result = PASS

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Service Graph BD Forceful Routing')
def service_bd_forceful_routing_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["Bridge Domain (Tenant:BD)", "Service Graph Device (Tenant:Device)"]
    data = []
    unformatted_headers = ["DN of fvRtEPpInfoToBD"]
    unformatted_data = []
    recommended_action = (
        "\n\tConfirm that within these BDs there is no bridging traffic with the destination IP that doesn't belong to them."
        "\n\tPlease check the reference document for details."
    )
    doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#service-graph-bd-forceful-routing"

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if not (cversion.older_than("6.0(2a)") and tversion.newer_than("6.0(2a)")):
        return Result(result=NA, msg=VER_NOT_AFFECTED)

    dn_regex = r"uni/tn-(?P<bd_tn>[^/]+)/BD-(?P<bd>[^/]+)/"
    dn_regex += r"rtvnsEPpInfoToBD-\[uni/tn-(?P<sg_tn>[^/])+/LDevInst-\[uni/tn-(?P<ldev_tn>[^/]+)/lDevVip-(?P<ldev>[^\]]+)\].*\]"

    fvRtEPpInfoToBDs = icurl("class", "fvRtEPpInfoToBD.json")
    for fvRtEPpInfoToBD in fvRtEPpInfoToBDs:
        m = re.search(dn_regex, fvRtEPpInfoToBD["fvRtEPpInfoToBD"]["attributes"]["dn"])
        if not m:
            log.error("Failed to match %s", fvRtEPpInfoToBD["fvRtEPpInfoToBD"]["attributes"]["dn"])
            unformatted_data.append([fvRtEPpInfoToBD["fvRtEPpInfoToBD"]["attributes"]["dn"]])
            continue
        data.append([
            "{}:{}".format(m.group("bd_tn"), m.group("bd")),
            "{}:{}".format(m.group("ldev_tn"), m.group("ldev")),
        ])

    if data or unformatted_data:
        result = MANUAL
    return Result(
        result=result,
        headers=headers,
        data=data,
        unformatted_headers=unformatted_headers,
        unformatted_data=unformatted_data,
        recommended_action=recommended_action,
        doc_url=doc_url,
    )


# Connection Base Check
@check_wrapper(check_title='Observer Database Size')
def observer_db_size_check(username, password, **kwargs):
    result = PASS
    headers = ["Node", "File Location", "Size (GB)"]
    data = []
    recommended_action = 'Contact TAC to analyze and truncate large DB files'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations#observer-database-size'

    topSystem_api = 'topSystem.json'
    topSystem_api += '?query-target-filter=eq(topSystem.role,"controller")'

    controllers = icurl('class', topSystem_api)
    if not controllers:
        return Result(result=ERROR, msg='topSystem response empty. Is the cluster healthy?')

    has_error = False
    prints('')
    for apic in controllers:
        attr = apic['topSystem']['attributes']
        node_title = 'Checking %s...' % attr['name']
        print_title(node_title)
        try:
            c = Connection(attr['address'])
            c.username = username
            c.password = password
            c.log = LOG_FILE
            c.connect()
        except Exception as e:
            data.append([attr['id'], attr['name'], str(e)])
            print_result(node_title, ERROR)
            has_error = True
            continue
        try:
            cmd = r"ls -lh /data2/dbstats | awk '{print $5, $9}'"
            c.cmd(cmd)
            if "No such file or directory" in c.output:
                data.append([attr['id'], '/data2/dbstats/ not found', "Check user permissions or retry as 'apic#fallback\\\\admin'"])
                print_result(node_title, ERROR)
                has_error = True
                continue
            dbstats = c.output.split("\n")
            for line in dbstats:
                observer_gig_regex = r"(?P<size>\d{1,3}(?:\.\d)?G)\s(?P<file>observer_\d{1,3}.db)"
                size_match = re.match(observer_gig_regex, line)
                if size_match:
                    file_size = size_match.group("size")
                    file_name = "/data2/dbstats/" + size_match.group("file")
                    data.append([attr['id'], file_name, file_size])
            print_result(node_title, DONE)
        except Exception as e:
            data.append([attr['id'], attr['name'], str(e)])
            print_result(node_title, ERROR)
            has_error = True
            continue
    if has_error:
        result = ERROR
    elif data:
        result = FAIL_UF
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url, adjust_title=True)


@check_wrapper(check_title='AVE End-of-Life')
def ave_eol_check(tversion, **kwargs):
    result = NA
    headers = ["AVE Domain Name"]
    data = []
    recommended_action = 'AVE domain(s) must be migrated to supported domain types prior to 6.0+ upgrade'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#ave-end-of-life'

    ave_api = 'vmmDomP.json'
    ave_api += '?query-target-filter=eq(vmmDomP.enableAVE,"true")'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if tversion.newer_than("6.0(1a)"):
        ave = icurl('class', ave_api)
        for domain in ave:
            name = domain['vmmDomP']['attributes']['name']
            data.append([name])
    if data:
        result = FAIL_O

    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='Stale pconsRA Objects')
def stale_pcons_ra_mo_check(cversion, tversion, **kwargs):
    result = PASS
    headers = ["Stale pconsRA DN", "Non-Existing DN"]
    data = []
    recommended_action = 'Contact Cisco TAC to delete stale pconsRA before upgrading'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#stale-pconsra-object'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if cversion.older_than("6.0(3d)") and tversion.newer_than("6.0(3c)") and tversion.older_than("6.1(4a)"):
        pcons_rssubtreedep_api = 'pconsRsSubtreeDep.json?query-target-filter=wcard(pconsRsSubtreeDep.tDn,"/instdn-")'
        pcons_rssubtreedep_mo = icurl('class', pcons_rssubtreedep_api)
        pcons_inst_dn_reg = r'registry/class-\d+/instdn-\[(?P<policy_dn>.+?)\]/ra'
        pcons_ra_dn_reg = r'(?P<pcons_ra_dn>.+?)/p...-\['

        pcons_ra_set = set()
        policy_dn_set = set()

        for mo in pcons_rssubtreedep_mo:
            pcons_rssubtreedep_tdn = mo['pconsRsSubtreeDep']['attributes']['tDn']
            instdn_found = re.search(pcons_inst_dn_reg, pcons_rssubtreedep_tdn)
            radn_found = re.search(pcons_ra_dn_reg, pcons_rssubtreedep_tdn)
            if instdn_found and radn_found:
                pcons_ra_dn = radn_found.group('pcons_ra_dn')
                policy_dn = instdn_found.group('policy_dn')
                if pcons_ra_dn not in pcons_ra_set:
                    pcons_ra_set.add(pcons_ra_dn)
                if policy_dn not in policy_dn_set:
                    policy_dn_set.add(policy_dn)

        for policy_dn in policy_dn_set:
            policy_dn_api = policy_dn + '.json'
            policy_dn_mo = icurl('mo', policy_dn_api)
            if not policy_dn_mo:
                for pcons_ra_dn in pcons_ra_set:
                    if policy_dn in pcons_ra_dn:
                        pcons_ra_api = pcons_ra_dn + '.json'
                        pcons_ra_dn_mo = icurl('mo', pcons_ra_api)
                        if pcons_ra_dn_mo:
                            data.append([pcons_ra_dn, policy_dn])
    else:
        return Result(result=NA, msg=VER_NOT_AFFECTED)

    if data:
        result = FAIL_O
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


@check_wrapper(check_title='ISIS DTEPs Byte Size')
def isis_database_byte_check(tversion, **kwargs):
    result = PASS
    headers = ["ISIS DTEPs Byte Size", "ISIS DTEPs"]
    data = []
    recommended_action = 'Upgrade to a version with the fix for CSCwp15375. Current target version is affected.'
    doc_url = 'https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#isis-dteps-byte-size'

    if not tversion:
        return Result(result=MANUAL, msg=TVER_MISSING)

    if tversion.newer_than("6.1(1a)") and tversion.older_than("6.1(3g)"):
        isisDTEp_api = 'isisDTEp.json'
        isisDTEp_api += '?query-target-filter=eq(isisDTEp.role,"spine")'

        isisDTEps = icurl('class', isisDTEp_api)

        physical_ids = set()
        proxy_acast_ids = set()

        for entry in isisDTEps:
            dtep_type = entry['isisDTEp']['attributes']['type']
            dtep_id = entry['isisDTEp']['attributes']['id']

            if dtep_type == "physical":
                physical_ids.add(dtep_id)
            elif "physical,proxy-acast" in dtep_type:
                proxy_acast_ids.add(dtep_id)

        for physical_id in physical_ids:
            combined_dteps = ",".join([physical_id] + list(proxy_acast_ids))
            total_bytes = len(combined_dteps)

            if total_bytes > 57:
                result = FAIL_O
                data.append([total_bytes, combined_dteps])
                break
    else:
        return Result(result=NA, msg=VER_NOT_AFFECTED)
    return Result(result=result, headers=headers, data=data, recommended_action=recommended_action, doc_url=doc_url)


# ---- Script Execution ----

def parse_args(args):
    parser = ArgumentParser(description="ACI Pre-Upgrade Validation Script - %s" % SCRIPT_VERSION)
    parser.add_argument("-t", "--tversion", action="store", type=str, help="Upgrade Target Version. Ex. 6.2(1a)")
    parser.add_argument("-c", "--cversion", action="store", type=str, help="Override Current Version. Ex. 6.1(1a)")
    parser.add_argument("-d", "--debug-function", action="store", type=str, help="Name of a single function to debug. Ex. 'apic_version_md5_check'")
    parser.add_argument("-a", "--api-only", action="store_true", help="For built-in PUV. API Checks only. Checks using SSH are skipped.")
    parser.add_argument("-n", "--no-cleanup", action="store_true", help="Skip all file cleanup after script execution.")
    parser.add_argument("-v", "--version", action="store_true", help="Only show the script version, then end.")
    parser.add_argument("--total-checks", action="store_true", help="Only show the total number of checks, then end.")
    parsed_args = parser.parse_args(args)
    return parsed_args


def initialize():
    """
    Initialize the script environment, create necessary directories and set up log.
    Not required for some options such as `--version` or `--total-checks`.
    """
    if os.path.isdir(DIR):
        log.info("Cleaning up previous run files in %s", DIR)
        shutil.rmtree(DIR)
    log.info("Creating directories %s and %s", DIR, JSON_DIR)
    os.mkdir(DIR)
    os.mkdir(JSON_DIR)
    fmt = '[%(asctime)s.%(msecs)03d{} %(levelname)-8s %(funcName)20s:%(lineno)-4d] %(message)s'.format(tz)
    logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, format=fmt, datefmt='%Y-%m-%d %H:%M:%S')


def prepare(api_only, arg_tversion, arg_cversion, total_checks):
    prints('    ==== %s%s, Script Version %s  ====\n' % (ts, tz, SCRIPT_VERSION))
    prints('!!!! Check https://github.com/datacenter/ACI-Pre-Upgrade-Validation-Script for Latest Release !!!!\n')

    username = password = None
    if not api_only:
        username, password = get_credentials()
    try:
        cversion = get_current_version(arg_cversion)
        tversion = get_target_version(arg_tversion)
        vpc_nodes = get_vpc_nodes()
        sw_cversion = get_switch_version()
    except Exception as e:
        prints('\n\nError: %s' % e)
        prints("Initial query failed. Ensure APICs are healthy. Ending script run.")
        log.exception(e)
        sys.exit()
    inputs = {'username': username, 'password': password,
              'cversion': cversion, 'tversion': tversion,
              'vpc_node_ids': vpc_nodes, 'sw_cversion': sw_cversion}
    metadata = {
        "name": "PreupgradeCheck",
        "method": "standalone script",
        "datetime": ts + tz,
        "script_version": str(SCRIPT_VERSION),
        "cversion": str(cversion),
        "tversion": str(tversion),
        "sw_cversion": str(sw_cversion),
        "api_only": api_only,
        "total_checks": total_checks,
    }
    with open(META_FILE, "w") as f:
        json.dump(metadata, f, indent=2)
    return inputs


def get_checks(api_only, debug_function):
    api_checks = [
        # General Checks
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
        validate_32_64_bit_image_check,
        fabric_link_redundancy_check,

        # Faults
        apic_disk_space_faults_check,
        switch_bootflash_usage_check,
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
        equipment_disk_limits_exceeded,

        # Configurations
        vpc_paired_switches_check,
        overlapping_vlan_pools_check,
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
        unsupported_fec_configuration_ex_check,
        cloudsec_encryption_depr_check,
        out_of_service_ports_check,
        tep_to_tep_ac_counter_check,
        https_throttle_rate_check,
        aes_encryption_check,
        service_bd_forceful_routing_check,
        ave_eol_check,

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
        fabricPathEp_target_check,
        lldp_custom_int_description_defect_check,
        rtmap_comm_match_defect_check,
        static_route_overlap_check,
        fc_ex_model_check,
        vzany_vzany_service_epg_check,
        clock_signal_component_failure_check,
        stale_decomissioned_spine_check,
        n9408_model_check,
        pbr_high_scale_check,
        standby_sup_sync_check,
        stale_pcons_ra_mo_check,
        isis_database_byte_check,

    ]
    conn_checks = [
        # General
        apic_version_md5_check,

        # Faults
        standby_apic_disk_space_check,
        apic_ssd_check,

        # Bugs
        observer_db_size_check,

    ]
    if debug_function:
        return [check for check in api_checks + conn_checks if check.__name__ == debug_function]
    if api_only:
        return api_checks
    return conn_checks + api_checks


def run_checks(checks, inputs):
    summary_headers = [PASS, FAIL_O, FAIL_UF, MANUAL, POST, NA, ERROR, 'TOTAL']
    summary = {key: 0 if key != 'TOTAL' else len(checks) for key in summary_headers}
    for idx, check in enumerate(checks):
        try:
            r = check(idx + 1, len(checks), **inputs)
            summary[r] += 1
        except KeyboardInterrupt:
            prints('\n\n!!! KeyboardInterrupt !!!\n')
            break

    prints('\n=== Summary Result ===\n')
    res = max(summary_headers, key=len)
    max_header_len = len(res)
    for key in summary_headers:
        prints('{:{}} : {:2}'.format(key, max_header_len, summary[key]))

    with open(SUMMARY_FILE, 'w') as f:
        json.dump(summary, f, indent=2)


def wrapup(no_cleanup):
    subprocess.check_output(['tar', '-czf', BUNDLE_NAME, DIR])
    bundle_loc = '/'.join([os.getcwd(), BUNDLE_NAME])
    prints("""
    Pre-Upgrade Check Complete.
    Next Steps: Address all checks flagged as FAIL, ERROR or MANUAL CHECK REQUIRED

    Result output and debug info saved to below bundle for later reference.
    Attach this bundle to Cisco TAC SRs opened to address the flagged checks.

      Result Bundle: {bundle}
    """.format(bundle=bundle_loc))
    prints('==== Script Version %s FIN ====' % (SCRIPT_VERSION))

    # puv integration needs to keep reading files from `JSON_DIR` under `DIR`.
    if not no_cleanup and os.path.isdir(DIR):
        log.info('Cleaning up temporary files and directories...')
        shutil.rmtree(DIR)


def main(_args=None):
    args = parse_args(_args)
    if args.version:
        print(SCRIPT_VERSION)
        return
    checks = get_checks(args.api_only, args.debug_function)
    if args.total_checks:
        print("Total Number of Checks: {}".format(len(checks)))
        return

    initialize()
    inputs = prepare(args.api_only, args.tversion, args.cversion, len(checks))
    run_checks(checks, inputs)
    wrapup(args.no_cleanup)


if __name__ == "__main__":
    main()
