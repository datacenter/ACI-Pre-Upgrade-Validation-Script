import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "mpod_spine_coop_sync_check"

fabricNodes = read_data(dir, "fabricNode.json")

modular_spines = ["N9K-C9408" , "N9K-C9504", "N9K-C9508", "N9K-C9516"]

fabricSetupPs = "fabricSetupP.json"

spine_ips = [
    mo["fabricNode"]["attributes"]["address"]
    for mo in fabricNodes
    if mo["fabricNode"]["attributes"]["model"] in modular_spines
]

bootflash_cmd = "ls bootflash/ | grep boots"
bootflash_output_neg = """
bootscript
bootstrap.xml
"""
bootflash_output_pos = "bootstrap.xml"
bootflash_output_no_such_file = ""


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, tversion, conn_failure, conn_cmds, expected_result, expected_data",
    [
        # MANUAL, Tversion not provided
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP.json")
            },
            read_data(dir, "fabricNode-neg.json"),
            None,
            False,
            [],
            script.MANUAL,
            [],
        ),
        # NA, Version not affected, Models not affected
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP.json")
            },
            read_data(dir, "fabricNode-neg.json"),
            "6.0(5h)",
            False,
            [],
            script.NA,
            [],
        ),
        # NA, Versions not affected, Models affected
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP.json")
            },
            fabricNodes,
            "5.2(7f)",
            False,
            [],
            script.NA,
            [],
        ),
        # NA, Version Affected, NO fabricNode with affected models
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP.json")
            },
            read_data(dir, "fabricNode-Neg.json"),
            "6.1(4h)",
            False,
            [],
            script.NA,
            [],
        ),
        # NA, Version affected, Models affected, NO Multipod
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP-neg.json") 
            },
            fabricNodes,
            "6.1(4h)",
            False,
            [],
            script.NA,
            [],
        ),
        # Connection failure
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP.json")
            },
            fabricNodes,
            "6.1(4h)",
            True,
            [],
            script.ERROR,
            [
                ["201", "spine1", "Simulated exception at connect()"],
                ["202", "spine2", "Simulated exception at connect()"],
                ["203", "spine3", "Simulated exception at connect()"],
                ["204", "spine4", "Simulated exception at connect()"],
            ],
        ),
        # Simulated exception at `ls bootflash/ command` command
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP.json")
            },
            fabricNodes,
            "6.1(4h)",            
            False,
            {
                switch_ip: [
                    {
                        "cmd": bootflash_cmd,
                        "output": "",
                        "exception": Exception("Simulated exception at `ls` command"),
                    }
                ]
                for switch_ip in spine_ips
            },
            script.ERROR,
            [
                ["201", "spine1", "Simulated exception at `ls` command"],
                ["202", "spine2", "Simulated exception at `ls` command"],
                ["203", "spine3", "Simulated exception at `ls` command"],
                ["204", "spine4", "Simulated exception at `ls` command"],
            ],
        ),
        # PASS Affected Models, both bootstrap and bootscrip files present
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP.json")
            },
            fabricNodes,
            "6.1(4h)",
            False,
            {
                switch_ip: [
                    {
                        "cmd": bootflash_cmd,
                        "output": "\n".join([bootflash_cmd, bootflash_output_neg]),
                        "exception": None,
                    }
                ]
                for switch_ip in spine_ips
            },
            script.PASS,
            [],
        ),
        # FAIL_O Affected Models, bootscript missing, bootstrap.xml present,
        (
            {
                fabricSetupPs: read_data(dir, "fabricSetupP.json")
            },
            fabricNodes,
            "6.1(4h)",            
            False,
            {
                switch_ip: [
                    {
                        "cmd": bootflash_cmd,
                        "output": "\n".join([bootflash_cmd, bootflash_output_pos]),
                        "exception": None,
                    }
                ]
                for switch_ip in spine_ips
            },
            script.FAIL_O,
            [
                ["201", "spine1", "bootscript file missing!!"],
                ["202", "spine2", "bootscript file missing!!"],
                ["203", "spine3", "bootscript file missing!!"],
                ["204", "spine4", "bootscript file missing!!"],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, tversion, mock_conn, expected_result, expected_data):
    result = run_check(
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data