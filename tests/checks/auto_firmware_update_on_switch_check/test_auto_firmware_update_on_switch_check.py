import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "auto_firmware_update_on_switch_check"

# icurl queries
auto_firmware_update_api = "uni/fabric/fwrepop.json"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result, expected_data",
    [
        # MANUAL cases
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            None,
            None,
            script.MANUAL,
            [],
        ),
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "5.2(7a)",
            None,
            script.MANUAL,
            [],
        ),
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            None,
            "6.0(3d)",
            script.MANUAL,
            [],
        ),
        # NA cases
        # firmwareRepoP   cversion  < 5.2(7) , tversion < 6.0(3) Result NA
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "5.2(7a)",
            "6.0(2d)",
            script.NA,
            [],
        ),
        # firmwareRepoP   5.2(7) < cversion < 6.0(1) , tversion < 6.0(3) Result NA
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "5.3(2a)",
            "6.0(2d)",
            script.NA,
            [],
        ),
        # firmwareRepoP   5.2(7) < cversion < 6.0(1) , tversion > 6.0(3) Result NA
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "5.3(2a)",
            "6.0(9d)",
            script.NA,
            [],
        ),
        # firmwareRepoP   cversion  > 6.0(3) , tversion > 6.0(3) Result NA
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "6.0(3d)",
            "6.0(9d)",
            script.NA,
            [],
        ),
        # Failure cases
        # firmwareRepoP   cversion  < 5.2(7) , tversion > 6.0(3) Result MANUAL
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "5.2(7a)",
            "6.0(3d)",
            script.MANUAL,
            [["Enabled", "n9000-16.0(9d)", "6.0(3d)"]],
        ),
        # firmwareRepoP  cversion is 6.0(1) or 6.0(2) , tversion > 6.0(3) Result MANUAL
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-pos.json")},
            "6.0(2a)",
            "6.0(3d)",
            script.MANUAL,
            [["Enabled", "n9000-16.0(9d)", "6.0(3d)"]],
        ),
        # Pass cases
        # no firmwareRepoP   cversion is < 5.2(7) , tversion > 6.0(3) Result PASS
        (
            {auto_firmware_update_api: []},
            "5.2(7a)",
            "6.0(3d)",
            script.PASS,
            [],
        ),
        # no firmwareRepoP   cversion is 6.0(1) or 6.0(2) , tversion > 6.0(3) Result PASS
        (
            {auto_firmware_update_api: []},
            "6.0(2a)",
            "6.0(3d)",
            script.PASS,
            [],
        ),
        # no firmwareRepoP   cversion is < 5.2(7) , tversion > 6.0(3) Result PASS
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-neg.json")},
            "5.2(7a)",
            "6.0(3d)",
            script.PASS,
            [],
        ),
        # no firmwareRepoP   cversion is 6.0(1) or 6.0(2) , tversion > 6.0(3) Result PASS
        (
            {auto_firmware_update_api: read_data(dir, "firmwareRepoP-neg.json")},
            "6.0(2a)",
            "6.0(3d)",
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result, expected_data):

    result = run_check(
        cversion=script.AciVersion(cversion) if cversion else None,
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data
