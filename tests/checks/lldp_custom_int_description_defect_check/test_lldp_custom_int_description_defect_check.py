import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "lldp_custom_int_description_defect_check"

# icurl queries
infraPortBlks = 'infraPortBlk.json?query-target-filter=ne(infraPortBlk.descr,"")&rsp-subtree-include=count'
fvRsDomAtts = 'fvRsDomAtt.json?query-target-filter=and(eq(fvRsDomAtt.tCl,"vmmDomP"),eq(fvRsDomAtt.resImedcy,"lazy"))&rsp-subtree-include=count'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            {
                infraPortBlks: read_data(dir, "infraPortBlk_pos.json"),
                fvRsDomAtts: read_data(dir, "fvRsDomAtt_pos.json"),
            },
            "6.0(2d)",
            script.FAIL_O,
        ),
        (
            {
                infraPortBlks: read_data(dir, "infraPortBlk_pos.json"),
                fvRsDomAtts: read_data(dir, "fvRsDomAtt_pos.json"),
            },
            "6.0(1e)",
            script.FAIL_O,
        ),
        (
            {
                infraPortBlks: read_data(dir, "infraPortBlk_pos.json"),
                fvRsDomAtts: read_data(dir, "fvRsDomAtt_pos.json"),
            },
            "6.0(4d)",
            script.PASS,
        ),
        (
            {
                infraPortBlks: read_data(dir, "infraPortBlk_pos.json"),
                fvRsDomAtts: read_data(dir, "fvRsDomAtt_pos.json"),
            },
            "4.2(7d)",
            script.PASS,
        ),
        (
            {
                infraPortBlks: read_data(dir, "infraPortBlk_pos.json"),
                fvRsDomAtts: read_data(dir, "fvRsDomAtt_neg.json"),
            },
            "6.0(2a)",
            script.PASS,
        ),
        (
            {
                infraPortBlks: read_data(dir, "infraPortBlk_neg.json"),
                fvRsDomAtts: read_data(dir, "fvRsDomAtt_pos.json"),
            },
            "6.0(2a)",
            script.PASS,
        ),
        (
            {
                infraPortBlks: read_data(dir, "infraPortBlk_neg.json"),
                fvRsDomAtts: read_data(dir, "fvRsDomAtt_neg.json"),
            },
            "6.0(2a)",
            script.PASS,
        ),
        (
            {
                infraPortBlks: read_data(dir, "infraPortBlk_neg.json"),
                fvRsDomAtts: read_data(dir, "fvRsDomAtt_neg.json"),
            },
            "5.2(5d)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion))
    assert result.result == expected_result
