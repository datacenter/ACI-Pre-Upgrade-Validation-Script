import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "apic_storage_inode_check"
faultInst_api = "faultInst.json"
faultInst_api += (
    '?query-target-filter=or(eq(faultInst.code,"F4388"),eq(faultInst.code,"F4389"),eq(faultInst.code,"F4390"))'
)


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_data",
    [
        # PASS - No raised faults
        (
            {faultInst_api: []},
            script.PASS,
            [],
        ),
        # FAIL - Soaking faults
        (
            {faultInst_api: read_data(dir, "Fault_soaking.json")},
            script.FAIL_UF,
            [
                ["F4388", "1", "1", "/data/admin/bin/avread", "82%"],
                ["F4388", "1", "1", "/etc/hosts", "82%"],
                ["F4388", "1", "1", "/", "82%"],
            ],
        ),
        # FAIL - Raised faults
        (
            {faultInst_api: read_data(dir, "Fault_raised.json")},
            script.FAIL_UF,
            [
                ["F4388", "1", "1", "/data/admin/bin/avread", "82%"],
                ["F4388", "1", "1", "/etc/hosts", "82%"],
                ["F4388", "1", "1", "/", "82%"],
            ],
        ),
        # PASS - Faults exist but not raised nor soaking (cleared)
        (
            {faultInst_api: read_data(dir, "Fault_exists_not_raised.json")},
            script.PASS,
            [],
        ),
        # FAIL - Raised faults with multiple status - Cleared and Active
        (
            {faultInst_api: read_data(dir, "Fault_combination.json")},
            script.FAIL_UF,
            [
                ["F4388", "1", "1", "/data/admin/bin/avread", "82%"],
                ["F4388", "1", "1", "/etc/hosts", "82%"],
            ],
        ),
        #   FAIL - Raised faults with unknown mount point (unformatted data)
        (
            {faultInst_api: read_data(dir, "Fault_unformatted_data.json")},
            script.FAIL_UF,
            [
                ["F4388", "topology/pod-1/node-1/sys/ch/invalid/fault-F4388"],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, expected_result, expected_data):
    result = run_check()
    assert result.result == expected_result
    if result.data:
        assert result.data == expected_data
    else:
        assert result.unformatted_data == expected_data
