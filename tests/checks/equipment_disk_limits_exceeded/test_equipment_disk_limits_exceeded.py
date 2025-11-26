import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "equipment_disk_limits_exceeded"

f182x_api = 'faultInst.json'
f182x_api += '?query-target-filter=or(eq(faultInst.code,"F1820"),eq(faultInst.code,"F1821"),eq(faultInst.code,"F1822"))'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {f182x_api: read_data(dir, "faultInst_neg.json")},
            script.PASS,
        ),
        (
            {f182x_api: read_data(dir, "faultInst_pos.json")},
            script.FAIL_UF,
        )
    ],
)
def test_logic(run_check, mock_icurl, expected_result):
    result = run_check()
    assert result.result == expected_result
