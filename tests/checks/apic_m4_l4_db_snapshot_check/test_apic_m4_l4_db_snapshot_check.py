import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_m4_l4_db_snapshot_check"


@pytest.mark.parametrize(
    "tversion, fabric_nodes, expected_result",
    [
        # Test 1: MANUAL - No target version
        (
            None,
            read_data(dir, "fabricNode_m4.json"),
            script.MANUAL,
        ),
        # Test 2: NA - Target version not affected (5.2 train)
        (
            "5.2(7f)",
            read_data(dir, "fabricNode_m4.json"),
            script.NA,
        ),
        # Test 3: NA - Target version not affected (4.2 train)
        (
            "4.2(7t)",
            read_data(dir, "fabricNode_m4.json"),
            script.NA,
        ),
        # Test 4: NA - Target version not affected (6.1 train)
        (
            "6.1(3a)",
            read_data(dir, "fabricNode_m4.json"),
            script.NA,
        ),
        # Test 5: NA - Target version 5.3(2f) or newer
        (
            "5.3(2f)",
            read_data(dir, "fabricNode_m4.json"),
            script.NA,
        ),
        # Test 6: NA - Target version 6.0(9c) or newer
        (
            "6.0(9c)",
            read_data(dir, "fabricNode_m4.json"),
            script.NA,
        ),
        # Test 7: FAIL_O - M4 model with affected 5.3 version
        (
            "5.3(2a)",
            read_data(dir, "fabricNode_m4.json"),
            script.FAIL_O,
        ),
        # Test 8: FAIL_O - M4 model with affected 6.0 version
        (
            "6.0(8a)",
            read_data(dir, "fabricNode_m4.json"),
            script.FAIL_O,
        ),
        # Test 9: FAIL_O - L4 model with affected 5.3 version
        (
            "5.3(1a)",
            read_data(dir, "fabricNode_l4.json"),
            script.FAIL_O,
        ),
        # Test 10: FAIL_O - L4 model with affected 6.0 version
        (
            "6.0(5a)",
            read_data(dir, "fabricNode_l4.json"),
            script.FAIL_O,
        ),
        # Test 11: PASS - L2 model (not affected) with affected version
        (
            "5.3(2a)",
            read_data(dir, "fabricNode_l2.json"),
            script.PASS,
        ),
        # Test 12: PASS - L2 model (not affected) with affected version
        (
            "6.0(8a)",
            read_data(dir, "fabricNode_l2.json"),
            script.PASS,
        ),
    ],
)
def test_logic(run_check, tversion, fabric_nodes, expected_result):
    if tversion:
        result = run_check(tversion=script.AciVersion(tversion), fabric_nodes=fabric_nodes)
    else:
        result = run_check(tversion=None, fabric_nodes=fabric_nodes)
    assert result.result == expected_result
