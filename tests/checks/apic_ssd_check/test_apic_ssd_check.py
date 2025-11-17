import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_ssd_check"


faultInst = 'faultInst.json?query-target-filter=or(eq(faultInst.code,"F2731"),eq(faultInst.code,"F2732"))'

apic_ips = [
    node["fabricNode"]["attributes"]["address"]
    for node in read_data(dir, "fabricNode.json")
    if node["fabricNode"]["attributes"]["role"] == "controller"
]

grep_cmd = 'grep -oE "SSD Wearout Indicator is [0-9]+"  /var/log/dme/log/svc_ifc_ae.bin.log | tail -1'
grep_output_hit = "5504||2023-01-11T22:11:26.851446656+00:00||ifc_ae||DBG4||fn=[getWearout]||SSD Wearout Indicator is 4||../svc/ae/src/gen/ifc/beh/imp/./eqpt/StorageBI.cc||395"
grep_output_no_hit = "5504||2023-01-11T22:11:26.851446656+00:00||ifc_ae||DBG4||fn=[getWearout]||SSD Wearout Indicator is 5||../svc/ae/src/gen/ifc/beh/imp/./eqpt/StorageBI.cc||395"


@pytest.mark.parametrize(
    "icurl_outputs, conn_failure, conn_cmds, cversion, fabric_nodes, expected_result, expected_data",
    [
        # New Versions, F273x are effective and raised
        (
            {faultInst: read_data(dir, "fault_F2731.json")},
            False,
            [],
            "4.2(7w)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
            [["2", "3", "/dev/sdb", "<5% (Fault F2731)", "Contact TAC for replacement"]],
        ),
        (
            {faultInst: read_data(dir, "fault_F2731.json")},
            False,
            [],
            "5.2(1h)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
            [["2", "3", "/dev/sdb", "<5% (Fault F2731)", "Contact TAC for replacement"]],
        ),
        # New Versions, F273x are effective and NOT raised
        (
            {faultInst: []},
            False,
            [],
            "4.2(7w)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
        (
            {faultInst: []},
            False,
            [],
            "5.2(1h)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
        # Old Versions, but F273x was still raised.
        (
            {faultInst: read_data(dir, "fault_F2731.json")},
            False,
            [],
            "4.2(6o)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
            [["2", "3", "/dev/sdb", "<5% (Fault F2731)", "Contact TAC for replacement"]],
        ),

        # --- Old Versions, no F273x was raised. ---

        # No fabricNode for APICs
        (
            {faultInst: []},
            False,
            [],
            "4.2(6o)",
            read_data(dir, "fabricNode_no_apic.json"),
            script.ERROR,
            [],
        ),
        # Exception failure at the very first connection()
        (
            {faultInst: []},
            True,
            [],
            "4.2(6o)",
            read_data(dir, "fabricNode.json"),
            script.ERROR,
            [
                ["1", "1", "-", "-", "Simulated exception at connect()"],
                ["1", "2", "-", "-", "Simulated exception at connect()"],
                ["2", "3", "-", "-", "Simulated exception at connect()"],
            ],
        ),
        # Exception failure at the grep command
        (
            {faultInst: []},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "",
                        "exception": Exception("Simulated exception at `grep` command"),
                    }
                ]
                for apic_ip in apic_ips
            },
            "4.2(6o)",
            read_data(dir, "fabricNode.json"),
            script.ERROR,
            [
                ["1", "1", "-", "-", "Simulated exception at `grep` command"],
                ["1", "2", "-", "-", "Simulated exception at `grep` command"],
                ["2", "3", "-", "-", "Simulated exception at `grep` command"],
            ],
        ),
        # SSD Wearout Indicator is less than 5
        (
            {faultInst: []},
            False,
            {
                apic_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_hit]),
                        "exception": None,
                    },
                ],
                apic_ips[1]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_hit]),
                        "exception": None,
                    },
                ],
                apic_ips[2]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_hit]),
                        "exception": None,
                    },
                ],
            },
            "4.2(6o)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
            [
                ["1", "1", "Solid State Disk", "4", "Contact TAC for replacement"],
                ["1", "2", "Solid State Disk", "5", "No Action Required"],
                ["2", "3", "Solid State Disk", "4", "Contact TAC for replacement"],
            ],
        ),
        # Pass
        (
            {faultInst: []},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_hit]),
                        "exception": None,
                    },
                ]
                for apic_ip in apic_ips
            },
            "4.2(6o)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, mock_conn, cversion, fabric_nodes, expected_result, expected_data):
    result = run_check(
        cversion=script.AciVersion(cversion),
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
