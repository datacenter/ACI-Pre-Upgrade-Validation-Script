import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "switch_micron_ssd_firmware_check"

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

# icurl queries
eqptFlash = 'eqptFlash.json?query-target-filter=or(wcard(eqptFlash.model,"Micron_5300*"),wcard(eqptFlash.model,"Micron_5100*"),wcard(eqptFlash.model,"Micron_5400*"))'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result, expected_data",
    [
        # PASS - No Micron SSDs found
        (
            {eqptFlash: []},
            "6.0(1a)",
            script.PASS,
            [],
        ),
        # PASS - All Micron SSDs have current firmware
        (
            {eqptFlash: read_data(dir, "eqptFlash_pass.json")},
            "6.0(1a)",
            script.PASS,
            [],
        ),
        # FAIL_O - M5100 with outdated firmware
        (
            {eqptFlash: read_data(dir, "eqptFlash_m5100_outdated.json")},
            "6.0(1a)",
            script.FAIL_O,
            [
                ["101", "Micron_5100_MTFDDAK256TBN", "D0MU070"],
            ],
        ),
        # FAIL_O - M5300 D3CN with outdated firmware
        (
            {eqptFlash: read_data(dir, "eqptFlash_m5300_d3cn_outdated.json")},
            "6.0(1a)",
            script.FAIL_O,
            [
                ["102", "Micron_5300_MTFDDAK480TDS", "D3CN001"],
            ],
        ),
        # FAIL_O - M5300 D3MU with outdated firmware
        (
            {eqptFlash: read_data(dir, "eqptFlash_m5300_d3mu_outdated.json")},
            "6.0(1a)",
            script.FAIL_O,
            [
                ["103", "Micron_5300_MTFDDAK960TDS", "D3MU003"],
            ],
        ),
        # FAIL_O - M5400 with outdated firmware
        (
            {eqptFlash: read_data(dir, "eqptFlash_m5400_outdated.json")},
            "6.0(1a)",
            script.FAIL_O,
            [
                ["104", "Micron_5400_MTFDDAK1T9TGP", "D4CN003"],
            ],
        ),
        # FAIL_O - Multiple SSDs with outdated firmware
        (
            {eqptFlash: read_data(dir, "eqptFlash_multiple_outdated.json")},
            "6.0(1a)",
            script.FAIL_O,
            [
                ["101", "Micron_5100_MTFDDAK256TBN", "D0MU070"],
                ["102", "Micron_5300_MTFDDAK480TDS", "D3CN001"],
                ["104", "Micron_5400_MTFDDAK1T9TGP", "D4CN003"],
            ],
        ),
        # NA - Target version is 6.1(5e) or newer
        (
            {eqptFlash: read_data(dir, "eqptFlash_m5100_outdated.json")},
            "6.1(5e)",
            script.NA,
            [],
        ),
        # NA - Target version is newer than 6.1(5e)
        (
            {eqptFlash: read_data(dir, "eqptFlash_m5100_outdated.json")},
            "6.2(1a)",
            script.NA,
            [],
        ),
        # MANUAL - No target version provided
        (
            {eqptFlash: read_data(dir, "eqptFlash_m5100_outdated.json")},
            None,
            script.MANUAL,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data
