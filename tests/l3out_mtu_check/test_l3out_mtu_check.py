import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
regular_api = "l3extRsPathL3OutAtt.json"
floating_api = "l3extVirtualLIfP.json"
l2Pols = "uni/fabric/l2pol-default.json"


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # No Response from neither l3extRsPathL3OutAtt or l3extVirtualLIfP, result is NA
        ({regular_api: [], floating_api: [], l2Pols: []}, script.NA),
        # No Response from l3extRsPathL3OutAtt, Version too old for l3extVirtualLIfP, result is NA
        ({regular_api: [], floating_api: read_data(dir, "l3extVirtualLIfP_unresolved.json"), l2Pols: []}, script.NA),
        # No Response from l3extVirtualLIfP, Reponse from l3extRsPathL3OutAtt result is MANUAL
        ({regular_api: read_data(dir, "l3extRsPathL3OutAtt.json"), floating_api: [], l2Pols: read_data(dir, "l2pol-default.json")}, script.MANUAL),
        # No Response from l3extRsPathL3OutAtt, Reponse from l3extVirtualLIfP result is MANUAL
        ({regular_api: [], floating_api: read_data(dir, "l3extVirtualLIfP.json"), l2Pols: read_data(dir, "l2pol-default.json")}, script.MANUAL),
        # Response from l3extRsPathL3OutAtt and l3extVirtualLIfP result is MANUAL
        (
            {
                regular_api: read_data(dir, "l3extRsPathL3OutAtt.json"),
                floating_api: read_data(dir, "l3extVirtualLIfP.json"),
                l2Pols: read_data(dir, "l2pol-default.json"),
            },
            script.MANUAL,
        ),
        # Response from l3extRsPathL3OutAtt, Version too old for l3extVirtualLIfP, result is MANUAL
        (
            {
                regular_api: read_data(dir, "l3extRsPathL3OutAtt.json"),
                floating_api: read_data(dir, "l3extVirtualLIfP_unresolved.json"),
                l2Pols: read_data(dir, "l2pol-default.json"),
            },
            script.MANUAL,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.l3out_mtu_check(1, 1)
    assert result == expected_result
