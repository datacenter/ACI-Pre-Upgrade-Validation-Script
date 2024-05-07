import os
import pytest
import logging
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    "cversion, tversion, expected_result",
    [
        ("4.2(1b)", "5.2(2a)", script.FAIL_O),
        ("3.2(1a)", "4.2(4d)", script.PASS),
        ("3.2(1a)", "5.2(6a)", script.PASS),
        ("4.2(3a)", "4.2(7d)", script.PASS),
        ("2.2(3a)", "2.2(4r)", script.PASS),
        ("5.2(1a)", None, script.MANUAL),
    ],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.contract_22_defect_check(
        1,
        1,
        script.AciVersion(cversion),
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result
