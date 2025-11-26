import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
Result = script.Result

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "switch_ssd_check"

# icurl queries
faultInst = 'faultInst.json?query-target-filter=or(eq(faultInst.code,"F3073"),eq(faultInst.code,"F3074"))'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_data",
    [
        (
            {faultInst: []},
            script.PASS,
            [],
        ),
        (
            {faultInst: read_data(dir, "faultInst.json")},
            script.FAIL_O,
            [
                [
                    "F3073",
                    "1",
                    "205",
                    "Micron_M550_MTFDDAT256MAY",
                    "90%",
                    "Contact Cisco TAC for replacement procedure",
                ],
                [
                    "F3074",
                    "1",
                    "101",
                    "Micron_M600_MTFDDAT064MBF",
                    "80%",
                    "Monitor (no impact to upgrades)",
                ],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, expected_result, expected_data):
    result = run_check()
    assert result.result == expected_result
    assert result.data == expected_data
