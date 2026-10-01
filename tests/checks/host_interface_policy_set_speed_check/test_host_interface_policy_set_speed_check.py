import os
import pytest
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

dir = os.path.dirname(os.path.abspath(__file__))
test_function = "host_interface_policy_set_speed_check"


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
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result


def test_policy_group_types(run_check, mock_icurl, icurl_outputs):
    icurl_outputs[host_interface_policy_api] = read_data(
        dir, "fabricHIfPol-pos.json"
    )
    result = run_check(
        tversion=script.AciVersion("6.0(9d)"),
    )

    assert result.result == script.FAIL_O
    assert result.headers == [
        "Host Interface Policy",
        "Set Speed",
        "Associated Interface Policy Group",
        "Group Type",
    ]
    assert result.data == [
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
