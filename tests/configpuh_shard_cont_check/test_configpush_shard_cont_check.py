import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

# icurl queries
configpushShardCont = 'configpushShardCont.json'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # MANUAL cases
        (
            {configpushShardCont: read_data(dir, "posHead-configpushShardCont.json")},
            None,
            script.MANUAL,
        ),
        # Failure cases
        (
            ## TARGET VERSION IS OLDER THAN 6.1(4), configpushShardCont has non-zero headTx, VALIDATION RESULT : FAIL_O
            {configpushShardCont: read_data(dir, "posHead-configpushShardCont.json")},
            "6.0(3a)",
            script.FAIL_O,
        ),
        (
            ## TARGET VERSION IS OLDER THAN 6.1(4), configpushShardCont has non-zero tailTx, VALIDATION RESULT : FAIL_O
            {configpushShardCont: read_data(dir, "posTail-configpushShardCont.json")},
            "6.0(3a)",
            script.FAIL_O,
        ),        
        # Pass cases
        (
            ## TARGET VERSION IS OLDER THAN 6.1(4), configpushShardCont with zero headTx, VALIDATION RESULT : PASS
            {configpushShardCont: read_data(dir, "neg-configpushShardCont.json")},
            "5.2(6a)",
            script.PASS,
        ),
        # NA cases
        (
            ## TARGET VERSION IS OLDER THAN 6.1(4), NO configpushShardCont, VALIDATION RESULT : NA 
            {configpushShardCont: read_data(dir, "na-configpushShardCont.json")},
            "5.2(6b)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.1(4a), configpushShardCont has non-zero headTx, VALIDATION RESULT : NA
            {configpushShardCont: read_data(dir, "posHead-configpushShardCont.json")},
            "6.1(6b)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.1(4a), configpushShardCont has non-zero tailTx, VALIDATION RESULT : NA
            {configpushShardCont: read_data(dir, "posTail-configpushShardCont.json")},
            "6.1(6b)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.1(4), configpushShardCont with zero headTx, VALIDATION RESULT : NA            
            {configpushShardCont: read_data(dir, "neg-configpushShardCont.json")},
            "6.1(4b)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.1(4), NO configpushShardCont, VALIDATION RESULT : NA           
            {configpushShardCont: read_data(dir, "na-configpushShardCont.json")},
            "6.1(4a)",
            script.NA,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    tversion = script.AciVersion(tversion) if tversion else None
    result = script.configpush_shard_check(1, 1, tversion)
    assert result == expected_result
