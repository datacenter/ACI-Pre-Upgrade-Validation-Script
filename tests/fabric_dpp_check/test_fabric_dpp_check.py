import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
lbpPol =  'lbpPol.json'
lbpPol += '?query-target-filter=eq(lbpPol.pri,"on")'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # DPP is on
        (
            {lbpPol: read_data(dir, "lbpPol_POS.json")},
            "5.2(2h)",
            script.FAIL_O,
        ),
        (
            {lbpPol: read_data(dir, "lbpPol_POS.json")},
            "5.2(8e)",
            script.PASS,
        ),
        (
            {lbpPol: read_data(dir, "lbpPol_POS.json")},
            "6.0(2h)",
            script.FAIL_O,
        ),
        (
            {lbpPol: read_data(dir, "lbpPol_POS.json")},
            "6.0(3d)",
            script.PASS,
        ),
        # DPP is off
        (
            {lbpPol: read_data(dir, "lbpPol_NEG.json")},
            "5.0(2h)",
            script.PASS,
        ),
        (
            {lbpPol: read_data(dir, "lbpPol_NEG.json")},
            "5.2(8e)",
            script.PASS,
        ),
        (
            {lbpPol: read_data(dir, "lbpPol_NEG.json")},
            "6.0(2h)",
            script.PASS,
        ),
        (
            {lbpPol: read_data(dir, "lbpPol_NEG.json")},
            "6.0(3d)",
            script.PASS,
        ),

    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.fabric_dpp_check(
        1, 1, script.AciVersion(tversion)
    )
    assert result == expected_result
