import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
host_interface_policy_api = 'fabricHIfPol.json'
host_interface_policy_api += '?query-target-filter=and(eq(fabricHIfPol.speed,"auto"))'
host_interface_policy_api += '&rsp-subtree=children&rsp-subtree-class=fabricRtHIfPol'

@pytest.mark.parametrize( "icurl_outputs, tversion, expected_result",
    [
        # MANUAL Cases
        # No tversion given
        (
            {host_interface_policy_api: read_data(dir, "fabricHIfPol-pos.json")},
            None,
            script.MANUAL,
        ),
        # FAIL_O Cases
        # fabricHIfPol with 'auto' speed found
        (
            {host_interface_policy_api: read_data(dir, "fabricHIfPol-pos.json")},
            "6.0(9d)",
            script.FAIL_O,
        ),
        # PASS Cases
        # No fabricHIfPol with 'auto' speed found
        (
            {host_interface_policy_api: []},
            "6.0(1g)",
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    tversion = script.AciVersion(tversion) if tversion else None
    result = script.host_interface_policy_set_speed_check(
        1, 1, tversion
    )
    assert result == expected_result


def test_policy_group_types(mock_icurl, icurl_outputs, monkeypatch):
    icurl_outputs[host_interface_policy_api] = read_data(
        dir, "fabricHIfPol-pos.json"
    )
    rendered_result = {}

    def capture_print_result(**kwargs):
        rendered_result.update(kwargs)

    monkeypatch.setattr(script, "print_result", capture_print_result)

    result = script.host_interface_policy_set_speed_check(
        1, 1, script.AciVersion("6.0(9d)")
    )

    assert result == script.FAIL_O
    assert rendered_result["headers"] == [
        "Host Interface Policy",
        "Set Speed",
        "Associated Interface Policy Group",
        "Group Type",
    ]
    assert rendered_result["data"] == [
        [
            "uni/infra/hintfpol-fernandh_interface",
            "auto",
            "fernandh_interface",
            "Leaf Access",
        ],
        ["uni/infra/hintfpol-AUTO", "auto", "av_accessB", "Leaf Access"],
        ["uni/infra/hintfpol-AUTO", "auto", "av-access", "PC/vPC"],
        [
            "uni/infra/hintfpol-AUTO",
            "auto",
            "av-override",
            "PC/vPC Override",
        ],
        [
            "uni/infra/hintfpol-AUTO",
            "auto",
            "spine-access",
            "Spine Access",
        ],
    ]