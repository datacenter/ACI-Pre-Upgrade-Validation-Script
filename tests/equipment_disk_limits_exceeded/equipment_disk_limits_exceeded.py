import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

equipment_json = 'faultInst.json?query-target-filter=or(eq(faultInst.code,"F1820"),eq(faultInst.code,"F1821"))'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {equipment_json: read_data(dir, "equipment_disk_limits_exceeded_null.json"),
            script.PASS,
        ),
        (
            {partitions: read_data(dir, "eqptcapacityFSPartition.json"),
            script.PASS,
        )
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.equipment_disk_limits_exceeded(1, 1)
    assert result == expected_result