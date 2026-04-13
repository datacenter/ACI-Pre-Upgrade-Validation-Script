import os
import pytest
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

dir = os.path.dirname(os.path.abspath(__file__))

test_function = "wred_affected_model_check"

# icurl queries
qosCong_api = "qosCong.json"
eqptLC_api = "eqptLC.json"
eqptFC_api = "eqptFC.json"


@pytest.mark.parametrize(
    "tversion, fabric_nodes, icurl_outputs, expected_result, expected_data",
    [
        # Case 1: No target version provided (-t flag missing).
        # Check cannot determine version gate. Expected: MANUAL CHECK REQUIRED.
        (
            None,
            read_data(dir, "fabricNode_leaf_affected.json"),
            {},
            script.MANUAL,
            [],
        ),
        # Case 2: Target version 6.2(2a) is the first fixed release and not in the affected range.
        # Version gate fails. Expected: NA without any API calls.
        (
            "6.2(2a)",
            read_data(dir, "fabricNode_leaf_affected.json"),
            {},
            script.NA,
            [],
        ),
        # Case 3: All 3 gates triggered via an affected leaf node.
        # Version 6.1(5e) is in affected range, WRED is enabled, leaf model N9K-C9236C is affected.
        # Expected: FAIL_O with node 101 reported under Source=Leaf.
        (
            "6.1(5e)",
            read_data(dir, "fabricNode_leaf_affected.json"),
            {
                qosCong_api: read_data(dir, "qosCong_wred.json"),
                eqptLC_api: read_data(dir, "eqptLC_empty.json"),
                eqptFC_api: read_data(dir, "eqptFC_empty.json"),
            },
            script.FAIL_O,
            [["101", "leaf101", "Leaf", "N9K-C9236C"]],
        ),
        # Case 4: All 3 gates triggered via affected LC and FM on a spine node.
        # Version 6.2(1f) is in affected range. Spine itself is not an affected leaf model,
        # but it has an affected Line Card (N9K-C92304QC) and Fabric Module (N9K-C9508-FM-E).
        # Multiple QoS policies exist (one tail-drop, one wred) - WRED gate still triggers.
        # Expected: FAIL_O with both FM and LC rows reported for node 1001.
        (
            "6.2(1f)",
            read_data(dir, "fabricNode_spine.json"),
            {
                qosCong_api: read_data(dir, "qosCong_mixed.json"),
                eqptLC_api: read_data(dir, "eqptLC_affected.json"),
                eqptFC_api: read_data(dir, "eqptFC_affected.json"),
            },
            script.FAIL_O,
            [
                ["1001", "spine1001", "FM", "N9K-C9508-FM-E"],
                ["1001", "spine1001", "LC", "N9K-C92304QC"],
            ],
        ),
        # Case 5: Version is affected and leaf model is affected, but WRED is not enabled (tail-drop).
        # WRED gate fails. Expected: PASS - confirms all 3 gates must be true simultaneously.
        (
            "6.1(5e)",
            read_data(dir, "fabricNode_leaf_affected.json"),
            {
                qosCong_api: read_data(dir, "qosCong_tail_drop.json"),
                eqptLC_api: read_data(dir, "eqptLC_empty.json"),
                eqptFC_api: read_data(dir, "eqptFC_empty.json"),
            },
            script.PASS,
            [],
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
