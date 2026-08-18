import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "n9k_c93180yc_fx3_switch_memory_check"

# icurl query - affected node IDs are filtered from the response
proc_mem_query = 'procMemUsage.json?query-target-filter=and(wcard(procMemUsage.dn,"memusage-sup"),lt(procMemUsage.Total,"32000000"))'


def make_fx3_nodes(count):
    return [
        {
            "fabricNode": {
                "attributes": {
                    "dn": "topology/pod-1/node-{}".format(node_id),
                    "id": str(node_id),
                    "name": "leaf{}".format(node_id),
                    "model": "N9K-C93180YC-FX3",
                    "role": "leaf",
                }
            }
        }
        for node_id in range(101, 101 + count)
    ]


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
                proc_mem_query: [],
            },
            script.PASS,
            '',
            [],
        ),
        # Multiple nodes, only N9K-C93180YC-FX3 checked, all >=32GB - API returns empty
        (
            read_data(dir, "fabricNode_two.json"),
            {
                proc_mem_query: [],
            },
            script.PASS,
            '',
            [],
        ),
        # Low-memory results for other switch models are ignored
        (
            read_data(dir, "fabricNode_two.json"),
            {
                proc_mem_query: read_data(dir, "procMemUsage_lt32gb_unaffected.json"),
            },
            script.PASS,
            '',
            [],
        ),
        # Query remains below APIC's 20-expression limit on large fabrics
        (
            make_fx3_nodes(55),
            {
                proc_mem_query: [],
            },
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
            script.FAIL_O,
            (
                'N9K-C93180YC-FX3 requires a minimum of 32GB RAM for proper operation in ACI mode. '
                'One or more switches with less than 32GB of memory may experience service instability. '
                'Upgrade the switch memory to at least 32GB.'
            ),
            [["101", "leaf101", "N9K-C93180YC-FX3", "16.0"]],
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