import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "static_route_overlap_check"

# icurl queries
staticRoutes = 'ipRouteP.json?query-target-filter=and(wcard(ipRouteP.dn,"/32"))'
staticroute_vrf = "l3extRsEctx.json"
bds_in_vrf = "fvRsCtx.json"
subnets_in_bd = "fvSubnet.json"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # FAIL = AFFECTED VERSION + AFFECTED MO
        (
            {
                staticRoutes: read_data(dir, "ipRouteP_pos.json"),
                staticroute_vrf: read_data(dir, "l3extRsEctx.json"),
                bds_in_vrf: read_data(dir, "fvRsCtx.json"),
                subnets_in_bd: read_data(dir, "fvSubnet.json"),
            },
            "4.2(7f)",
            "5.2(4d)",
            script.FAIL_O,
        ),
        # FAIL = AFFECTED VERSION + AFFECTED MO
        (
            {
                staticRoutes: read_data(dir, "ipRouteP_pos.json"),
                staticroute_vrf: read_data(dir, "l3extRsEctx.json"),
                bds_in_vrf: read_data(dir, "fvRsCtx.json"),
                subnets_in_bd: read_data(dir, "fvSubnet.json"),
            },
            "5.1(1a)",
            "5.2(4d)",
            script.FAIL_O,
        ),
        # PASS = AFFECTED VERSION + NON-AFFECTED MO
        (
            {
                staticRoutes: read_data(dir, "ipRouteP_neg.json"),
                staticroute_vrf: read_data(dir, "l3extRsEctx.json"),
                bds_in_vrf: read_data(dir, "fvRsCtx.json"),
                subnets_in_bd: read_data(dir, "fvSubnet.json"),
            },
            "4.2(7f)",
            "5.2(4d)",
            script.PASS,
        ),
        # PASS = AFFECTED VERSION + AFFECTED MO NON EXISTING
        (
            {
                staticRoutes: read_data(dir, "ipRouteP_empty.json"),
                staticroute_vrf: read_data(dir, "l3extRsEctx.json"),
                bds_in_vrf: read_data(dir, "fvRsCtx.json"),
                subnets_in_bd: read_data(dir, "fvSubnet.json"),
            },
            "4.2(7f)",
            "5.2(4d)",
            script.PASS,
        ),
        # PASS = NON-AFFECTED VERSION + AFFECTED MO
        (
            {
                staticRoutes: read_data(dir, "ipRouteP_pos.json"),
                staticroute_vrf: read_data(dir, "l3extRsEctx.json"),
                bds_in_vrf: read_data(dir, "fvRsCtx.json"),
                subnets_in_bd: read_data(dir, "fvSubnet.json"),
            },
            "4.2(7f)",
            "5.2(6e)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion),
    )
    assert result.result == expected_result
