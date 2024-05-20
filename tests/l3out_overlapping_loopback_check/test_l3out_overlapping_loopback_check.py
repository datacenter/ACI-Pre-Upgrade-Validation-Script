import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
api = 'l3extOut.json'
api += '?rsp-subtree=full'
api += '&rsp-subtree-class=l3extRsEctx,l3extRsNodeL3OutAtt,l3extLoopBackIfP,l3extRsPathL3OutAtt,l3extMember'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # No overlap
        ({api: read_data(dir, "no_overlap.json")}, script.PASS),
        # Overlap across different nodes
        ({api: read_data(dir, "overlap_on_diff_nodes.json")}, script.PASS),
        # Overlap within the same L3Out - Router ID as loopback (non-VPC)
        ({api: read_data(dir, "same_l3out_rtrId_non_vpc.json")}, script.FAIL_O),
        # Overlap within the same L3Out - Router ID as loopback (VPC)
        ({api: read_data(dir, "same_l3out_rtrId.json")}, script.FAIL_O),
        # Overlap within the same L3Out - Explicit loopback (VPC)
        ({api: read_data(dir, "same_l3out_loopback.json")}, script.FAIL_O),
        # Overlap within the same L3Out - Explicit loopback and Router ID as loopback (VPC)
        ({api: read_data(dir, "same_l3out_loopback_and_rtrId.json")}, script.FAIL_O),
        # Overlap across different L3Outs - Router ID as loopback (VPC)
        ({api: read_data(dir, "diff_l3out_rtrId.json")}, script.FAIL_O),
        # Overlap across different L3Outs - Explicit loopback (VPC)
        ({api: read_data(dir, "diff_l3out_loopback.json")}, script.FAIL_O),
        # Overlap across different L3Outs - Explicit loopback and Router ID as loopback (VPC)
        ({api: read_data(dir, "diff_l3out_loopback_and_rtrId.json")}, script.FAIL_O),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.l3out_overlapping_loopback_check(1, 1)
    assert result == expected_result
