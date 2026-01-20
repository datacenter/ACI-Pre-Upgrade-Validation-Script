import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_disk_space_faults_check"

# icurl queries
faultInst = 'faultInst.json?query-target-filter=or(eq(faultInst.code,"F1527"),eq(faultInst.code,"F1528"),eq(faultInst.code,"F1529"))'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, expected_result",
    [
        # PASS - No raised faults
        (
            {faultInst: []},
            "4.2(1h)",
            script.PASS,
        ),
        # FAIL - Raised faults with /firmware,/techsupport,/data/log mount points
        (
            {
                faultInst: read_data(dir, "Fault_raised.json")
            },
            "4.2(1h)",
            script.FAIL_UF,
        ),
        
        # PASS - Faults exist but not raised (cleared)
        (
            {
                faultInst: read_data(dir, "Fault_exists_not_raised.json")
            },
            "4.2(1h)",
            script.PASS,
        ),

        # FAIL - Raised faults with multiple status - Cleared and Active
        (
            {
                faultInst: read_data(dir, "Fault_combination.json")
            },
            "4.2(1h)",
            script.FAIL_UF,
        ),

        # FAIL - Raised faults with unknown mount point (unformatted data)
        (
            {
                faultInst: read_data(dir, "Fault_unformatted_data.json")
            },
            "4.2(1h)",
            script.FAIL_UF,
        ),
        # FAIL - Raised faults with CSCvn13119 affected version
        (
            {
                faultInst: read_data(dir, "Fault_raised.json")
            },
            "4.0(1h)",
            script.FAIL_UF,
        ),
        # PASS - No raised faults with CSCvn13119 affected version
        (
            {faultInst: []},
            "4.0(1h)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, expected_result):
    result = run_check(cversion=script.AciVersion(cversion))
    assert result.result == expected_result