import importlib
import logging
import os

import pytest

from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "port_tracking_active_fabric_port_check"
infra_port_track_pol_api = "uni/infra/trackEqptFabP-default.json"
doc_url = "https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/validations/#port-tracking-active-fabric-port-zero"


@pytest.mark.parametrize(
    "icurl_outputs, tversion, vpc_node_ids, expected_result, expected_data",
    [
        (
            {},
            None,
            ["101", "102"],
            script.MANUAL,
            [],
        ),
        (
            {},
            "6.0(9c)",
            ["101", "102"],
            script.NA,
            [],
        ),
        (
            {},
            "6.0(9e)",
            ["101", "102"],
            script.NA,
            [],
        ),
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_neg.json")},
            "6.0(9d)",
            ["101", "102"],
            script.PASS,
            [],
        ),
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_neg1.json")},
            "6.0(9d)",
            ["101", "102"],
            script.PASS,
            [],
        ),
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_pos.json")},
            "6.0(9d)",
            ["101", "102"],
            script.FAIL_O,
            [["on", "0"]],
        ),
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_pos.json")},
            "6.1(3f)",
            ["101", "102"],
            script.FAIL_O,
            [["on", "0"]],
        ),
        (
            {},
            "6.1(3f)",
            [],
            script.NA,
            [],
        ),
        (
            {infra_port_track_pol_api: []},
            "6.1(3f)",
            ["101", "102"],
            script.ERROR,
            [],
        ),
        (
            {
                infra_port_track_pol_api: [
                    {"infraPortTrackPol": {"attributes": {"adminSt": "on"}}}
                ]
            },
            "6.1(3f)",
            ["101", "102"],
            script.ERROR,
            [],
        ),
        (
            {
                infra_port_track_pol_api: [
                    {"infraPortTrackPol": {"attributes": {"adminSt": "on", "minlinks": "0"}}},
                    {"infraPortTrackPol": {"attributes": {"adminSt": "off", "minlinks": "0"}}},
                ]
            },
            "6.1(3f)",
            ["101", "102"],
            script.ERROR,
            [],
        ),
    ],
)


def test_logic(run_check, mock_icurl, tversion, vpc_node_ids, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        vpc_node_ids=vpc_node_ids,
    )
    assert result.result == expected_result
    assert result.data == expected_data
    assert result.doc_url == doc_url


def test_failure_result_contract(run_check, mock_icurl, icurl_outputs):
    icurl_outputs[infra_port_track_pol_api] = read_data(dir, "infraPortTrackPol_pos.json")

    result = run_check(
        tversion=script.AciVersion("6.1(3f)"),
        vpc_node_ids=["101", "102"],
    )

    assert "fixed release" in result.recommended_action
    assert "disable Port Tracking" in result.recommended_action
    assert "more than two operational fabric uplinks" in result.recommended_action
    assert "reload the affected switch" in result.recommended_action

    aci_result = script.AciResult(test_function, "Port Tracking Minimal Uplink Zero", result)
    assert aci_result.ruleStatus == script.AciResult.FAIL
    assert aci_result.severity == "critical"
    assert aci_result.docUrl == doc_url
    assert aci_result.failureDetails["header"] == ["Admin State", "Port Tracking Active Fabric Ports"]
    assert aci_result.failureDetails["data"] == [
        {"Admin State": "on", "Port Tracking Active Fabric Ports": "0"}
    ]
