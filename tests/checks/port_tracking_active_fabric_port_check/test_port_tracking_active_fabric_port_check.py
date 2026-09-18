import os
import pytest
import logging
import importlib
from helpers.utils import read_data
script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "port_tracking_active_fabric_port_check"
infra_port_track_pol_api = 'uni/infra/trackEqptFabP-default.json'
@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [   
        # tversion not given 
        (
            {infra_port_track_pol_api: []},
            None,
            script.MANUAL,
        ),
        # tversion is not hit
        (
            {infra_port_track_pol_api: []},
            "6.0(9e)",
            script.NA,
        ),
        #adminSt is off.
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_neg.json")},
            "6.0(9d)",
            script.PASS,
        ),
        #adminSt is on, but minlinks is not zero.
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_neg1.json")},
            "6.0(9d)",
            script.PASS,
        ),
        #adminSt is on, and minlinks is zero.
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_pos.json")},
            "6.0(9d)",
            script.FAIL_O,
        )
    ],
)

def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
