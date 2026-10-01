import importlib

import pytest


script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "cimc_cscwo74485_advisory_check"
eqptCh_api = 'eqptCh.json?query-target-filter=wcard(eqptCh.descr,"APIC")'


def apic_node(node_id="1", model="M4", cimc_version="4.3(4.241063)"):
    attributes = {
        "descr": "APIC-SERVER-" + model,
        "dn": "topology/pod-1/node-{}/sys/ch".format(node_id),
    }
    if cimc_version is not None:
        attributes["cimcVersion"] = cimc_version
    return {"eqptCh": {"attributes": attributes}}


def target_compat_api(model):
    return ('uni/fabric/compcat-default/ctlrfw-apic-6.2(3)/rssuppHw-'
            '[uni/fabric/compcat-default/ctlrhw-apic{}].json').format(model.lower())


def serialized_results():
    cversion = script.AciVersion("5.3(1d)")
    generic = script.cimc_compatibilty_check.__wrapped__(
        tversion=script.AciVersion("6.2(3f)"), cversion=cversion,
    )
    advisory = script.cimc_cscwo74485_advisory_check.__wrapped__(cversion=cversion)
    return (
        script.AciResult("cimc_compatibilty_check", "APIC CIMC Compatibility", generic),
        script.AciResult(test_function, "CIMC Upgrade Order (CSCwo74485)", advisory),
    )


@pytest.mark.parametrize("icurl_outputs", [{eqptCh_api: [apic_node()]}])
def test_affected_node_returns_manual_with_rows(run_check, mock_icurl):
    result = run_check(cversion=script.AciVersion("5.3(1d)"))

    assert result.result == script.MANUAL
    assert result.msg == ""
    assert result.data == [[
        "node-1", "APIC-SERVER-M4", "5.3(1d)", "4.3(4.241063)",
        "Review CIMC upgrade order",
    ]]
    assert result.recommended_action == (
        "If a CIMC upgrade is required, review CSCwo74485 and upgrade APIC software "
        "to a fixed release before upgrading CIMC."
    )

    aci_result = script.AciResult(test_function, "CIMC Upgrade Order (CSCwo74485)", result)
    assert aci_result.ruleStatus == script.AciResult.FAIL
    assert aci_result.severity == "warning"
    assert aci_result.failureDetails["failType"] == script.MANUAL
    assert aci_result.failureDetails["data"][0]["Node ID"] == "node-1"


@pytest.mark.parametrize("icurl_outputs", [{eqptCh_api: [apic_node(cimc_version=None)]}])
def test_unverifiable_node_uses_row_and_empty_message(run_check, mock_icurl):
    result = run_check(cversion=script.AciVersion("5.3(1d)"))

    assert result.result == script.MANUAL
    assert result.msg == ""
    assert result.data[0][-1] == "Cannot verify CSCwo74485"
    assert result.recommended_action == "Review CSCwo74485 before upgrading CIMC."


@pytest.mark.parametrize("icurl_outputs", [{eqptCh_api: []}])
def test_unverifiable_without_rows_uses_short_message(run_check, mock_icurl):
    result = run_check(cversion=script.AciVersion("5.3(1d)"))

    assert result.result == script.MANUAL
    assert result.data == []
    assert result.msg == "Cannot verify CSCwo74485."
    assert result.recommended_action == "Review CSCwo74485 before upgrading CIMC."


@pytest.mark.parametrize("icurl_outputs", [{}])
def test_missing_current_version_uses_short_message(run_check, mock_icurl):
    result = run_check(cversion=None)

    assert result.result == script.MANUAL
    assert result.data == []
    assert result.msg == "Cannot verify CSCwo74485."


@pytest.mark.parametrize("icurl_outputs, cversion", [
    ({}, "6.1(4h)"),
    ({}, "6.2(1a)"),
])
def test_fixed_apic_version_is_not_applicable(run_check, mock_icurl, cversion):
    result = run_check(cversion=script.AciVersion(cversion))

    assert result.result == script.NA
    assert result.msg == ""
    assert result.data == []
    assert result.recommended_action == ""

    aci_result = script.AciResult(test_function, "CIMC Upgrade Order (CSCwo74485)", result)
    assert aci_result.ruleStatus == script.AciResult.PASS
    assert aci_result.showValidation is False
    assert aci_result.severity == "informational"


@pytest.mark.parametrize("icurl_outputs", [
    {eqptCh_api: [apic_node(model="M3")]},
    {eqptCh_api: [apic_node(cimc_version="4.3(5)")]},
])
def test_no_applicable_nodes_returns_na(run_check, mock_icurl):
    result = run_check(cversion=script.AciVersion("5.3(1d)"))

    assert result.result == script.NA
    assert result.msg == ""
    assert result.data == []


@pytest.mark.parametrize("icurl_outputs", [{eqptCh_api: [
    apic_node(node_id="1"),
    apic_node(node_id="2", cimc_version="4.3(5)"),
    apic_node(node_id="3", model="M3", cimc_version="4.0(1a)"),
]}])
def test_mixed_nodes_only_include_applicable_rows(run_check, mock_icurl):
    result = run_check(cversion=script.AciVersion("5.3(1d)"))

    assert result.result == script.MANUAL
    assert [row[0] for row in result.data] == ["node-1"]


@pytest.mark.parametrize("icurl_outputs", [{
    eqptCh_api: [apic_node()],
    target_compat_api("M4"): [{"compatRsSuppHw": {"attributes": {"cimcVersion": "4.0(2g)"}}}],
}])
def test_advisory_only_serializes_as_warning(mock_icurl):
    generic, advisory = serialized_results()

    assert generic.ruleStatus == script.AciResult.PASS
    assert generic.severity == "informational"
    assert generic.failureDetails["data"] == []
    assert advisory.ruleStatus == script.AciResult.FAIL
    assert advisory.severity == "warning"
    assert advisory.failureDetails["failType"] == script.MANUAL
    assert [row["Node ID"] for row in advisory.failureDetails["data"]] == ["node-1"]


@pytest.mark.parametrize("icurl_outputs", [{
    eqptCh_api: [apic_node(model="M3", cimc_version="4.0(1a)")],
    target_compat_api("M3"): [{"compatRsSuppHw": {"attributes": {"cimcVersion": "4.3(2.250016)"}}}],
}])
def test_failure_only_serializes_as_critical(mock_icurl):
    generic, advisory = serialized_results()

    assert generic.ruleStatus == script.AciResult.FAIL
    assert generic.severity == "critical"
    assert generic.failureDetails["failType"] == script.FAIL_UF
    assert [row["Node ID"] for row in generic.failureDetails["data"]] == ["node-1"]
    assert advisory.ruleStatus == script.AciResult.PASS
    assert advisory.showValidation is False
    assert advisory.failureDetails["data"] == []


@pytest.mark.parametrize("icurl_outputs", [{
    eqptCh_api: [
        apic_node(node_id="1"),
        apic_node(node_id="2", model="M3", cimc_version="4.0(1a)"),
    ],
    target_compat_api("M4"): [{"compatRsSuppHw": {"attributes": {"cimcVersion": "4.0(2g)"}}}],
    target_compat_api("M3"): [{"compatRsSuppHw": {"attributes": {"cimcVersion": "4.3(2.250016)"}}}],
}])
def test_mixed_results_serialize_rows_under_matching_severity(mock_icurl):
    generic, advisory = serialized_results()

    assert generic.severity == "critical"
    assert generic.failureDetails["failType"] == script.FAIL_UF
    assert [row["Node ID"] for row in generic.failureDetails["data"]] == ["node-2"]
    assert advisory.severity == "warning"
    assert advisory.failureDetails["failType"] == script.MANUAL
    assert [row["Node ID"] for row in advisory.failureDetails["data"]] == ["node-1"]
