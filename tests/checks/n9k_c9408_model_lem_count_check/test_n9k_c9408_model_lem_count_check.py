import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "n9k_c9408_model_lem_count_check"

# icurl queries
eqptLC_api = 'eqptLC.json?query-target-filter=eq(eqptLC.model,"N9K-X9400-16W")'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, fabric_nodes, expected_result, expected_data, expected_msg",
    [
        # Version not affected (lower than 6.1(2f))
        (
            {eqptLC_api: read_data(dir, "eqptLC_empty.json")},
            "6.1(2e)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.NA,
            [],
            script.VER_NOT_AFFECTED,
        ),
        # Version not affected (higher than 6.2(1g))
        (
            {eqptLC_api: read_data(dir, "eqptLC_empty.json")},
            "6.2(1h)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.NA,
            [],
            script.VER_NOT_AFFECTED,
        ),
        # Applicable version but no N9K-C9408 nodes found
        (
            {eqptLC_api: read_data(dir, "eqptLC_6_node.json")},
            "6.1(2f)",
            read_data(dir, "fabricNode_no_n9k_c9408.json"),
            script.NA,
            [],
            "No N9K-C9408 nodes found. Skipping.",
        ),
        # Applicable version, C9408 exists, no LEM entries
        (
            {eqptLC_api: read_data(dir, "eqptLC_empty.json")},
            "6.1(2f)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.PASS,
            [],
            "",
        ),
        # Applicable version, C9408 exists, with <=5 LEMs -> PASS
        (
            {eqptLC_api: read_data(dir, "eqptLC_5_node.json")},
            "6.2(1g)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.PASS,
            [],
            "",
        ),
        # Applicable version with 6 LEMs -> FAIL_O
        (
            {eqptLC_api: read_data(dir, "eqptLC_6_node.json")},
            "6.2(1g)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.FAIL_O,
            [["101", "N9K-C9408", "N9K-X9400-16W", 6]],
            "",
        ),
        # Applicable mid-train version 6.1(5e), less than 6 LEMs on C9408 -> PASS
        (
            {eqptLC_api: read_data(dir, "eqptLC_5_node.json")},
            "6.1(5e)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.PASS,
            [],
            "",
        ),
        # Applicable mid-train version 6.1(5e), 6 LEMs on C9408 -> FAIL_O
        (
            {eqptLC_api: read_data(dir, "eqptLC_6_node.json")},
            "6.1(5e)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.FAIL_O,
            [["101", "N9K-C9408", "N9K-X9400-16W", 6]],
            "",
        ),
        # Version not affected (fixed after 6.1(5e))
        (
            {eqptLC_api: read_data(dir, "eqptLC_6_node.json")},
            "6.1(5f)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.NA,
            [],
            script.VER_NOT_AFFECTED,
        ),
        # Applicable version, 6 LEMs on C9408 -> FAIL_O
        (
            {eqptLC_api: read_data(dir, "eqptLC_6_node.json")},
            "6.1(2f)",
            read_data(dir, "fabricNode_n9k_c9408.json"),
            script.FAIL_O,
            [["101", "N9K-C9408", "N9K-X9400-16W", 6]],
            "",
        ),
        # Count only C9408 nodes and only matching LEM model
        (
            {eqptLC_api: read_data(dir, "eqptLC_mixed.json")},
            "6.1(3a)",
            read_data(dir, "fabricNode_mixed.json"),
            script.FAIL_O,
            [
                ["101", "N9K-C9408", "N9K-X9400-16W", 6],
                ["102", "N9K-C9408", "N9K-X9400-16W", 6],
            ],
            "",
        ),
    ],
)
def test_logic(run_check, mock_icurl, icurl_outputs, tversion, fabric_nodes, expected_result, expected_data, expected_msg):
    result = run_check(
        tversion=script.AciVersion(tversion),
        fabric_nodes=fabric_nodes,
    )

    assert result.result == expected_result
    assert result.data == expected_data
    assert result.msg == expected_msg

    if expected_result == script.FAIL_O:
        assert "boot loop" in result.recommended_action
