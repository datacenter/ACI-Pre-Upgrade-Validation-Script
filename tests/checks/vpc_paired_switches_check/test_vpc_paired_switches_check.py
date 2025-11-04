import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "vpc_paired_switches_check"

# icurl queries
topSystems = "topSystem.json"


@pytest.mark.parametrize(
    "icurl_outputs, vpc_node_ids, expected_result",
    [
        # all leaf switches are in vPC
        (
            {topSystems: read_data(dir, "topSystem.json")},
            ["101", "102", "103", "204", "206"],
            script.PASS,
        ),
        # not all leaf switches are in vPC
        (
            {topSystems: read_data(dir, "topSystem.json")},
            ["101", "103", "204", "206"],
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check, mock_icurl, vpc_node_ids, expected_result):
    result = run_check(vpc_node_ids=vpc_node_ids)
    assert result.result == expected_result
