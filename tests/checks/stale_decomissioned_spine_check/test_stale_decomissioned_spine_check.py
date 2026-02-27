import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "stale_decomissioned_spine_check"

# icurl queries
decomissioned_api = "fabricRsDecommissionNode.json"


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result, expected_data",
    [
        # TVERSION not supplied
        (
            {decomissioned_api: read_data(dir, "fabricRsDecommissionNode_POS.json")},
            None,
            script.MANUAL,
            [],
        ),
        # No decom objects
        (
            {decomissioned_api: []},
            "5.2(5e)",
            script.PASS,
            [],
        ),
        # Spine has stale decom object, and going to affected version
        (
            {decomissioned_api: read_data(dir, "fabricRsDecommissionNode_POS.json")},
            "5.2(6a)",
            script.FAIL_O,
            [["106", "spine2", "active"]],
        ),
        # Fixed Target Version
        (
            {decomissioned_api: read_data(dir, "fabricRsDecommissionNode_POS.json")},
            "6.0(4a)",
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        fabric_nodes=read_data(dir, "fabricNode.json"),
    )
    assert result.result == expected_result
    assert result.data == expected_data
