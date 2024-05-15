import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
hpath_api =  'infraRsHPathAtt.json?query-target-filter=wcard(infraRsHPathAtt.dn,"eth")'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_pos.json")},
            script.FAIL_UF,
        ),
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_neg.json")},
            script.PASS,
        ),

    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.invalid_fex_rs_check(1, 1)
    assert result == expected_result
