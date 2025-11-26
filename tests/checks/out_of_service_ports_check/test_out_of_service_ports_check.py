import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "out_of_service_ports_check"

# operst: '1' = 'up'
# usage: '32' = 'blacklist', '2' = 'epg'. '34'= 'blacklist,epg'
ethpmPhysIf_api = 'ethpmPhysIf.json'
ethpmPhysIf_api += '?query-target-filter=and(eq(ethpmPhysIf.operSt,"2"),bw(ethpmPhysIf.usage,"32","34"))'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            # Two 'up' ports flagged with 'blacklist,epg'
            {ethpmPhysIf_api: read_data(dir, "ethpmPhysIf-pos.json")},
            script.FAIL_O,
        ),
        (
            # 0 ports returned
            {ethpmPhysIf_api: read_data(dir, "ethpmPhysIf-neg.json")},
            script.PASS,
        )
    ],
)
def test_logic(run_check, mock_icurl, expected_result):
    result = run_check()
    assert result.result == expected_result
