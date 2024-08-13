import os
import pytest
import logging
import importlib
from helpers.utils import read_data
script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
eqptPortP = 'eqptPortP.json?query-target-filter=eq(eqptPortP.ctrl,"uplink")'


@pytest.mark.parametrize(
    "icurl_outputs, cver, tver, expected_result",
    [
        (
            {
                eqptPortP: read_data(dir, "eqptPortP_POS.json")
            },
            "5.2(3g)",
            "6.0(2h)",
            script.FAIL_O,
        ),
        (
            {
                eqptPortP: read_data(dir, "eqptPortP_empty.json")
            },
            "5.2(3g)",
            "6.0(2h)",
            script.PASS,
        ),
        (
            {
                eqptPortP: read_data(dir, "eqptPortP_POS.json")
            },
            "5.2(3g)",
            "5.2(7a)",
            script.PASS,
        ),
        (
            {
                eqptPortP: read_data(dir, "eqptPortP_NEG.json")
            },
            "5.2(3g)",
            "6.0(2h)",
            script.PASS,
        )
    ],
)
def test_logic(mock_icurl, cver, tver, expected_result):
    result = script.uplink_limit_check(
        1, 1, script.AciVersion(cver), script.AciVersion(tver)
    )
    assert result == expected_result
