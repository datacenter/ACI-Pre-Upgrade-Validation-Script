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
    "icurl_outputs, cversion, expected_result, expected_data",
    [
        # PASS - No raised faults
        (
            {faultInst: []},
            "4.2(1h)",
            script.PASS,
            [],
        ),
        # FAIL - Raised faults with /firmware,/techsupport,/data/log mount points
        (
            {faultInst: read_data(dir, "Fault_raised.json")},
            "4.2(1h)",
            script.FAIL_UF,
            [
                ["F1528", "1", "1", "/data/log", "89%", "Remove unneeded logs in var/log/dme/log"],
                ["F1528", "1", "1", "/firmware", "89%", "Remove unneeded images"],
                ["F1528", "1", "1", "/techsupport", "89%", "Remove unneeded techsupports/cores"],
            ],
        ),
        # PASS - Faults exist but not raised nor soaking (cleared)
        (
            {faultInst: read_data(dir, "Fault_exists_not_raised.json")},
            "4.2(1h)",
            script.PASS,
            [],
        ),
        # FAIL - Raised faults with multiple status - Cleared and Active
        (
            {faultInst: read_data(dir, "Fault_combination.json")},
            "4.2(1h)",
            script.FAIL_UF,
            [
                ["F1529", "1", "1", "/data/log", "94%", "Remove unneeded logs in var/log/dme/log"],
                ["F1528", "1", "1", "/firmware", "89%", "Remove unneeded images"],
            ],
        ),
        # FAIL - Raised faults with unknown mount point (unformatted data)
        (
            {faultInst: read_data(dir, "Fault_unformatted_data.json")},
            "4.2(1h)",
            script.FAIL_UF,
            [
                ["F1528", "1", "1", "/unknown", "88%", "Contact Cisco TAC."],
            ],
        ),
        # FAIL - Raised faults with CSCvn13119 affected version
        (
            {faultInst: read_data(dir, "Fault_unformatted_data.json")},
            "4.0(1h)",
            script.FAIL_UF,
            [
                ["F1528", "1", "1", "/unknown", "88%", "Contact Cisco TAC. A typical issue is CSCvn13119."],
            ],
        ),
        # PASS - No raised faults with CSCvn13119 affected version
        (
            {faultInst: []},
            "4.0(1h)",
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, expected_result, expected_data):
    result = run_check(cversion=script.AciVersion(cversion))
    assert result.result == expected_result
    assert result.data == expected_data
