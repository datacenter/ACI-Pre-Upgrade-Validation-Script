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
_graph_subtree = "&rsp-subtree=full&rsp-subtree-class=vnsNodeInst,vnsTermNodeInst,vnsConnectionInst,vnsRsConnectionInstConns"
# cversion < 6.1(4): scoped to applied graphs
vnsGraphInst_applied_query = 'vnsGraphInst.json?query-target-filter=eq(vnsGraphInst.configSt,"applied")' + _graph_subtree
# cversion >= 6.1(4): all graph states (catches failed-to-apply on re-render)
vnsGraphInst_all_query = "vnsGraphInst.json?" + _graph_subtree.lstrip("&")
fvCtx_query = "fvCtx.json?rsp-subtree=children&rsp-subtree-class=fvSiteAssociated&rsp-subtree-include=required"
vzRsAnyToCons_query = "vzRsAnyToCons.json"
vzRsAnyToProv_query = "vzRsAnyToProv.json"

# Graph instance DN reused across fixtures (VRF1 scope)
GI_DN_VRF1 = (
    "uni/tn-Tenant1/GraphInst_C-[uni/tn-Tenant1/brc-Contract1]"
    "-G-[uni/tn-Tenant1/AbsGraph-Graph1]-S-[uni/tn-Tenant1/ctx-VRF1]"
)
# Graph instance DN with no parseable -S-[...] scope
GI_DN_NO_SCOPE = (
    "uni/tn-Tenant1/GraphInst_C-[uni/tn-Tenant1/brc-Contract1]"
    "-G-[uni/tn-Tenant1/AbsGraph-Graph1]"
)

XLATE_DN = (
    "uni/tn-Tenant1/mscGraphXlateCont/epgDefXlate-["
    "uni/tn-Tenant1/GraphInst_C-[uni/tn-Tenant1/brc-Contract1]"
    "-G-[uni/tn-Tenant1/AbsGraph-Graph1]"
    "-S-[uni/tn-Tenant1/ctx-VRF1]"
    "/NodeInst-FirstNode/LegVNode-0/EPgDef-consumer].json"
)
XLATE_DN_VRF2 = (
    "uni/tn-Tenant1/mscGraphXlateCont/epgDefXlate-["
    "uni/tn-Tenant1/GraphInst_C-[uni/tn-Tenant1/brc-Contract1]"
    "-G-[uni/tn-Tenant1/AbsGraph-Graph1]"
    "-S-[uni/tn-Tenant1/ctx-VRF2]"
    "/NodeInst-FirstNode/LegVNode-0/EPgDef-consumer].json"
)


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result, expected_data, expected_unformatted, expected_msg",
    [
        # Target version missing -> MANUAL
        (
            {},
            "6.0(1a)",
            None,
            script.MANUAL,
            [],
            None,
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
            None,
        ),
        # No service graphs -> PASS
        (
            {
                vnsGraphInst_applied_query: [],
            },
            "6.0(1a)",
            "6.1(4a)",
            script.PASS,
            [],
            None,
            None,
        ),
        # PBR SGs but no stretched VRFs -> PASS
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
            None,
        ),
        # PBR SGs + stretched VRFs but contract not in vzAny -> PASS
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
            None,
        ),
        # Non-PBR graph (routingMode unspecified) -> skipped -> PASS
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_non_pbr.json"),
            },
            "6.0(1a)",
            "6.1(4a)",
            script.PASS,
            [],
            None,
            None,
        ),
        # NDO/MSC-managed graph (orchestrator:msc annotation) -> skipped -> PASS
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_ndo_managed.json"),
            },
            "6.0(1a)",
            "6.1(4a)",
            script.PASS,
            [],
            None,
            None,
        ),
        # cversion >= 6.1(4): polls all graph states, xlate missing -> FAIL_O
        (
            {
                vnsGraphInst_all_query: read_data(dir, "vnsGraphInst_with_consumer.json"),
                fvCtx_query: read_data(dir, "fvCtx_stretched_vrf.json"),
                vzRsAnyToCons_query: read_data(dir, "vzRsAnyToCons_consumer.json"),
                vzRsAnyToProv_query: [],
                XLATE_DN: [],
            },
            "6.1(4a)",
            "6.1(5a)",
            script.FAIL_O,
            [["Tenant1", "VRF1", "Contract1", "Graph1", "Missing vnsEpgDefXlate for 1st node consumer leg"]],
            None,
            None,
        ),
        # Two stretched VRFs share one contract, only VRF2 missing xlate -> FAIL_O identifies VRF2
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_two_vrfs.json"),
                fvCtx_query: read_data(dir, "fvCtx_two_stretched_vrfs.json"),
                vzRsAnyToCons_query: read_data(dir, "vzRsAnyToCons_two_vrfs.json"),
                vzRsAnyToProv_query: [],
                XLATE_DN: read_data(dir, "mscGraphXlateCont_with_xlate.json"),
                XLATE_DN_VRF2: [],
            },
            "6.0(1a)",
            "6.1(4a)",
            script.FAIL_O,
            [["Tenant1", "VRF2", "Contract1", "Graph1", "Missing vnsEpgDefXlate for 1st node consumer leg"]],
            None,
            None,
        ),
        # First consumer node cannot be determined -> ERROR with retained evidence
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_no_firstnode.json"),
                fvCtx_query: read_data(dir, "fvCtx_stretched_vrf.json"),
                vzRsAnyToCons_query: read_data(dir, "vzRsAnyToCons_consumer.json"),
                vzRsAnyToProv_query: [],
            },
            "6.0(1a)",
            "6.1(4a)",
            script.ERROR,
            [],
            [[GI_DN_VRF1, "Unable to determine the first consumer node"]],
            None,
        ),
        # Graph instance missing contract DN -> ERROR with retained evidence
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_no_contract.json"),
            },
            "6.0(1a)",
            "6.1(4a)",
            script.ERROR,
            [],
            [[GI_DN_VRF1, "Service graph instance missing contract DN (ctrctDn)"]],
            None,
        ),
        # Graph instance with unparseable VRF scope -> ERROR with retained evidence
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_bad_scope.json"),
            },
            "6.0(1a)",
            "6.1(4a)",
            script.ERROR,
            [],
            [[GI_DN_NO_SCOPE, "Unable to parse the VRF scope from the graph instance DN"]],
            None,
        ),
        # Malformed vzAny relationship DN -> ERROR with retained evidence
        (
            {
                vnsGraphInst_applied_query: read_data(dir, "vnsGraphInst_with_consumer.json"),
                fvCtx_query: read_data(dir, "fvCtx_stretched_vrf.json"),
                vzRsAnyToCons_query: read_data(dir, "vzRsAnyToCons_bad_dn.json"),
                vzRsAnyToProv_query: [],
            },
            "6.0(1a)",
            "6.1(4a)",
            script.ERROR,
            [],
            [["uni/tn-Tenant1/malformed-rsanyToCons", "Unable to parse the VRF scope from the vzRsAnyToCons DN"]],
            None,
        ),
        # Error querying service graphs -> ERROR
        (
            None,  # None signals exception on first icurl call
            "6.0(1a)",
            "6.1(4a)",
            script.ERROR,
            None,
            None,
            None,
        ),
    ],
)
def test_vzany_svcgraph_stretched_vrf_check(run_check, mock_icurl, cversion, tversion, expected_result, expected_data, expected_unformatted, expected_msg):
    """Test vzany_svcgraph_stretched_vrf_check with various scenarios"""
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        cversion=script.AciVersion(cversion),
    )
    assert result.result == expected_result
    if expected_data is not None:
        assert result.data == expected_data
    if expected_unformatted is not None:
        assert result.unformatted_headers == ["Graph Instance DN", "Issue"]
        assert result.unformatted_data == expected_unformatted
    if expected_msg is not None:
        assert result.msg == expected_msg
