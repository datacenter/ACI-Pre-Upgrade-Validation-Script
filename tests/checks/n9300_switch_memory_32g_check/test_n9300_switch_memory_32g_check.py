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
            'No N9K-C93180YC-FX3 switches found. Skipping.',
            [],
        ),
        # Non-N9K-C93180YC-FX3 node
        (
            read_data(dir, "fabricNode_non_n9300.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_node201_gt32gb.json"),
            },
            "6.0(3c)",
            script.NA,
            'No N9K-C93180YC-FX3 switches found. Skipping.',
            [],
        ),
        # N9K-C93180YC-FX3 node with >=32GB memory
        (
            read_data(dir, "fabricNode_one.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_gt32gb.json"),
            },
            "6.0(3c)",
            script.PASS,
            '',
            [],
        ),
        # Multiple nodes, only N9K-C93180YC-FX3 checked, all >=32GB
        (
            read_data(dir, "fabricNode_two.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_all_gt32gb.json"),
            },
            "6.0(3c)",
            script.PASS,
            '',
            [],
        ),
        # Invalid procMemUsage Total value
        (
            read_data(dir, "fabricNode_one.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_invalid_total.json"),
            },
            "6.0(3c)",
            script.ERROR,
            'Failed to parse procMemUsage Total for one or more nodes.',
            [["topology/pod-1/node-101/sys/procmem/memusage-sup", "unknown"]],
        ),
        # Missing procMemUsage data for affected node
        (
            read_data(dir, "fabricNode_one.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_missing_affected_node.json"),
            },
            "6.0(3c)",
            script.ERROR,
            'Missing procMemUsage data for one or more affected N9K-C93180YC-FX3 nodes.',
            [["101", "leaf101", "N9K-C93180YC-FX3"]],
        ),
        # N9K-C93180YC-FX3 node with <32GB memory
        (
            read_data(dir, "fabricNode_two.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_mixed.json"),
            },
            "6.0(3c)",
            script.PASS,
            '',
            [],
        ),
        # N9K-C93180YC-FX3 node with <32GB memory (fail case)
        (
            read_data(dir, "fabricNode_one.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_lt32gb.json"),
            },
            "6.0(3c)",
            script.FAIL_O,
            '',
            [["101", "leaf101", "N9K-C93180YC-FX3", 25.31]],
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