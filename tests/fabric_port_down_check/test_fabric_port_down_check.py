import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
faultInsts =  'faultInst.json'
faultInsts += '?&query-target-filter=and(eq(faultInst.code,"F1394")'
faultInsts += ',eq(faultInst.rule,"ethpm-if-port-down-fabric"))'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {
                faultInsts: read_data(dir, "faultInst_pos.json"),
            },
            script.FAIL_O,
        ),
        (
            {
                faultInsts: [],
            },
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.fabric_port_down_check(1, 1)
    assert result == expected_result
