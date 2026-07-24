import copy
import importlib
import logging
import os

import pytest

from helpers.utils import read_data


script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "rtc_battery_voltage_low_check"
faultInst_api = (
    'faultInst.json?query-target-filter=and(eq(faultInst.code,"F2421"),'
    'wcard(faultInst.descr,"reason:The RTC battery voltage is low"))'
)
active_faults = read_data(dir, "f2421.json")["imdata"]
retaining_faults = copy.deepcopy(active_faults)
retaining_faults[0]["faultInst"]["attributes"]["lc"] = "retaining"
malformed_faults = copy.deepcopy(active_faults)
malformed_faults[0]["faultInst"]["attributes"]["dn"] = (
    "topology/pod-1/node-122/sys/diag/rule-rtc-test-trig-forever/"
    "subj-[topology/pod-1/node-122/sys/ch/supslot-1/sup-bad]/fault-F2421"
)
non_exact_reason_faults = []
for reason in [
    "The RTC battery voltage is low or unavailable",
    "Warning: The RTC battery voltage is low",
    "Power-on self-test failed",
]:
    fault = copy.deepcopy(active_faults[0])
    fault["faultInst"]["attributes"]["descr"] = (
        "Diagnostics test failed. reason:" + reason
    )
    non_exact_reason_faults.append(fault)


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_data, expected_unformatted_data",
    [
        (
            {faultInst_api: active_faults},
            script.FAIL_UF,
            [["F2421", "1", "122", "1", "minor", "raised"]],
            [],
        ),
        ({faultInst_api: []}, script.PASS, [], []),
        ({faultInst_api: retaining_faults}, script.PASS, [], []),
        ({faultInst_api: non_exact_reason_faults}, script.PASS, [], []),
        (
            {faultInst_api: active_faults + malformed_faults},
            script.FAIL_UF,
            [["F2421", "1", "122", "1", "minor", "raised"]],
            [[
                "F2421",
                "topology/pod-1/node-122/sys/diag/rule-rtc-test-trig-forever/"
                "subj-[topology/pod-1/node-122/sys/ch/supslot-1/sup-bad]/fault-F2421",
                "Diagnostics test failed. reason:The RTC battery voltage is low",
                "minor",
                "raised",
            ]],
        ),
    ],
)
def test_logic(
    run_check,
    mock_icurl,
    expected_result,
    expected_data,
    expected_unformatted_data,
):
    result = run_check()
    assert result.result == expected_result
    assert result.data == expected_data
    assert result.unformatted_data == expected_unformatted_data
