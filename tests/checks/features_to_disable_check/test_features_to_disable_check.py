import importlib


script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "features_to_disable_check"

active_plugins_api = 'apPlugin.json?&query-target-filter=ne(apPlugin.pluginSt,"inactive")'
infra_api = 'uni/infra.json?query-target=subtree&target-subtree-class=infrazoneZone,epControlP'


def plugin(dn, name, status="active"):
    return {"apPlugin": {"attributes": {"dn": dn, "name": name, "pluginSt": status}}}


def test_crossing_612_replaces_app_failure_with_message(run_check, mock_icurl, icurl_outputs):
    # The App Center deprecation check owns application findings on this path, so
    # this check does not need the active-only apPlugin query.
    icurl_outputs.clear()
    icurl_outputs[infra_api] = []

    result = run_check(
        cversion=script.AciVersion("6.1(1f)"),
        tversion=script.AciVersion("6.1(2a)"),
    )

    assert result.result == script.PASS
    assert result.msg == "App Center deprecated on 6.1(2)."
    assert result.data == []


def test_crossing_612_preserves_other_feature_failures(run_check, mock_icurl, icurl_outputs):
    icurl_outputs.clear()
    icurl_outputs[infra_api] = [{"infrazoneZone": {"attributes": {
        "deplMode": "disabled",
        "name": "locked-zone",
    }}}]

    result = run_check(
        cversion=script.AciVersion("6.0(9h)"),
        tversion=script.AciVersion("6.1(2g)"),
    )

    assert result.result == script.FAIL_O
    assert result.msg == "App Center deprecated on 6.1(2)."
    assert result.data == [[
        "Config Zone",
        "locked-zone",
        "Locked",
        'Change the status to "Open" or remove the zone',
    ]]


def test_non_crossing_keeps_active_app_behavior(run_check, mock_icurl, icurl_outputs):
    icurl_outputs.clear()
    icurl_outputs[active_plugins_api] = [
        plugin("pluginContr/plugin-Example_CustomApp", "Custom App"),
    ]
    icurl_outputs[infra_api] = []

    result = run_check(
        cversion=script.AciVersion("6.0(8a)"),
        tversion=script.AciVersion("6.1(1f)"),
    )

    assert result.result == script.FAIL_O
    assert result.msg == ""
    assert result.data == [["App Center", "Custom App", "active", "Disable the app"]]


def test_missing_target_keeps_active_app_behavior(run_check, mock_icurl, icurl_outputs):
    icurl_outputs.clear()
    icurl_outputs[active_plugins_api] = [
        plugin("pluginContr/plugin-Example_CustomApp", "Custom App"),
    ]
    icurl_outputs[infra_api] = []

    result = run_check(
        cversion=script.AciVersion("6.1(1f)"),
        tversion=None,
    )

    assert result.result == script.FAIL_O
    assert result.msg == ""
    assert result.data == [["App Center", "Custom App", "active", "Disable the app"]]
