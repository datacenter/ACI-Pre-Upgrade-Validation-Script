import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "bgp_golf_route_target_type_check"

# icurl queries
fvCtxs = 'fvCtx.json?rsp-subtree=full&rsp-subtree-class=l3extGlobalCtxName,bgpRtTarget&rsp-subtree-include=required'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        (
            {fvCtxs: read_data(dir, "fvCtx_pos.json")},
            "4.2(1b)",
            "5.2(2a)",
            script.PASS,
        ),
        (
            {fvCtxs: read_data(dir, "fvCtx_pos.json")},
            "3.2(1a)",
            "4.2(4d)",
            script.FAIL_O,
        ),
        (
            {fvCtxs: read_data(dir, "fvCtx_pos.json")},
            "3.2(1a)",
            "5.2(6a)",
            script.FAIL_O,
        ),
        (
            {fvCtxs: read_data(dir, "fvCtx_pos.json")},
            "4.2(3a)",
            "4.2(7d)",
            script.PASS,
        ),
        (
            {fvCtxs: read_data(dir, "fvCtx_pos.json")},
            "2.2(3a)",
            "2.2(4r)",
            script.PASS,
        ),
        (
            {fvCtxs: read_data(dir, "fvCtx_pos.json")},
            "5.2(1a)",
            None,
            script.MANUAL,
        ),
        (
            {fvCtxs: read_data(dir, "fvCtx_pos.json")},
            "4.1(1a)",
            "5.2(7f)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
