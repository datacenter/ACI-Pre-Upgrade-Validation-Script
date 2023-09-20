import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
lbpPol = "lbpPol.json"


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # DPP is on and affected version 6+
        (
            {lbpPol: read_data(dir, "lbpPol_NEG.json")},
            "6.0(2h)",
            script.FAIL_O,
        ),
        # DPP is off and affected version
        (
            {lbpPol: read_data(dir, "lbpPol_POS.json")},
            "6.0(2h)",
            script.PASS,
        ),
        # DPP is on and affected version 5+
        (
            {lbpPol: read_data(dir, "lbpPol_NEG.json")},
            "5.2(2h)",
            script.FAIL_O,
        ),
        # DPP is on and non affected version 5+
        (
            {lbpPol: read_data(dir, "lbpPol_NEG.json")},
            "5.2(8e)",
            script.PASS,
        ),
        # DPP is on and non affected version 6+
        (
            {lbpPol: read_data(dir, "lbpPol_NEG.json")},
            "6.0(3d)",
            script.PASS,
        ),
        # DPP is off and non affected version 5+
        (
            {lbpPol: read_data(dir, "lbpPol_POS.json")},
            "5.2(8e)",
            script.PASS,
        ),
        # DPP is off and non affected version 6+
        (
            {lbpPol: read_data(dir, "lbpPol_POS.json")},
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
