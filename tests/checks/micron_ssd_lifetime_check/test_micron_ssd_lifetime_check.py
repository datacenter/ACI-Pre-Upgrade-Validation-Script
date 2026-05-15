import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "micron_ssd_lifetime_check"

# API query
eqptflash_micron = 'eqptFlash.json?query-target-filter=eq(eqptFlash.vendor,"Micron")'

# Test data loaded from JSON files
no_micron_drives     = read_data(dir, "eqptFlash_no_micron.json")
micron_drives_single = read_data(dir, "eqptFlash_single_micron.json")
micron_drives_multi  = read_data(dir, "eqptFlash_multi_micron.json")


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result, expected_data",
    [
        # Test 0: MANUAL - tversion missing
        ({}, None, script.MANUAL, []),
        # Test 1: NA - tversion not affected (older)
        ({}, "6.0(2h)", script.NA, []),
        # Test 2: NA - tversion not affected (newer)
        ({}, "6.2(2a)", script.NA, []),
        # Test 3: PASS - affected version 6.1(5e) but no Micron drives
        (
            {eqptflash_micron: no_micron_drives},
            "6.1(5e)",
            script.PASS,
            [],
        ),
        # Test 4: PASS - affected version 6.2(1g) but no Micron drives
        (
            {eqptflash_micron: no_micron_drives},
            "6.2(1g)",
            script.PASS,
            [],
        ),
        # Test 5: FAIL_O - affected version 6.1(5e) with single Micron drive
        (
            {eqptflash_micron: micron_drives_single},
            "6.1(5e)",
            script.FAIL_O,
            [["1", "101", "MTFDDAK240MBB"]],
        ),
        # Test 6: FAIL_O - affected version 6.2(1g) with single Micron drive
        (
            {eqptflash_micron: micron_drives_single},
            "6.2(1g)",
            script.FAIL_O,
            [["1", "101", "MTFDDAK240MBB"]],
        ),
        # Test 7: FAIL_O - multiple Micron drives across pods and nodes
        (
            {eqptflash_micron: micron_drives_multi},
            "6.1(5e)",
            script.FAIL_O,
            [
                ["1", "101", "MTFDDAK240MBB"],
                ["2", "201", "MTFDDAK480MBB"],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        username="fake_username",
        password="fake_password",
    )
    assert result.result == expected_result
    assert result.data == expected_data