import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
decomissioned_api ='fabricRsDecommissionNode.json'

active_spine_api = 'topSystem.json'
active_spine_api +=	'?query-target-filter=eq(topSystem.role,"spine")'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            {
                active_spine_api: read_data(dir, "topSystem.json"),
                decomissioned_api: read_data(dir,"fabricRsDecommissionNode_NEG.json")
            },
            None,
            script.MANUAL,
        ),
        (
            {
                active_spine_api: read_data(dir, "topSystem.json"),
                decomissioned_api: read_data(dir,"fabricRsDecommissionNode_NEG.json")
            },
            "5.2(5e)",
            script.PASS,
        ),
        (
            {
                active_spine_api: read_data(dir, "topSystem.json"),
                decomissioned_api: read_data(dir,"fabricRsDecommissionNode_POS.json")
            },
            "5.2(6a)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.stale_decomissioned_spine_check(
        1,
        1,
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result
