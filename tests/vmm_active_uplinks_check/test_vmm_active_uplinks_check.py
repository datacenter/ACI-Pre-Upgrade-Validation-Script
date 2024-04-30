import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
uplink_api =  'fvUplinkOrderCont.json' 
uplink_api += '?query-target-filter=eq(fvUplinkOrderCont.active,"")'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {uplink_api: read_data(dir, "fvUplinkOrderCont_pos.json")},
            script.FAIL_O,
        ),
        (
            {uplink_api: read_data(dir, "fvUplinkOrderCont_neg.json")},
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.vmm_active_uplinks_check(1, 1)
    assert result == expected_result
