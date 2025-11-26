import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "rtmap_comm_match_defect_check"

# icurl queries
rtctrlSubjPs = "rtctrlSubjP.json?rsp-subtree=full&rsp-subtree-class=rtctrlMatchCommFactor,rtctrlMatchRtDest&rsp-subtree-include=required"
rtctrlCtxPs = "rtctrlCtxP.json?rsp-subtree=full&rsp-subtree-class=rtctrlRsCtxPToSubjP,rtctrlRsScopeToAttrP&rsp-subtree-include=required"


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            {
                rtctrlSubjPs: read_data(dir, "rtctrlSubjP_NEG.json"),
                rtctrlCtxPs: read_data(dir,"rtctrlCtxP_NEG.json")
            },
            None,
            script.MANUAL,
        ),
        (
            {
                rtctrlSubjPs: [],
                rtctrlCtxPs: []
            },
            "5.2(4d)",
            script.PASS,
        ),
        (
            {
                rtctrlSubjPs: read_data(dir, "rtctrlSubjP_NEG.json"),
                rtctrlCtxPs: read_data(dir,"rtctrlCtxP_NEG.json")
            },
            "5.2(5e)",
            script.PASS,
        ),
        (
            {
                rtctrlSubjPs: read_data(dir, "rtctrlSubjP_POS.json"),
                rtctrlCtxPs: read_data(dir,"rtctrlCtxP_POS.json")
            },
            "5.2(6a)",
            script.FAIL_O,
        ),
        (
            {
                rtctrlSubjPs: read_data(dir, "rtctrlSubjP_POS.json"),
                rtctrlCtxPs: read_data(dir,"rtctrlCtxP_POS.json")
            },
            "5.2(8d)",
            script.PASS,
        ),
        (
            {
                rtctrlSubjPs: read_data(dir, "rtctrlSubjP_POS.json"),
                rtctrlCtxPs: read_data(dir,"rtctrlCtxP_POS.json")
            },
            "6.0(3d)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
