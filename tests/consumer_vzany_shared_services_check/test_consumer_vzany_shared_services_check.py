import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
fvCtx_query = "fvCtx.json?rsp-subtree=full&rsp-subtree-class=vzAny,vzRsAnyToCons"
provider_esg_query = "uni/tn-vzAny-consumer/ap-ap1/esg-esg2.json"
provider_epg_query = "uni/tn-vzAny-consumer/ap-ap1/epg-epg2-unmatched.json"
provider_instp_query = "uni/tn-vzAny-consumer/out-out2/instP-l3instp2.json"
global_contract_query = (
    'vzBrCP.json?query-target-filter=eq(vzBrCP.scope,"global")'
    '&rsp-subtree=children'
    '&rsp-subtree-class=vzRtAnyToCons,vzRtProv'
    '&rsp-subtree-include=required'
)
graph_query = (
    'vnsGraphInst.json?query-target-filter=eq(vnsGraphInst.configSt,"applied")'
    '&rsp-subtree=children&rsp-subtree-class=vnsNodeInst&rsp-subtree-include=required'
)

@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # 1. Target version missing -> MANUAL (TVER_MISSING)
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
            },
            "5.2(8f)",
            None,
            script.MANUAL,
        ),
        # 2. Target version below 5.3(2d) -> NA
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
            },
            "4.2(8f)",
            "5.2(9e)",
            script.NA,
        ),
        # 3. No vzAny consumers -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_no_consumers.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
            },
            "5.2(8f)",
            "5.3(3a)",
            script.PASS,
        ),
        # 4. Shared-service case crossing 5.3(2d) version line (Only EPG/External EPG providers) -> MANUAL
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                provider_epg_query: read_data(dir, "epg_epg2_unmatched.json"),
                provider_instp_query: read_data(dir, "instp_l3instp2.json"),
            },
            "5.2(8f)",
            "5.3(3a)",
            script.MANUAL,
        ),
        # 5. Provider VRF same as consumer (no shared service) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_same_vrf.json"),
                global_contract_query: read_data(dir, "global_contracts_same_vrf.json"),
                provider_epg_query: read_data(dir, "epg_epg2_unmatched.json"),
                provider_instp_query: read_data(dir, "instp_l3instp2.json"),
            },
            "5.2(8f)",
            "5.3(3a)",
            script.PASS,
        ),
        # 6. Shared service crossing 6.1(4) version line (EPG/InstP/ESG) -> MANUAL
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: read_data(dir, "global_contracts_shared.json"),
                graph_query: read_data(dir, "vnsGraphInst_redirect.json"),
                provider_epg_query: read_data(dir, "epg_epg2_unmatched.json"),
                provider_instp_query: read_data(dir, "instp_l3instp2.json"),
                provider_esg_query: read_data(dir, "esg_esg2.json"),
            },
            "5.0(2h)",
            "6.1(4b)",
            script.MANUAL,
        ),
        # 7. No global contracts (vzAny consumer exists) -> PASS
        (
            {
                fvCtx_query: read_data(dir, "fvCtx_consumer_shared.json"),
                global_contract_query: [],
            },
            "5.2(8f)",
            "5.4(3a)",
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.consumer_vzany_shared_services_check(
        1,
        1,
        script.AciVersion(cversion),
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result