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
decomissioned_api = 'fabricRsDecommissionNode.json'

active_spine_api = 'topSystem.json'
active_spine_api += '?query-target-filter=eq(topSystem.role,"spine")'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # TVERSION not supplied
        (
            {
                active_spine_api: read_data(dir, "topSystem.json"),
                decomissioned_api: read_data(dir,"fabricRsDecommissionNode_NEG.json")
            },
            None,
            script.MANUAL,
        ),
        # No decom objects
        (
            {
                active_spine_api: read_data(dir, "topSystem.json"),
                decomissioned_api: read_data(dir,"fabricRsDecommissionNode_NEG.json")
            },
            "5.2(5e)",
            script.PASS,
        ),
        # Spine has stale decom object, and going to affected version
        (
            {
                active_spine_api: read_data(dir, "topSystem.json"),
                decomissioned_api: read_data(dir,"fabricRsDecommissionNode_POS.json")
            },
            "5.2(6a)",
            script.FAIL_O,
        ),
        # Fixed Target Version
        (
            {
                active_spine_api: read_data(dir, "topSystem.json"),
                decomissioned_api: read_data(dir,"fabricRsDecommissionNode_POS.json")
            },
            "6.0(4a)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
