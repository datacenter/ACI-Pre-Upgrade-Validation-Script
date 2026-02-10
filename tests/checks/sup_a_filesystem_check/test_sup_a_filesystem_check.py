import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "sup_a_filesystem_check"

n9k_sup_api = 'eqptSupC.json'
n9k_sup_api += '?query-target-filter=and(wcard(eqptSupC.model,"N9K-SUP-A"))'

fabricNodes = read_data(dir, "fabricNode.json")
switch_ips = [
    mo["fabricNode"]["attributes"]["address"]
    for mo in fabricNodes
    if mo["fabricNode"]["attributes"]["role"] == "spine"
]

mntpss_cmd = "du -ahm /mnt/pss/bootlogs/ | sort -rh | head -15"
mntpss_output_neg = """\
5	/mnt/pss/bootlogs/
2	/mnt/pss/bootlogs/1/sysmgr.log
2	/mnt/pss/bootlogs/1
1	/mnt/pss/bootlogs/9/sysmgr.log
1	/mnt/pss/bootlogs/9/nvram_prev_oops_blk_2.log
1	/mnt/pss/bootlogs/9/nvram_prev_oops_blk_1.log
1	/mnt/pss/bootlogs/9/nvram_prev_dmesg_blk_2_inactive.log
1	/mnt/pss/bootlogs/9/nvram_prev_dmesg_blk_1_active.log
1	/mnt/pss/bootlogs/9/isan.log
"""


mntpss_output_pos = """\
55	/mnt/pss/bootlogs/
32	/mnt/pss/bootlogs/1/sysmgr.log
31	/mnt/pss/bootlogs/9/nvram_prev_dmesg_blk_1_active.log
1	/mnt/pss/bootlogs/9/isan.log
"""

mntpss_output_no_such_file = """\
ls: cannot access /mnt/pss/bootlogs: No such file or directory
spine#
"""

@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, tversion, conn_failure, conn_cmds, expected_result, expected_data",
    [
        # MANUAL, no tversion 
        (
            {
                n9k_sup_api: read_data(dir, "eqptSupC-pos.json")
                },
            fabricNodes,
            False,
            False,
            [],
            script.MANUAL,
            [],
        ),
        # NA, no fabricNode with affected models
        (
            {
                n9k_sup_api: []
                },
            fabricNodes,
            "6.0(8a)",
            False,
            [],
            script.NA,
            [],
        ),
        # NA, Versions not affected
        (
            {
                n9k_sup_api: read_data(dir, "eqptSupC-pos.json")
                },
            fabricNodes,
            "6.1(4d)",
            False,
            [],
            script.NA,
            [],
        ),
        # Connection failure
        (
            {
                n9k_sup_api: read_data(dir, "eqptSupC-pos.json")
                },
            fabricNodes,
            "4.2(4c)",
            True,
            [],
            script.ERROR,
            [
                ["1201", "spine1","-", "Simulated exception at connect()"],
                ["1202", "spine2", "-","Simulated exception at connect()"],
                ["1203", "spine3", "-","Simulated exception at connect()"],
            ],
        ),
        # Simulated exception at `du /mnt/pss ` command
        (
            {
                n9k_sup_api: read_data(dir, "eqptSupC-pos.json")
                },
            fabricNodes,
            "5.2(4l)",            
            False,
            {
                switch_ip: [
                    {
                        "cmd": mntpss_cmd,
                        "output": "\n".join([mntpss_cmd, mntpss_output_no_such_file]),
                        "exception": Exception("Simulated exception at `du` command"),
                    }
                ]
                for switch_ip in switch_ips
            },
            script.ERROR,
            [
                ["1201", "spine1", "-", "Simulated exception at `du` command"],
                ["1202", "spine2", "-", "Simulated exception at `du` command"],
                ["1203", "spine3", "-", "Simulated exception at `du` command"],
            ],
        ),
        # PASS Affected Models, cpu-info is correct (0x0)
        (
            {
                n9k_sup_api: read_data(dir, "eqptSupC-pos.json")
                },
            fabricNodes,
            "5.2(4c)",
            False,
            {
                switch_ip: [
                    {
                        "cmd": mntpss_cmd,
                        "output": "\n".join([mntpss_cmd, mntpss_output_neg]),
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
            {
                n9k_sup_api: read_data(dir, "eqptSupC-pos.json")
                },
            fabricNodes,
            "5.2(4p)",            
            False,
            {
                switch_ip: [
                    {
                        "cmd": mntpss_cmd,
                        "output": "\n".join([mntpss_cmd, mntpss_output_pos]),
                        "exception": None,
                    }
                ]
                for switch_ip in switch_ips
            },
            script.FAIL_UF,
            [
                ["1201", "spine1", "32", "/mnt/pss/bootlogs/1/sysmgr.log"],
                ["1201", "spine1", "31", "/mnt/pss/bootlogs/9/nvram_prev_dmesg_blk_1_active.log"],
                ["1202", "spine2", "32", "/mnt/pss/bootlogs/1/sysmgr.log"],
                ["1202", "spine2", "31", "/mnt/pss/bootlogs/9/nvram_prev_dmesg_blk_1_active.log"],
                ["1203", "spine3", "32", "/mnt/pss/bootlogs/1/sysmgr.log"],
                ["1203", "spine3", "31", "/mnt/pss/bootlogs/9/nvram_prev_dmesg_blk_1_active.log"],
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