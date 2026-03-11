import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "supported_hardware_check"
# icurl queries
eqptLC = "eqptLC.json"
eqptExtCh = "eqptExtCh.json"
eqptSupC = "eqptSupC.json"

@pytest.mark.parametrize(
    "icurl_outputs, tversion, fabric_nodes, expected_result, expected_data",
    [
        # FAIL - unsupported Gen1 and 6.1(1)+ deprecated hardware found
        (
            {
                eqptLC: read_data(dir, "eqptLC_with_unsupported.json"),
                eqptExtCh: read_data(dir, "eqptExtCh_with_unsupported.json"),
                eqptSupC: read_data(dir, "eqptSupC_with_unsupported.json"),
            },
            "6.1(1f)",
            read_data(dir, "fabricNode_with_unsupported_hardware.json"),
            script.FAIL_UF,
            [
                ["6.1(1f)", "101", "N9K-C9372TX-E", "Switch", "Not supported on 5.x+"],
                ["6.1(1f)", "1001", "N9K-M6PQ", "Expansion Module", "Not supported on 5.x+"],
                ["6.1(1f)", "102", "N9K-C93180LC-EX", "Switch", "Deprecated from 6.1(1)+"],
                ["6.1(1f)", "101", "N2K-C2232PP-10GE", "FEX", "Deprecated from 6.1(1)+"],
                ["6.1(1f)", "1001", "N9K-SUP-B", "Supervisor", "Deprecated from 6.1(1)+"],
            ],
        ),
        # PASS - no unsupported hardware found
        (
            {
                eqptLC: read_data(dir, "eqptLC_supported_only.json"),
                eqptExtCh: read_data(dir, "eqptExtCh_supported_only.json"),
                eqptSupC: read_data(dir, "eqptSupC_supported_only.json"),
            },
            "6.1(1f)",
            read_data(dir, "fabricNode_supported_only.json"),
            script.PASS,
            [],
        ),
        # FAIL - pre 6.1(1f): only Gen1 hit should be reported
        (
            {
                eqptLC: read_data(dir, "eqptLC_supported_only.json"),
            },
            "6.1(1a)",
            read_data(dir, "fabricNode_with_unsupported_hardware.json"),
            script.FAIL_UF,
            [["6.1(1a)", "101", "N9K-C9372TX-E", "Switch", "Not supported on 5.x+"]],
        ),
        # PASS - pre 5.x: unsupported hardware checks should not trigger
        (
            {
                eqptLC: read_data(dir, "eqptLC_with_unsupported.json"),
                eqptExtCh: read_data(dir, "eqptExtCh_with_unsupported.json"),
                eqptSupC: read_data(dir, "eqptSupC_with_unsupported.json"),
            },
            "4.2(7r)",
            read_data(dir, "fabricNode_with_unsupported_hardware.json"),
            script.PASS,
            [],
        ),
        # FAIL - 6.0(1)+ unsupported switch model
        (
            {
                eqptLC: read_data(dir, "eqptLC_supported_only.json"),
            },
            "6.0(1a)",
            [
                {
                    "fabricNode": {
                        "attributes": {
                            "id": "201",
                            "model": "N9K-C93120TX",
                        }
                    }
                }
            ],
            script.FAIL_UF,
            [["6.0(1a)", "201", "N9K-C93120TX", "Switch", "Deprecated from 6.0(1)+"]],
        ),
        # PASS - empty fabric nodes and supported inventory
        (
            {
                eqptLC: read_data(dir, "eqptLC_supported_only.json"),
                eqptExtCh: read_data(dir, "eqptExtCh_supported_only.json"),
                eqptSupC: read_data(dir, "eqptSupC_supported_only.json"),
            },
            "6.1(1f)",
            [],
            script.PASS,
            [],
        ),
        # FAIL - malformed DN should fall back to '-'
        (
            {
                eqptLC: read_data(dir, "eqptLC_with_unsupported_bad_dn.json"),
                eqptExtCh: read_data(dir, "eqptExtCh_with_unsupported_bad_dn.json"),
                eqptSupC: read_data(dir, "eqptSupC_with_unsupported_bad_dn.json"),
            },
            "6.1(1f)",
            read_data(dir, "fabricNode_supported_only.json"),
            script.FAIL_UF,
            [
                ["6.1(1f)", "-", "N9K-M6PQ-E", "Expansion Module", "Not supported on 5.x+"],
                ["6.1(1f)", "-", "N2K-C2232PP-10GE", "FEX", "Deprecated from 6.1(1)+"],
                ["6.1(1f)", "-", "N9K-SUP-B", "Supervisor", "Deprecated from 6.1(1)+"],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, fabric_nodes, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        fabric_nodes=fabric_nodes,
    )

    assert result.result == expected_result
    assert result.data == expected_data
