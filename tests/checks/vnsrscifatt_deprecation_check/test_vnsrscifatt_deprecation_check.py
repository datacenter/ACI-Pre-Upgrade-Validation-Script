import os
import pytest
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

dir = os.path.dirname(os.path.abspath(__file__))

test_function = "vnsRsCIfAtt_deprecation_check"

# icurl queries (only the 3 queries vnsRsCIfAtt_deprecation_check actually issues)
vnsLIf_with_rel_api = (
    "vnsLIf.json?rsp-prop-include=config-only"
    "&rsp-subtree=children"
    "&rsp-subtree-class=vnsRsCIfAtt,vnsRsCIfAttN"
)
vnsGraphInst_api = 'vnsGraphInst.json?query-target-filter=eq(vnsGraphInst.configSt,"applied")'
vnsLDevCtx_all_api = (
    'vnsLDevCtx.json?'
    'rsp-prop-include=config-only'
    '&rsp-subtree=full'
    '&rsp-subtree-class=vnsLIfCtx,vnsRsLIfCtxToLIf'
    '&rsp-subtree-include=required'
)

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result, expected_data, expected_msg",
    [
        # Target version missing
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_empty.json"),
            },
            None,
            script.MANUAL,
            [],
            script.TVER_MISSING,
        ),
        # Target version is not affected (< 6.0(3d))
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_empty.json"),
            },
            "6.0(2h)",
            script.NA,
            [],
            script.VER_NOT_AFFECTED,
        ),
        # 6.0(3d) is affected; if service graph is unconfigured, return PASS
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_empty.json"),
            },
            "6.0(3d)",
            script.PASS,
            [],
            "No deployed service graph interfaces found.",
        ),
        # Both vnsRsCIfAtt and vnsRsCIfAttN are missing but service graph is unconfigured -> PASS
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_empty.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
            "No deployed service graph interfaces found.",
        ),
        # Both vnsRsCIfAtt and vnsRsCIfAttN are missing while vnsLIf exists, but service graph is unconfigured -> PASS
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_only.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
            "No deployed service graph interfaces found.",
        ),
        # Legacy behavior: when vnsRsCIfAtt is absent but vnsRsCIfAttN exists, return PASS
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_new_match.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
            "No deployed service graph interfaces found.",
        ),
        # All vnsRsCIfAtt relations have matching vnsRsCIfAttN relations
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_old_new_match.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
            "No deployed service graph interfaces found.",
        ),
        # One vnsRsCIfAtt relation (cons) missing in vnsRsCIfAttN, but service graph unconfigured -> PASS
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_old_new_missing_cons.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
            "No deployed service graph interfaces found.",
        ),
        # vnsRsCIfAttN is empty and old relations exist, but service graph unconfigured -> PASS
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_old_only.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
            "No deployed service graph interfaces found.",
        ),
        # vnsLIf target from vnsLIfCtx relation is covered when global vnsRsCIfAttN exists
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_missing_rscifattn.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_new_match.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
            "No user-configured vnsRsCIfAtt payload found.",
        ),
        # vnsLDevIfLIf target must be converted to vnsLIf DN before subtree check
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLDevIfLIf_missing_rscifattn.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_new_match.json"),
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "common",
                    "common-device",
                    "common-cons",
                    "cons",
                    "uni/tn-common/lDevVip-common-device/lIf-common-cons",
                ]
            ],
            "",
        ),
        # Parent-only subtree no longer affects result when global vnsRsCIfAttN exists
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_missing_rscifattn.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_new_match.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
            "No user-configured vnsRsCIfAtt payload found.",
        ),
        # vnsRsLIfCtxToLIf may omit tCl; infer LDevIfLIf from tDn pattern and still fail when missing
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLDevIfLIf_missing_tcl.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_new_match.json"),
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "common",
                    "common-device",
                    "common-cons",
                    "cons",
                    "uni/tn-common/lDevVip-common-device/lIf-common-cons",
                ]
            ],
            "",
        ),
        # If only one common interface is referenced in vnsLDevCtx, expand to all LIfs under the same device
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLDevIfLIf_missing_tcl.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_common_empty.json"),
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "common",
                    "common-device",
                    "common-cons",
                    "cons",
                    "uni/tn-common/lDevVip-common-device/lIf-common-cons",
                ],
                [
                    "common",
                    "common-device",
                    "common-prov",
                    "prov",
                    "uni/tn-common/lDevVip-common-device/lIf-common-prov",
                ],
            ],
            "",
        ),
        # Imported graph label should still map to applied graph and detect missing common interfaces
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLDevIfLIf_missing_tcl_imported.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_common_empty.json"),
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "common",
                    "common-device",
                    "common-cons",
                    "cons",
                    "uni/tn-common/lDevVip-common-device/lIf-common-cons",
                ],
                [
                    "common",
                    "common-device",
                    "common-prov",
                    "prov",
                    "uni/tn-common/lDevVip-common-device/lIf-common-prov",
                ],
            ],
            "",
        ),
        # If both vnsRsCIfAtt and vnsRsCIfAttN are globally empty, result should be FAIL
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLDevIfLIf_missing_tcl.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_common_empty.json"),
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "common",
                    "common-device",
                    "common-cons",
                    "cons",
                    "uni/tn-common/lDevVip-common-device/lIf-common-cons",
                ],
                [
                    "common",
                    "common-device",
                    "common-prov",
                    "prov",
                    "uni/tn-common/lDevVip-common-device/lIf-common-prov",
                ],
            ],
            "",
        ),
        # LIF names with a numeric multi-connector suffix (e.g. "-cons-1") must still resolve the
        # missing concrete interface role to "cons"/"prov", not the trailing digit
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_numbered_suffix.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_common_numbered.json"),
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "common",
                    "common-device",
                    "common-cons-1",
                    "cons",
                    "uni/tn-common/lDevVip-common-device/lIf-common-cons-1",
                ],
                [
                    "common",
                    "common-device",
                    "common-prov-1",
                    "prov",
                    "uni/tn-common/lDevVip-common-device/lIf-common-prov-1",
                ],
            ],
            "",
        ),
        # Consistency check: a stale vnsRsCIfAtt pointing at a different concrete interface than the
        # matching vnsRsCIfAttN must still be flagged, even though the LIF itself is otherwise covered
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_cons_and_prov.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_stale_old_cif_mismatch.json"),
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "user-11",
                    "test",
                    "intf-cons",
                    "cons-old",
                    "uni/tn-user-11/lDevVip-test/lIf-intf-cons/rscIfAtt-[uni/tn-user-11/lDevVip-test/cDev-cdev/cIf-[cons-old]]",
                ],
            ],
            "",
        ),
        # A same-name context in another tenant is configured-only, never an outage result.
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_tenantA.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_tenantB_namecollision.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_tenantB_empty.json"),
            },
            "6.1(5e)",
            script.MANUAL,
            [["tenantB", "tenantB-device", "tenantB-cons", "cons", "uni/tn-tenantB/lDevVip-tenantB-device/lIf-tenantB-cons"]],
            "",
        ),
    ],
)
def test_logic(run_check, mock_icurl, icurl_outputs, tversion, expected_result, expected_data, expected_msg):
    # cversion is fixed to a pre-6.0(3d) release here so every case above continues to exercise
    # the legacy (post_cifatt_delete=False) path; the post-6.0(3d) path is covered separately below.
    result = run_check(
        cversion=script.AciVersion("5.2(8h)"),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data
    assert result.msg == expected_msg


@pytest.mark.parametrize(
    "icurl_outputs, tversion, cversion, expected_result, expected_data, expected_msg",
    [
        # Current version not supplied while target version is affected -> MANUAL
        (
            {
                vnsGraphInst_api: [],
                vnsLDevCtx_all_api: [],
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_empty.json"),
            },
            "6.1(5e)",
            None,
            script.MANUAL,
            [],
            "Current version not supplied. Skipping.",
        ),
        # Post-cifatt-delete (cversion >= 6.0(3d)): deployed LIF missing vnsRsCIfAttN, and the LIF's tenant
        # ("common") differs from the referencing contract's tenant ("user") -> implicit-objects message
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLDevIfLIf_missing_rscifattn.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_new_match.json"),
            },
            "6.1(5e)",
            "6.0(3d)",
            script.FAIL_O,
            [
                ["common", "common-device", "common-cons"],
            ],
            "",
        ),
        # Post-cifatt-delete (cversion >= 6.0(3d)): deployed LIFs missing vnsRsCIfAttN, but the tenant is
        # not "common" so the implicit-objects check does not apply -> generic missing message
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_missing_rscifattn.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_only.json"),
            },
            "6.1(5e)",
            "6.1(5e)",
            script.FAIL_O,
            [
                ["user-11", "test", "intf-cons"],
                ["user-11", "test", "intf-prov"],
            ],
            "",
        ),
        # Post-cifatt-delete (cversion >= 6.0(3d)): deployed LIF already has vnsRsCIfAttN -> PASS
        (
            {
                vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
                vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_missing_rscifattn.json"),
                vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_new_match.json"),
            },
            "6.1(5e)",
            "6.1(5e)",
            script.PASS,
            [],
            "All deployed service graph interfaces have vnsRsCIfAttN.",
        ),
    ],
)
def test_cversion_and_post_delete_branch(run_check, mock_icurl, icurl_outputs, tversion, cversion, expected_result, expected_data, expected_msg):
    result = run_check(
        cversion=script.AciVersion(cversion) if cversion else None,
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data
    assert result.msg == expected_msg


@pytest.mark.parametrize("cversion", ["5.2(8h)", "6.1(5e)"])
@pytest.mark.parametrize("icurl_outputs", [{
    vnsGraphInst_api: [],
    vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_cons_and_prov.json"),
    vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_only.json"),
}])
def test_configured_only_context_is_manual(run_check, mock_icurl, cversion):
    result = run_check(cversion=script.AciVersion(cversion), tversion=script.AciVersion("6.1(5e)"))
    assert result.result == script.MANUAL
    assert len(result.data) == 2
    assert all(row[0] == "user-11" for row in result.data)
    assert result.msg == ""
    assert "not currently deployed" in result.recommended_action
    assert "before the upgrade completes" in result.recommended_action
    assert "before deployment" in result.recommended_action


@pytest.mark.parametrize("icurl_outputs", [{
    vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
    vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_cons_and_prov.json"),
    vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_only.json"),
}])
def test_deployed_failure_moves_condition_to_recommended_action(run_check, mock_icurl):
    result = run_check(cversion=script.AciVersion("5.2(8h)"), tversion=script.AciVersion("6.1(5e)"))
    assert result.result == script.FAIL_O
    assert result.msg == ""
    assert len(result.data) == 2
    assert not result.unformatted_data
    assert result.recommended_action.startswith(
        "vnsLIf has neither vnsRsCIfAtt nor vnsRsCIfAttN. "
        "Missing concrete interface mapping can cause service graph inconsistency."
    )


@pytest.mark.parametrize("icurl_outputs", [{
    vnsGraphInst_api: [],
    vnsLDevCtx_all_api: read_data(dir, "vnsLDevCtx_vnsLIf_cons_and_prov.json"),
    vnsLIf_with_rel_api: read_data(dir, "vnsLIf_with_rel_old_only.json"),
}])
def test_old_only_relations_on_configured_context_are_manual(run_check, mock_icurl):
    result = run_check(cversion=script.AciVersion("5.2(8h)"), tversion=script.AciVersion("6.1(5e)"))
    assert result.result == script.MANUAL
    assert len(result.data) == 2
    assert all(row[0] == "user-11" for row in result.data)


@pytest.mark.parametrize("icurl_outputs", [{
    vnsGraphInst_api: read_data(dir, "vnsGraphInst_applied_single.json"),
    vnsLDevCtx_all_api: (
        read_data(dir, "vnsLDevCtx_vnsLIf_cons_and_prov.json")
        + read_data(dir, "vnsLDevCtx_vnsLIf_tenantB_namecollision.json")
    ),
    vnsLIf_with_rel_api: (
        read_data(dir, "vnsLIf_with_rel_only.json")
        + read_data(dir, "vnsLIf_with_rel_tenantB_empty.json")
    ),
}])
def test_deployed_failure_lists_configured_only_for_manual_review(run_check, mock_icurl):
    result = run_check(cversion=script.AciVersion("5.2(8h)"), tversion=script.AciVersion("6.1(5e)"))
    assert result.result == script.FAIL_O
    assert all(row[0] == "user-11" for row in result.data)
    assert result.unformatted_headers[0].startswith("MANUAL review:")
    assert len(result.unformatted_data) == 1
    assert result.unformatted_data[0][0] == "tenantB"
    assert result.msg == ""
    assert "Missing concrete interface mapping can cause service graph inconsistency." in result.recommended_action
    assert "Deploying them before the upgrade completes may cause the condition described in CSCwr51759." in result.recommended_action
    assert ". The listed configured-only service graph interfaces are not currently deployed." in result.recommended_action
