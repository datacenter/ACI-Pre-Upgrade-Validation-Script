import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_vmm_inventory_sync_faults_check"


f0132_api = 'faultInst.json'
f0132_api += '?query-target-filter=eq(faultInst.code,"F0132")'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {f0132_api: read_data(dir, "faultInst_neg.json")},
            script.PASS,
        ),
        (
            {f0132_api: read_data(dir, "faultInst_neg1.json")},
            script.PASS,
        ),
        (
            {f0132_api: read_data(dir, "faultInst_pos.json")},
            script.MANUAL,
        ),
        (
            {f0132_api: read_data(dir, "faultInst_pos2.json")},
            script.MANUAL,
        )
    ],
)
def test_logic(run_check, mock_icurl, expected_result):
    result = run_check()
    assert result.result == expected_result
