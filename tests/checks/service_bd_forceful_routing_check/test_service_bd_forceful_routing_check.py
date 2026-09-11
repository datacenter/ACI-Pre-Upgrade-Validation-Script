import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "service_bd_forceful_routing_check"

# icurl queries
fvRtLIfCtxToBD = "fvRtLIfCtxToBD.json"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result, expected_data, expected_unformatted_data",
    [
        # tversion missing
        (
            {fvRtLIfCtxToBD: read_data(dir, "fvRtLIfCtxToBD.json")},
            "5.2(8h)",
            None,
            script.MANUAL,
            [],
            [],
        ),
        # Version not affected (both new)
        (
            {fvRtLIfCtxToBD: read_data(dir, "fvRtLIfCtxToBD.json")},
            "6.0(2h)",
            "6.1(3b)",
            script.NA,
            [],
            [],
        ),
        # Version not affected (both old)
        (
            {fvRtLIfCtxToBD: read_data(dir, "fvRtLIfCtxToBD.json")},
            "4.2(7s)",
            "6.0(1h)",
            script.NA,
            [],
            [],
        ),
        # Version affected with L4L7 service graph BD
        (
            {fvRtLIfCtxToBD: read_data(dir, "fvRtLIfCtxToBD.json")},
            "5.2(8h)",
            "6.0(2h)",
            script.MANUAL,
            [
                ["TK:BD4", "TK:N9K_PBR_C", "TK:N9K_PBR", "N1", "provider"],
                ["TK:BD3", "TK:N9K_PBR_C", "TK:N9K_PBR", "N1", "consumer"],
                ["TK:BD_PBR", "TK:PBR", "TK:FW_PBR", "N1", "provider"],
                ["TK:BD_PBR", "TK:PBR", "TK:FW_PBR", "N1", "consumer"],
                ["TK:BD_PBR_inside", "common:CMN_LB_C", "common:CMN_LB", "N1", "cluster-if1"],
                ["TK:BD_PBR_outside", "common:CMN_LB_C", "common:CMN_LB", "N1", "cluster-if1"],
            ],
            [["uni/tn-TK/BD-BD1/rtvnsLIfCtxToBD-[unexpected-dn-format]"]],
        ),
        # Version affected without L4L7 service graph BD
        (
            {fvRtLIfCtxToBD: []},
            "5.2(8h)",
            "6.0(2h)",
            script.PASS,
            [],
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result, expected_data, expected_unformatted_data):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data
    assert result.unformatted_data == expected_unformatted_data
