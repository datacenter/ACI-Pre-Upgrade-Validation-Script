import importlib
import logging
import os
import pytest

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.parametrize(
    "cversion, tversion, expected_result",
    [
        (None, None, script.MANUAL),
        ("4.2(1b)", None, script.MANUAL),
        (None, "5.2(2a)", script.MANUAL),
        ("5.2(2a)", "6.1(4a)", script.PASS),
        ("6.1(3a)", "6.1(4c)", script.PASS),
        ("6.1(3a)", "6.2(1a)", script.MANUAL),
        ("6.1(3a)", "6.2(2a)", script.MANUAL),
        ("6.2(1a)", "6.2(2c)", script.PASS),
    ],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.controller_621_pre_warning(
        1,
        1,
        script.AciVersion(cversion) if cversion else None,
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result
