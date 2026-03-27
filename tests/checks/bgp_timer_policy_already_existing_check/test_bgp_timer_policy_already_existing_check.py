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
    "icurl_outputs, expected_result, expected_data, expected_unformatted_data",
    [
        (
            {faultDelegates: read_data(dir, "faultDelegate_POS.json")},
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
            script.PASS,
            [],
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, expected_result, expected_data, expected_unformatted_data):
    result = run_check()
    assert result.result == expected_result
    assert result.data == expected_data
    assert result.unformatted_data == expected_unformatted_data
