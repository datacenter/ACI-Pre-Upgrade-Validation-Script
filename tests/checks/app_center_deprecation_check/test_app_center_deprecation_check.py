import importlib

import pytest


script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "app_center_deprecation_check"

plugins_api = "apPlugin.json"

native_impact = "App Infrastructure is removed; equivalent functionality is native in APIC 6.1(2) or later."
native_action = "Disable the legacy App Center application before upgrade and validate the native feature after upgrade."
removed_impact = "App Infrastructure is removed; this application functionality is unavailable after upgrade."
removed_action = "Review operational dependencies, disable the application before upgrade, and identify a replacement for any required functionality."


def plugin(dn, name, status="active"):
    return {"apPlugin": {"attributes": {"dn": dn, "name": name, "pluginSt": status}}}


@pytest.mark.parametrize(
    "current_version,target_version",
    [
        ("6.1(1f)", None),
        ("6.0(9h)", "6.1(1f)"),
        ("6.1(2a)", "6.1(3a)"),
        ("6.1(2g)", "6.2(1a)"),
    ],
)
def test_non_crossing_versions_are_not_applicable(
    run_check, mock_icurl, current_version, target_version
):
    result = run_check(
        cversion=script.AciVersion(current_version),
        tversion=script.AciVersion(target_version) if target_version else None,
    )

    assert result.result == script.NA
    expected_msg = script.TVER_MISSING if target_version is None else script.VER_NOT_AFFECTED
    assert result.msg == expected_msg
    assert result.data == []


def test_crossing_without_apps_passes(run_check, mock_icurl, icurl_outputs):
    icurl_outputs.clear()
    icurl_outputs[plugins_api] = []

    result = run_check(
        cversion=script.AciVersion("6.1(1f)"),
        tversion=script.AciVersion("6.1(2a)"),
    )

    assert result.result == script.PASS
    assert result.data == []


def test_crossing_reports_active_and_inactive_apps(run_check, mock_icurl, icurl_outputs):
    icurl_outputs.clear()
    icurl_outputs[plugins_api] = [
        plugin("pluginContr/plugin-Example_ActiveApp", "Active App"),
        plugin("pluginContr/plugin-Example_InactiveApp", "Inactive App", "inactive"),
    ]

    result = run_check(
        cversion=script.AciVersion("6.0(9h)"),
        tversion=script.AciVersion("6.1(2g)"),
    )

    assert result.result == script.MANUAL
    assert result.data == [
        ["Active App", "Example_ActiveApp", "active", removed_impact, removed_action],
        ["Inactive App", "Example_InactiveApp", "inactive", removed_impact, removed_action],
    ]


def test_native_transition_apps_use_verified_package_ids(run_check, mock_icurl, icurl_outputs):
    icurl_outputs.clear()
    icurl_outputs[plugins_api] = [
        plugin("pluginContr/plugin-Cisco_PreUpgradeValidator", "Pre-Upgrade Validator"),
        plugin("pluginContr/plugin-Cisco_NIBASE", "Nexus Insights Cloud Connector", "inactive"),
        plugin("pluginContr/plugin-Cisco_ElamAssistant", "ELAM Assistant"),
    ]

    result = run_check(
        cversion=script.AciVersion("5.2(8h)"),
        tversion=script.AciVersion("6.1(2a)"),
    )

    assert result.result == script.MANUAL
    assert result.data == [
        ["Pre-Upgrade Validator", "Cisco_PreUpgradeValidator", "active", native_impact, native_action],
        ["Nexus Insights Cloud Connector", "Cisco_NIBASE", "inactive", native_impact, native_action],
        ["ELAM Assistant", "Cisco_ElamAssistant", "active", native_impact, native_action],
    ]


def test_internal_plugins_are_excluded_and_apicvision_is_not_elam(
    run_check, mock_icurl, icurl_outputs
):
    icurl_outputs.clear()
    icurl_outputs[plugins_api] = [
        plugin("pluginContr/plugin-Cisco_IntersightDC", "Intersight Device Connector"),
        plugin("pluginContr/plugin-Cisco_NIALite", "NIA Lite"),
        plugin("pluginContr/plugin-Cisco_ApicVision", "ApicVision"),
    ]

    result = run_check(
        cversion=script.AciVersion("6.1(1f)"),
        tversion=script.AciVersion("6.1(3a)"),
    )

    assert result.result == script.PASS
    assert result.data == []


def test_manual_result_serializes_for_apic_workflow(run_check, mock_icurl, icurl_outputs):
    icurl_outputs.clear()
    icurl_outputs[plugins_api] = [
        plugin("pluginContr/plugin-Example_CustomApp", "Custom App", "inactive"),
    ]

    result = run_check(
        cversion=script.AciVersion("6.1(1f)"),
        tversion=script.AciVersion("6.1(2a)"),
    )
    serialized = script.AciResult(test_function, "App Center deprecation", result).as_dict()

    assert serialized["ruleStatus"] == script.AciResult.FAIL
    assert serialized["severity"] == "warning"
    assert serialized["failureDetails"]["failType"] == script.MANUAL
    assert serialized["failureDetails"]["data"][0]["Application"] == "Custom App"
