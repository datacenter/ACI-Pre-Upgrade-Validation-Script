import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "fabric_link_redundancy_check"

fabric_nodes_api = 'fabricNode.json'
fabric_nodes_api += '?query-target-filter=and(or(eq(fabricNode.role,"leaf"),eq(fabricNode.role,"spine")),eq(fabricNode.fabricSt,"active"))'

# icurl queries
lldp_adj_api = 'lldpAdjEp.json'
lldp_adj_api += '?query-target-filter=wcard(lldpAdjEp.sysDesc,"topology/pod")'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # FAILING = T1 leaf101 single-homed, T1 leaf102 none, T1 leaf103 multi-homed
        (
            {
                fabric_nodes_api: read_data(dir, "fabricNode.json"),
                lldp_adj_api: read_data(dir, "lldpAdjEp_pos_spine_only.json"),
            },
            script.FAIL_O,
        ),
        # FAILING = T1 leafs multi-homed, T2 leaf111 single-homed, T2 leaf112 multi-homed
        (
            {
                fabric_nodes_api: read_data(dir, "fabricNode.json"),
                lldp_adj_api: read_data(dir, "lldpAdjEp_pos_t1_only.json"),
            },
            script.FAIL_O,
        ),
        # FAILING = T1 leaf101 single-homed, T1 leaf102 none, T1 leaf103 multi-homed
        #           T2 leaf111 single-homed, T2 leaf112 multi-homed
        (
            {
                fabric_nodes_api: read_data(dir, "fabricNode.json"),
                lldp_adj_api: read_data(dir, "lldpAdjEp_pos_spine_t1.json"),
            },
            script.FAIL_O,
        ),
        # PASSING = ALL LEAF SWITCHES ARE MULTI-HOMED except for RL
        (
            {
                fabric_nodes_api: read_data(dir, "fabricNode.json"),
                lldp_adj_api: read_data(dir, "lldpAdjEp_neg.json"),
            },
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl , expected_result):
    result = run_check()
    assert result.result == expected_result
