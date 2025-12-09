import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "switch_status_check"

# icurl queries
gir_nodes = 'fabricRsDecommissionNode.json?&query-target-filter=eq(fabricRsDecommissionNode.debug,"yes")'


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, expected_result, expected_data",
    [
        # FAIL - Some switches are not active
        (
            {gir_nodes: read_data(dir, "fabricRsDecommissionNode.json")},
            read_data(dir, "fabricNode_POS.json"),
            script.FAIL_UF,
            [
                ["1", "103", "inactive"],
                ["1", "112", "inactive (Maintenance)"],
                ["1", "121", "inactive"],
            ],
        ),
        # PASS - All switches are active
        (
            {gir_nodes: []},
            read_data(dir, "fabricNode_NEG.json"),
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
    assert result.data == expected_data
