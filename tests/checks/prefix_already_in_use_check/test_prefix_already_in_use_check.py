import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "prefix_already_in_use_check"

# icurl queries
faultInst = 'faultInst.json?query-target-filter=and(wcard(faultInst.changeSet,"prefix-entry-already-in-use"),wcard(faultInst.dn,"uni/epp/rtd"))'
fvCtx = "fvCtx.json"
l3extRsEctx = "l3extRsEctx.json"
l3extSubnet = "l3extSubnet.json"


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # fault before CSCvq93592
        (
            {
                faultInst: read_data(
                    dir, "faultInst_F0467_prefix-entry-already-in-use_old.json"
                ),
                fvCtx: read_data(dir, "fvCtx.json"),
                l3extRsEctx: read_data(dir, "l3extRsEctx.json"),
                l3extSubnet: read_data(dir, "l3extSubnet_overlap.json"),
            },
            script.FAIL_O,
        ),
        # fault after CSCvq93592
        (
            {
                faultInst: read_data(
                    dir, "faultInst_F0467_prefix-entry-already-in-use_new.json"
                ),
                fvCtx: read_data(dir, "fvCtx.json"),
                l3extRsEctx: read_data(dir, "l3extRsEctx.json"),
                l3extSubnet: read_data(dir, "l3extSubnet_overlap.json"),
            },
            script.FAIL_O,
        ),
        (
            {
                faultInst: [],
                fvCtx: read_data(dir, "fvCtx.json"),
                l3extRsEctx: read_data(dir, "l3extRsEctx.json"),
                l3extSubnet: read_data(dir, "l3extSubnet_no_overlap.json"),
            },
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, expected_result):
    result = run_check()
    assert result.result == expected_result
