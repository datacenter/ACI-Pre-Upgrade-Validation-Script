import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "n9k_c93108tc_fx3p_interface_down_check"


@pytest.mark.parametrize(
    "tversion, fabric_nodes, expected_result, expected_data",
    [
        # Version not supplied
        (None, read_data(dir, "fabricNode_FX3P3H.json"), script.MANUAL, []),
        # Version not affected
        ("5.2(8h)", read_data(dir, "fabricNode_FX3P3H.json"), script.PASS, []),
        ("5.3(2b)", read_data(dir, "fabricNode_FX3P3H.json"), script.PASS, []),
        ("6.0(4c)", read_data(dir, "fabricNode_FX3P3H.json"), script.PASS, []),
        # Affected version, no FX3P or FX3H
        ("5.2(8g)", read_data(dir, "fabricNode_no_FX3P3H.json"), script.PASS, []),
        ("5.3(1d)", read_data(dir, "fabricNode_no_FX3P3H.json"), script.PASS, []),
        ("6.0(2h)", read_data(dir, "fabricNode_no_FX3P3H.json"), script.PASS, []),
        # Affected version, FX3P
        (
            "5.2(8g)",
            read_data(dir, "fabricNode_FX3P.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3P"], ["114", "leaf114", "N9K-C93108TC-FX3P"]],
        ),
        (
            "5.3(1d)",
            read_data(dir, "fabricNode_FX3P.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3P"], ["114", "leaf114", "N9K-C93108TC-FX3P"]],
        ),
        (
            "6.0(2h)",
            read_data(dir, "fabricNode_FX3P.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3P"], ["114", "leaf114", "N9K-C93108TC-FX3P"]],
        ),
        # Affected version, FX3H
        (
            "5.2(8g)",
            read_data(dir, "fabricNode_FX3H.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3H"], ["114", "leaf114", "N9K-C93108TC-FX3H"]],
        ),
        (
            "5.3(1d)",
            read_data(dir, "fabricNode_FX3H.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3H"], ["114", "leaf114", "N9K-C93108TC-FX3H"]],
        ),
        (
            "6.0(2h)",
            read_data(dir, "fabricNode_FX3H.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3H"], ["114", "leaf114", "N9K-C93108TC-FX3H"]],
        ),
        # Affected version, FX3P and FX3H
        (
            "5.2(8g)",
            read_data(dir, "fabricNode_FX3P3H.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3P"], ["114", "leaf114", "N9K-C93108TC-FX3H"]],
        ),
        (
            "5.3(1d)",
            read_data(dir, "fabricNode_FX3P3H.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3P"], ["114", "leaf114", "N9K-C93108TC-FX3H"]],
        ),
        (
            "6.0(2h)",
            read_data(dir, "fabricNode_FX3P3H.json"),
            script.FAIL_O,
            [["113", "leaf113", "N9K-C93108TC-FX3P"], ["114", "leaf114", "N9K-C93108TC-FX3H"]],
        ),
    ],
)
def test_logic(run_check, tversion, fabric_nodes, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
