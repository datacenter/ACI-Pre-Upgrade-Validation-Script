import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
Result = script.Result

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "switch_ssd_check"

# icurl queries
faultInst = 'faultInst.json?query-target-filter=or(eq(faultInst.code,"F3073"),eq(faultInst.code,"F3074"))'
eqptFlash = 'eqptFlash.json?query-target-filter=eq(eqptFlash.vendor,"Micron")'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, cversion, expected_result, expected_data",
    [
        # MANUAL - tversion missing (TVER_MISSING), no faults
        (
            {faultInst: []},
            None, "6.0(2h)",
            script.MANUAL,
            [],
        ), 
        # FAIL_O - genuine F3073/F3074 faults, version not affected
        (
            {faultInst: read_data(dir, "faultInst.json")},
            "6.0(2h)", "6.0(1a)",
            script.FAIL_O,
            [
                [
                    "F3073",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "90%",
                    "Contact Cisco TAC for replacement procedure",
                ],
                [
                    "F3074",
                    "1",
                    "101",
                    "Micron_M600_MTFDDAT064MBF",
                    "80%",
                    "Monitor (no impact to upgrades)",
                ],
            ],
        ),
        # PASS - no faults, version not affected (Micron block skipped)
        (
            {faultInst: []},
            "6.0(2h)", "6.0(1a)",
            script.PASS,
            [],
        ),
        # PASS - no faults, tversion affected 6.1(5e), no Micron drives
        (
            {faultInst: [], eqptFlash: []},
            "6.1(5e)", "6.0(2h)",
            script.PASS,
            [],
        ),
        # PASS - no faults, tversion affected 6.2(1g), no Micron drives
        (
            {faultInst: [], eqptFlash: []},
            "6.2(1g)", "6.0(2h)",
            script.PASS,
            [],
        ),
        # PASS - no faults, cversion affected 6.1(5e), no Micron drives
        (
            {faultInst: [], eqptFlash: []},
            "6.2(2a)", "6.1(5e)",
            script.PASS,
            [],
        ),
        # MANUAL - no faults, tversion affected 6.1(5e), single Micron drive
        (
            {faultInst: [], eqptFlash: read_data(dir, "eqptFlash_single_micron_noFault.json")},
            "6.1(5e)", "6.0(2h)",
            script.MANUAL,
            [
                [
                    "CSCwt38698 (False Fault Micron SSD defect)",
                    "1",
                    "103",
                    "MTFDDAK240MBB",
                    "N/A",
                    "",
                ],
            ],
        ),
        # MANUAL - no faults, multiple Micron drives, tversion affected
        (
            {faultInst: [], eqptFlash: read_data(dir, "eqptFlash_multi_micron.json")},
            "6.1(5e)", "6.0(2h)",
            script.MANUAL,
            [
                [
                    "CSCwt38698 (False Fault Micron SSD defect)",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "N/A",
                    "",
                ],
                [
                    "CSCwt38698 (False Fault Micron SSD defect)",
                    "1",
                    "101",
                    "Micron_M600_MTFDDAT064MBF",
                    "N/A",
                    "",
                ],
            ],
        ),
        # MANUAL - false fault present + cversion affected + Micron drive
        (
            {
                faultInst: read_data(dir, "faultInst.json"),
                eqptFlash: read_data(dir, "eqptFlash_multi_micron.json"),
            },
            "6.2(2a)", "6.1(5e)",
            script.MANUAL,
            [
                [
                    "CSCwt38698 (False Fault Micron SSD defect)",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "N/A",
                    "",
                ],
                [
                    "CSCwt38698 (False Fault Micron SSD defect)",
                    "1",
                    "101",
                    "Micron_M600_MTFDDAT064MBF",
                    "N/A",
                    "",
                ],
            ],
        ),
        # FAIL_O - Genuine fault present + cversion affected + Micron drive
        (
            {
                faultInst: read_data(dir, "faultInst.json"),
                eqptFlash: read_data(dir, "eqptFlash_single_micron_noFault.json"),
            },
            "6.2(2a)", "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "F3073",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "90%",
                    "Contact Cisco TAC for replacement procedure",
                ],
                [
                    "F3074",
                    "1",
                    "101",
                    "Micron_M600_MTFDDAT064MBF",
                    "80%",
                    "Monitor (no impact to upgrades)",
                ],
            ],
        ),
        # FAIL_O - fault present + tversion matched + Micron drive found
        (
            {
                faultInst: read_data(dir, "faultInst.json"),
                eqptFlash: read_data(dir, "eqptFlash_single_micron_noFault.json"),
            },
            "6.1(5e)", "6.0(2h)",
            script.FAIL_O,
            [
                [
                    "F3073",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "90%",
                    "Contact Cisco TAC for replacement procedure",
                ],
                [
                    "F3074",
                    "1",
                    "101",
                    "Micron_M600_MTFDDAT064MBF",
                    "80%",
                    "Monitor (no impact to upgrades)",
                ],
            ],
        ),
        # MANUAL - false fault present + cversion matched + Micron drive found
        (
            {
                faultInst: read_data(dir, "faultInst.json"),
                eqptFlash: read_data(dir, "eqptFlash_multi_micron.json"),
            },
            "6.2(2a)", "6.1(5e)",
            script.MANUAL,
            [
                [
                    "CSCwt38698 (False Fault Micron SSD defect)",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "N/A",
                    "",
                ],
                [
                    "CSCwt38698 (False Fault Micron SSD defect)",
                    "1",
                    "101",
                    "Micron_M600_MTFDDAT064MBF",
                    "N/A",
                    "",
                ],
            ],
        ),
        # FAIL_O - fault present + cversion matched + Micron drive absent
        (
            {
                faultInst: read_data(dir, "faultInst.json"),
                eqptFlash: [],
            },
            "6.2(2a)", "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "F3073",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "90%",
                    "Contact Cisco TAC for replacement procedure",
                ],
                [
                    "F3074",
                    "1",
                    "101",
                    "Micron_M600_MTFDDAT064MBF",
                    "80%",
                    "Monitor (no impact to upgrades)",
                ],
            ],
        ),
        # FAIL_O - Genuine + false fault present + cversion matched + Micron drive found
        (
            {
                faultInst: read_data(dir, "faultInst.json"),
                eqptFlash: read_data(dir, "eqptFlash_single_micron_withFault.json"),
            },
            "6.2(2a)", "6.1(5e)",
            script.FAIL_O,
            [
                [
                    'F3074', 
                    '1', 
                    '101', 
                    'Micron_M600_MTFDDAT064MBF', 
                    '80%', 
                    'Monitor (no impact to upgrades)'
                ],
                [
                    "CSCwt38698 (False Fault Micron SSD defect)",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "N/A",
                    "",
                ],
            ],
        ),
        # FAIL_O - Same node (205), different slots: genuine fault (Intel SSD) + false fault (Micron SSD)
        (
            {
                faultInst: read_data(dir, "faultInst.json"),
                eqptFlash: read_data(dir, "eqptFlash_mixed_node.json"),
            },
            "6.2(2a)", "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "F3073",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "90%",
                    "Contact Cisco TAC for replacement procedure",
                ],
                [
                    'F3074', 
                    '1', 
                    '101', 
                    'Micron_M600_MTFDDAT064MBF', 
                    '80%', 
                    'Monitor (no impact to upgrades)'
                ],
            ],
        ), 
    ],
)
def test_logic(run_check, mock_icurl, tversion, cversion, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        cversion=script.AciVersion(cversion) if cversion else None
    )
    assert result.result == expected_result
    assert result.data == expected_data