import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

# icurl queries
isisDTEp_api = 'isisDTEp.json'
isisDTEp_api += '?query-target-filter=eq(isisDTEp.role,"spine")'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [

        # MANUAL cases
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_POS.json")},
            None,
            script.MANUAL,
        ),
        # Failure cases
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_POS.json")},
            "6.0(1f)",
            script.NA,
        ),

        # Failure cases
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_POS.json")},
            "6.1(1f)",
            script.FAIL_O,
        ),
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_POS.json")},
            "6.1(2f)",
            script.FAIL_O,
        ),
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_POS.json")},
            "6.1(2g)",
            script.FAIL_O,
        ),
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_POS.json")},
            "6.1(3f)",
            script.FAIL_O,
        ),

        # Pass cases
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_NEG.json")},
            "6.1(1f)",
            script.PASS,
        ),
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_NEG.json")},
            "6.1(2f)",
            script.PASS,
        ),
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_NEG.json")},
            "6.1(2g)",
            script.PASS,
        ),
        (
            {isisDTEp_api: read_data(dir, "isisDTEp_NEG.json")},
            "6.1(3f)",
            script.PASS,
        )
    ]
)
def test_logic(mock_icurl, tversion, expected_result):
    tversion = script.AciVersion(tversion) if tversion else None
    result = script.isis_database_byte_check(1, 1, tversion)
    assert result == expected_result
