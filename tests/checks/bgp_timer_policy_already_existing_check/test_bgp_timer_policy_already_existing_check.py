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
    "icurl_outputs, tversion, cversion, expected_result, expected_data, expected_msg",
    [
        # target release not affected (> 6.2(1g))
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.2(2a)",
            "6.1(1a)",
            script.NA,
            [],
            None,
        ),
        # target release not affected on 6.1 train (> 6.1(5e))
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.1(5f)",
            "6.1(1a)",
            script.NA,
            [],
            None,
        ),
        # boundary version is still affected for strict newer_than check
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.2(1g)",
            "6.1(1a)",
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
            None,
        ),
        # 6.1 boundary version is still affected for strict newer_than check
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.1(5e)",
            "6.1(1a)",
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
            None,
        ),
        # target release affected on 6.1 train (< 6.1(5e))
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.1(5a)",
            "6.1(1a)",
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
            None,
        ),
        # current and target versions both beyond affected range: manual clearance required
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
            "6.2(2a)",
            "6.2(2a)",
            script.MANUAL,
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
            "Clear the fault code F0467 for bgp timer policy",
        ),
        (
            {faultDelegates: read_data(dir, "faultDelegate_NEG.json")},
            "6.1(5a)",
            "6.1(1a)",
            script.PASS,
            [],
            None,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, cversion, expected_result, expected_data, expected_msg):
    result = run_check(tversion=script.AciVersion(tversion), cversion=script.AciVersion(cversion))
    assert result.result == expected_result
    assert result.data == expected_data
    if expected_msg is not None:
        assert result.msg == expected_msg