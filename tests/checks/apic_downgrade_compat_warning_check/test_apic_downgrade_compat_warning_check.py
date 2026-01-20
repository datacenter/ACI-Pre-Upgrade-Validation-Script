import importlib
import logging
import os
import pytest

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_downgrade_compat_warning_check"


@pytest.mark.parametrize(
    "cversion, tversion, expected_result",
    [
        (None, None, script.MANUAL),
        ("4.2(1b)", None, script.MANUAL),
        (None, "5.2(2a)", script.MANUAL),
        ("5.2(2a)", "6.1(4a)", script.NA),
        ("6.1(3a)", "6.1(4c)", script.NA),
        ("6.1(3a)", "6.2(1a)", script.MANUAL),
        ("6.1(3a)", "6.2(2a)", script.MANUAL),
        ("6.2(1a)", "6.2(2c)", script.NA),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion) if cversion else None,
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
