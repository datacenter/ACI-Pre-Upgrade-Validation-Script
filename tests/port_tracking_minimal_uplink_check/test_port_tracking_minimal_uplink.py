import os
import pytest
import logging
import importlib
from helpers.utils import read_data
script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
infra_port_track_pol_api = 'uni/infra/trackEqptFabP-default.json'
@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_neg.json")},
            script.PASS,
        ),
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_neg1.json")},
            script.PASS,
        ),
        (
            {infra_port_track_pol_api: read_data(dir, "infraPortTrackPol_pos.json")},
            script.FAIL_O,
        )
    ],
)

def test_logic(mock_icurl, tversion, expected_result):
    tversion = script.AciVersion(tversion) if tversion else None
    result = script.port_tracking_minimal_uplink_check(1, 1, tversion)
    assert result == expected_result