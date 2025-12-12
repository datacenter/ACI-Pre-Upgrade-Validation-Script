import os
import pytest
import logging
import importlib
from helpers.utils import read_data
script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "disabled_cipher_check"
# icurl queries
disabled_ciphers_api= 'commCipher.json?query-target-filter=and(or(wcard(commCipher.id,"ECDHE-RSA"),wcard(commCipher.id,"DHE-RSA"),wcard(commCipher.id,"TLS_AES_256")),eq(commCipher.state,"disabled"))'

@pytest.mark.parametrize(
    "icurl_outputs, conn_cmds, tversion, expected_result",
    [
        # tversion not given
        (
            {disabled_ciphers_api: []},
            {},
            None,
            script.MANUAL,
        ),
        # tversion is not hit
        (
            {disabled_ciphers_api: []},
            {},
            "6.0(6c)",
            script.NA,
        ),
        # tversion is hit, no disabled ciphers
        (
            {disabled_ciphers_api: read_data(dir,"commCipher_no_disabled_ciphers.json")},
            {},
            "6.0(2h)",
            script.PASS,
        ),
        # tversion is hit, disabled ciphers found but no fabric_nodes (empty list)
        (
            {disabled_ciphers_api: read_data(dir,"commCipher_disabled_ciphers.json")},
            {},
            "6.0(2h)",
            script.ERROR,
        ),
        # tversion is hit, disabled ciphers found with APIC details, nginx error FOUND
        (
            {disabled_ciphers_api: read_data(dir,"commCipher_disabled_ciphers.json")},
            {
                "10.0.0.1": [{
                    "cmd": 'zgrep "Failed to write nginxproxy conf file" /var/log/dme/log/nginx.bin.war* 2>/dev/null | head -20',
                    "output": "2025-12-12 Failed to write nginxproxy conf file\n",
                    "exception": None
                }],
                "10.0.0.2": [{
                    "cmd": 'zgrep "Failed to write nginxproxy conf file" /var/log/dme/log/nginx.bin.war* 2>/dev/null | head -20',
                    "output": "2025-12-12 Failed to write nginxproxy conf file\n",
                    "exception": None
                }],
                "10.0.0.3": [{
                    "cmd": 'zgrep "Failed to write nginxproxy conf file" /var/log/dme/log/nginx.bin.war* 2>/dev/null | head -20',
                    "output": "2025-12-12 Failed to write nginxproxy conf file\n",
                    "exception": None
                }],
            },
            "6.0(2h)",
            script.FAIL_O,
        ),
        # tversion is hit, disabled ciphers found with APIC details, nginx error NOT found
        (
            {disabled_ciphers_api: read_data(dir,"commCipher_disabled_ciphers.json")},
            {
                "10.0.0.1": [{
                    "cmd": 'zgrep "Failed to write nginxproxy conf file" /var/log/dme/log/nginx.bin.war* 2>/dev/null | head -20',
                    "output": "",
                    "exception": None
                }],
                "10.0.0.2": [{
                    "cmd": 'zgrep "Failed to write nginxproxy conf file" /var/log/dme/log/nginx.bin.war* 2>/dev/null | head -20',
                    "output": "",
                    "exception": None
                }],
                "10.0.0.3": [{
                    "cmd": 'zgrep "Failed to write nginxproxy conf file" /var/log/dme/log/nginx.bin.war* 2>/dev/null | head -20',
                    "output": "",
                    "exception": None
                }],
            },
            "6.0(2h)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, mock_conn, tversion, expected_result):
    # For ERROR test case, pass empty fabric_nodes to simulate missing controllers
    if expected_result == script.ERROR:
        fabric_nodes = []
    else:
        fabric_nodes = read_data(dir, "fabricNode.json")
    
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        username="admin",
        password="password",
        fabric_nodes=fabric_nodes
    )
    assert result.result == expected_result