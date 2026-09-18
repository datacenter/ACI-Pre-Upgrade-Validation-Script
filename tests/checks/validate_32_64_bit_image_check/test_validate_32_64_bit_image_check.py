import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "validate_32_64_bit_image_check"

# icurl queries
firmware_60_api = "firmwareFirmware.json"
firmware_60_api += '?query-target-filter=eq(firmwareFirmware.fullVersion,"n9000-16.0(3e)")'

# icurl queries
firmware_52_api = "firmwareFirmware.json"
firmware_52_api += '?query-target-filter=eq(firmwareFirmware.fullVersion,"n9000-15.2(7d)")'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # NO TVERSION - MANUAL
        (
            {firmware_60_api: read_data(dir, "firmwareFirmware_pos.json")},
            "5.2(1a)",
            None,
            script.MANUAL,
        ),
        # APIC not yet upgraded to 6.0(2)+ - POST
        (
            {firmware_60_api: read_data(dir, "firmwareFirmware_pos.json")},
            "5.2(1a)",
            "6.0(3e)",
            script.POST,
        ),
        # FAILING = AFFECTED VERSION + ONLY 64 BIT Image
        (
            {firmware_60_api: read_data(dir, "firmwareFirmware_pos.json")},
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_UF,
        ),
        # FAILING = AFFECTED VERSION + Images were uploaded before upgrade
        (
            {firmware_60_api: read_data(dir, "firmwareFirmware_pos2.json")},
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_UF,
        ),
        # FAILING = AFFECTED VERSION + 32-bit image shows NA
        (
            {firmware_60_api: read_data(dir, "firmwareFirmware_pos3.json")},
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_UF,
        ),
        # FAILING = AFFECTED VERSION + 64-bit image shows NA
        (
            {firmware_60_api: read_data(dir, "firmwareFirmware_pos4.json")},
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_UF,
        ),
        # FAILING = AFFECTED VERSION + AFFECTED MO NON EXISTING
        (
            {firmware_60_api: read_data(dir, "firmwareFirmware_empty.json")},
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_UF,
        ),
        # PASSING = AFFECTED VERSION + NON-AFFECTED MO
        (
            {firmware_60_api: read_data(dir, "firmwareFirmware_neg.json")},
            "6.0(3e)",
            "6.0(3e)",
            script.PASS,
        ),
        # PASSING = NON-AFFECTED VERSION + AFFECTED MO
        (
            {firmware_52_api: read_data(dir, "firmwareFirmware_empty.json")},
            "5.2(1a)",
            "5.2(7d)",
            script.NA,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None
    )
    assert result.result == expected_result
