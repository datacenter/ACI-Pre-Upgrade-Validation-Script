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


# --- Batch query coverage ---
# Mirrors the check's batch_size so tests break if the constant drifts.
BATCH_SIZE = 20


def _fx3_fabric_nodes(node_ids):
    return [
        {
            "fabricNode": {
                "attributes": {
                    "dn": "topology/pod-1/node-{}".format(nid),
                    "id": nid,
                    "name": "leaf{}".format(nid),
                    "model": "N9K-C93180YC-FX3",
                    "role": "leaf",
                }
            }
        }
        for nid in node_ids
    ]


def _batch_query(node_ids, min_memory_kb=32000000):
    node_filter = 'or({})'.format(','.join(
        'wcard(procMemUsage.dn,"node-{}/")'.format(nid) for nid in node_ids
    ))
    return 'procMemUsage.json?query-target-filter=and({},wcard(procMemUsage.dn,"memusage-sup"),lt(procMemUsage.Total,"{}"))'.format(
        node_filter, min_memory_kb
    )


def _proc_mem_usage(node_id, total_kb):
    return [
        {
            "procMemUsage": {
                "attributes": {
                    "dn": "topology/pod-1/node-{}/sys/procmem/memusage-sup".format(node_id),
                    "Modname": "sup",
                    "Total": str(total_kb),
                }
            }
        }
    ]


def test_batch_at_boundary_issues_single_query(run_check, monkeypatch):
    node_ids = [str(nid) for nid in range(101, 101 + BATCH_SIZE)]  # exactly BATCH_SIZE nodes
    fabric_nodes = _fx3_fabric_nodes(node_ids)
    query = _batch_query(node_ids)

    calls = []

    def _mock_icurl(apitype, q, page=0, page_size=100000):
        calls.append(q)
        assert q == query
        return []

    monkeypatch.setattr(script, "icurl", _mock_icurl)

    result = run_check(fabric_nodes=fabric_nodes)

    assert len(calls) == 1
    assert result.result == script.PASS


def test_batch_split_across_two_queries(run_check, monkeypatch):
    # 25 affected nodes -> batch1 has 20 IDs, batch2 has the remaining 5.
    node_ids = [str(nid) for nid in range(101, 126)]
    fabric_nodes = _fx3_fabric_nodes(node_ids)
    batch1_ids, batch2_ids = node_ids[:BATCH_SIZE], node_ids[BATCH_SIZE:]
    query1, query2 = _batch_query(batch1_ids), _batch_query(batch2_ids)

    # One low-memory node in each batch to confirm results from both queries are merged.
    responses = {
        query1: _proc_mem_usage(batch1_ids[0], 16000000),
        query2: _proc_mem_usage(batch2_ids[-1], 16000000),
    }
    calls = []

    def _mock_icurl(apitype, q, page=0, page_size=100000):
        calls.append(q)
        return responses[q]

    monkeypatch.setattr(script, "icurl", _mock_icurl)

    result = run_check(fabric_nodes=fabric_nodes)

    assert sorted(calls) == sorted([query1, query2])
    assert result.result == script.FAIL_O
    expected_data = [
        [batch1_ids[0], "leaf{}".format(batch1_ids[0]), "N9K-C93180YC-FX3", 16.0],
        [batch2_ids[-1], "leaf{}".format(batch2_ids[-1]), "N9K-C93180YC-FX3", 16.0],
    ]
    assert result.data == expected_data