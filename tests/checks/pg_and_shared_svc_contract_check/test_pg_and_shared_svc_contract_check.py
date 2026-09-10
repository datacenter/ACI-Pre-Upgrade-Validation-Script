import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "pg_and_shared_svc_contract_check"

# icurl queries
# shared contracts
shrd_contracts_api = 'vzBrCP.json'
shrd_contracts_api += '?query-target-filter=or(eq(vzBrCP.scope,"global"),eq(vzBrCP.scope,"tenant"))'

# global epgs (17 <= pcTag <= 16385) with Preferred Group enabled and provided contracts

glbl_epgs_api = 'fvAEPg.json'
glbl_epgs_api += '?query-target-filter=and(le(fvAEPg.pcTag,"16385"),ge(fvAEPg.pcTag,"17"),eq(fvAEPg.prefGrMemb,"include"))'
glbl_epgs_api += '&rsp-subtree=children&rsp-subtree-class=fvRsProv'

# global external EPGs (17 <= pcTag <= 16385) with Preferred Group enabled and provided contracts

glbl_ext_epgs_api = 'l3extInstP.json'
glbl_ext_epgs_api += '?query-target-filter=and(le(l3extInstP.pcTag,"16385"),ge(l3extInstP.pcTag,"17"),eq(l3extInstP.prefGrMemb,"include"))'
glbl_ext_epgs_api += '&rsp-subtree=children&rsp-subtree-class=fvRsProv'

ctx_defs_api = 'fvCtxDef.json'
provider_relationships_api = 'vzFromEPg.json'
provider_relationships_api += '?query-target-filter=and(eq(vzFromEPg.membType,"prov"),'
provider_relationships_api += 'le(vzFromEPg.pcTag,"16385"),ge(vzFromEPg.pcTag,"17"))'
provider_relationships_api += '&rsp-subtree=children&rsp-subtree-class=vzToEPg'

childless_fvAEPg = {
    "fvAEPg": {
        "attributes": {
            "dn": "uni/tn-test/ap-test/epg-no-provider",
            "pcTag": "100"
        }
    }
}
childless_l3extInstP = {
    "l3extInstP": {
        "attributes": {
            "dn": "uni/tn-test/out-test/instP-no-provider",
            "pcTag": "101"
        }
    }
}
provider_dn = "uni/tn-common/ap-apptest/epg-epg1"
provider_scope = "2261001"
provider_ctx_def_dn = "uni/ctx-[uni/tn-common/ctx-provider]"
external_provider_dn = "uni/tn-common/out-test-L3Out/instP-testExtEPG"
external_provider_scope = "2490368"
external_provider_ctx_def_dn = "uni/ctx-[uni/tn-common/ctx-external-provider]"
ordinary_consumer_dn = "uni/tn-consumer/ap-app/epg-consumer"
different_vrf_l3out_consumer_dn = "uni/tn-consumer/out-consumer/instP-different-vrf"
same_vrf_l3out_consumer_dn = "uni/tn-consumer/out-consumer/instP-same-vrf"
different_ctx_def_dn = "uni/ctx-[uni/tn-consumer/ctx-consumer]"


def ctx_def(scope, ctx_def_dn):
    return {
        "fvCtxDef": {
            "attributes": {
                "dn": ctx_def_dn,
                "scope": scope
            }
        }
    }


def provider_relationship(
    contract,
    provider,
    provider_scope_id,
    consumer,
    consumer_ctx_def_dn,
    consumer_scope_id="999"
):
    return {
        "vzFromEPg": {
            "attributes": {
                "dn": "cdef-[{}]/epgCont-[{}]/fr-[provider]".format(
                    contract,
                    provider
                ),
                "epgDn": provider,
                "membType": "prov",
                "scopeId": provider_scope_id
            },
            "children": [
                {
                    "vzToEPg": {
                        "attributes": {
                            "ctxDefDn": consumer_ctx_def_dn,
                            "dn": (
                                "cdef-[{}]/epgCont-[{}]/fr-[provider]/"
                                "to-[{}]"
                            ).format(contract, provider, consumer),
                            "epgDn": consumer,
                            "scopeId": consumer_scope_id
                        }
                    }
                }
            ]
        }
    }


provider_ctx_defs = [
    ctx_def(provider_scope, provider_ctx_def_dn),
    ctx_def(external_provider_scope, external_provider_ctx_def_dn)
]
cross_context_ordinary_relationship = provider_relationship(
    "uni/tn-common/brc-AD_C",
    provider_dn,
    provider_scope,
    ordinary_consumer_dn,
    different_ctx_def_dn
)
same_context_ordinary_relationship = provider_relationship(
    "uni/tn-common/brc-AD_C",
    provider_dn,
    provider_scope,
    ordinary_consumer_dn,
    provider_ctx_def_dn,
    provider_scope
)
cross_context_l3out_relationship = provider_relationship(
    "uni/tn-common/brc-AD_C",
    provider_dn,
    provider_scope,
    different_vrf_l3out_consumer_dn,
    different_ctx_def_dn
)
same_context_l3out_relationship = provider_relationship(
    "uni/tn-common/brc-AD_C",
    provider_dn,
    provider_scope,
    same_vrf_l3out_consumer_dn,
    provider_ctx_def_dn,
    provider_scope
)
external_provider_l3out_relationship = provider_relationship(
    "uni/tn-common/brc-AD_C",
    external_provider_dn,
    external_provider_scope,
    different_vrf_l3out_consumer_dn,
    different_ctx_def_dn
)
tenant_contract = {
    "vzBrCP": {
        "attributes": {
            "dn": "uni/tn-test/brc-tenant-shared",
            "name": "tenant-shared",
            "scope": "tenant"
        }
    }
}
tenant_provider = {
    "fvAEPg": {
        "attributes": {
            "dn": "uni/tn-test/ap-provider/epg-provider",
            "pcTag": "102",
            "scope": "1000"
        },
        "children": [
            {
                "fvRsProv": {
                    "attributes": {
                        "tDn": "uni/tn-test/brc-tenant-shared"
                    }
                }
            }
        ]
    }
}
tenant_provider_ctx_def_dn = "uni/ctx-[uni/tn-test/ctx-provider]"
tenant_consumer_ctx_def_dn = "uni/ctx-[uni/tn-test/ctx-consumer]"
tenant_l3out_consumer_dn = "uni/tn-test/out-consumer/instP-consumer"
tenant_vzany_consumer_dn = "uni/tn-test/ctx-consumer/any"
tenant_mismatch_consumer_dn = "uni/tn-other/out-consumer/instP-consumer"
tenant_ctx_defs = [
    ctx_def("1000", tenant_provider_ctx_def_dn)
]
tenant_l3out_relationship = provider_relationship(
    "uni/tn-test/brc-tenant-shared",
    "uni/tn-test/ap-provider/epg-provider",
    "1000",
    tenant_l3out_consumer_dn,
    tenant_consumer_ctx_def_dn,
    "2000"
)
tenant_vzany_relationship = provider_relationship(
    "uni/tn-test/brc-tenant-shared",
    "uni/tn-test/ap-provider/epg-provider",
    "1000",
    tenant_vzany_consumer_dn,
    tenant_consumer_ctx_def_dn,
    "2000"
)
tenant_mismatch_relationship = provider_relationship(
    "uni/tn-test/brc-tenant-shared",
    "uni/tn-test/ap-provider/epg-provider",
    "1000",
    tenant_mismatch_consumer_dn,
    "uni/ctx-[uni/tn-other/ctx-consumer]",
    "3000"
)


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [

        # MANUAL cases
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json"),
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [cross_context_ordinary_relationship]
            },
            "4.2(4a)", None,
            script.MANUAL,
        ),
        # NA cases
        # Target version is lower than 4.2, Result = NA
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json"),
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [cross_context_ordinary_relationship]
            },
            "4.2(1a)", "4.1(2a)",
            script.NA,
        ),
        # Target version predates Preferred Group-specific F0467 enforcement,
        # but the forwarding risk is still present.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json"),
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [cross_context_ordinary_relationship]
            },
            "4.2(1a)", "5.1(1g)",
            script.FAIL_O,
        ),
        # There are no global contracts, Result = NA
        (
            {
                shrd_contracts_api: [],
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "6.1(1g)",
            script.NA,
        ),
        # FAIL_O Cases
        # Target version is older than 6.0(1g), Result = FAIL_O
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json"),
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [cross_context_ordinary_relationship]
            },
            "4.2(1a)", "6.0(1f)",
            script.FAIL_O,
        ),
        # Tenant-scope contracts carry the same broad forwarding risk through 5.2.
        (
            {
                shrd_contracts_api: [tenant_contract],
                glbl_epgs_api: [tenant_provider],
                glbl_ext_epgs_api: [],
                ctx_defs_api: tenant_ctx_defs,
                provider_relationships_api: [tenant_l3out_relationship]
            },
            "4.2(1a)", "5.2(8i)",
            script.FAIL_O,
        ),
        # Target version is newer than 6.0(1g), both global_pg EPGs and extEPGs , Result = FAIL_O
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json"),
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [cross_context_l3out_relationship]
            },
            "4.2(1a)", "6.0(1g)",
            script.FAIL_O,
        ),
        # Target version is newer than 6.0(1g), no EPGS, only global_pg extEPGs , Result = FAIL_O
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [],
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json"),
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [external_provider_l3out_relationship]
            },
            "4.2(1a)", "6.0(1g)",
            script.FAIL_O,
        ),
        # A childless fvAEPg does not hide a later affected fvAEPg.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [childless_fvAEPg] + read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: [],
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [cross_context_ordinary_relationship]
            },
            "4.2(1a)", "5.2(8i)",
            script.FAIL_O,
        ),
        # A childless l3extInstP does not hide a later affected l3extInstP.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [],
                glbl_ext_epgs_api: [childless_l3extInstP] + read_data(dir, "global_pg_l3extInstP.json"),
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [external_provider_l3out_relationship]
            },
            "4.2(1a)", "6.0(1g)",
            script.FAIL_O,
        ),
        # PASS Cases
        # Target version is older than 6.0(1g), no global_pg EPGs or extEPGs , Result = PASS
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [],
                glbl_ext_epgs_api: []
            },
            "4.2(1a)", "6.0(1f)",
            script.PASS,
        ),
        # Target version is newer than 6.0(1g), no global_pg EPGs or extEPGs , Result = PASS
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [],
                glbl_ext_epgs_api: []
            },
            "4.2(1a)", "6.0(1h)",
            script.PASS,
        ),
        # Target version is newer than 6.0(1g), only global_pg EPGs , no global_pg extEPGs , Result = PASS
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: [],
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: []
            },
            "4.2(1a)", "6.0(1h)",
            script.PASS,
        ),
        # Preferred-group objects without provider children are not affected.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [childless_fvAEPg],
                glbl_ext_epgs_api: [childless_l3extInstP]
            },
            "4.2(1a)", "5.2(8i)",
            script.PASS,
        ),
        # No L3Out consumer means an ordinary EPG consumer cannot trigger this check.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: [],
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [cross_context_ordinary_relationship]
            },
            "4.2(1a)", "6.0(1g)",
            script.PASS,
        ),
        # A same-VRF L3Out consumer does not trigger the cross-VRF restriction.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [read_data(dir, "global_pg_fvAEPg.json")[0]],
                glbl_ext_epgs_api: [],
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: [same_context_l3out_relationship]
            },
            "4.2(1a)", "6.0(1g)",
            script.PASS,
        ),
        # Unrelated L3Out and vzAny consumers do not affect the provider.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: [],
                ctx_defs_api: provider_ctx_defs,
                provider_relationships_api: []
            },
            "4.2(1a)", "6.0(1g)",
            script.PASS,
        ),
    ]
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None
    )
    assert result.result == expected_result


def test_provider_queries_exclude_reserved_and_local_pctags(run_check, monkeypatch):
    queries = []

    def recording_icurl(apitype, query, page=0, page_size=100000):
        queries.append(query)
        if query == shrd_contracts_api:
            return [tenant_contract]
        return []

    monkeypatch.setattr(script, "icurl", recording_icurl)

    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("5.2(8i)")
    )

    assert result.result == script.PASS
    assert queries == [shrd_contracts_api, glbl_epgs_api, glbl_ext_epgs_api]
    assert 'ge(fvAEPg.pcTag,"17")' in glbl_epgs_api
    assert 'le(fvAEPg.pcTag,"16385")' in glbl_epgs_api
    assert 'ge(l3extInstP.pcTag,"17")' in glbl_ext_epgs_api
    assert 'le(l3extInstP.pcTag,"16385")' in glbl_ext_epgs_api
    assert 'ge(vzFromEPg.pcTag,"17")' in provider_relationships_api
    assert 'le(vzFromEPg.pcTag,"16385")' in provider_relationships_api


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
            glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json"),
            ctx_defs_api: provider_ctx_defs,
            provider_relationships_api: [cross_context_l3out_relationship]
        }
    ]
)
@pytest.mark.parametrize(
    "tversion",
    [
        "4.2(5n)",
        "4.2(6d)",
        "5.1(1h)",
        "5.1(3e)",
        "5.2(1g)",
        "5.2(8i)",
        "6.0(1g)",
    ]
)
def test_all_4_2_and_newer_targets_are_checked(run_check, mock_icurl, tversion):
    result = run_check(
        cversion=script.AciVersion("4.2(1a)"),
        tversion=script.AciVersion(tversion)
    )
    assert result.result not in (script.NA, script.ERROR)


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: [read_data(dir, "global_pg_fvAEPg.json")[0]],
            glbl_ext_epgs_api: [],
            ctx_defs_api: provider_ctx_defs,
            provider_relationships_api: [cross_context_l3out_relationship]
        }
    ]
)
def test_reports_correlated_l3out_consumer(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("6.0(1g)")
    )

    assert result.result == script.FAIL_O
    assert result.data == [[
        "uni/tn-common/brc-AD_C",
        "uni/tn-common/ap-apptest/epg-epg1",
        "5555",
        "uni/tn-consumer/out-consumer/instP-different-vrf"
    ]]
    assert "remove each listed provider from the Preferred Group" in result.recommended_action
    assert "stop it from providing the listed shared-service contract" in result.recommended_action
    assert "remove the unsupported L3Out/vzAny consumer relationship" in result.recommended_action
    assert "F0467 or F4684" in result.recommended_action
    assert result.doc_url.endswith("/#preferred-group-shared-service-provider")


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: [tenant_contract],
            glbl_epgs_api: [tenant_provider],
            glbl_ext_epgs_api: [],
            ctx_defs_api: tenant_ctx_defs,
            provider_relationships_api: [tenant_l3out_relationship]
        }
    ]
)
def test_reports_tenant_scope_contract_across_vrfs(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("6.0(1g)")
    )

    assert result.result == script.FAIL_O
    assert result.data == [[
        "uni/tn-test/brc-tenant-shared",
        "uni/tn-test/ap-provider/epg-provider",
        "102",
        "uni/tn-test/out-consumer/instP-consumer"
    ]]


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: [tenant_contract],
            glbl_epgs_api: [tenant_provider],
            glbl_ext_epgs_api: [],
            ctx_defs_api: tenant_ctx_defs,
            provider_relationships_api: [tenant_vzany_relationship]
        }
    ]
)
def test_reports_correlated_vzany_consumer(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("6.0(1g)")
    )

    assert result.result == script.FAIL_O
    assert result.data == [[
        "uni/tn-test/brc-tenant-shared",
        "uni/tn-test/ap-provider/epg-provider",
        "102",
        "uni/tn-test/ctx-consumer/any"
    ]]


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: [tenant_contract],
            glbl_epgs_api: [tenant_provider],
            glbl_ext_epgs_api: [],
            ctx_defs_api: tenant_ctx_defs,
            provider_relationships_api: [provider_relationship(
                "uni/tn-test/brc-tenant-shared",
                "uni/tn-test/ap-provider/epg-provider",
                "1000",
                tenant_vzany_consumer_dn,
                tenant_provider_ctx_def_dn,
                "1000"
            )]
        }
    ]
)
def test_same_context_vzany_consumer_is_not_reported(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("6.0(1g)")
    )

    assert result.result == script.PASS


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: [tenant_contract],
            glbl_epgs_api: [tenant_provider],
            glbl_ext_epgs_api: [],
            ctx_defs_api: tenant_ctx_defs,
            provider_relationships_api: [tenant_mismatch_relationship]
        }
    ]
)
def test_tenant_scope_relationship_requires_matching_tenant(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("6.0(1g)")
    )

    assert result.result == script.PASS


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: [read_data(dir, "global_pg_fvAEPg.json")[0]],
            glbl_ext_epgs_api: [],
            ctx_defs_api: provider_ctx_defs,
            provider_relationships_api: []
        }
    ]
)
def test_provider_without_materialized_relationship_is_not_reported(
    run_check,
    mock_icurl
):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("5.2(8i)")
    )

    assert result.result == script.PASS


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: [read_data(dir, "global_pg_fvAEPg.json")[0]],
            glbl_ext_epgs_api: [],
            ctx_defs_api: provider_ctx_defs,
            provider_relationships_api: [same_context_ordinary_relationship]
        }
    ]
)
def test_same_context_relationship_is_not_reported_before_6_0(
    run_check,
    mock_icurl
):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("5.2(8i)")
    )

    assert result.result == script.PASS


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: [read_data(dir, "global_pg_fvAEPg.json")[0]],
            glbl_ext_epgs_api: [],
            ctx_defs_api: [],
            provider_relationships_api: [cross_context_l3out_relationship]
        }
    ]
)
def test_missing_provider_context_is_an_error(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("6.0(1g)")
    )

    assert result.result == script.ERROR
    assert result.msg == (
        "Unable to resolve context for one or more derived contract relationships"
    )
    assert result.data == [[
        (
            "cdef-[uni/tn-common/brc-AD_C]/"
            "epgCont-[uni/tn-common/ap-apptest/epg-epg1]/fr-[provider]"
        ),
        "No fvCtxDef found for scopeId 2261001"
    ]]
    assert "Retry the check" in result.recommended_action
    assert "contact Cisco TAC" in result.recommended_action


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: [read_data(dir, "global_pg_fvAEPg.json")[0]],
            glbl_ext_epgs_api: [],
            ctx_defs_api: provider_ctx_defs,
            provider_relationships_api: [provider_relationship(
                "uni/tn-common/brc-AD_C",
                provider_dn,
                provider_scope,
                different_vrf_l3out_consumer_dn,
                ""
            )]
        }
    ]
)
def test_missing_consumer_context_is_an_error(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("6.0(1g)")
    )

    assert result.result == script.ERROR
    assert result.msg == (
        "Unable to resolve context for one or more derived contract relationships"
    )
    assert result.data == [[
        (
            "cdef-[uni/tn-common/brc-AD_C]/"
            "epgCont-[uni/tn-common/ap-apptest/epg-epg1]/fr-[provider]/"
            "to-[uni/tn-consumer/out-consumer/instP-different-vrf]"
        ),
        "vzToEPg.ctxDefDn is empty"
    ]]
    assert "Retry the check" in result.recommended_action
    assert "contact Cisco TAC" in result.recommended_action


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: [read_data(dir, "global_pg_fvAEPg.json")[0]],
            glbl_ext_epgs_api: [],
            ctx_defs_api: provider_ctx_defs,
            provider_relationships_api: [
                cross_context_l3out_relationship,
                provider_relationship(
                    "uni/tn-common/brc-AD_C",
                    provider_dn,
                    "missing-scope",
                    ordinary_consumer_dn,
                    different_ctx_def_dn
                )
            ]
        }
    ]
)
def test_context_error_preserves_confirmed_affected_relationship(
    run_check,
    mock_icurl
):
    result = run_check(
        cversion=script.AciVersion("5.2(8i)"),
        tversion=script.AciVersion("6.0(1g)")
    )

    assert result.result == script.ERROR
    assert result.data[0][1] == "No fvCtxDef found for scopeId missing-scope"
    assert result.unformatted_data == [[
        "uni/tn-common/brc-AD_C",
        provider_dn,
        "5555",
        different_vrf_l3out_consumer_dn
    ]]
