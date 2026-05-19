import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "false_micron_ssd_failure_fault_check"

# API query
eqptflash_micron = 'eqptFlash.json?query-target-filter=eq(eqptFlash.vendor,"Micron")'

# Test data loaded from JSON files
no_micron_drives     = read_data(dir, "eqptFlash_no_micron.json")
micron_drives_single = read_data(dir, "eqptFlash_single_micron.json")
micron_drives_multi  = read_data(dir, "eqptFlash_multi_micron.json")


@pytest.mark.parametrize(
    "icurl_outputs, tversion, cversion, expected_result, expected_data",
    [
        # Test 0: MANUAL - tversion missing
        ({}, None, "6.0(2h)", script.MANUAL, []),
        # Test 1: NA - tversion not affected (older), cversion not affected
        ({}, "6.0(2h)", "6.0(1a)", script.NA, []),
        # Test 2: NA - tversion not affected (newer), cversion not affected
        ({}, "6.2(2a)", "6.0(2h)", script.NA, []),
        # Test 3: PASS - tversion affected 6.1(5e), cversion not affected, no Micron drives
        (
            {eqptflash_micron: no_micron_drives},
            "6.1(5e)", "6.0(2h)",
            script.PASS,
            [],
        ),
        # Test 4: PASS - tversion affected 6.2(1g), cversion not affected, no Micron drives
        (
            {eqptflash_micron: no_micron_drives},
            "6.2(1g)", "6.0(2h)",
            script.PASS,
            [],
        ),
        # Test 5: PASS - tversion not affected, cversion affected 6.1(5e), no Micron drives
        (
            {eqptflash_micron: no_micron_drives},
            "6.2(2a)", "6.1(5e)",
            script.PASS,
            [],
        ),
        # Test 6: PASS - tversion not affected, cversion affected 6.2(1g), no Micron drives
        (
            {eqptflash_micron: no_micron_drives},
            "6.2(2a)", "6.2(1g)",
            script.PASS,
            [],
        ),
        # Test 7: FAIL_O - tversion affected 6.1(5e), cversion not affected, single Micron drive
        (
            {eqptflash_micron: micron_drives_single},
            "6.1(5e)", "6.0(2h)",
            script.FAIL_O,
            [["1", "101", "MTFDDAK240MBB"]],
        ),
        # Test 8: FAIL_O - tversion affected 6.2(1g), cversion not affected, single Micron drive
        (
            {eqptflash_micron: micron_drives_single},
            "6.2(1g)", "6.0(2h)",
            script.FAIL_O,
            [["1", "101", "MTFDDAK240MBB"]],
        ),
        # Test 9: FAIL_O - tversion not affected, cversion affected 6.1(5e), single Micron drive
        (
            {eqptflash_micron: micron_drives_single},
            "6.2(2a)", "6.1(5e)",
            script.FAIL_O,
            [["1", "101", "MTFDDAK240MBB"]],
        ),
        # Test 10: FAIL_O - multiple Micron drives across pods and nodes
        (
            {eqptflash_micron: micron_drives_multi},
            "6.1(5e)", "6.0(2h)",
            script.FAIL_O,
            [
                ["1", "101", "MTFDDAK240MBB"],
                ["2", "201", "MTFDDAK480MBB"],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, cversion, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        cversion=script.AciVersion(cversion) if cversion else None,
        username="fake_username",
        password="fake_password",
    )
    assert result.result == expected_result
    assert result.data == expected_data