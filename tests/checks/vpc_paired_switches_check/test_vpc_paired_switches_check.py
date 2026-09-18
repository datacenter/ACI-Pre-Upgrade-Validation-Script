import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "vpc_paired_switches_check"


@pytest.mark.parametrize(
    "vpc_node_ids, expected_result, expected_data",
    [
        # all leaf switches are in vPC
        (
            ["101", "102", "103", "104", "111", "112", "121", "122"],
            script.PASS,
            [],
        ),
        # not all leaf switches are in vPC
        (
            ["101", "102", "111", "112"],
            script.MANUAL,
            [["103", "LF103"], ["104", "LF104"], ["121", "RL_LF121"], ["122", "RL_LF122"]],
        ),
    ],
)
def test_logic(run_check, vpc_node_ids, expected_result, expected_data):
    result = run_check(
        vpc_node_ids=vpc_node_ids,
        fabric_nodes=read_data(dir, "fabricNode.json"),
    )
    assert result.result == expected_result
    assert result.data == expected_data
