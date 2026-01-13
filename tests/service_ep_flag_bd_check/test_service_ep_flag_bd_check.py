import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
vnsLIfCtx_api = "vnsLIfCtx.json"
vnsLIfCtx_api += "?query-target=self&rsp-subtree=children"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # tversion missing
        (
            {vnsLIfCtx_api: read_data(dir, "vnsLIfCtx-na.json")},
            "5.2(8h)",
            None,
            script.MANUAL
        ),
        # Version not affected (both new)
        (
            {vnsLIfCtx_api: read_data(dir, "vnsLIfCtx-pos.json")},
            "6.0(8h)",
            "6.1(1g)",
            script.NA,
        ),
        # Version not affected (both old)
        (
            {vnsLIfCtx_api: read_data(dir, "vnsLIfCtx-pos.json")},
            "4.2(7s)",
            "5.2(4c)",
            script.NA,
        ),
        # Version affected with L4L7 Interface connector without PBR
        (
            {vnsLIfCtx_api: read_data(dir, "vnsLIfCtx-pos.json")},
            "5.2(8h)",
            "6.0(8e)",
            script.FAIL_O
        ),
        # Version affected with L4L7 Interface connector without PBR
        (
            {vnsLIfCtx_api: read_data(dir, "vnsLIfCtx-pos.json")},
            "5.2(8h)",
            "6.1(1f)",
            script.FAIL_O
        ),
        # Version affected with L4L7 Interface connector without PBR
        (
            {vnsLIfCtx_api: read_data(dir, "vnsLIfCtx-neg.json")},
            "5.2(8h)",
            "6.0(8e)",
            script.PASS
        ),
        # Version affected with L4L7 Interface connector without PBR
        (
            {vnsLIfCtx_api: read_data(dir, "vnsLIfCtx-neg.json")},
            "5.2(8h)",
            "6.1(1f)",
            script.PASS
        ),
    ],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    cversion = script.AciVersion(cversion)
    tversion = script.AciVersion(tversion) if tversion else None
    result = script.service_ep_flag_bd_check(1, 1, cversion, tversion)
    assert result == expected_result
