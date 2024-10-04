import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

# icurl queries
leaf_nodes_api =	'fabricNode.json'
leaf_nodes_api +=	'?query-target-filter=eq(fabricNode.role,"leaf")'

#icurl queries
spine_nodes_api = 'fabricNode.json'
spine_nodes_api += '?query-target-filter=eq(fabricNode.role,"spine")'

# icurl queries
lldp_adj_api =	'lldpAdjEp.json'
lldp_adj_api +=	'?query-target-filter=wcard(lldpAdjEp.sysDesc,"topology/pod")'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        ##FAILING =  ONE LEAF SWITCH IS SINGLE-HOMED, OTHER IS MULTI-HOMED, TIER2 LEAF IN THE NODE LIST
        (
            {
                leaf_nodes_api: read_data(dir, "fabricNode-leaf.json"),
                lldp_adj_api: read_data(dir, "lldpAdjEp-neg.json"),
                spine_nodes_api: read_data(dir, "fabricNode-spine.json") 
            },
            script.FAIL_O,
        ),
        ##PASSING = ALL LEAF SWITCHES ARE MULTI-HOMED , TIER2 LEAF IN THE NODE LIST
        (
            {
                leaf_nodes_api: read_data(dir, "fabricNode-leaf.json"),
                lldp_adj_api: read_data(dir, "lldpAdjEp-pos.json"),
                spine_nodes_api: read_data(dir, "fabricNode-spine.json") 
            },
            script.PASS,
        ),

    ],
)
def test_logic(mock_icurl , expected_result):
    result = script.leaf_to_spine_redundancy_check(1, 1 )
    assert result == expected_result