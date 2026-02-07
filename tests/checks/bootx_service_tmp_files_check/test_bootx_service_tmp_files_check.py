import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "bootx_service_tmp_files_check"

fabricNodes = read_data(dir, "fabricNode.json")
apic_ips = [
    mo["fabricNode"]["attributes"]["address"]
    for mo in fabricNodes
    if mo["fabricNode"]["attributes"]["role"] == "controller"
]

ls_cmd = "ls -ltr /firmware/tmp | head -1"
ls_output_neg = "total 171"
ls_output_pos = "total 17880"
ls_output_no_such_file = """\
ls: cannot access /firmware/tmp: No such file or directory
apic1#
"""


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, cversion, conn_failure, conn_cmds, expected_result, expected_data",
    [
        # Connection failure
        (
            {},
            fabricNodes,
            "6.0(8h)",
            True,
            [],
            script.ERROR,
            [
                ["1", "apic1", "-", "Simulated exception at connect()"],
                ["2", "apic2", "-", "Simulated exception at connect()"],
                ["3", "apic3", "-", "Simulated exception at connect()"],
            ],
        ),
        # Simulatated exception at `ls` command
        (
            {},
            fabricNodes,
            "6.0(8h)",
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "",
                        "exception": Exception("Simulated exception at `ls` command"),
                    }
                ]
                for apic_ip in apic_ips
            },
            script.ERROR,
            [
                ["1", "apic1", "-", "Simulated exception at `ls` command"],
                ["2", "apic2", "-", "Simulated exception at `ls` command"],
                ["3", "apic3", "-", "Simulated exception at `ls` command"],
            ],
        ),
        # /firmware/tmp dir not found/not accessible
        (
            {},
            fabricNodes,
            "6.0(8h)",
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output_no_such_file]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            script.ERROR,
            [
                ["1", "apic1", "/firmware/tmp not found", "Check user permissions or retry as 'apic#fallback\\\\admin'"],
                ["2", "apic2", "/firmware/tmp not found", "Check user permissions or retry as 'apic#fallback\\\\admin'"],
                ["3", "apic3", "/firmware/tmp not found", "Check user permissions or retry as 'apic#fallback\\\\admin'"],
            ],
        ),
        # /firmware/tmp dir found, less than 1000 files
        (
            {},
            fabricNodes,
            "6.0(8h)",
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output_neg]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            script.PASS,
            [],
        ),
        # FAIL_O /firmware/tmp dir found, more than 1000 files
        (
            {},
            fabricNodes,
            "6.0(8h)",
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output_pos]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            script.FAIL_O,
            [
                ["1", "apic1", "/firmware/tmp", "17880"],
                ["2", "apic2", "/firmware/tmp", "17880"],
                ["3", "apic3", "/firmware/tmp", "17880"],
            ],
        ),
        # ERROR, fabricNode failure
        (
            {},
            read_data(dir, "fabricNode_no_apic.json"),
            "6.0(8h)",
            False,
            [],
            script.ERROR,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, cversion, mock_conn, expected_result, expected_data):
    result = run_check(
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
        cversion=script.AciVersion(cversion),
    )
    assert result.result == expected_result
    assert result.data == expected_data
