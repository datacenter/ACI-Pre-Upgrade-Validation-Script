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
virtual_l3out_api = 'l3extVirtualLIfP.json'
l2Pols = 'uni/fabric/l2pol-default.json'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # No Response from neither  l3extRsPathL3OutAtt or l3extVirtualLIfP, result is NA
        ({response_json: [], l2Pols: [], virtual_l3out_api:[]}, script.NA),
        # No Response from l3extVirtualLIfP, Reponse from l3extRsPathL3OutAtt result is MANUAL
        ({response_json: read_data(dir, "l3extRsPathL3OutAtt.json"), l2Pols: read_data(dir, "l2pol-default.json"),
          virtual_l3out_api: []}, script.MANUAL),
        # No Response from l3extRsPathL3OutAtt, Reponse from l3extVirtualLIfP result is MANUAL
        ({response_json: [], l2Pols: read_data(dir, "l2pol-default.json"),
          virtual_l3out_api: read_data(dir, "l3extVirtualLIfP.json")}, script.MANUAL),
        # Response from l3extRsPathL3OutAtt and l3extVirtualLIfP result is MANUAL
        ({response_json: read_data(dir, "l3extRsPathL3OutAtt.json"), 
          l2Pols: read_data(dir, "l2pol-default.json"),
          virtual_l3out_api: read_data(dir, "l3extVirtualLIfP.json")}, script.MANUAL),        

    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.l3out_mtu_check(1, 1)
    assert result == expected_result
