import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))




fabric_nodes_api = 'fabricNode.json'
fabric_nodes_api += '?query-target-filter=and(or(eq(fabricNode.role,"leaf"),eq(fabricNode.role,"spine")),eq(fabricNode.fabricSt,"active"))'

# icurl queries
lldp_adj_api =	'lldpAdjEp.json'
lldp_adj_api +=	'?query-target-filter=wcard(lldpAdjEp.sysDesc,"topology/pod")'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        ##FAILING =  ONE LEAF SWITCH IS SINGLE-HOMED, OTHER IS MULTI-HOMED, TIER2 LEAF IN THE NODE LIST
        (
            {
                fabric_nodes_api: read_data(dir, "fabricNode.json"),
                lldp_adj_api: read_data(dir, "lldpAdjEp_pos.json"),
            },
            script.FAIL_O,
        ),
        ##PASSING = ALL LEAF SWITCHES ARE MULTI-HOMED , TIER2 LEAF IN THE NODE LIST
        (
            {
                fabric_nodes_api: read_data(dir, "fabricNode.json"),
                lldp_adj_api: read_data(dir, "lldpAdjEp_neg.json"),
            },
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl , expected_result):
    result = script.leaf_to_spine_redundancy_check(1, 1 )
    assert result == expected_result