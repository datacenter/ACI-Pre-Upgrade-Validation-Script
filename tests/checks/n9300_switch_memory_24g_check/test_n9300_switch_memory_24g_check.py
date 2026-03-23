import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "n9300_switch_memory_check"

# icurl queries
proc_mem_query = 'procMemUsage.json'


@pytest.mark.parametrize(
    "fabric_nodes, icurl_outputs, tversion, expected_result, expected_msg, expected_data",
    [
        # No nodes returned
        (
            [],
            {},
            "6.0(3c)",
            script.NA,
            'No N9300 switches found. Skipping.',
            [],
        ),
        # Non-N9300 node with >=24GB memory
        (
            read_data(dir, "fabricNode_non_n9300.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_node201_gt24gb.json"),
            },
            "6.0(3c)",
            script.NA,
            'No N9300 switches found. Skipping.',
            [],
        ),
        # N9300 node with >=24GB memory
        (
            read_data(dir, "fabricNode_one.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_gt24gb.json"),
            },
            "6.0(3c)",
            script.PASS,
            '',
            [],
        ),
        # Multiple N9300 nodes, all >=24GB memory
        (
            read_data(dir, "fabricNode_two.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_all_gt24gb.json"),
            },
            "6.0(3c)",
            script.PASS,
            '',
            [],
        ),
        # N9300 node with <24GB memory
        (
            read_data(dir, "fabricNode_two.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_mixed.json"),
            },
            "6.0(3c)",
            script.FAIL_O,
            '',
            [["102", "leaf102", "N9K-C9364C", 21.49]],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, tversion, expected_result, expected_msg, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion),
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.msg == expected_msg
    assert result.data == expected_data