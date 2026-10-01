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


@pytest.mark.parametrize(
    "code, partition, change_set, expected_result, expected_percent",
    [
        ("F1820", "log", "avail:4900, used:5100", script.PASS, None),
        ("F1820", "log", "avail (New: 2040), used (New: 7960)", script.PASS, None),
        ("F1820", "log", "avail:2000, used:8000", script.FAIL_UF, "80"),
        ("F1820", "cfg", "avail:4900, used:5100", script.FAIL_UF, "51"),
        ("F1821", "log", "avail:4900, used:5100", script.FAIL_UF, "51"),
        ("F1822", "log", "avail:4900, used:5100", script.FAIL_UF, "51"),
        ("F1820", "log", "avail:4900, used:invalid", script.FAIL_UF, "NA"),
        ("F1820", "log", "avail:0, used:0", script.FAIL_UF, "NA"),
    ],
)
def test_cosmetic_log_fault_threshold(
    run_check, mock_icurl, icurl_outputs, code, partition, change_set, expected_result, expected_percent
):
    dn = "topology/pod-1/node-101/sys/eqptcapacity/fspartition-ifc:{}/fault-{}".format(partition, code)
    description = "Disk usage for /mnt/ifc/{} is above normal".format(partition)
    icurl_outputs[f182x_api] = [{"faultInst": {"attributes": {
        "changeSet": change_set,
        "code": code,
        "descr": description,
        "dn": dn,
    }}}]

    result = run_check()

    assert result.result == expected_result
    if expected_percent is None:
        assert result.data == []
    else:
        assert result.data == [["1", "101", code, expected_percent, description]]
    assert result.unformatted_data == []
