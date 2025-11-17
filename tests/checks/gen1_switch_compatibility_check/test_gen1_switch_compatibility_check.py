import os
import pytest
import logging
import importlib
from helpers.utils import read_data

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion

test_function = "gen1_switch_compatibility_check"


@pytest.mark.parametrize(
    "tversion, fabric_nodes, expected_result, expected_data",
    [
        # FAIL - gen1 HW does not support t_ver
        (
            "5.2(3b)",
            read_data(dir, "fabricNode_with_gen1.json"),
            script.FAIL_UF,
            [
                ["5.2(3b)", "101", "N9K-C9372TX-E", "Not supported on 5.x+"],
                ["5.2(3b)", "102", "N9K-C9372TX-E", "Not supported on 5.x+"],
                ["5.2(3b)", "1001", "N9K-C9332PQ", "Not supported on 5.x+"],
            ],
        ),
        # PASS - gen1 HW supports t_ver
        ("4.2(7r)", read_data(dir, "fabricNode_with_gen1.json"), script.PASS, []),
        # PASS - no gen1 hw found
        ("5.2(3b)", read_data(dir, "fabricNode_no_gen1.json"), script.PASS, []),
    ],
)
def test_logic(run_check, tversion, fabric_nodes, expected_result, expected_data):
    result = run_check(
        tversion=AciVersion(tversion) if tversion else None,
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
