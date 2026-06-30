import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "vzany_svcgraph_stretched_vrf_check"

# icurl query keys (in execution order)
vnsGraphInst_applied_query = 'vnsGraphInst.json?query-target-filter=eq(vnsGraphInst.configSt,"applied")&rsp-subtree=full'
fvCtx_query = "fvCtx.json?rsp-subtree=children&rsp-subtree-class=fvSiteAssociated&rsp-subtree-include=required"
vzRsAnyToCons_query = "vzRsAnyToCons.json"
vzRsAnyToProv_query = "vzRsAnyToProv.json"

XLATE_DN = (
    "uni/tn-Tenant1/mscGraphXlateCont/epgDefXlate-["
    "uni/tn-Tenant1/GraphInst_C-[uni/tn-Tenant1/brc-Contract1]"
    "-G-[uni/tn-Tenant1/AbsGraph-Graph1]"
    "-S-[uni/tn-Tenant1/ctx-VRF1]"
    "/NodeInst-FirstNode/LegVNode-0/EPgDef-consumer].json"
)


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result, expected_data, expected_msg",
    [
        # Target version missing -> MANUAL
        (
            {},
            "6.0(1a)",
            None,
            script.MANUAL,
            [],
            None,
        ),
        # Target version older than 6.1(4) -> PASS (version gate, no API calls)
        (
            {},
            "6.0(1a)",
            "6.1(3d)",
            script.PASS,
            [],
            None,
        ),
        # No applied service graphs -> PASS
        (
            {
                vnsGraphInst_applied_query: [],
            },
            "6.0(1a)",
            "6.1(4a)",
            script.PASS,
            [],
            None,
        ),
        # Applied SGs but no stretched VRFs -> PASS
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_with_consumer.json"),
                fvCtx_query: read_data(dir, "fvCtx_no_stretched_vrf.json"),
            },
            "6.0(1a)",
            "6.1(4a)",
            script.PASS,
            [],
            None,
        ),
        # Applied SGs + stretched VRFs but contract not in vzAny -> PASS
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_with_consumer.json"),
                fvCtx_query: read_data(dir, "fvCtx_stretched_vrf.json"),
                vzRsAnyToCons_query: [],
                vzRsAnyToProv_query: [],
            },
            "6.0(1a)",
            "6.1(4a)",
            script.PASS,
            [],
            None,
        ),
        # All conditions met, xlate present -> PASS
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_with_consumer.json"),
                fvCtx_query: read_data(dir, "fvCtx_stretched_vrf.json"),
                vzRsAnyToCons_query: read_data(dir, "vzRsAnyToCons_consumer.json"),
                vzRsAnyToProv_query: [],
                XLATE_DN: read_data(dir, "mscGraphXlateCont_with_xlate.json"),
            },
            "6.0(1a)",
            "6.1(4a)",
            script.PASS,
            [],
            None,
        ),
        # All conditions met, xlate missing -> FAIL_O
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_with_consumer.json"),
                fvCtx_query: read_data(dir, "fvCtx_stretched_vrf.json"),
                vzRsAnyToCons_query: read_data(dir, "vzRsAnyToCons_consumer.json"),
                vzRsAnyToProv_query: [],
                XLATE_DN: [],
            },
            "6.0(1a)",
            "6.1(4a)",
            script.FAIL_O,
            [["Tenant1", "VRF1", "Contract1", "Graph1", "Missing vnsEpgDefXlate for 1st node consumer leg"]],
            None,
        ),
        # Error querying applied service graphs -> ERROR
        (
            None,  # None signals exception on first icurl call
            "6.0(1a)",
            "6.1(4a)",
            script.ERROR,
            None,
            None,
        ),
    ],
)
def test_vzany_svcgraph_stretched_vrf_check(run_check, mock_icurl, cversion, tversion, expected_result, expected_data, expected_msg):
    """Test vzany_svcgraph_stretched_vrf_check with various scenarios"""
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        cversion=script.AciVersion(cversion),
    )
    assert result.result == expected_result
    if expected_data is not None:
        assert result.data == expected_data
    if expected_msg is not None:
        assert result.msg == expected_msg
