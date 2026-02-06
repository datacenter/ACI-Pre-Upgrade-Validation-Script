import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "gx_hw_changes_bit_check"

fabricNodes = read_data(dir, "fabricNode-Pos.json")
switch_ips = [
    mo["fabricNode"]["attributes"]["address"]
    for mo in fabricNodes
    if "-GX" in mo["fabricNode"]["attributes"]["model"]
]

sprom_cmd = "vsh -c 'show sprom cpu-info' | grep 'HW Changes Bits'"
sprom_output_neg = " HW Changes Bits : 0x0"
sprom_output_pos = " HW Changes Bits : 0x3"

sprom_output_no_such_file = ""


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, cversion, tversion, conn_failure, conn_cmds, expected_result, expected_data",
    [
        # NA, no fabricNode with affected models
        (
            {},
            read_data(dir, "fabricNode-Neg.json"),
            "4.2(3b)",
            "4.2(4p)",
            False,
            [],
            script.NA,
            [],
        ),
        # NA, Versions not affected
        (
            {},
            read_data(dir, "fabricNode-Neg.json"),
            "4.2(5l)",
            "6.0(1h)",
            False,
            [],
            script.NA,
            [],
        ),
        # NA, Versions not affected
        (
            {},
            read_data(dir, "fabricNode-Neg.json"),
            "4.2(1f)",
            "5.2(7f)",
            False,
            [],
            script.NA,
            [],
        ),
        # Connection failure
        (
            {},
            fabricNodes,
            "4.2(3b)",
            "4.2(4b)",
            True,
            [],
            script.ERROR,
            [
                ["101", "leaf1", "Simulated exception at connect()"],
                ["103", "leaf3", "Simulated exception at connect()"],
            ],
        ),
        # Simulated exception at `show sprom cpu-info` command
        (
            {},
            fabricNodes,
            "4.2(3b)",
            "4.2(4p)",            
            False,
            {
                switch_ip: [
                    {
                        "cmd": sprom_cmd,
                        "output": "",
                        "exception": Exception("Simulated exception at `vsh` command"),
                    }
                ]
                for switch_ip in switch_ips
            },
            script.ERROR,
            [
                ["101", "leaf1", "Simulated exception at `vsh` command"],
                ["103", "leaf3", "Simulated exception at `vsh` command"],
            ],
        ),
        # PASS Affected Models, cpu-info is correct (0x0)
        (
            {},
            fabricNodes,
            "4.2(3b)",
            "4.2(4c)",
            False,
            {
                switch_ip: [
                    {
                        "cmd": sprom_cmd,
                        "output": "\n".join([sprom_cmd, sprom_output_neg]),
                        "exception": None,
                    }
                ]
                for switch_ip in switch_ips
            },
            script.PASS,
            [],
        ),
        # FAIL_UF Affected Models, cpu-info is incorrect (0x3)
        (
            {},
            fabricNodes,
            "4.2(3b)",
            "4.2(4p)",            
            False,
            {
                switch_ip: [
                    {
                        "cmd": sprom_cmd,
                        "output": "\n".join([sprom_cmd, sprom_output_pos]),
                        "exception": None,
                    }
                ]
                for switch_ip in switch_ips
            },
            script.FAIL_UF,
            [
                ["101", "leaf1", "0x3 Found!"],
                ["103", "leaf3", "0x3 Found!"],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, cversion, tversion, mock_conn, expected_result, expected_data):
    result = run_check(
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data
