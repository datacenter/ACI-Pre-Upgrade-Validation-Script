import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
staticRoutes =  'ipRouteP.json'
route_vrf = 'l3extRsEctx.json?query-target-filter=and(wcard(l3extRsEctx.dn,"tn-av.*.av_static"))'
bds_in_vrf = 'fvRsCtx.json?query-target-filter=and(eq(fvRsCtx.tDn,"uni/tn-av/ctx-1"))'
subnets_in_bd = 'fvSubnet.json?query-target-filter=and(wcard(fvSubnet.dn,"uni/tn-av/BD-bd1"))'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
    	##FAILING
        (
            {staticRoutes: read_data(dir, "ipRouteP.json"), route_vrf: read_data(dir, "l3extRsEctx.json"), 
             bds_in_vrf: read_data(dir, "fvRsCtx.json"),subnets_in_bd: read_data(dir, "fvSubnet.json")},
            "4.2(7f)", "5.2(8h)", script.FAIL_O,
        ),
        ##PASSING
        (
            {staticRoutes: read_data(dir, "ipRouteP-outside.json"), route_vrf: read_data(dir, "l3extRsEctx.json"), 
             bds_in_vrf: read_data(dir, "fvRsCtx.json"),subnets_in_bd: read_data(dir, "fvSubnet.json")},
            "4.2(7f)", "5.2(8h)", script.FAIL_O,
        ),
        (
        	{}, "5.0(1h)", "6.2(8h)", script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.static_route_overlap_check(1, 1, script.AciVersion(cversion), script.AciVersion(tversion))
    assert result == expected_result
