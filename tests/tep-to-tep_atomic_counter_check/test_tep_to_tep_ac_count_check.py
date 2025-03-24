import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

# icurl queries
atomic_counter_api = 'dbgAcPath.json'
atomic_counter_api += '&rsp-subtree-include=count'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        ##FAILING = COUNT > 1600
        (
            {atomic_counter_api: read_data(dir, "dbgAcPath_max.json"), 
            },
            script.FAIL_UF,
        ),
        ##PASSING = COUNT > 0 < = 1600
        (
            {atomic_counter_api: read_data(dir, "dbgAcPath_pass.json"),
            },
            script.PASS,
        ),
        ##N/A = COUNT EQUAL 0
        (
            {atomic_counter_api: read_data(dir, "dbgAcPath_na.json"),
            },
            script.NA,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.validate_tep_to_tep_ac_counter_check(1, 1)
    assert result == expected_result