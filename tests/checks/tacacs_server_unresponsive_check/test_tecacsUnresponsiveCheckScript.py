import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "tacacs_server_unresponsive_check"

fabricNodes = read_data(dir, "fabricNode.json")
controllers = [mo for mo in fabricNodes if mo["fabricNode"]["attributes"]["role"] == "controller"]

grep_cmd = 'cd /var/log/dme/log && zgrep -c "AAA server is unresponsive or too slow to respond" nginx.bin.log'

grep_output_zero = "0"
grep_output_with_events_apic1 = "150"
grep_output_with_events_apic2 = "200"
grep_output_with_events_apic3 = "75"


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, conn_failure, conn_cmds, tversion, expected_result",
    [
        # NO TVERSION PROVIDED - MANUAL CHECK
        (
            {},
            fabricNodes,
            False,
            {},
            None,
            script.MANUAL,
        ),
        # TVERSION >= 6.1(4h) - Not Affected
        (
            {},
            fabricNodes,
            False,
            {},
            "6.1(4h)",
            script.PASS,
        ),
        # No fabricNode for APICs
        (
            {},
            read_data(dir, "fabricNode_noApic.json"),
            False,
            {},
            "6.1(3a)",
            script.ERROR,
        ),
        # Exception failure at grep command on all APICs
        (
            {},
            fabricNodes,
            False,
            {
                controller["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "",
                        "exception": Exception("Simulated exception at grep command"),
                    }
                ]
                for controller in controllers
            },
            "6.1(3a)",
            script.ERROR,
        ),
        # TVERSION < 6.1(4h) and no TACACS events found (count = 0 on all APICs)
        (
            {},
            fabricNodes,
            False,
            {
                controller['fabricNode']['attributes']['address']: [
                    {
                        "cmd": grep_cmd,
                        "output": "0\n",
                        "exception": None,
                    }
                ]
                for controller in controllers
            },
            "5.2(1a)",
            script.PASS,
        ),
        # TVERSION < 6.1(4h) and TACACS events found on all APICs
        (
            {},
            fabricNodes,
            False,
            {
                controllers[0]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "150\n",
                        "exception": None,
                    }
                ],
                controllers[1]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "200\n",
                        "exception": None,
                    }
                ],
                controllers[2]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "75\n",
                        "exception": None,
                    }
                ],
            },
            "6.1(3a)",
            script.FAIL_O,
        ),
        # Mixed scenario: Some APICs have events, some don't
        (
            {},
            fabricNodes,
            False,
            {
                controllers[0]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "150\n",
                        "exception": None,
                    }
                ],
                controllers[1]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "0\n",
                        "exception": None,
                    }
                ],
                controllers[2]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "75\n",
                        "exception": None,
                    }
                ],
            },
            "6.0(2a)",
            script.FAIL_O,
        ),
        # Mixed scenario: Connection failure on one APIC, success with events on others
        (
            {},
            fabricNodes,
            False,
            {
                controllers[0]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "150\n",
                        "exception": None,
                    }
                ],
                controllers[1]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "",
                        "exception": Exception("SSH timeout"),
                    }
                ],
                controllers[2]["fabricNode"]["attributes"]["address"]: [
                    {
                        "cmd": grep_cmd,
                        "output": "0\n",
                        "exception": None,
                    }
                ],
            },
            "6.1(2a)",
            script.ERROR,
        ),
    ],
)
def test_logic( run_check,mock_icurl,mock_conn,icurl_outputs,fabric_nodes,tversion,expected_result):
    result = run_check(fabric_nodes=fabric_nodes,tversion=script.AciVersion(tversion) if tversion else None,username="admin",password="password")
    assert result.result == expected_result