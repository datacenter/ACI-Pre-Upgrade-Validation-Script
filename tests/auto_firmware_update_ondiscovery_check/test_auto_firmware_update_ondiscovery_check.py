import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

# icurl queries
auto_firmware_update_api = 'firmwareRepoP.json'
auto_firmware_update_api += '?query-target-filter=eq(firmwareRepoP.enforceBootscriptVersionValidation,"true")'

@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [

        # MANUAL cases
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            None, None,
            script.MANUAL,
        ),
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "5.2(7a)", None,
            script.MANUAL,
        ),
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            None, "6.0(3d)",
            script.MANUAL,
        ),
        # NA cases
        # firmwareRepoP   cversion  < 5.2(7) , tversion < 6.0(3) Result NA
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "5.2(7a)", "6.0(2d)",
            script.NA,
        ),
        # firmwareRepoP   cversion  > 6.0(3) , tversion > 6.0(3) Result NA
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "6.0(3a)", "6.0(9d)",
            script.NA,
        ),
        # Failure cases
        # firmwareRepoP   cversion  < 5.2(7) , tversion > 6.0(3) Result FAIL_O
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "5.2(7a)", "6.0(3d)",
            script.FAIL_O,
        ),
        # firmwareRepoP  cversion is < 6.0(2) , tversion > 6.0(3) Result FAIL_O
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "6.0(2a)", "6.0(3d)",
            script.FAIL_O,
        ),
        # Pass cases
        # no firmwareRepoP   cversion is < 5.2(7) , tversion > 6.0(3) Result PASS
        (
            {auto_firmware_update_api: []},
            "5.2(7a)", "6.0(3d)",
            script.PASS,
        ),
        # no firmwareRepoP   cversion is < 6.0(2) , tversion > 6.0(3) Result PASS
        (
            {auto_firmware_update_api: []},
            "5.2(7a)", "6.0(3d)",
            script.PASS,
        ),
    ]
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    tversion = script.AciVersion(tversion) if tversion else None
    cversion = script.AciVersion(cversion) if cversion else None

    result = script.auto_firmware_update_ondiscovery_check(1, 1, cversion, tversion)
    assert result == expected_result