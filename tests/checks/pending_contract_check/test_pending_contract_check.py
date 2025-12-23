import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "pending_contract_check"

# icurl queries
pending_contract_api = 'fvPndgCtrct.json'
pending_contract_api += '?rsp-subtree-include=count'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # NO TVERSION PROVIDED - MANUAL CHECK
        (
            {pending_contract_api: read_data(dir, "fvPndgCtrct_count_zero.json")},
            None,
            script.MANUAL,
        ),
        # TVERSION > 6.1(3g) and no pending contracts - NA
        (
            {pending_contract_api: read_data(dir, "fvPndgCtrct_count_zero.json")},
            "6.1(5a)",
            script.NA,
        ),
        # TVERSION > 6.1(3g) and pending contracts exist - NA 
        (
            {pending_contract_api: read_data(dir, "fvPndgCtrct_count_not_zero.json")},
            "6.1(5a)",
            script.NA,
        ),
        # TVERSION < 6.1(3g) and no pending contracts - PASS
        (
            {pending_contract_api: read_data(dir, "fvPndgCtrct_count_zero.json")},
            "5.2(1a)",
            script.PASS,
        ),
        # TVERSION < 6.1(3g) and pending contracts exist - FAIL_O
        (
            {pending_contract_api: read_data(dir, "fvPndgCtrct_count_not_zero.json")},
            "5.2(1a)",
            script.FAIL_O,
        ),
       
    ],
)
def test_logic(run_check, mock_icurl, icurl_outputs, tversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result