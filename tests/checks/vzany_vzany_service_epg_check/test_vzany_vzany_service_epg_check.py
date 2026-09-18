import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "vzany_vzany_service_epg_check"

# icurl queries
vzRsSubjGraphAtts = "vzRsSubjGraphAtt.json"
vzRtAnys = "uni/tn-T1/brc-contract1.json"
vzRtAnys += "?query-target=children"
vzRtAnys += "&target-subtree-class=vzRtAnyToCons,vzRtAnyToProv"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # Target version missing
        (
            {
                vzRsSubjGraphAtts: read_data(dir, "vzRsSubjGraphAtt.json"),
                vzRtAnys: read_data(dir, "vzRtAny_vzAny_vzAny.json"),
            },
            "3.2(10e)",
            None,
            script.MANUAL,
        ),
        # Version not affected
        (
            {
                vzRsSubjGraphAtts: read_data(dir, "vzRsSubjGraphAtt.json"),
                vzRtAnys: read_data(dir, "vzRtAny_vzAny_vzAny.json"),
            },
            "3.2(10e)",
            "4.2(7f)",
            script.NA,
        ),
        # Version not affected
        (
            {
                vzRsSubjGraphAtts: read_data(dir, "vzRsSubjGraphAtt.json"),
                vzRtAnys: read_data(dir, "vzRtAny_vzAny_vzAny.json"),
            },
            "5.0(1e)",
            "5.2(8f)",
            script.NA,
        ),
        # vzAny-vzAny in one VRF
        (
            {
                vzRsSubjGraphAtts: read_data(dir, "vzRsSubjGraphAtt.json"),
                vzRtAnys: read_data(dir, "vzRtAny_vzAny_vzAny.json"),
            },
            "4.2(7s)",
            "5.2(8f)",
            script.FAIL_O,
        ),
        # vzAny-vzAny in two VRFs
        # vzAny as a provider is not supported for inter-VRF. The assumption is
        # the same contract with scope VRF is used for two different VRFs as
        # vzAny-vzAny on both VRFs individually.
        (
            {
                vzRsSubjGraphAtts: read_data(dir, "vzRsSubjGraphAtt.json"),
                vzRtAnys: read_data(dir, "vzRtAny_vzAny_vzAny_2_VRFs.json"),
            },
            "4.2(7s)",
            "5.2(8f)",
            script.FAIL_O,
        ),
        # vzAny prov only
        (
            {
                vzRsSubjGraphAtts: read_data(dir, "vzRsSubjGraphAtt.json"),
                vzRtAnys: read_data(dir, "vzRtAny_vzAny_prov_only.json"),
            },
            "4.2(7s)",
            "5.2(8f)",
            script.PASS,
        ),
        # vzAny prov in VRF A, vzAny cons in VRF B but not inter-VRF.
        # vzAny as a provider is not supported for inter-VRF. The assumption is
        # the same contract with scope VRF is used for two different VRFs as
        # vzAny prov only in VRF A and vzAny cons only in VRF B.
        # We do not consider a case where this is configured with a contract of
        # scope tenant/global as that's not a supported configuration.
        (
            {
                vzRsSubjGraphAtts: read_data(dir, "vzRsSubjGraphAtt.json"),
                vzRtAnys: read_data(dir, "vzRtAny_vzAny_prov_cons_diff_VRFs.json"),
            },
            "4.2(7s)",
            "5.2(8f)",
            script.PASS,
        ),
        # no vzAny
        (
            {
                vzRsSubjGraphAtts: read_data(dir, "vzRsSubjGraphAtt.json"),
                vzRtAnys: [],
            },
            "4.2(7s)",
            "5.2(8f)",
            script.PASS,
        ),
        # no SG
        (
            {
                vzRsSubjGraphAtts: [],
                vzRtAnys: [],
            },
            "4.2(7s)",
            "5.2(8f)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
