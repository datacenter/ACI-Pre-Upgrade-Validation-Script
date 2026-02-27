import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "internal_vlanpool_check"

# icurl queries
fvnsVlanInstPs = "fvnsVlanInstP.json?rsp-subtree=children&rsp-subtree-class=fvnsRtVlanNs,fvnsEncapBlk&rsp-subtree-include=required"
vmmDomPs = "vmmDomP.json"


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_pos.json"),
                vmmDomPs: read_data(dir, "vmmDomP_pos.json"),
            },
            "5.2(2a)",
            script.FAIL_O,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_pos.json"),
                vmmDomPs: read_data(dir, "vmmDomP_pos.json"),
            },
            "4.2(4d)",
            script.PASS,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_pos.json"),
                vmmDomPs: read_data(dir, "vmmDomP_pos.json"),
            },
            "5.2(6a)",
            script.FAIL_O,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_pos.json"),
                vmmDomPs: read_data(dir, "vmmDomP_pos.json"),
            },
            "4.2(7d)",
            script.FAIL_O,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_pos.json"),
                vmmDomPs: read_data(dir, "vmmDomP_pos.json"),
            },
            "2.2(4r)",
            script.PASS,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_neg.json"),
                vmmDomPs: read_data(dir, "vmmDomP_neg.json"),
            },
            "5.2(2a)",
            script.PASS,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_neg.json"),
                vmmDomPs: read_data(dir, "vmmDomP_neg.json"),
            },
            "4.2(4d)",
            script.PASS,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_neg.json"),
                vmmDomPs: read_data(dir, "vmmDomP_neg.json"),
            },
            "5.2(6a)",
            script.PASS,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_neg.json"),
                vmmDomPs: read_data(dir, "vmmDomP_neg.json"),
            },
            "4.2(7d)",
            script.PASS,
        ),
        (
            {
                fvnsVlanInstPs: read_data(dir, "fvnsVlanInstP_neg.json"),
                vmmDomPs: read_data(dir, "vmmDomP_neg.json"),
            },
            "2.2(4r)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion))
    assert result.result == expected_result
