import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "configpush_shard_check"

# icurl queries
configpushShardCont_api = 'configpushShardCont.json'
configpushShardCont_api += '?query-target-filter=and(eq(configpushShardCont.tailTx,"0"),ne(configpushShardCont.headTx,"0"))'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # tversion not given 
        (
            {configpushShardCont_api: []},
            None,
            script.MANUAL,
        ),
        # Non-fixed Versions
        (
            # affected tversion, configpushShardCont_api has non-zero headTx / tailTx
            {configpushShardCont_api: read_data(dir, "configpushShardCont_pos.json")},
            "6.0(3a)",
            script.FAIL_O,
        ),
        (
            # affected tversion, all configpushShardCont_api tx are 0
            {configpushShardCont_api: []},
            "5.2(6a)",
            script.PASS,
        ),
        # Fixed Versions
        (
            # non-affected tversion, configpushShardCont_api has non-zero headTx / tailTx
            {configpushShardCont_api: read_data(dir, "configpushShardCont_pos.json")},
            "6.1(6b)",
            script.NA,
        ),
        (
            # non-affected tversion, all configpushShardCont_api tx are 0
            {configpushShardCont_api: []},
            "6.1(4b)",
            script.NA,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
