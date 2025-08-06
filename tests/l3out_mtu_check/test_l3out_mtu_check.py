import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
response_json = 'l3extRsPathL3OutAtt.json'
response_json_virtual = 'l3extVirtualLIfP.json'
l2Pols = 'uni/fabric/l2pol-default.json'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # No Response, result is NA
        ({response_json: [], l2Pols: []}, script.NA),
        # Overlap across different nodes
        ({response_json: read_data(dir, "l3extRsPathL3OutAtt.json"), l2Pols: read_data(dir, "l2pol-default.json")}, script.MANUAL),
        # Overlap within the same L3Out - Router ID as loopback (non-VPC)
        # ({response_json: read_data(dir, "same_l3out_rtrId_non_vpc.json")}, script.FAIL_O),
        # # Overlap within the same L3Out - Router ID as loopback (VPC)
        # ({response_json: read_data(dir, "same_l3out_rtrId.json")}, script.FAIL_O),
        # # Overlap within the same L3Out - Explicit loopback (VPC) - IPv4/v6
        # ({response_json: read_data(dir, "same_l3out_loopback.json")}, script.FAIL_O),
        # # Overlap within the same L3Out - Explicit loopback (VPC) - IPv4/v6 - 2 l3extLoopBackIfP's under same l3extRsNodeL3OutAtt.
        # ({response_json: read_data(dir, "same_l3out_two_loopbacks.json")}, script.FAIL_O),
        # # Overlap within the same L3Out - Explicit loopback with subnet mask /32,/128 (VPC) - IPv4/v6
        # ({response_json: read_data(dir, "same_l3out_loopback_with_subnet_mask.json")}, script.FAIL_O),
        # # Overlap within the same L3Out - Explicit loopback and Router ID as loopback (VPC)
        # ({response_json: read_data(dir, "same_l3out_loopback_and_rtrId.json")}, script.FAIL_O),
        # # Overlap across different L3Outs - Router ID as loopback (VPC)
        # ({response_json: read_data(dir, "diff_l3out_rtrId.json")}, script.FAIL_O),
        # # Overlap across different L3Outs - Explicit loopback (VPC)
        # ({response_json: read_data(dir, "diff_l3out_loopback.json")}, script.FAIL_O),
        # # Overlap across different L3Outs - Explicit loopback and Router ID as loopback (VPC)
        # ({response_json: read_data(dir, "diff_l3out_loopback_and_rtrId.json")}, script.FAIL_O),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.l3out_mtu_check(1, 1)
    assert result == expected_result
