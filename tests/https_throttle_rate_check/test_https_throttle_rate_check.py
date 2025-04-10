import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
commHttps = "commHttps.json"


@pytest.mark.parametrize(
    "icurl_outputs, cver, tver, expected_result",
    [
        # Target version missing
        (
            {commHttps: read_data(dir, "commHttps_neg1.json")},
            "4.2(7f)",
            None,
            script.MANUAL,
        ),
        # Version not affected. cversion newer than 6.1(2a). Upgrade
        (
            {commHttps: read_data(dir, "commHttps_neg1.json")},
            "6.1(2g)",
            "6.1(3a)",
            script.NA,
        ),
        # Version not affected. cversion newer than 6.1(2a). Downgrade
        (
            {commHttps: read_data(dir, "commHttps_neg1.json")},
            "6.1(2g)",
            "5.2(8g)",
            script.NA,
        ),
        # Version not affected. Both cversion and tversion older than 6.1(2).
        (
            {commHttps: read_data(dir, "commHttps_neg1.json")},
            "4.2(7f)",
            "5.2(8g)",
            script.PASS,
        ),
        # Throttle rates are lower than the threshold
        (
            {commHttps: read_data(dir, "commHttps_neg1.json")},
            "4.2(7f)",
            "6.1(2g)",
            script.PASS,
        ),
        # Throttle rates are higher than the threshold but throttling is disabled.
        (
            {commHttps: read_data(dir, "commHttps_neg2.json")},
            "4.2(7f)",
            "6.1(2g)",
            script.PASS,
        ),
        # Throttle rates are higher than the threshold but throttling is enabled.
        (
            {commHttps: read_data(dir, "commHttps_pos.json")},
            "4.2(7f)",
            "6.1(2g)",
            script.FAIL_UF,
        ),
        # Throttle rates are higher than the threshold but throttling is enabled.
        (
            {commHttps: read_data(dir, "commHttps_pos.json")},
            "4.2(7f)",
            "6.0(2a)",
            script.MANUAL,
        ),
    ],
)
def test_logic(mock_icurl, cver, tver, expected_result):
    cversion = script.AciVersion(cver)
    tversion = script.AciVersion(tver) if tver else None
    result = script.https_throttle_rate_check(1, 1, cversion, tversion)
    assert result == expected_result
