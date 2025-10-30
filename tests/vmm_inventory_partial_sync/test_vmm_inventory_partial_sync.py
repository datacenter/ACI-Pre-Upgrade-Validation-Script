import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

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
        )
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.apic_vmm_inventory_sync_faults_check(1, 1)
    assert result == expected_result
