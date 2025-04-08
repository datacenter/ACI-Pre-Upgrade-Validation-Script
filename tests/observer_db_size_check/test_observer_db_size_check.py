import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

topSystems = 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {topSystems: read_data(dir, "topSystem_controller_pos.json")},
            script.FAIL_UF,
        ),
        (
            {topSystems: read_data(dir, "topSystem_controller_na.json")},
            script.ERROR,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.observer_db_size_check(1, 1)
    assert result == expected_result
