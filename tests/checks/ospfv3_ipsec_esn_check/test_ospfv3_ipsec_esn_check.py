import os
import pytest
import logging
import importlib
from helpers.utils import read_data

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "ospfv3_ipsec_esn_check"

esp_config_api = 'fvProtoAuthPol.json?query-target-filter=and(wcard(fvProtoAuthPol.proto,"esp"))'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # PASS cases
        # Targer version in affected range, IPSec ESP not enabled
        (
            {esp_config_api: read_data(dir, "esp_not_enabled.json")},
            "6.1(3f)",
            script.PASS,
        ),
        # Target version in lower affected version, IPSec ESP not enabled
        (
            {esp_config_api: read_data(dir, "esp_not_enabled.json")},
            "6.1(1f)",
            script.PASS,
        ),
        # Target version in upper affected version, IPSec ESP not enabled
        (
            {esp_config_api: read_data(dir, "esp_not_enabled.json")},
            "6.1(4h)",
            script.PASS,
        ),
        # Not Applicable cases
        # Target version below affected range
        (
            {esp_config_api: read_data(dir, "esp_enabled.json")},
            "6.0(9e)",
            script.NA,
        ),
        # Target version above affected range
        (
            {esp_config_api: read_data(dir, "esp_enabled.json")},
            "6.2(2f)",
            script.NA,
        ),
        # Manual cases
        # Target version not provided
        (
            {esp_config_api: read_data(dir, "esp_enabled.json")},
            "",
            script.MANUAL,
        ),
        # Fail cases
        # Target version in affected range, IPSec ESP enabled
        (
            {esp_config_api: read_data(dir, "esp_enabled.json")},
            "6.1(3f)",
            script.FAIL_O,
        ),
        # Target version in lower affected version, IPSec ESP enabled
        (
            {esp_config_api: read_data(dir, "esp_enabled.json")},
            "6.1(1f)",
            script.FAIL_O,
        ),
        # Target version in upper affected version, IPSec ESP enabled
        (
            {esp_config_api: read_data(dir, "esp_enabled.json")},
            "6.1(4h)",
            script.FAIL_O,
        ),
    ],
    ids = [
        "PASS - Target version in affected range, IPSec ESP not enabled",
        "PASS - Target version in lower affected version, IPSec ESP not enabled",
        "PASS - Target version in upper affected version, IPSec ESP not enabled",
        "NA - Target version below affected range",
        "NA - Target version above affected range",
        "MANUAL - Target version not provided",
        "FAIL - Target version in affected range, IPSec ESP enabled",
        "FAIL - Target version in lower affected version, IPSec ESP enabled",
        "FAIL - Target version in upper affected version, IPSec ESP enabled",
    ]
)
def test_ospfv3_ipsec_esn_check(run_check, mock_icurl, tversion, expected_result):
    """Test OSPFv3 IPsec ESN Check"""
    result = run_check(tversion = script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result