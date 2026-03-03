import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "svccore_ctrl_and_node_check"

# icurl queries
svccoreCtrlr = "svccoreCtrlr.json"
svccoreNode = "svccoreNode.json"

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # MANUAL TVersion not found
        (
            {
                svccoreCtrlr: read_data(dir, "svccoreCtrlr-pos.json"),
                svccoreNode: read_data(dir, "svccoreNode-pos.json")
                },
            None,
            script.MANUAL,
        ),
        # NA Version not affected
        (
            {
                svccoreCtrlr: read_data(dir, "svccoreCtrlr-pos.json"),
                svccoreNode: read_data(dir, "svccoreNode-pos.json")
                },
            "6.2(1b)",
            script.NA,
        ),
        # PASS Affected version,  low svccoreCtrlr and svccoreNode count
        (
            {
                svccoreCtrlr: read_data(dir, "svccoreCtrlr-neg.json"),
                svccoreNode: read_data(dir, "svccoreNode-neg.json")
                },
            "6.0(3e)",
            script.PASS,
        ),
        # FAIL_UF Affected version,  low svccoreCtrlr count , high svccoreNode count
        (
            {
                svccoreCtrlr: read_data(dir, "svccoreCtrlr-neg.json"),
                svccoreNode: read_data(dir, "svccoreNode-pos.json")
                },
            "6.0(3e)",
            script.FAIL_UF,
        ),
        # FAIL_UF Affected version,  hig svccoreCtrlr count , low svccoreNode count
        (
            {
                svccoreCtrlr: read_data(dir, "svccoreCtrlr-pos.json"),
                svccoreNode: read_data(dir, "svccoreNode-neg.json")
                },
            "6.0(3e)",
            script.FAIL_UF,
        ),
        # FAIL_UF Affected version,  high svccoreCtrlr and svccoreNode count
        (
            {
                svccoreCtrlr: read_data(dir, "svccoreCtrlr-pos.json"),
                svccoreNode: read_data(dir, "svccoreNode-pos.json")
                },
            "6.0(3e)",
            script.FAIL_UF,
        )
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result
