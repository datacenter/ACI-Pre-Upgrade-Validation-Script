import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
leaf_api = 'fabricNode.json?query-target-filter=eq(fabricNode.model,"N9K-C93180YC-FX3")'
procMemUsage_api = 'procMemUsage.json'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # Version not supplied
        ({leaf_api: []}, None, script.MANUAL),
        # no  N9K-C93180YC-FX3
        ({leaf_api: [], procMemUsage_api: []}, "6.0(9c)", script.NA),
        ({leaf_api: [], procMemUsage_api: []}, "6.1(1f)", script.NA),
        #  N9K-C93180YC-FX3 Present, Memory not affected
        ({
            leaf_api: read_data(dir, "fabricNode_YC-FX3.json"), 
            procMemUsage_api: read_data(dir, "procMemUsagegt32gb.json")}, 
          "6.0(9d)", script.PASS),

        ({
            leaf_api: read_data(dir, "fabricNode_YC-FX3.json"), 
            procMemUsage_api: read_data(dir, "procMemUsagegt32gb.json")}, 
          "6.1(2f)", script.PASS),
        #  N9K-C93180YC-FX3 Present, Memory affected, Less than 32GB
        ({
            leaf_api: read_data(dir, "fabricNode_YC-FX3.json"), 
            procMemUsage_api: read_data(dir, "procMemUsagelt32gb.json")}, 
          "6.0(9d)", script.FAIL_O),

        ({
            leaf_api: read_data(dir, "fabricNode_YC-FX3.json"), 
            procMemUsage_api: read_data(dir, "procMemUsagelt32gb.json")}, 
          "6.1(2f)", script.FAIL_O),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.n9k_c93108yc_fx3_mem_check(
        1,
        1,
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result
