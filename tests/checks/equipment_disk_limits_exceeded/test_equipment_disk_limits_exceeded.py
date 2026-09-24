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
    "icurl_outputs, expected_result, expected_data, expected_unformatted_data",
    [
        (
            {f182x_api: read_data(dir, "faultInst_neg.json")},
            script.PASS,
            [],
            [],
        ),
        (
            {f182x_api: read_data(dir, "faultInst_pos.json")},
            script.FAIL_UF,
            [
                ["1", "101", "F1820", "98", "Disk usage for /mnt/ifc/log is high on node 101 of fabric POD1 with a hostname leaf1"],
                ["1", "102", "F1821", "97", "Disk usage for /mnt/ifc/cfg is high on node 102 of fabric POD1 with a hostname leaf2"],
                ["1", "104", "F1821", "100", "Disk usage for / is high on node 104 of fabric POD1 with a hostname LEAF-104"],
            ],
            [[
                "topology/pod-1/node-[103]/sys/eqptcapacity/fspartition-ifc:cfg/fault-F1821",
                "NA",
                "Disk usage for /mnt/ifc/cfg is high on node 103 of fabric POD1 with a hostname leaf3",
            ]],
        ),
        (
            {f182x_api: read_data(dir, "faultInst_compact.json")},
            script.FAIL_UF,
            [["1", "107", "F1820", "81", "Disk usage for /mnt/ifc/cfg is above normal"]],
            [],
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
    for row in result.data:
        assert isinstance(row[3], str)
