import os
import pytest
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

dir = os.path.dirname(os.path.abspath(__file__))

test_function = "vnsrscifattn_missing_check"

# icurl queries
vnsRsCIfAtt_api = "vnsRsCIfAtt.json?rsp-prop-include=config-only"
vnsRsCIfAttN_api = "vnsRsCIfAttN.json?rsp-prop-include=config-only"
vnsLIf_api = "vnsLIf.json?rsp-prop-include=config-only"

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result, expected_data",
    [
        # Target version missing
        (
            {},
            None,
            script.MANUAL,
            [],
        ),
        # Target version is not affected (< 6.0(3d))
        (
            {},
            "6.0(2h)",
            script.NA,
            [],
        ),
        # Both vnsRsCIfAtt and vnsRsCIfAttN are missing (no vnsLIf rows)
        (
            {
                vnsRsCIfAtt_api: read_data(dir, "vnsRsCIfAtt_empty.json"),
                vnsRsCIfAttN_api: read_data(dir, "vnsRsCIfAtt_empty.json"),
                vnsLIf_api: [],
            },
            "6.1(5e)",
            script.MANUAL,
            [],
        ),
        # Both vnsRsCIfAtt and vnsRsCIfAttN are missing while vnsLIf exists
        (
            {
                vnsRsCIfAtt_api: read_data(dir, "vnsRsCIfAtt_empty.json"),
                vnsRsCIfAttN_api: read_data(dir, "vnsRsCIfAtt_empty.json"),
                vnsLIf_api: read_data(dir, "vnsLIf_only.json"),
            },
            "6.1(5e)",
            script.MANUAL,
            [
                [
                    "CSCwj49418",
                    "test",
                    "intf-cons",
                    "N/A",
                    "uni/tn-CSCwj49418/lDevVip-test/lIf-intf-cons",
                ],
                [
                    "CSCwj49418",
                    "test",
                    "intf-prov",
                    "N/A",
                    "uni/tn-CSCwj49418/lDevVip-test/lIf-intf-prov",
                ],
            ],
        ),
        # All vnsRsCIfAtt relations have matching vnsRsCIfAttN relations
        (
            {
                vnsRsCIfAtt_api: read_data(dir, "vnsRsCIfAtt_match.json"),
                vnsRsCIfAttN_api: read_data(dir, "vnsRsCIfAttN_match.json"),
            },
            "6.1(5e)",
            script.PASS,
            [],
        ),
        # One vnsRsCIfAtt relation (cons) missing in vnsRsCIfAttN
        (
            {
                vnsRsCIfAtt_api: read_data(dir, "vnsRsCIfAtt_match.json"),
                vnsRsCIfAttN_api: read_data(dir, "vnsRsCIfAttN_missing_cons.json"),
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "CSCwj49418",
                    "test",
                    "intf-cons",
                    "cons",
                    "uni/tn-CSCwj49418/lDevVip-test/lIf-intf-cons/rscIfAtt-[uni/tn-CSCwj49418/lDevVip-test/cDev-cdev/cIf-[cons]]",
                ]
            ],
        ),
        # vnsRsCIfAttN is empty; all vnsRsCIfAtt relations are missing
        (
            {
                vnsRsCIfAtt_api: read_data(dir, "vnsRsCIfAtt_match.json"),
                vnsRsCIfAttN_api: [],
            },
            "6.1(5e)",
            script.FAIL_O,
            [
                [
                    "CSCwj49418",
                    "test",
                    "intf-cons",
                    "cons",
                    "uni/tn-CSCwj49418/lDevVip-test/lIf-intf-cons/rscIfAtt-[uni/tn-CSCwj49418/lDevVip-test/cDev-cdev/cIf-[cons]]",
                ],
                [
                    "CSCwj49418",
                    "test",
                    "intf-prov",
                    "prov",
                    "uni/tn-CSCwj49418/lDevVip-test/lIf-intf-prov/rscIfAtt-[uni/tn-CSCwj49418/lDevVip-test/cDev-cdev/cIf-[prov]]",
                ],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data
