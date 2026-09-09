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

# global epgs  ( 16 <= pgtag <= 16385) with Preferred group enabled with provided contracts

glbl_epgs_api = 'fvAEPg.json'
glbl_epgs_api += '?query-target-filter=and(le(fvAEPg.pcTag,"16385"),ge(fvAEPg.pcTag,"16"),eq(fvAEPg.prefGrMemb,"include"))'
glbl_epgs_api += '&rsp-subtree=children&rsp-subtree-class=fvRsProv'

# global external Epgs  ( 16 <= pgtag <= 16385) with Preferred group enabled with provided contracts

glbl_ext_epgs_api = 'l3extInstP.json'
glbl_ext_epgs_api += '?query-target-filter=and(le(l3extInstP.pcTag,"16385"),ge(l3extInstP.pcTag,"16"),eq(l3extInstP.prefGrMemb,"include"))'
glbl_ext_epgs_api += '&rsp-subtree=children&rsp-subtree-class=fvRsProv'

l3out_consumers_api = 'l3extInstP.json'
l3out_consumers_api += '?rsp-subtree=children&rsp-subtree-class=fvRsCons'

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
different_vrf_l3out_consumer = {
    "l3extInstP": {
        "attributes": {
            "dn": "uni/tn-consumer/out-consumer/instP-different-vrf",
            "scope": "999"
        },
        "children": [
            {
                "fvRsCons": {
                    "attributes": {
                        "tDn": "uni/tn-common/brc-AD_C"
                    }
                }
            }
        ]
    }
}
same_vrf_l3out_consumer = {
    "l3extInstP": {
        "attributes": {
            "dn": "uni/tn-consumer/out-consumer/instP-same-vrf",
            "scope": "2261001"
        },
        "children": [
            {
                "fvRsCons": {
                    "attributes": {
                        "tDn": "uni/tn-common/brc-AD_C"
                    }
                }
            }
        ]
    }
}
unrelated_l3out_consumer = {
    "l3extInstP": {
        "attributes": {
            "dn": "uni/tn-consumer/out-consumer/instP-unrelated",
            "scope": "999"
        },
        "children": [
            {
                "fvRsCons": {
                    "attributes": {
                        "tDn": "uni/tn-common/brc-unrelated"
                    }
                }
            }
        ]
    }
}
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
tenant_l3out_consumer = {
    "l3extInstP": {
        "attributes": {
            "dn": "uni/tn-test/out-consumer/instP-consumer",
            "scope": "2000"
        },
        "children": [
            {
                "fvRsCons": {
                    "attributes": {
                        "tDn": "uni/tn-test/brc-tenant-shared"
                    }
                }
            }
        ]
    }
}


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [

        # MANUAL cases
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
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
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
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
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
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
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "6.0(1f)",
            script.FAIL_O,
        ),
        # Tenant-scope contracts carry the same broad forwarding risk through 5.2.
        (
            {
                shrd_contracts_api: [tenant_contract],
                glbl_epgs_api: [tenant_provider],
                glbl_ext_epgs_api: []
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
                l3out_consumers_api: [different_vrf_l3out_consumer]
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
                l3out_consumers_api: [different_vrf_l3out_consumer]
            },
            "4.2(1a)", "6.0(1g)",
            script.FAIL_O,
        ),
        # A childless fvAEPg does not hide a later affected fvAEPg.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [childless_fvAEPg] + read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: []
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
                l3out_consumers_api: [different_vrf_l3out_consumer]
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
                glbl_ext_epgs_api: [],
                l3out_consumers_api: []
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
                l3out_consumers_api: []
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
                l3out_consumers_api: [childless_l3extInstP]
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
                l3out_consumers_api: [same_vrf_l3out_consumer]
            },
            "4.2(1a)", "6.0(1g)",
            script.PASS,
        ),
        # An unrelated L3Out consumer does not affect the provider.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: [],
                l3out_consumers_api: [unrelated_l3out_consumer]
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


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
            glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json"),
            l3out_consumers_api: [different_vrf_l3out_consumer]
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
            l3out_consumers_api: [different_vrf_l3out_consumer]
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


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: [tenant_contract],
            glbl_epgs_api: [tenant_provider],
            glbl_ext_epgs_api: [],
            l3out_consumers_api: [tenant_l3out_consumer]
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
