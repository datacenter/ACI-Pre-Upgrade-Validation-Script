import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
exportcryptkey = "uni/exportcryptkey.json"


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # AES enabled (tversion > 6.1.2a)
        (
            {exportcryptkey: read_data(dir, "exportcryptkey.json")},
            "6.1(3b)",
            script.PASS,
        ),
        # AES enabled (tversion < 6.1.2a)
        (
            {exportcryptkey: read_data(dir, "exportcryptkey.json")},
            "5.2(8g)",
            script.PASS,
        ),
        # AES disabled (tversion > 6.1.2a)
        (
            {exportcryptkey: read_data(dir, "exportcryptkey_disabled.json")},
            "6.1(3b)",
            script.FAIL_UF,
        ),
        # AES disabled (tversion < 6.1.2a)
        (
            {exportcryptkey: read_data(dir, "exportcryptkey_disabled.json")},
            "5.2(8g)",
            script.MANUAL,
        ),
        # AES MO not found (tversion > 6.1.2a)
        (
            {exportcryptkey: []},
            "6.1(3b)",
            script.FAIL_UF,
        ),
        # AES MO not found (tversion < 6.1.2a)
        (
            {exportcryptkey: []},
            "5.2(8g)",
            script.MANUAL,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.aes_encryption_check(1, 1, script.AciVersion(tversion))
    assert result == expected_result
