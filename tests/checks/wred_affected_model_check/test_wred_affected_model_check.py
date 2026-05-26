import os
import pytest
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

dir = os.path.dirname(os.path.abspath(__file__))

test_function = "wred_affected_model_check"

# icurl queries
qosCong_api = "qosCong.json"
eqptFC_api = "eqptFC.json"


@pytest.mark.parametrize(
    "tversion, fabric_nodes, icurl_outputs, expected_result, expected_data",
    [
        # Case 1: Target version not supplied. Expected: MANUAL.
        (
            None,
            read_data(dir, "fabricNode_spine.json"),
            {},
            script.MANUAL,
            [],
        ),
        # Case 2: Target version 6.2(2a) is the first fixed release and not in the affected range.
        # Version gate fails. Expected: NA without any API calls.
        (
            "6.2(2a)",
            read_data(dir, "fabricNode_spine.json"),
            {},
            script.NA,
            [],
        ),
        # Case 2: All 3 gates triggered via an affected FM on a spine node.
        # Version 6.2(1g) is in affected range, WRED is enabled, FM model N9K-C9508-FM-E is affected.
        # Expected: FAIL_O with node 1001 reported under Source=FM.
        (
            "6.2(1g)",
            read_data(dir, "fabricNode_spine.json"),
            {
                qosCong_api: read_data(dir, "qosCong_wred.json"),
                eqptFC_api: read_data(dir, "eqptFC_affected.json"),
            },
            script.FAIL_O,
            [["1001", "spine1001", "FM", "N9K-C9508-FM-E"]],
        ),
        # Case 3: Version is affected but no affected FM hardware found.
        # WRED is enabled so the script proceeds to the FM check, which finds nothing.
        # Hardware gate fails. Expected: NA - issue is model-specific.
        (
            "6.1(5e)",
            read_data(dir, "fabricNode_spine.json"),
            {
                qosCong_api: read_data(dir, "qosCong_wred.json"),
                eqptFC_api: read_data(dir, "eqptFC_empty.json"),
            },
            script.NA,
            [],
        ),
        # Case 4: Version is affected and FM is affected, but WRED is not enabled (tail-drop).
        # WRED gate fails. Expected: PASS - confirms all 3 gates must be true simultaneously.
        (
            "6.1(5e)",
            read_data(dir, "fabricNode_spine.json"),
            {
                qosCong_api: read_data(dir, "qosCong_tail_drop.json"),
                eqptFC_api: read_data(dir, "eqptFC_affected.json"),
            },
            script.PASS,
            [],
        ),
        # Case 5: Multiple FM objects - one affected (N9K-C9508-FM-E), one unaffected (N9K-C9504-FM-G).
        # WRED is enabled. Only the affected FM should be reported.
        # Expected: FAIL_O with only the affected FM row reported.
        (
            "6.1(5e)",
            read_data(dir, "fabricNode_spine.json"),
            {
                qosCong_api: read_data(dir, "qosCong_wred.json"),
                eqptFC_api: read_data(dir, "eqptFC_mixed.json"),
            },
            script.FAIL_O,
            [["1001", "spine1001", "FM", "N9K-C9508-FM-E"]],
        ),
        # Case 6: Version is affected, WRED is enabled, but no affected FM models found.
        # FM gate fails. Expected: NA.
        (
            "6.2(1g)",
            read_data(dir, "fabricNode_spine.json"),
            {
                qosCong_api: read_data(dir, "qosCong_wred.json"),
                eqptFC_api: read_data(dir, "eqptFC_empty.json"),
            },
            script.NA,
            [],
        ),
        # Case 7: Same node has two FM slots with the same affected model (duplicate eqptFC objects).
        # Deduplication by (node_id, model) must result in only one row.
        # Expected: FAIL_O with a single row for node 1001.
        (
            "6.2(1g)",
            read_data(dir, "fabricNode_spine.json"),
            {
                qosCong_api: read_data(dir, "qosCong_wred.json"),
                eqptFC_api: read_data(dir, "eqptFC_duplicate.json"),
            },
            script.FAIL_O,
            [["1001", "spine1001", "FM", "N9K-C9508-FM-E"]],
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
