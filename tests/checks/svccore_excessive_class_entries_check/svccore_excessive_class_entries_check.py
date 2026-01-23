import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "svccoreCtrlr_excessive_entries_check"

# icurl queries
svccoreClassEntry = 'svccoreCtrlr.json'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        #tverson missing
        (
            {svccoreClassEntry: read_data(dir, "svccore_positive.json")},
            None,
            script.MANUAL
        ),
        # tversion not applicable
        (
            {svccoreClassEntry: read_data(dir, "svccore_positive.json")},
            "6.3(2h)",
            script.NA,
        ),
        # No excessive class entries
        (
            {svccoreClassEntry: read_data(dir, "svccore_positive.json")},
            "5.2(8e)",
            script.PASS,
        ),
        # Excessive class entries found
        (
            {svccoreClassEntry: read_data(dir, "svccore_negative.json")},
            "5.2(8e)",
            script.FAIL_O,
        ),
    ],
)

def test_logic(run_check,mock_icurl,tversion,expected_result):
    result = run_check(tversion = script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result
    