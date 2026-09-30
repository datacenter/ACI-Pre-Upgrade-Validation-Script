import importlib

import pytest

script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "apic_cluster_size_check"
apic_api = ('fabricNode.json?query-target-filter='
            'and(eq(fabricNode.role,"controller"),'
            'eq(fabricNode.apicType,"apic"),'
            'eq(fabricNode.fabricSt,"commissioned"))')


def fabric_nodes(models):
    return [{"fabricNode": {"attributes": {
        "id": str(index + 1), "name": "apic{}".format(index + 1), "model": model,
    }}} for index, model in enumerate(models)]


@pytest.mark.parametrize(
    "models, expected_result",
    [
        (["APIC-SERVER-G5"] * 3, script.PASS),
        (["APIC-SERVER-G5"] * 4, script.MANUAL),
        (["APIC-SERVER-G5"] * 4 + ["APIC-SERVER-L2"], script.PASS),
        (["APIC-SERVER-L1"] * 4, script.PASS),
        (["APIC-SERVER-M2"] * 4, script.PASS),
        (["APIC-SERVER-M1"] * 4, script.PASS),
        (["APIC-SERVER-L4T"] * 4, script.PASS),
        (["APIC-SERVER-M4T"] * 4, script.PASS),
        (["APIC-SERVER-G5"] * 4, script.MANUAL),
        (["APIC-SERVER-G5T"] * 4, script.MANUAL),
    ],
)
def test_logic(monkeypatch, models, expected_result):
    monkeypatch.setattr(script, "icurl", lambda apitype, query: fabric_nodes(models))
    result = script.apic_cluster_size_check(
        tversion=script.AciVersion("6.3(1a)"),
        finalize_check=lambda check_id, result: None,
    )
    assert result.result == expected_result


def test_reports_models_and_recommended_action(monkeypatch):
    monkeypatch.setattr(script, "icurl", lambda apitype, query: fabric_nodes(["APIC-SERVER-G5"] * 4))
    result = script.apic_cluster_size_check(
        tversion=script.AciVersion("6.3(1a)"),
        finalize_check=lambda check_id, result: None,
    )
    assert result.headers == ["Node ID", "Node Name", "Model", "Excluded from 3-Node Limit"]
    assert result.data == [
        [str(index), "apic{}".format(index), "APIC-SERVER-G5", "no"]
        for index in range(1, 5)
    ]
    assert "Reduce the APIC cluster to three nodes" in result.recommended_action


@pytest.mark.parametrize("target_version", ["6.2(7f)", "6.3(0a)"])
def test_older_targets_are_not_blocked(monkeypatch, target_version):
    def unexpected_api_call(*args):
        pytest.fail("APIC cluster size should not be checked for this target")

    monkeypatch.setattr(script, "icurl", unexpected_api_call)
    result = script.apic_cluster_size_check(
        tversion=script.AciVersion(target_version),
        finalize_check=lambda check_id, result: None,
    )
    assert result.result == script.NA


def test_missing_target_version_is_manual():
    result = script.apic_cluster_size_check(
        tversion=None,
        finalize_check=lambda check_id, result: None,
    )
    assert result.result == script.MANUAL
    assert result.msg == script.TVER_MISSING
