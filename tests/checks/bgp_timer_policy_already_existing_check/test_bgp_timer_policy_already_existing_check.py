import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "bgpProto_timer_policy_already_existing_check"
# icurl queries
faultDelegates = 'faultDelegate.json?query-target-filter=and(eq(faultDelegate.code,"F0467"),wcard(faultDelegate.changeSet,"bgpProt-policy-already-existing"))'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result, expected_data, expected_unformatted_data",
    [
        # target release not affected (>= 6.2(3a))
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.2(3a)",
            script.NA,
            [],
            [],
        ),
        # target release not affected on 6.1 train (>= 6.1(6a))
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.1(6a)",
            script.NA,
            [],
            [],
        ),
        # target release affected (< 6.2(3a))
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.2(2a)",
            script.FAIL_O,
            [
                [
                    "F0467",
                    "common",
                    "L3outY",
                    "configQual:bgpProt-policy-already-existing, configSt:failed-to-apply, temporaryError:no",
                ],
                [
                    "F0467",
                    "prod",
                    "L3outA",
                    "configQual:bgpProt-policy-already-existing, configSt:failed-to-apply, temporaryError:no",
                ],
            ],
            [],
        ),
        # target release affected on 6.1 train (< 6.1(6a))
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.1(5a)",
            script.FAIL_O,
            [
                [
                    "F0467",
                    "common",
                    "L3outY",
                    "configQual:bgpProt-policy-already-existing, configSt:failed-to-apply, temporaryError:no",
                ],
                [
                    "F0467",
                    "prod",
                    "L3outA",
                    "configQual:bgpProt-policy-already-existing, configSt:failed-to-apply, temporaryError:no",
                ],
            ],
            [],
        ),
        (
            {faultDelegates: read_data(dir, "faultDelegate_UNFORMATTED.json")},
            "6.1(5a)",
            script.FAIL_O,
            [],
            [
                [
                    "F0467",
                    "resPolCont/rtdOutCont/rtdOutDef-[uni/invalid]/nwissues",
                    "configQual:bgpProt-policy-already-existing, configSt:failed-to-apply, temporaryError:no",
                ],
            ],
        ),
        (
            {faultDelegates: read_data(dir, "faultDelegate_NEG.json")},
            "6.1(5a)",
            script.PASS,
            [],
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result, expected_data, expected_unformatted_data):
    result = run_check(tversion=script.AciVersion(tversion))
    assert result.result == expected_result
    assert result.data == expected_data
    assert result.unformatted_data == expected_unformatted_data
