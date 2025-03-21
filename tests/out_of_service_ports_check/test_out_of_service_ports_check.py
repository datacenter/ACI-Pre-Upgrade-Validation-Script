import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
ethpmPhysIf_api = 'ethpmPhysIf.json'
ethpmPhysIf_api += '?query-target-filter=and(eq(ethpmPhysIf.operSt,"2"),bw(ethpmPhysIf.usage,"32","34"))'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            ## TWO DISABLED PORTS , ETHPMPHYSIF PORTS with one UP, one DOWN, RESULT = UPGRADE FAILS
            {ethpmPhysIf_api: read_data(dir, "ethpmPhysIf-pos.json")},
            script.FAIL_O,
        ),
        (
            ## TWO DISABLED PORTS , ETHPMPHYSIF PORTS all ports DOWN, RESULT = PASS
            {ethpmPhysIf_api: read_data(dir, "ethpmPhysIf-neg.json")},
            script.PASS,
        )
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.out_of_service_ports_check(1, 1)
    assert result == expected_result
