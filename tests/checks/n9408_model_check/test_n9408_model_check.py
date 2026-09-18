import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "n9408_model_check"

# icurl queries

eqptCh_api = 'eqptCh.json'
eqptCh_api += '?query-target-filter=eq(eqptCh.model,"N9K-C9400-SW-GX2A")'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # FABRIC HAS GX2A NODE and going to affected tversion
        (
            {eqptCh_api: read_data(dir, "eqptCh_POS.json")},
            "6.1(3b)",
            script.FAIL_O,
        ),
        # FABRIC HAS GX2A NODE and going to NOT-affected tversion
        (
            {eqptCh_api: read_data(dir, "eqptCh_POS.json")},
            "6.0(7e)",
            script.PASS,
        ),
        # TVERSION NOT AFFECTED
        (
            {eqptCh_api: read_data(dir, "eqptCh_NEG.json")},
            "6.1(3b)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion))
    assert result.result == expected_result
