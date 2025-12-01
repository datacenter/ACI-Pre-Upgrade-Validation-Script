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
    "icurl_outputs, tversion,expected_result",
    [
        #Check pass case
        (
            {
                presListener: read_data(
                    dir, "presListener.json"
                ),
                fabricNode: read_data(
                    dir, "fabricNode.json"
                ),
            },
            "6.1(2f)",
            script.PASS,
        ),
        #Check with missing nodes
        (
            {
                presListener: read_data(
                    dir, "presListener_missing_node.json"
                ),
                fabricNode: read_data(
                    dir, "fabricNode.json"
                ),
            },
            "6.1(2f)",
            script.FAIL_O
        ),
        #Check with missing nodes on affected version
        (
            {
                presListener: read_data(
                    dir, "presListener_missing_node.json"
                ),
                fabricNode: read_data(
                    dir, "fabricNode.json"
                ),
            },
            "5.2(8h)",
            script.FAIL_O,
        ),
        #Check with empty responses for latest version
        (
            {
                presListener: read_data(
                    dir, "presListener_empty.json"
                ),
                fabricNode: read_data(
                    dir, "fabricNode_empty.json"
                ),
            },
            "6.1(3h)",
            script.NA,
        ),
        #Check with empty responses for affected version
        (
            {
                presListener: read_data(
                    dir, "presListener_empty.json"
                ),
                fabricNode: read_data(
                    dir, "fabricNode_empty.json"
                ),
            },
            "5.2(8h)",
            script.FAIL_UF,
        ),
        # tversion not given
        (
            {
                presListener: read_data(
                    dir, "presListener_missing_node.json"
                ),
                fabricNode: read_data(
                    dir, "fabricNode.json"
                ),
            },
            None,
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check,mock_icurl, tversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result
