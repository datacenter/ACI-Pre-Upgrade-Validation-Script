import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "ave_eol_check"

# icurl queries
ave_api = 'vmmDomP.json'
ave_api += '?query-target-filter=eq(vmmDomP.enableAVE,"true")'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # FABRIC HAS AVE and going to affected tversion
        (
            {ave_api: read_data(dir, "vmmDomP_POS.json")},
            "6.1(3b)",
            script.FAIL_O,
        ),
        # FABRIC HAS AVE and going to NOT-affected tversion
        (
            {ave_api: read_data(dir, "vmmDomP_POS.json")},
            "5.2(7e)",
            script.NA,
        ),
        # NO AVE
        (
            {ave_api: []},
            "6.1(3b)",
            script.NA,
        ),
        # NO TVERSION
        (
            {ave_api: []},
            None,
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
