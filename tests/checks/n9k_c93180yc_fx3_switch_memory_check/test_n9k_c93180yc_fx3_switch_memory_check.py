import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "n9k_c93180yc_fx3_switch_memory_check"

# icurl queries - filtered by affected node IDs and memory threshold
proc_mem_query_node101 = 'procMemUsage.json?query-target-filter=and(or(wcard(procMemUsage.dn,"node-101/")),wcard(procMemUsage.dn,"memusage-sup"),lt(procMemUsage.Total,"32000000"))'


@pytest.mark.parametrize(
    "fabric_nodes, icurl_outputs, expected_result, expected_msg, expected_data",
    [
        # No nodes returned
        (
            [],
            {},
            script.NA,
            'No N9K-C93180YC-FX3 switches found. Skipping.',
            [],
        ),
        # Non-N9K-C93180YC-FX3 node (N9K-C9508)
        (
            read_data(dir, "fabricNode_N9K-C9508.json"),
            {},
            script.NA,
            'No N9K-C93180YC-FX3 switches found. Skipping.',
            [],
        ),
        # N9K-C93180YC-FX3 node with >=32GB memory - API returns empty (filtered by lt)
        (
            read_data(dir, "fabricNode_one.json"),
            {
                proc_mem_query_node101: [],
            },
            script.PASS,
            '',
            [],
        ),
        # Multiple nodes, only N9K-C93180YC-FX3 checked, all >=32GB - API returns empty
        (
            read_data(dir, "fabricNode_two.json"),
            {
                proc_mem_query_node101: [],
            },
            script.PASS,
            '',
            [],
        ),
        # N9K-C93180YC-FX3 node with <32GB memory (fail case)
        (
            read_data(dir, "fabricNode_one.json"),
            {
                proc_mem_query_node101: read_data(dir, "procMemUsage_lt32gb.json"),
            },
            script.FAIL_O,
            (
                'N9K-C93180YC-FX3 requires a minimum of 32GB RAM for proper operation in ACI mode. '
                'One or more switches with less than 32GB of memory may experience service instability. '
                'Upgrade the switch memory to at least 32GB.'
            ),
            [["101", "leaf101", "N9K-C93180YC-FX3", 16.0]],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, expected_result, expected_msg, expected_data):
    result = run_check(
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.msg == expected_msg
    if result.data:
        assert result.data == expected_data
    else:
        assert result.unformatted_data == expected_data