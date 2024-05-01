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
        ("3.2(5e)", script.PASS),
        ("3.2(10g)", script.PASS),
        ("4.1(2a)", script.PASS),
        ("4.2(4j)", script.PASS),
        ("5.0(1l)", script.PASS),
        # Affected version
        ("3.2(4a)", script.FAIL_UF),
        ("4.0(1a)", script.FAIL_UF),
        ("4.2(3a)", script.FAIL_UF),
        ("5.0(1a)", script.FAIL_UF),
    ],
)
def test_logic(mock_icurl, cversion, expected_result):
    result = script.eventmgr_db_defect_check(
        1, 1, script.AciVersion(cversion)
    )
    assert result == expected_result
