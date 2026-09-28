import importlib

import pytest

script = importlib.import_module("aci-preupgrade-validation-script")
test_function = "service_ep_flag_bd_check"

LEAF_DN = "topology/pod-1/node-101"
BD_DN = "uni/tn-test/BD-service_bd"
EPG_DN = (
    "uni/tn-test/LDevInst-[uni/tn-test/lDevVip-device]-ctx-vrf/"
    "G-graphctxvrf-N-service_bd-C-consumer"
)
GRAPH_DN = (
    "uni/tn-test/GraphInst_C-[uni/tn-test/brc-contract]-"
    "G-[uni/tn-test/AbsGraph-graph]-S-[uni/tn-test]"
)
NODE_DN = GRAPH_DN + "/NodeInst-N1"
EPG_DEF_DN = NODE_DN + "/LegVNode-0/EPgDef-consumer"
LDEV_DN = "uni/tn-test/ldevCtx-c-contract-g-graph-n-N1"
CTX_DN = LDEV_DN + "/lIfCtx-c-consumer"
POLICY_DN = "uni/tn-test/svcCont/svcRedirectPol-policy"
FLAG_QUERY = 'vlanCktEp.json?query-target-filter=allbits(vlanCktEp.ctrl,"service-ep")'


def make_payload(redirect=False):
    children = [
        {"vnsRsLIfCtxToBD": {"attributes": {"tDn": BD_DN}}},
        {"vnsRsLIfCtxToLIf": {"attributes": {"tDn": "uni/tn-test/lDevVip-device/lIf-consumer"}}},
    ]
    if redirect:
        # Redirect is deliberately after BD and logical interface.
        children.append({
            "vnsRsLIfCtxToSvcRedirectPol": {
                "attributes": {"tDn": POLICY_DN, "state": "formed"}
            }
        })
    return {
        "flagged": [{
            "vlanCktEp": {"attributes": {
                "dn": LEAF_DN + "/sys/ctx-[vxlan-1]/bd-[vxlan-2]/vlan-[vlan-10]",
                "epgDn": EPG_DN,
                "ctrl": "policy-enforced,service-ep",
            }}
        }],
        "epps": [{
            "vnsEPpInfo": {
                "attributes": {"dn": EPG_DN},
                "children": [
                    {"vnsRtEPpInfoAtt": {"attributes": {"tDn": EPG_DEF_DN}}},
                    {"vnsRsEPpInfoToBD": {"attributes": {"tDn": BD_DN}}},
                ],
            }
        }],
        "node_relations": [{
            "vnsRsNodeInstToLDevCtx": {"attributes": {
                "dn": NODE_DN + "/rsNodeInstToLDevCtx",
                "tDn": LDEV_DN,
            }}
        }],
        "contexts": [{
            "vnsLIfCtx": {
                "attributes": {"dn": CTX_DN},
                "children": children,
            }
        }],
    }


def run_case(monkeypatch, run_check, payload, leaf_version="5.2(8h)",
             target_version="6.0(8e)"):
    calls = []

    def fake_icurl(api_type, query, page_size=100000):
        assert api_type == "class"
        calls.append(query)
        if query == FLAG_QUERY:
            return payload["flagged"]
        if query.startswith("vnsEPpInfo.json?"):
            assert "query-target-filter=" in query
            return payload["epps"]
        if query == "vnsRsNodeInstToLDevCtx.json":
            return payload["node_relations"]
        if query.startswith("vnsLIfCtx.json?"):
            assert "rsp-subtree-class=" in query
            return payload["contexts"]
        raise AssertionError("Unexpected API query: {}".format(query))

    monkeypatch.setattr(script, "icurl", fake_icurl)
    fabric_nodes = [{
        "fabricNode": {"attributes": {
            "dn": LEAF_DN,
            "role": "leaf",
            "version": leaf_version,
        }}
    }]
    result = run_check(
        cversion=script.AciVersion("5.2(8h)"),
        tversion=script.AciVersion(target_version) if target_version else None,
        fabric_nodes=fabric_nodes,
    )
    return result, calls


@pytest.mark.parametrize(
    "leaf_version,target_version,expected,call_count",
    [
        ("5.2(5b)", "6.0(8e)", script.PASS, 1),
        ("5.2(5c)", "6.0(8e)", script.FAIL_O, 4),
        ("5.2(5d)", "6.0(8e)", script.FAIL_O, 4),
        ("6.0(1f)", "6.0(8e)", script.PASS, 1),
        ("6.0(1g)", "6.0(8e)", script.FAIL_O, 4),
        ("6.0(1h)", "6.0(8e)", script.FAIL_O, 4),
        ("6.0(8d)", "6.0(8e)", script.FAIL_O, 4),
        ("6.0(8e)", "6.0(8e)", script.PASS, 1),
        ("6.1(1a)", "6.1(1e)", script.NA, 0),
        ("6.1(1a)", "6.1(1f)", script.FAIL_O, 4),
        ("6.1(1a)", "6.1(1g)", script.FAIL_O, 4),
        ("6.1(1f)", "6.1(1g)", script.PASS, 1),
        ("5.2(8h)", "6.0(7f)", script.NA, 0),
        ("5.2(8h)", "6.2(1a)", script.FAIL_O, 4),
        ("5.3(2d)", "6.1(1f)", script.MANUAL, 1),
    ],
)
def test_release_transition(monkeypatch, run_check, leaf_version,
                            target_version, expected, call_count):
    result, calls = run_case(monkeypatch, run_check, make_payload(),
                             leaf_version, target_version)
    assert result.result == expected
    assert len(calls) == call_count
    if expected == script.FAIL_O:
        assert result.data == [[LEAF_DN, EPG_DN, BD_DN, CTX_DN]]


def test_missing_target_stops_before_api(monkeypatch, run_check):
    result, calls = run_case(monkeypatch, run_check, make_payload(),
                             target_version=None)
    assert result.result == script.MANUAL
    assert calls == []


def test_no_operational_flag_needs_one_api_call(monkeypatch, run_check):
    payload = make_payload()
    payload["flagged"] = []
    result, calls = run_case(monkeypatch, run_check, payload)
    assert result.result == script.PASS
    assert calls == [FLAG_QUERY]


def test_flag_without_epg_dn_requires_manual_review(monkeypatch, run_check):
    payload = make_payload()
    vlan_dn = payload["flagged"][0]["vlanCktEp"]["attributes"]["dn"]
    del payload["flagged"][0]["vlanCktEp"]["attributes"]["epgDn"]
    result, calls = run_case(monkeypatch, run_check, payload)
    assert result.result == script.MANUAL
    assert result.unformatted_data[0][:2] == [LEAF_DN, vlan_dn]
    assert calls == [FLAG_QUERY]


def test_repeated_flagged_epg_is_reported_once(monkeypatch, run_check):
    payload = make_payload()
    payload["flagged"].append(payload["flagged"][0])
    result, calls = run_case(monkeypatch, run_check, payload)
    assert result.result == script.FAIL_O
    assert result.data == [[LEAF_DN, EPG_DN, BD_DN, CTX_DN]]
    assert len(calls) == 4


def test_formed_redirect_after_other_children_is_not_flagged(monkeypatch, run_check):
    result, calls = run_case(monkeypatch, run_check, make_payload(redirect=True))
    assert result.result == script.PASS
    assert len(calls) == 4
    assert result.data == []


def test_unresolved_redirect_requires_manual_review(monkeypatch, run_check):
    payload = make_payload(redirect=True)
    redirect = payload["contexts"][0]["vnsLIfCtx"]["children"][-1]
    redirect["vnsRsLIfCtxToSvcRedirectPol"]["attributes"]["state"] = "unformed"
    result, _ = run_case(monkeypatch, run_check, payload)
    assert result.result == script.MANUAL
    assert result.unformatted_data[0][:2] == [LEAF_DN, EPG_DN]


def test_missing_bd_is_not_an_outage_warning(monkeypatch, run_check):
    payload = make_payload()
    payload["epps"][0]["vnsEPpInfo"]["children"].pop()
    result, calls = run_case(monkeypatch, run_check, payload)
    assert result.result == script.MANUAL
    assert result.data == []
    assert result.unformatted_data[0][:2] == [LEAF_DN, EPG_DN]
    assert len(calls) == 2


def test_missing_epg_mapping_preserves_identifiers(monkeypatch, run_check):
    payload = make_payload()
    payload["epps"] = []
    result, calls = run_case(monkeypatch, run_check, payload)
    assert result.result == script.MANUAL
    assert result.unformatted_data[0][:2] == [LEAF_DN, EPG_DN]
    assert len(calls) == 2


def test_unusual_epg_dn_is_not_silently_skipped(monkeypatch, run_check):
    payload = make_payload()
    unusual_dn = "uni/tn-test/unknown-service-epg"
    payload["flagged"][0]["vlanCktEp"]["attributes"]["epgDn"] = unusual_dn
    payload["epps"] = []
    result, calls = run_case(monkeypatch, run_check, payload)
    assert result.result == script.MANUAL
    assert result.unformatted_data[0][:2] == [LEAF_DN, unusual_dn]
    assert len(calls) == 2


def test_mismatched_connector_bd_requires_manual_review(monkeypatch, run_check):
    payload = make_payload()
    payload["contexts"][0]["vnsLIfCtx"]["children"][0] = {
        "vnsRsLIfCtxToBD": {"attributes": {"tDn": "uni/tn-test/BD-other"}}
    }
    result, _ = run_case(monkeypatch, run_check, payload)
    assert result.result == script.MANUAL
    assert result.data == []
    assert result.unformatted_data[0][:2] == [LEAF_DN, EPG_DN]


def test_empty_connector_children_requires_manual_review(monkeypatch, run_check):
    payload = make_payload()
    payload["contexts"][0]["vnsLIfCtx"]["children"] = []
    result, _ = run_case(monkeypatch, run_check, payload)
    assert result.result == script.MANUAL
    assert result.data == []


def test_shared_service_epg_with_one_pbr_connector_is_expected(monkeypatch, run_check):
    payload = make_payload()
    provider_def_dn = NODE_DN + "/LegVNode-0/EPgDef-provider"
    payload["epps"][0]["vnsEPpInfo"]["children"].append({
        "vnsRtEPpInfoAtt": {"attributes": {"tDn": provider_def_dn}}
    })
    provider_ctx_dn = LDEV_DN + "/lIfCtx-c-provider"
    payload["contexts"].append({
        "vnsLIfCtx": {
            "attributes": {"dn": provider_ctx_dn},
            "children": [
                {"vnsRsLIfCtxToBD": {"attributes": {"tDn": BD_DN}}},
                {"vnsRsLIfCtxToSvcRedirectPol": {
                    "attributes": {"tDn": POLICY_DN, "state": "formed"}
                }},
            ],
        }
    })
    result, _ = run_case(monkeypatch, run_check, payload)
    assert result.result == script.PASS
    assert result.data == []
