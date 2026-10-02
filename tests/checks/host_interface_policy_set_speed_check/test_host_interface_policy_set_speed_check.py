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


@pytest.mark.parametrize(
    "code, text, expected_result",
    [
        # Captured from APIC 4.2(7u): speed exists, but auto is not in its enum.
        (
            "301",
            "Incorrect filter format for fabricHIfPol.speed, value 'auto' is not valid",
            script.NA,
        ),
        # Other errors must not be classified as an unsupported auto speed.
        (
            "121",
            "Prop 'speed' not found in class 'fabricHIfPol' property table",
            script.ERROR,
        ),
        (
            "301",
            "Incorrect filter format for fabricHIfPol.speed, value 'invalid' is not valid",
            script.ERROR,
        ),
        (
            "301",
            "Incorrect filter format for fabricHIfPol.autoNeg, value 'auto' is not valid",
            script.ERROR,
        ),
        (
            "500",
            "Incorrect filter format for fabricHIfPol.speed, value 'auto' is not valid",
            script.ERROR,
        ),
        (
            "400",
            "Request failed, unresolved class for fabricHIfPol",
            script.ERROR,
        ),
        (
            "503",
            "Unable to deliver the message, Resolve timeout",
            script.ERROR,
        ),
        ("500", "Internal server error", script.ERROR),
        ("403", "Forbidden", script.ERROR),
    ],
)
def test_api_errors(run_check, mock_icurl, icurl_outputs, code, text, expected_result):
    icurl_outputs[host_interface_policy_api] = {
        "totalCount": "1",
        "imdata": [{"error": {"attributes": {"code": code, "text": text}}}],
    }
    result = run_check(
        cversion=script.AciVersion("4.2(7u)"),
        sw_cversion=script.AciVersion("4.2(7w)"),
        tversion=script.AciVersion("6.0(9d)"),
    )

    assert result.result == expected_result
    assert result.data == []
    if expected_result == script.NA:
        assert result.msg == 'Current APIC does not support fabricHIfPol.speed="auto".'
        assert result.doc_url.endswith("/#host-interface-policy-set-to-auto")
    else:
        assert result.msg.startswith("Unexpected Error:")
