from __future__ import division
from __future__ import print_function
from textwrap import TextWrapper
from getpass import getpass
from collections import defaultdict
from datetime import datetime
import time
import pexpect
import logging
import subprocess
import json
import sys
import os
import re

DONE = 'DONE'
PASS = 'PASS'
FAIL_O = 'FAIL - OUTAGE WARNING!!'
FAIL_UF = 'FAIL - UPGRADE FAILURE!!'
ERROR = 'ERROR !!'
MANUAL = 'MANUAL CHECK REQUIRED'
NA = 'N/A'
node_regex = r'topology/pod-(?P<pod>\d+)/node-(?P<node>\d+)'
ver_regex = r'(?:dk9\.)?[1]?(?P<major1>\d)\.(?P<major2>\d)(?:\.|\()(?P<maint>\d+)\.?(?P<patch>(?:[a-b]|[0-9a-z]+))\)?'

cco_md5_sum = {'aci-apic-dk9.2.2.1k.bin': '20202e6b2a72fc12904e89e79ff6d867',
            'aci-apic-dk9.2.2.1n.bin': 'bd03c72b489220612d806c22af583d64',
            'aci-apic-dk9.2.2.1o.bin': '24ba669e0f879862735f40cc5256529c',
            'aci-apic-dk9.2.2.2e.bin': '1fed95f6f3cac83312e74c7a921a52b8',
            'aci-apic-dk9.2.2.2f.bin': '864d1f2d69b214974e50eb2b09de0afb',
            'aci-apic-dk9.2.2.2i.bin': 'fb12d0a6213a1272b15f052c9bfcd0d0',
            'aci-apic-dk9.2.2.2j.bin': '13ed969f3b4da07d32951654d53f3e25',
            'aci-apic-dk9.2.2.2k.bin': '92d1d8d12899eadace960967a10d272f',
            'aci-apic-dk9.2.2.2q.bin': '6aa77815401a50582ea6c2fdc25aa47a',
            'aci-apic-dk9.2.2.3j.bin': 'e47cc213e24ae5e09e31a6cc2baf0d58',
            'aci-apic-dk9.2.2.3p.bin': 'bffc74e0159167094ac8dc4e585b6d0e',
            'aci-apic-dk9.2.2.3r.bin': '471195928dd5dc07dfc01ed108012182',
            'aci-apic-dk9.2.2.3s.bin': '7d24356b124bce9bb9484225ac23aef0',
            'aci-apic-dk9.2.2.3t.bin': 'cb597fdfbc7bcdb4e7b6044dd378ff67',
            'aci-apic-dk9.2.2.4f.bin': '9817de2462ce158b6fb852077d445f4f',
            'aci-apic-dk9.2.2.4p.bin': '5cd0f68413ee1eb75226831bca565321',
            'aci-apic-dk9.2.2.4q.bin': '2c9d33c5ab22bb854341b52fb4491356',
            'aci-apic-dk9.2.2.4r.bin': '2d5d06705328e74417a30d88a6550c6b',
            'aci-apic-dk9.2.3.1e.bin': 'f58f528367036a7aa2b62cbeccd3eca1',
            'aci-apic-dk9.2.3.1f.bin': 'dd9a1404ddf2f0c709eee48d5ddda608',
            'aci-apic-dk9.2.3.1i.bin': 'b0b1b9588cce61083d0daa47cd5b0570',
            'aci-apic-dk9.2.3.1l.bin': 'ad520f11b121f63737a4c3e2013bd1b7',
            'aci-apic-dk9.2.3.1o.bin': 'ead77a978005a7da0130e75e7b731536',
            'aci-apic-dk9.2.3.1p.bin': 'b5eea6c422cea82b8a1cce76249dbf28',
            'aci-apic-dk9.3.0.1k.bin': 'caf3a603694a527497b2e2c54eae2c11',
            'aci-apic-dk9.3.0.2h.bin': '28fc59bf04aa82d8d0bab5e0db54df49',
            'aci-apic-dk9.3.0.2k.bin': '3807db0698718d63207c088148324e57',
            'aci-apic-dk9.3.0.2n.bin': '1e384f35a6bc28edfac4fcc42607e7b4',
            'aci-apic-dk9.3.1.1i.bin': '062abd202a2410ada11107a00c4dd226',
            'aci-apic-dk9.3.1.2m.bin': '80bb69cb864983f0321df10ebfeeaee1',
            'aci-apic-dk9.3.1.2o.bin': '17cbbd32ce0f503543c433a0e88db7a7',
            'aci-apic-dk9.3.1.2p.bin': 'f2771fdacd651d81f35a161180833070',
            'aci-apic-dk9.3.1.2q.bin': '134318a66dd287151ee6e26d88eb0495',
            'aci-apic-dk9.3.1.2s.bin': '923594431496fa77764b57191d4d60e6',
            'aci-apic-dk9.3.1.2t.bin': '7b2d4ab96418b9d54152b582cd6b716d',
            'aci-apic-dk9.3.1.2u.bin': '93b3699e98b8d0de83bcb0a7a8e08335',
            'aci-apic-dk9.3.1.2v.bin': '9c357e38bb3ffc5543319c049e83dcef',
            'aci-apic-dk9.3.2.10e.bin': 'f10322ac8853e7f369208a47a1bef794',
            'aci-apic-dk9.3.2.10f.bin': 'e269b9167281989d7222dadab8e1403f',
            'aci-apic-dk9.3.2.1l.bin': 'a8661788d13a57f046567c6c5b8895ab',
            'aci-apic-dk9.3.2.1m.bin': '1324c126561a3175a422bb51fe03abb4',
            'aci-apic-dk9.3.2.2l.bin': '5562dd838742bb100ea944f16c482762',
            'aci-apic-dk9.3.2.2o.bin': 'a8ef1b1c808421abf1024e18fde82b2e',
            'aci-apic-dk9.3.2.3i.bin': '223123dd0d6e69d277c1e951938ce6bd',
            'aci-apic-dk9.3.2.3n.bin': 'f6c7cc42ab1e59f54d07c48b467831fa',
            'aci-apic-dk9.3.2.3o.bin': '6a72b7ea54eea444bc70b571d2d0f1f8',
            'aci-apic-dk9.3.2.3r.bin': '513a8ea89c1e416d8933e4f266d07ef8',
            'aci-apic-dk9.3.2.3s.bin': '307cf15cbc10655e6a81c339bb5f6e28',
            'aci-apic-dk9.3.2.4d.bin': 'a1658a7a9e5af858b6b5ba7951398d80',
            'aci-apic-dk9.3.2.4e.bin': '8d307c9051b1393c88aa99f7fd1e9b41',
            'aci-apic-dk9.3.2.5d.bin': '321b640db93e7a8adfcfa8f157f630a0',
            'aci-apic-dk9.3.2.5e.bin': '908db1ec003337e803ce66f0ecea319b',
            'aci-apic-dk9.3.2.5f.bin': '6a72cfb04b0d4357adf519a16abf8024',
            'aci-apic-dk9.3.2.6i.bin': '9b6a04e364bf85fb20107067b6d0780f',
            'aci-apic-dk9.3.2.7f.bin': '8a5ba193ed6f0d9e4bd3ed4ed80b1fcc',
            'aci-apic-dk9.3.2.7k.bin': 'd760860b4bc3199d2c031bec5cd6a8b3',
            'aci-apic-dk9.3.2.8d.bin': '4c475f5cf8a7418058d4ff6bf9019643',
            'aci-apic-dk9.3.2.9b.bin': 'e4fc495daad013552540fe43776ae638',
            'aci-apic-dk9.3.2.9f.bin': 'fb676f8a17831f632e03457c1bac5f70',
            'aci-apic-dk9.3.2.9h.bin': '3f0de3f08de2c8f1c27740a1fee7f13b',
            'aci-apic-dk9.4.0.1h.bin': 'e41cf40686528c6fa6befd9a6dcb7d50',
            'aci-apic-dk9.4.0.2c.bin': 'bebe0dc38ed91171aad9ff6b215b7624',
            'aci-apic-dk9.4.0.3c.bin': 'd0f35eed9df060386f935d2373a06c92',
            'aci-apic-dk9.4.0.3d.bin': '22eb03f5d1c0a9399effab0aac2dc731',
            'aci-apic-dk9.4.1.1i.bin': 'db7022e843dd58b7e9c0769c3a538a7b',
            'aci-apic-dk9.4.1.1j.bin': 'd4cef7210f4f53f75cf651140118721c',
            'aci-apic-dk9.4.1.1k.bin': 'cf602fd16193b1bb2b12ad31794ccfaf',
            'aci-apic-dk9.4.1.1l.bin': '386cabd6cac5db198e7421fa25e48a47',
            'aci-apic-dk9.4.1.2g.bin': '3054a7054cd1da536549e6d5e6fb7722',
            'aci-apic-dk9.4.1.2m.bin': '0ff66d4e9946c1d83a977f0807152fc6',
            'aci-apic-dk9.4.1.2o.bin': '64d4682486a8cba583775f640ba32589',
            'aci-apic-dk9.4.1.2s.bin': '3f567b83a83dd68d53a04488d238c0ca',
            'aci-apic-dk9.4.1.2u.bin': '278b7742a1e7adc84491c89c95447091',
            'aci-apic-dk9.4.1.2w.bin': '028234e177faffb82f00f0446f7e1ddc',
            'aci-apic-dk9.4.1.2x.bin': '923828595f3821dfbfddf0b485b53488',
            'aci-apic-dk9.4.2.1i.bin': '991aac53cae06fee3c261df237d4091b',
            'aci-apic-dk9.4.2.1j.bin': 'fb9dc07ec905a302dc79d5d6b736b162',
            'aci-apic-dk9.4.2.1l.bin': '1e9baa53f7d681574c92d58e634fa121',
            'aci-apic-dk9.4.2.2e.bin': '6a1a061fdf6c01f46fc9af09b603c882',
            'aci-apic-dk9.4.2.2f.bin': '81e83c51a7c79c850d13182d56d7044c',
            'aci-apic-dk9.4.2.3j.bin': 'b561d46467557b1e2457c456c6e48e67',
            'aci-apic-dk9.4.2.3l.bin': '26d21beddb374e00f43357f2d492ded2',
            'aci-apic-dk9.4.2.3n.bin': '0990fec361f6d9a7b92d270a3c0fcbcc',
            'aci-apic-dk9.4.2.3q.bin': '6642e631835647de75bbbf420a7bda0a',
            'aci-apic-dk9.4.2.4i.bin': '6f24f1f2d011046e5e851e97ce48692f',
            'aci-apic-dk9.4.2.4k.bin': '18e43d54f016a0d7423be67031d0be4a',
            'aci-apic-dk9.4.2.4o.bin': '9a896ba01917b2d33163e0a78aecc273',
            'aci-apic-dk9.4.2.4p.bin': '94bfed99024ead9a3d90d8346c4eef48',
            'aci-apic-dk9.4.2.5k.bin': 'a1f9ea609400205271a5a1a0112ab6a3',
            'aci-apic-dk9.4.2.5l.bin': '46fa1d86a4f6a46a88c35e37af5139a5',
            'aci-apic-dk9.4.2.5n.bin': '3111da2ee1b62d9679b0b43677c97201',
            'aci-apic-dk9.4.2.6d.bin': '92e7713d2d9d5b0e7ef17337ea672131',
            'aci-apic-dk9.4.2.6g.bin': '8e1201397db0aaa3238909a50d13fc8c',
            'aci-apic-dk9.4.2.6h.bin': '3621e75da8b36dc48da6258ed949eb86',
            'aci-apic-dk9.4.2.6l.bin': '1a5be7378720172536f5c53a82fbf053',
            'aci-apic-dk9.4.2.6o.bin': 'ce14ffe6f396566905cdab95e0062dbe',
            'aci-apic-dk9.4.2.7f.bin': '2177042b8f5e2ed11d731196f7045d72',
            'aci-apic-dk9.4.2.7l.bin': '75e316df7fea6f51d820a04b0c26f82c',
            'aci-apic-dk9.4.2.7q.bin': 'e7effd7f270f29bfa1d0f4b7f417912b',
            'aci-apic-dk9.5.0.1k.bin': '4d2c8f3bb6a6851a720107368acbabd3',
            'aci-apic-dk9.5.0.1l.bin': 'f1d3a51795964c509784c5f79f46a900',
            'aci-apic-dk9.5.0.2e.bin': 'eebfee269ce0243925a0c52531f6d77d',
            'aci-apic-dk9.5.0.2h.bin': '741bb04bf2a28a293317ef75975ac5bc',
            'aci-apic-dk9.5.0.2i.bin': '07fc18bfc230ff0a903a32e015f4fb84',
            'aci-apic-dk9.5.0.2j.bin': '39f593a40bffbdd83293ff348b307a42',
            'aci-apic-dk9.5.1.1h.bin': '1b312d58d39432bc34bbeac0d16ccf39',
            'aci-apic-dk9.5.1.2e.bin': '09bd8493666110d563efbcb5ae7434c4',
            'aci-apic-dk9.5.1.3e.bin': 'c01ffdb7d18d2bfe59e6906096fd4cd0',
            'aci-apic-dk9.5.1.4c.bin': '81e404745c0058dd0526abf310ba2c92',
            'aci-apic-dk9.5.2.1g.bin': 'f4c79ac1bb3070b4555e507c3d310826',
            'aci-apic-dk9.5.2.1h.bin': '06060f0ae1ca8cc3fa49239c3d94bed5',
            'aci-apic-dk9.5.2.2e.bin': 'e1614cb85fbc244ae2e876c30068abc1',
            'aci-apic-dk9.5.2.2f.bin': 'ffd287454694b780ad1d256c2c986b18',
            'aci-apic-dk9.5.2.2g.bin': '95ef341b64080d26b0cc7b913f6dcc4d',
            'aci-apic-dk9.5.2.2h.bin': 'daf36310cfad2d2c7b37d6432952ca9d',
            'aci-apic-dk9.5.2.3e.bin': '8c3fb4b0b541e7bca022f9557df349b5',
            }

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
                self._log = file(self.log, "a")
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
    logging.debug('response: ' + response)
    imdata = json.loads(response)['imdata']
    if imdata and "error" in imdata[0].keys():
        raise Exception('API call failed! Check debug log')
    else:
        return imdata


def get_credentials():
    while True:
        usr = raw_input('Enter username for APIC login          : ')
        if usr: break
    while True:
        pwd = getpass('Enter password for corresponding User  : ')
        if pwd: break
    print('')
    return usr, pwd


def get_current_version():
    """ Returns: x.y(z) """
    prints("Checking current APIC version (switch nodes are assumed to be on the same version)...", end='')
    firmwares = icurl('class', 'firmwareCtrlrRunning.json')
    for firmware in firmwares:
        if 'node-1' in firmware['firmwareCtrlrRunning']['attributes']['dn']:
            current_version = firmware['firmwareCtrlrRunning']['attributes']['version']
            break
    prints(current_version + '\n')
    return current_version


def get_target_version():
    """ Returns: aci-apic-dk9.x.y.z.bin """
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
            version_choice = raw_input("What is the Target Version?     : ")
            try:
                version_choice = int(version_choice)
                if version_choice < 1 or version_choice > len(repo_list): raise ValueError("")
            except ValueError:
                prints("Please select a value between 1 and %s" % len(repo_list))
                version_choice = None

        version = repo_list[version_choice - 1]
        prints('\nYou have chosen version "%s"\n' % version)
        return str(version)
    else:
        prints("No Firmware Detected!  Please Upload APIC Firmware and re-run the script.\n")
        return ''


class AciVersion():
    v_regex = r'(?:dk9\.)?[1]?(?P<major1>\d)\.(?P<major2>\d)(?:\.|\()(?P<maint>\d+)\.?(?P<patch>(?:[a-b]|[0-9a-z]+))\)?'

    def __init__(self, version):
        self.original = version
        v = re.search(self.v_regex, version)
        self.version = ('{major1}.{major2}({maint}{patch})'
                        .format(**v.groupdict()) if v else None)
        self.major1 = v.group('major1') if v else None
        self.major2 = v.group('major2') if v else None
        self.maint = v.group('maint') if v else None
        self.patch = v.group('patch') if v else None
        self.regex = v

    def older_than(self, version):
        v = re.search(self.v_regex, version)
        if not v: return None
        for i in range(1, len(v.groups())):
            if self.regex.group(i) > v.group(i):
                return False
            elif self.regex.group(i) < v.group(i):
                return True
        return False

    def newer_than(self, version):
        return not self.older_than(version) and not self.same_as(version)

    def same_as(self, version):
        v = re.search(self.v_regex, version)
        ver = ('{major1}.{major2}({maint}{patch})'
               .format(**v.groupdict()) if v else None)
        return self.version == ver


def is_firstver_gt_secondver(first_ver, second_ver):
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
    v = re.search(ver_regex, cversion)
    if v and ((v.group('major1') == 4 and v.group('major2') >= 2) or v.group('major1') >= 5):
        recommended_action = 'Troubleshoot by running "acidiag cluster" on APIC CLI'
    else:
        recommended_action = 'Follow "Initial Fabric Setup" in ACI Troubleshooting Guide 2nd Edition'

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

    cv = re.search(ver_regex, cversion)
    tv = re.search(ver_regex, tversion)
    if (cv and (int(cv.group('major1')) >= 4)) or (tv and (int(tv.group('major1')) <= 3)):
        result = NA
        msg = 'Versions not applicable'
    elif (cv and (int(cv.group('major1')) < 4)) and not tv:
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
            cv = re.search(ver_regex, cversion)
            tv = re.search(ver_regex, tversion)
            cv_is_4_1 = cv and (cv.group('major1') == '4' and cv.group('major2') == '1')
            tv_is_4_1 = tv and (tv.group('major1') == '4' and tv.group('major2') == '1')
            ra = ''
            if cv_is_4_1 and not tv_is_4_1:
                ra = 'Disable Rogue EP during the upgrade because your current version is 4.1'
            elif not cv_is_4_1 and tv_is_4_1:
                ra = 'Disable Rogue EP during the upgrade because your target version is 4.1'
            elif not cv or not tv:
                ra = 'Disable Rogue EP during the upgrade if your current version is 4.1 or your target version is 4.1'
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


def switch_bootflash_usage_check(index, total_checks, **kwargs):
    title = 'Switch Node /bootflash usage'
    result = FAIL_UF
    msg = ''
    headers = ["Pod-ID", "Node-ID", "Utilization", "Alert"]
    data = []
    print_title(title, index, total_checks)

    response_json = icurl('class',
                          'eqptcapacityFSPartition.json?query-target-filter=eq(eqptcapacityFSPartition.path,"/bootflash")')
    if not response_json:
        result = ERROR
        msg = 'bootflash objects not found'

    for eqptcapacityFSPartition in response_json:
        dn = re.search(node_regex, eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['dn'])
        pod = dn.group("pod")
        node = dn.group("node")
        avail = int(eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['avail'])
        used = int(eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['used'])

        usage = (used / (avail + used)) * 100
        if usage >= 50:
            data.append([pod, node, usage, "Over 50% usage! Contact Cisco TAC for Support"])
    if not data:
        result = PASS
        msg = 'all below 50%'
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
    recommended_action = 'Resolve the conflict by removing this config or other configs using this port as L3'
    print_title(title, index, total_checks)

    desc_regex = r'Configuration failed for (?P<failedEpg>.+) due.+Prefix entry sys/ctx-\[vxlan-(?P<vrfvnid>\d+)\]/pfx-\[(?P<prefixInUse>.+)\] is'
    faultInsts = icurl('class',
                       'faultInst.json?&query-target-filter=wcard(faultInst.descr,"prefix-entry-already-in-use")')
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
                data.append([fc, desc_array.group("failedEpg"), desc_array.group("vrfvnid"),
                             vrf_dict.get(desc_array.group("vrfvnid"), '??'), desc_array.group("prefixInUse"),
                             recommended_action])
            else:
                unformatted_data.append(
                    [fc, faultInst['faultInst']['attributes']['descr'], recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
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
        'actrlPrefix': 'Check that "operSt" are set to "enabled". F3544 does not exist on this version.',
        'F3544': 'Ensure that LPM and host routes usage are below the capacity and resolve the fault',
        'F3545': 'Ensure that Policy CAM usage is below the capacity and resolve the fault'
    }
    print_title(title, index, total_checks)
    cfw = AciVersion(cversion)

    # Faults F3544 and F3545 don't exist until 4.1(1a)+
    if cfw.older_than("4.1(1a)"):
        headers = ["Object Class", "Recommended Action"]
        classes = ["actrlRule", "actrlPrefix"]
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


def apic_ssd_check(index, total_checks, **kwargs):
    title = 'APIC SSD Health (F2731 equipment-wearout)'
    result = FAIL_UF
    msg = ''
    headers = ["Fault", "Pod", "Node", "Storage Unit", "% lifetime remaining", "Recommended Action"]
    data = []
    unformatted_headers = ["Fault", "Fault DN", "% lifetime remaining", "Recommended Action"]
    unformatted_data = []
    recommended_action = "Contact TAC for replacement"
    print_title(title, index, total_checks)

    dn_regex = node_regex + r'/.+p-\[(?P<storage>.+)\]-f'
    faultInsts = icurl('class', 'faultInst.json?query-target-filter=eq(faultInst.code,"F2731")')
    for faultInst in faultInsts:
        dn_array = re.search(dn_regex, faultInst['faultInst']['attributes']['dn'])
        lifetime_remaining = "1%"
        if dn_array:
            data.append(['F2731', dn_array.group("pod"), dn_array.group("node"), dn_array.group("storage"),
                         lifetime_remaining, recommended_action])
        else:
            unformatted_data.append(
                ['F2731', faultInst['faultInst']['attributes']['dn'], lifetime_remaining, recommended_action])
    if not data and not unformatted_data:
        result = PASS
    print_result(title, result, msg, headers, data, unformatted_headers, unformatted_data)
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
    for key, epg in epg_encap_dict.iteritems():
        for vlanKey, vlan in epg.iteritems():
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

    mismatch_hits.sort()
    for epg in mismatch_hits:
        for access_encap, nodeFabEncaps in epg["epgDeployment"].iteritems():
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
    cv = AciVersion(cversion)
    if cv.version and (cv.same_as('4.0(1h)') or cv.older_than('3.2(6i)')):
        default_action += ' A typical issue is CSCvn13119.'
    elif not cv.version:
        default_action += ' A typical issue is CSCvn13119 if your current version is affected.'
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
                        continue
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

    if tversion in cco_md5_sum:
        cco_md5 = cco_md5_sum[tversion]
    else:
        cco_md5 = None

    md5s = []
    md5_names = []
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
            c.cmd("ls -aslh /firmware/fwrepos/fwrepo/%s" % tversion)
        except Exception as e:
            data.append([apic_name, '-', '-',
                         'ls command via ssh failed due to:{}'.format(e), '-'])
            print_result(node_title, ERROR)
            continue
        if "No such file or directory" in c.output:
            data.append([apic_name, tversion, '-', 'image not found', recommended_action])
            print_result(node_title, FAIL_UF)
            continue

        try:
            c.cmd("cat /firmware/fwrepos/fwrepo/md5sum/%s" % tversion)
        except Exception as e:
            data.append([apic_name, tversion, '-',
                         'failed to check md5sum via ssh due to:{}'.format(e), '-'])
            print_result(node_title, ERROR)
            continue
        for line in c.output.split("\n"):
            if "md5sum" not in line and "fwrepo" in line:
                md5_regex = r'([^\s]+)'
                md5 = re.search(md5_regex, line)
                if md5 is not None:
                    md5s.append(md5.group(0))
                    if cco_md5 and md5 != cco_md5:
                        data.append([apic_name, tversion, md5.group(0), 'Corrupted image md5 not matching CCO', "Delete and redownload from CCO"])
                    md5_names.append(c.hostname)
        print_result(node_title, DONE)
    if len(set(md5s)) > 1:
        for name, md5 in zip(md5_names, md5s):
            data.append([name, tversion, md5, 'md5sum do not match on all APICs', recommended_action])
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


def apic_ssl_certs_check(index, total_checks, tversion, username, password, **kwargs):
    title = 'APIC SSL Certificate and SSH key Check'
    result = FAIL_UF
    msg = ''
    headers = ['Node-Id', 'Name', 'OpenSSL-Check', 'Cert-format-check', 'SSH-check', 'Recommended Action']
    data = []
    recommended_action = 'Contact Cisco TAC'
    print_title(title, index, total_checks)

    checked_apic = {}
    prints('')
    if tversion:
        tv = AciVersion(tversion)
    controller = icurl('class', 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")')
    for apic in controller:
        attr = apic['topSystem']['attributes']
        if attr['address'] in checked_apic:
            continue
        checked_apic = {attr['address']: 1}
        node_title = 'Checking %s...' % attr['name']
        print_title(node_title)
        try:
            c = Connection(attr['address'])
            c.username = username
            c.password = password
            c.log = LOG_FILE
            c.connect()
        except Exception as e:
            data.append([attr['id'], attr['name'], '-', '-', '-',  e])
            continue

        try:
            c.cmd("acidiag verifyapic")
        except Exception as e:
            data.append([attr['id'], attr['name'], '-', '-', '-',  e])
            continue

        openssl_check = "N/A"
        cert_format_check = "N/A"
        ssh_check = "N/A"
        all_check = "N/A"


        for line in c.output.split("\n"):
            if "serialNumber" in line:
                if "APIC-SERVER" not in line:
                    cert_format_check = "FAIL"
                    checked_apic[attr['address']] = 0
                else:
                    cert_format_check = "passed"
            elif "openssl_check" in line and "certificate" in line:
                continue
            elif "openssl_check" in line:
                if "passed" not in line:
                    openssl_check = "FAIL"
                    checked_apic[attr['address']] = 0
                else:
                    openssl_check = "passed"
            elif "apic_cert_format_check" in line:
                if "passed" not in line:
                    cert_format_check = "FAIL"
                    checked_apic[attr['address']] = 0
                else:
                    cert_format_check = "passed"
            elif "ssh_check" in line:
                if "passed" not in line:
                    ssh_check = "FAIL"
                    checked_apic[attr['address']] = 0
                else:
                    ssh_check = "passed"
        print_result(node_title, DONE)
        if checked_apic[attr['address']] == 0:
            data.append(
                [attr['id'], attr['name'], openssl_check, cert_format_check, ssh_check, recommended_action])

    if not controller:
        result = NA
        msg = 'Failed to Query Controllers'
    elif len(checked_apic) >= 1 and not data:
        result = PASS
    elif tv and tv.same_as('3.2(7f)') or tv.same_as('4.1(1i)') or tv.newer_than('3.2(7f)') or tv.newer_than('4.1(1i)'):
        result = FAIL_UF
    else:
        result = PASS
        msg = "At least one APIC has SSL Cert/SSH key issue"
    print_result(title, result, msg, headers, data, adjust_title=True)
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
    ver = re.search(ver_regex, tversion)
    if not ver:
        print_result(title, ERROR, 'Failed to parse the target firmware version')
        return ERROR

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

        major1 = ver.group('major1')
        major2 = ver.group('major2')
        maint = ver.group('maint')
        ra = ''
        if major1 == "4" and major2 == "2" and maint == "2" and direct_enabled is True:
            ra = recommended_action_4_2_2
        elif int(major1) >= 5 and direct_enabled is False:
            ra = recommended_action_5a
        elif int(major1) >= 5 and direct_enabled == 'Not Supported':
            ra = recommended_action_5b
        if ra:
            result = FAIL_O
            data.append([tversion, "Present", direct_enabled, ra])
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

    tfw = re.search(ver_regex, tversion)
    cfw = re.search(ver_regex, cversion)
    if not tversion:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'
    elif not tfw:
        result = ERROR
        msg = 'Failed to parse the target firmware version'
    elif not cfw:
        result = ERROR
        msg = 'Failed to parse the current firmware version'
    else:
        if cversion not in fixed_versions and int(cfw.group('major1')) < 3:
            current_version_affected = True

        if int(tfw.group('major1')) == 3:
            if int(tfw.group('major2')) >= 2 and int(tfw.group('maint')) >= 2:
                target_version_affected = True
        elif int(tfw.group('major1')) >= 4:
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


def vpc_paired_switches_check(index, total_checks, **kwargs):
    title = 'VPC-paired Leaf switches'
    result = FAIL_O
    msg = ''
    headers = ["Node ID", "Node Name", "Recommended Action"]
    data = []
    vpc_nodes = []
    recommended_action = 'Determine if dataplane redundancy is available if this node goes down'
    doc_url = '"All switch nodes in vPC" from Pre-Upgrade Check Lists'
    print_title(title, index, total_checks)

    top_system = icurl('class', 'topSystem.json')
    prot_pols = icurl('class', 'fabricNodePEp.json')
    if prot_pols:
        for vpc_node in prot_pols:
            vpc_nodes.append(vpc_node['fabricNodePEp']['attributes']['id'])
    else:
        msg = 'No VPC definitions found!'

    for node in top_system:
        node_id = node['topSystem']['attributes']['id']
        role = node['topSystem']['attributes']['role']
        if role == 'leaf' and (node_id not in vpc_nodes):
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
    headers = ["Node ID", "Current CIMC version", "Minimum Recommended CIMC Version"]
    data = []
    recommended_action = 'Plan to upgrade CIMC version prior to APIC upgrade'
    doc_url = '"Compatibility (CIMC Versions)" from Pre-Upgrade Checklists'
    print_title(title, index, total_checks)
    apic_obj = icurl('class', 'eqptCh.json?query-target-filter=wcard(eqptCh.descr,"APIC")')
    tfw = re.search(ver_regex, tversion)
    if apic_obj and tfw:
        pretty_tfw = '{maj1}.{maj2}({maint})'.format(maj1=tfw.group('major1'), maj2=tfw.group('major2'),
                                                     maint=tfw.group('maint'))
        try:
            for eqptCh in apic_obj:
                if eqptCh['eqptCh']['attributes']['cimcVersion']:
                    apic_model = eqptCh['eqptCh']['attributes']['descr']
                    model = "apic" + apic_model.split('-')[2].lower()
                    current_cimc = eqptCh['eqptCh']['attributes']['cimcVersion']
                    compat_lookup_dn = "uni/fabric/compcat-default/ctlrfw-apic-" + pretty_tfw + \
                                       "/rssuppHw-[uni/fabric/compcat-default/ctlrhw-" + model + "].json"
                    compatMo = icurl('mo', compat_lookup_dn)
                    recommended_cimc = compatMo[0]['compatRsSuppHw']['attributes']['cimcVersion']
                    if compatMo and recommended_cimc:
                        if is_firstver_gt_secondver(current_cimc, recommended_cimc):
                            pass
                        else:
                            nodeid = eqptCh['eqptCh']['attributes']['dn'].split('/')[2]
                            data.append([nodeid, current_cimc, recommended_cimc])

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


def eventmgr_db_defect_check(index, total_checks, cversion, **kwargs):
    title = 'Eventmgr DB size defect susceptibility'
    result = PASS
    msg = ''
    headers = ["Potential Defect", "Recommended Action"]
    data = []
    recommended_action = 'Contact Cisco TAC to check the DB size via root'
    print_title(title, index, total_checks)

    cv = AciVersion(cversion)
    if not cv.version:
        result = ERROR
        msg = 'Failed to parse the current firmware version'
    elif cv.older_than('3.2(5d)') or (cv.major1 == '4' and cv.older_than('4.1(1i)')):
        result = FAIL_UF
        data.append(['CSCvn20175', recommended_action])

    print_result(title, result, msg, headers, data)
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
    cfw = re.search(ver_regex, cversion)
    tfw = re.search(ver_regex, tversion)
    if cfw and tfw:
        pretty_tfw = '{maj1}.{maj2}({maint})'.format(maj1=tfw.group('major1'), maj2=tfw.group('major2'),
                                                     maint=tfw.group('maint'))

        pretty_cfw = '{maj1}.{maj2}({maint})'.format(maj1=cfw.group('major1'), maj2=cfw.group('major2'),
                                                     maint=cfw.group('maint'))

        if pretty_cfw != pretty_tfw:
            compatRsUpgRelString = "uni/fabric/compcat-default/ctlrfw-apic-" + pretty_cfw + \
                                   "/rsupgRel-[uni/fabric/compcat-default/ctlrfw-apic-" + pretty_tfw + "].json"
            compatRsUpgRel = icurl('mo', compatRsUpgRelString)
            if not compatRsUpgRel:
                compatRtUpgRelString = "uni/fabric/compcat-default/ctlrfw-apic-" + pretty_cfw + \
                                       "/rtupgRel-[uni/fabric/compcat-default/ctlrfw-apic-" + pretty_tfw + "].json"
                compatRtUpgRel = icurl('mo', compatRtUpgRelString)
                if not compatRtUpgRel:
                    data.append([cversion, tversion, 'Target version not a supported hop'])

        if not data:
            result = PASS

    else:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'

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
    if tversion:
        tfw = AciVersion(tversion)
        if is_firstver_gt_secondver(tfw.version, "5.0(1a)"):
            fabric_node = icurl('class', 'fabricNode.json')
            for node in fabric_node:
                if node['fabricNode']['attributes']['model'] in gen1_models:
                    data.append([tfw.version, node['fabricNode']['attributes']['id'],
                                 node['fabricNode']['attributes']['model'], 'Not supported on 5.x+'])

        if not data:
            result = PASS
    else:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def contract_22_defect_check(index, total_checks, cversion, tversion, **kwargs):
    title = 'Contract Port 22 Defect Check'
    result = PASS
    msg = ''
    headers = ["Potential Defect", "Reason"]
    data = []
    recommended_action = 'Review Software Advisory for details'
    doc_url = 'Cisco Software Advisory Notices for CSCvz65560 - http://cs.co/9007yh22H'
    cfw = AciVersion(cversion)
    print_title(title, index, total_checks)

    if tversion:
        tfw = AciVersion(tversion)
        if cfw.older_than("5.0(1a)") and tfw.newer_than("5.0(1a)"):
            result = FAIL_O
            data.append(["CSCvz65560", "Target Version susceptible to Defect"])
    else:
        result = MANUAL
        msg = 'Target version not supplied. Skipping.'

    print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


if __name__ == "__main__":
    prints('    ==== %s%s ====\n' % (ts, tz))
    username, password = get_credentials()
    try:
        cversion = get_current_version()
        tversion = get_target_version()
    except Exception as e:
        prints('')
        err = 'Error: %s' % e
        print_title(err)
        print_result(err, ERROR)
        print_title("Initial query failed. Ensure APICs are healthy. Ending script run.")
        logging.exception(e)
        sys.exit()
    inputs = {'username': username, 'password': password,
              'cversion': cversion, 'tversion': tversion}
    json_log = {"name": "PreupgradeCheck", "method": "standalone script", "datetime": ts + tz,
                "check_details": [], 'cversion': cversion, 'tversion': tversion}
    checks = [
        # General Checks
        apic_version_md5_check,
        apic_ssl_certs_check,
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
        bd_subnet_overlap_check,
        bd_duplicate_subnet_check,
        vmm_controller_status_check,
        vmm_controller_adj_check,
        lldp_with_infra_vlan_mismatch_check,
        hw_program_fail_check,
        scalability_faults_check,

        # Configurations
        vpc_paired_switches_check,
        overlapping_vlan_pools_check,
        vnid_mismatch_check,
        l3out_mtu_check,
        bgp_peer_loopback_check,
        l3out_route_map_direction_check,
        intersight_upgrade_status_check,

        # Bugs
        ep_announce_check,
        eventmgr_db_defect_check,
        contract_22_defect_check,
    ]
    summary = {PASS: 0, FAIL_O: 0, FAIL_UF: 0, ERROR: 0, MANUAL: 0, NA: 0, 'TOTAL': len(checks)}
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
    summary_headers = [PASS, FAIL_O, FAIL_UF, MANUAL, NA, ERROR, 'TOTAL']
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

    subprocess.check_output(['rm', '-rf', DIR])
