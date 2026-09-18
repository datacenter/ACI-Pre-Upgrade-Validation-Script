import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "fabric_link_redundancy_check"

# icurl queries
lldp_adj_api = "lldpAdjEp.json"
lldp_adj_api += '?query-target-filter=wcard(lldpAdjEp.sysDesc,"topology/pod")'


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, expected_result, expected_data",
    [
        # FAILING = T1 leaf101 single-homed, T1 leaf102 none, T1 leaf103 multi-homed
        (
            {lldp_adj_api: read_data(dir, "lldpAdjEp_pos_spine_only.json")},
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [
                ["LF101", "SP1001", "Only one spine adjacency"],
                ["LF102", "", "No spine adjacency"],
            ]
        ),
        # FAILING = T1 leafs multi-homed, T2 leaf111 single-homed, T2 leaf112 multi-homed
        (
            {lldp_adj_api: read_data(dir, "lldpAdjEp_pos_t1_only.json")},
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [
                ["T2_LF111", "LF102", "Only one tier 1 leaf adjacency"],
            ]
        ),
        # FAILING = T1 leaf101 single-homed, T1 leaf102 none, T1 leaf103 multi-homed
        #           T2 leaf111 single-homed, T2 leaf112 multi-homed
        (
            {lldp_adj_api: read_data(dir, "lldpAdjEp_pos_spine_t1.json")},
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [
                ["LF101", "SP1001", "Only one spine adjacency"],
                ["LF102", "", "No spine adjacency"],
                ["T2_LF111", "LF102", "Only one tier 1 leaf adjacency"],
            ]
        ),
        # PASSING = ALL LEAF SWITCHES ARE MULTI-HOMED except for RL
        (
            {lldp_adj_api: read_data(dir, "lldpAdjEp_neg.json")},
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, expected_result, expected_data):
    result = run_check(
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert sorted(result.data) == sorted(expected_data)
