import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "consumer_vzany_shared_services_check"

# icurl queries
fvCtx_query = "fvCtx.json?rsp-subtree=full&rsp-subtree-class=vzRsAnyToCons"
esg_query = "fvESg.json"
aepg_query = "fvAEPg.json"
l3instp_query = "l3extInstP.json"
global_contract_query = (
    'vzBrCP.json?query-target-filter=eq(vzBrCP.scope,"global")'
    '&rsp-subtree=children'
    '&rsp-subtree-class=vzRtProv'
    '&rsp-subtree-include=required'
)
graph_query = (
    'vnsGraphInst.json?query-target-filter=eq(vnsGraphInst.configSt,"applied")'
    '&rsp-subtree=children&rsp-subtree-class=vnsNodeInst&rsp-subtree-include=required'
)


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # Target version missing -> MANUAL (TVER_MISSING)
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
            },
            "5.2(8f)",
            None,
            script.MANUAL,
        ),
        # Target version below 5.3(2d) -> NA
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
            },
            "4.2(8f)",
            "5.2(9e)",
            script.NA,
        ),
        # 5.2(8f) -> 6.0(2h) (no new rule expansion versions hit) -> NA
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
            },
            "5.2(8f)",
            "6.0(2h)",
            script.NA,
        ),
        # 5.3(2g) -> 6.0(9h) (no new rule expansion versions hit) -> NA
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
            },
            "5.3(2g)",
            "6.0(9h)",
            script.NA,
        ),
        # 6.1(2g) -> 6.1(4h) (no new expansion; already past ESG threshold) -> NA
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
                esg_query: read_data(dir, "esg_esg2.json"),
            },
            "6.1(2g)",
            "6.1(4h)",
            script.NA,
        ),
        # 5.2(8f) -> 5.3(3a) (EPG expansion boundary crossed, but only ESG providers present) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_esg_only.json"),
                esg_query: read_data(dir, "esg_esg2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "5.2(8f)",
            "5.3(3a)",
            script.PASS,
        ),
        # 5.2(8f) -> 6.0(5a) (EPG expansion boundary crossed, but only ESG providers present) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_esg_only.json"),
                esg_query: read_data(dir, "esg_esg2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "5.2(8f)",
            "6.0(5a)",
            script.PASS,
        ),
        # 6.0(2h) -> 6.0(5a) (EPG expansion boundary crossed, but only ESG providers present) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_esg_only.json"),
                esg_query: read_data(dir, "esg_esg2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "6.0(2h)",
            "6.0(5a)",
            script.PASS,
        ),
        # 5.3(2g) -> 6.1(2g) (ESG expansion boundary crossed, but only EPG/InstP providers present) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_epg_only.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "5.3(2g)",
            "6.1(2g)",
            script.PASS,
        ),
        # 6.0(5a) -> 6.1(2g) (ESG expansion boundary crossed, but only EPG/InstP providers present) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_epg_only.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "6.0(5a)",
            "6.1(2g)",
            script.PASS,
        ),
        # 5.2(8f) -> 5.3(3a) (EPG expansion boundary crossed with relevant providers present) -> MANUAL
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "5.2(8f)",
            "5.3(3a)",
            script.MANUAL,
        ),
        # 5.2(8f) -> 6.0(5a) (EPG expansion boundary crossed with relevant providers present) -> MANUAL
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "5.2(8f)",
            "6.0(5a)",
            script.MANUAL,
        ),
        # 6.0(2h) -> 6.0(5a) (EPG expansion boundary crossed with relevant providers present) -> MANUAL
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "6.0(2h)",
            "6.0(5a)",
            script.MANUAL,
        ),
        # 5.3(2g) -> 6.1(2g) (ESG expansion boundary crossed with relevant providers present) -> MANUAL
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
                esg_query: read_data(dir, "esg_esg2.json"),
            },
            "5.3(2g)",
            "6.1(2g)",
            script.MANUAL,
        ),
        # 6.0(9h) -> 6.1(2g) (ESG expansion boundary crossed with relevant providers present) -> MANUAL
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
                esg_query: read_data(dir, "esg_esg2.json"),
            },
            "6.0(9h)",
            "6.1(2g)",
            script.MANUAL,
        ),
        # Shared service crossing 6.1(4) version line (EPG/InstP/ESG) -> MANUAL without PBR warning
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
                esg_query: read_data(dir, "esg_esg2.json"),
            },
            "5.0(2h)",
            "6.1(4b)",
            script.MANUAL,
        ),
        # No vzAny consumers -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_no_consumers.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
            },
            "5.2(8f)",
            "6.1(4h)",
            script.PASS,
        ),
        # No global contracts (vzAny consumer exists) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: [],
            },
            "5.2(8f)",
            "6.1(4h)",
            script.PASS,
        ),
        # Provider VRF same as consumer (no shared service) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_same_vrf.json"),
                global_contract_query: read_data(dir, "global_contracts_same_vrf.json"),
                aepg_query: read_data(dir, "epg_epg2_unmatched.json"),
                l3instp_query: read_data(dir, "instp_l3instp2.json"),
                esg_query: read_data(dir, "esg_esg2.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
            },
            "5.2(8f)",
            "6.1(4h)",
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
