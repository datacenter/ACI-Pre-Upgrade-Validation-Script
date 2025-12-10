import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "active_node_presListener_mo_object_check"

# icurl queries
presListener = 'presListener.json?query-target-filter=wcard(presListener.dn,"4307")'
fabricNode = 'fabricNode.json?query-target-filter=and(wcard(fabricNode.role,"leaf"),wcard(fabricNode.fabricSt,"active"))'

@pytest.mark.parametrize(
    "icurl_outputs, tversion,fabric_nodes,expected_result",
    [
        #CASE 1: Check pass case with all nodes present
        (
            {
                presListener: read_data(
                    dir, "presListener.json"
                )
            },
            "6.1(2f)",
            read_data(
                dir, "fabricNode.json"
            ),
            script.PASS,
        ),
        #CASE 2: Check with missing nodes in presListener mo
        (
            {
                presListener: read_data(
                    dir, "presListener_missing_node.json"
                )
            },
            "6.1(2f)",
            read_data(
                dir, "fabricNode.json"
            ),
            script.FAIL_O
        ),
        #CASE 3: Check with missing nodes in presListener mo on affected version
        (
            {
                presListener: read_data(
                    dir, "presListener_missing_node.json"
                )
            },
            "5.2(8h)",
            read_data(
                dir, "fabricNode.json"
            ),
            script.FAIL_O,
        ),
        #CASE 4: Check with empty responses  of fabric node and presListener mo for latest version
        (
            {
                presListener: read_data(
                    dir, "presListener_empty.json"
                )
            },
            "6.1(3h)",
            read_data(
                dir, "fabricNode_empty.json"
            ),
            script.NA,
        ),
        #CASE 5: Check with empty responses of fabric node and presListener mo for affected version
        (
            {
                presListener: read_data(
                    dir, "presListener_empty.json"
                ),
            },
            "5.2(8h)",
            read_data(
                dir, "fabricNode_empty.json"
            ),
            script.FAIL_UF,
        ),
        #CASE 6: tversion not given
        (
            {
                presListener: read_data(
                    dir, "presListener_missing_node.json"
                )
            },
            None,
            read_data(
                dir, "fabricNode.json"
            ),
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check,mock_icurl, tversion,fabric_nodes, expected_result):
    result = run_check(tversion=script.AciVersion(tversion) if tversion else None, fabric_nodes=fabric_nodes)
    assert result.result == expected_result
