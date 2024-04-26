import os
import pytest
import logging
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    "cversion, expected_result",
    [
        # Non-affected version
        ("4.2(4i)", script.PASS),
        ("5.0(1k)", script.PASS),
        # Affected version
        ("3.2(5e)", script.FAIL_UF),
        ("3.2(10g)", script.FAIL_UF),
        ("4.1(2a)", script.FAIL_UF),
        ("3.2(4a)", script.FAIL_UF),
        ("5.0(1a)", script.FAIL_UF),
        ("4.2(3q)", script.FAIL_UF),
        
        
    ],
)
def test_logic(mock_icurl, cversion, expected_result):
    result = script.eventmgr_db_defect_check(
        1, 1, script.AciVersion(cversion)
    )
    assert result == expected_result
