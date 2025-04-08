import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
hpath_api =  'infraRsHPathAtt.json'
oosPorts_api =  'fabricRsOosPath.json'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # Issue 1, wrong CLASSID in fabricPathEP
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_pos1.json"),
             oosPorts_api: read_data(dir, "fabricRsOosPath_pos1.json")},
            script.FAIL_UF,
        ),
        # Issue 2, malformed eths
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_pos2.json"),
             oosPorts_api: read_data(dir, "fabricRsOosPath_pos2.json")},
            script.FAIL_UF,
        ),
        # issue 3, FEX within eth instead of in ext path of tDn
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_pos3.json"),
             oosPorts_api: read_data(dir, "fabricRsOosPath_pos3.json")},
            script.FAIL_UF,
        ),
        # issue 4, FEX less than 101 within ext path definition
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_pos4.json"),
             oosPorts_api: read_data(dir, "fabricRsOosPath_pos4.json")},
            script.FAIL_UF,
        ),
        # Issue 5, breakout eth definition greather than 16
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_pos5.json"),
             oosPorts_api: read_data(dir, "fabricRsOosPath_pos5.json")},
            script.FAIL_UF,
        ),
        # Issue 6, eth with x/0 port defined
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_pos6.json"),
             oosPorts_api: read_data(dir, "fabricRsOosPath_pos6.json")},
            script.FAIL_UF,
        ),
        # NO ISSUES
        (
            {hpath_api: read_data(dir, "infraRsHPathAtt_neg.json"),
             oosPorts_api: read_data(dir, "fabricRsOosPath_neg.json")},
            script.PASS,
        ),

    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.fabricPathEP_target_check(1, 1)
    assert result == expected_result
