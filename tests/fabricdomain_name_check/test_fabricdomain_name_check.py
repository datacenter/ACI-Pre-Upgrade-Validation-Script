import os
import pytest
import logging
import importlib
from helpers.utils import read_data
script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
topSystem = 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")'

@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # # char test
        (
            {
                topSystem: read_data(dir, "topSystem_1POS.json")
            },
            "5.2(3g)",
            "6.0(2h)",
            script.FAIL_O,
        ),
        (
            {
                topSystem: read_data(dir, "topSystem_1POS.json")
            },
            "6.0(3a)",
            "6.0(2h)",
            script.FAIL_O,
        ),
         # ; char test
        (
            {
                topSystem: read_data(dir, "topSystem_2POS.json")
            },
            "5.2(3g)",
            "6.0(2h)",
            script.FAIL_O,
        ),
        (
            {
                topSystem: read_data(dir, "topSystem_2POS.json")
            },
            "6.0(3a)",
            "6.0(2h)",
            script.FAIL_O,
        ),
        # Neither ; or # in fabricDomain
        (
            {
                topSystem: read_data(dir, "topSystem_NEG.json")
            },
            "5.2(3g)",
            "6.0(2h)",
            script.PASS,
        ),
        # only affected 6.0(2h), regardless of special chars
        (
            {
                topSystem: read_data(dir, "topSystem_1POS.json")
            },
            "5.2(3g)",
            "6.0(1j)",
            script.PASS,
        ),
        # Eventual 6.0(3) has fix
        (
            {
                topSystem: read_data(dir, "topSystem_1POS.json")
            },
            "5.2(3g)",
            "6.0(3a)",
            script.PASS,
        ),
        (
            {
                topSystem: read_data(dir, "topSystem_1POS.json")
            },
            "6.0(3a)",
            "6.0(4a)",
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.fabricdomain_name_check(1, 1, cversion, tversion)
    assert result == expected_result
