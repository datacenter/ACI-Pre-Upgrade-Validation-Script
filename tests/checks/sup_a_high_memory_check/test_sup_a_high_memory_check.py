import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "sup_a_high_memory_check"

# icurl queries
eqptSupCs = "eqptSupC.json"


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # Version not affected
        (
            {eqptSupCs: read_data(dir, "eqptSupC_SUP_A_Aplus.json")},
            "5.3(2d)",
            script.PASS,
        ),
        # Version not affected
        (
            {eqptSupCs: read_data(dir, "eqptSupC_SUP_A_Aplus.json")},
            "6.0(6e)",
            script.PASS,
        ),
        # Affected version, no SUP-A nor SUP-A+
        (
            {eqptSupCs: read_data(dir, "eqptSupC_no_SUP_A_Aplus.json")},
            "6.0(3e)",
            script.PASS,
        ),
        # Affected version, both SUP-A and SUP-A+
        (
            {eqptSupCs: read_data(dir, "eqptSupC_SUP_A_Aplus.json")},
            "6.0(3e)",
            script.FAIL_O,
        ),
        # Affected version, SUP-A only
        (
            {eqptSupCs: read_data(dir, "eqptSupC_SUP_A.json")},
            "6.0(3e)",
            script.FAIL_O,
        ),
        # Affected version, SUP-A+ only
        (
            {eqptSupCs: read_data(dir, "eqptSupC_SUP_Aplus.json")},
            "6.0(3e)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion))
    assert result.result == expected_result
