import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_storage_inode_check"

# icurl queries
faultInst_api = 'faultInst.json'
faultInst_api += '?query-target-filter=or(eq(faultInst.code,"F4388"),eq(faultInst.code,"F4390"))'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # Target version in affected range (>= 5.3(2b)) and < 6.0(8f)) with raised faults
        (
            {faultInst_api: read_data(dir, "faultInst_pos_raised.json")},
            script.FAIL_O,
        ),
        # Target version in affected range with raised faults (F4390 - critical)
        (
            {faultInst_api: read_data(dir, "faultInst_pos_f4390.json")},
            script.FAIL_O,
        ),
        # Target version in affected range with NO raised faults (cleared faults)
        (
            {faultInst_api: read_data(dir, "faultInst_neg_cleared.json")},
            script.PASS,
        ),
        # Target version in affected range with NO faults at all
        (
            {faultInst_api: []},
            script.PASS,
        ),
        # Target version BELOW affected range (< 5.2(8i))
        (
            {faultInst_api: read_data(dir, "faultInst_pos_raised.json")},
            script.NA,
        ),
        # Target version ABOVE affected range (>= 6.0(8f))
        (
            {faultInst_api: read_data(dir, "faultInst_pos_raised.json")},
            script.NA,
        ),
        # Target version way above affected range
        (
            {faultInst_api: read_data(dir, "faultInst_pos_raised.json")},
            script.NA,
        ),
        # NO target version provided
        (
            {faultInst_api: []},
            script.MANUAL,
        ),
        # Multiple raised faults from different nodes
        (
            {faultInst_api: read_data(dir, "faultInst_pos_multiple.json")},
            script.FAIL_O,
        ),
        # Fault with unparseable DN (should go to unformatted_data)
        (
            {faultInst_api: read_data(dir, "faultInst_pos_unparseable.json")},
            script.FAIL_O,
        ),
    ],
)
def test_logic(run_check, mock_icurl, expected_result):
    result = run_check()
    assert result.result == expected_result
