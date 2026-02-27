import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "standby_sup_sync_check"

# icurl queries
eqptSupC_api = "eqptSupC.json"
eqptSupC_api += '?query-target-filter=eq(eqptSupC.rdSt,"standby")'

"""
Bug cversion/tversion matrix based on image size

4.2(7t)+ - fixed versions LT 2 Gigs: 4.2(7t)+
5.2(5d)+ - fixed versions LT 2 Gigs: 5.2(7f)+
5.3(1d)+ - fixed versions LT 2 Gigs: 5.3(1d)+
6.0(1g)+ - fixed versions LT 2 Gigs: 6.0(1g), 6.0(1j). 32-bit only: 6.0(2h), 6.0(2j). 64-bit: NONE
6.1(1f)+ - fixed versions LT 2 Gigs: NONE
"""


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # NO TVERSION - MANUAL
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "5.2(1a)",
            None,
            script.MANUAL,
        ),
        # CVERSION 4.2
        # cversion 4.2 -nofix, tversion 4.2 -fix LT 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "4.2(7a)",
            "4.2(8d)",
            script.PASS,
        ),
        # cversion 4.2 -nofix, tversion 5.2 -fix but over 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "4.2(7a)",
            "5.2(5d)",
            script.FAIL_UF,
        ),
        # cversion 4.2 -nofix, tversion 5.2 -fix and LT 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "4.2(7a)",
            "5.2(7f)",
            script.PASS,
        ),
        # cversion 4.2 -nofix, tversion 5.3 -fix and LT 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "4.2(7a)",
            "5.3(1d)",
            script.PASS,
        ),
        # cversion 4.2 -nofix, tversion 6.0 -fix and LT 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "4.2(7a)",
            "6.0(8d)",
            script.FAIL_UF,
        ),
        # cversion 4.2 -nofix, tversion 6.1 -fix and LT 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "4.2(7a)",
            "6.1(1f)",
            script.FAIL_UF,
        ),
        # cversion 4.2 -fix, tversion 6.0 -fix but over 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "4.2(7t)",
            "6.0(6h)",
            script.PASS,
        ),
        # cversion 4.2 -fix, tversion 6.1 -fix but over 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "4.2(7t)",
            "6.1(1f)",
            script.PASS,
        ),
        # CVERSION 5.2
        # cversion 5.2 -nofix, tversion 5.2 -fix but over 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "5.2(4a)",
            "5.2(7a)",
            script.FAIL_UF,
        ),
        # cversion 5.2 -nofix, tversion 5.2 -fix LT 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "5.2(4a)",
            "5.2(7f)",
            script.PASS,
        ),
        # cversion 5.2 -nofix, tversion 5.3 -fix LT 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "5.2(4a)",
            "5.3(1d)",
            script.PASS,
        ),
        # cversion 5.2 -nofix, tversion 6.0 -fix but over 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "5.2(4a)",
            "6.0(8d)",
            script.FAIL_UF,
        ),
        # cversion 5.2 -nofix, tversion 6.1 -fix but over 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "5.2(4a)",
            "6.1(1f)",
            script.FAIL_UF,
        ),
        # cversion 5.2 -fix, tversion 6.1 -fix but over 2G
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_POS.json")},
            "5.2(5d)",
            "6.1(1f)",
            script.PASS,
        ),
        # NO STANDBY SUPS
        (
            {eqptSupC_api: read_data(dir, "eqptSupC_NEG.json")},
            "4.2(7a)",
            "6.1(1f)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None
    )
    assert result.result == expected_result
