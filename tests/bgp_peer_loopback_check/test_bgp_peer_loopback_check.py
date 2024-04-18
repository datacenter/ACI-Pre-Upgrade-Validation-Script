import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
l3extLNodePs = "l3extLNodeP.json?rsp-subtree=full&rsp-subtree-class=bgpPeerP,l3extRsNodeL3OutAtt,l3extLoopBackIfP"


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # "rtrIdLoopBack": "no", l3extLoopBackIfP does exist
        (
            {l3extLNodePs: read_data(dir, "l3extRsNodeL3OutAtt_pos.json")},
            script.PASS,
        ),
        # "rtrIdLoopBack": "yes"
        (
            {l3extLNodePs: read_data(dir, "l3extRsNodeL3OutAtt_pos1.json")},
            script.PASS,
        ),
        # no bgp peers
        (
            {l3extLNodePs: read_data(dir, "l3extRsNodeL3OutAtt_pos2.json")},
            script.PASS,
        ),
        # "rtrIdLoopBack": "no", l3extLoopBackIfP does not exist
        (
            {l3extLNodePs: read_data(dir, "l3extRsNodeL3OutAtt_neg.json")},
            script.FAIL_O,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.bgp_peer_loopback_check(1, 1)
    assert result == expected_result
