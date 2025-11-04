import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "mini_aci_6_0_2_check"

# icurl queries
topSystems = 'topSystem.json?query-target-filter=wcard(topSystem.role,"controller")'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        (
            {topSystems: read_data(dir, "topSystem_controller_neg.json")},
            "3.2(1a)",
            "5.2(6a)",
            script.PASS,
        ),
        (
            {topSystems: read_data(dir, "topSystem_controller_neg.json")},
            "6.0(2e)",
            "6.0(5d)",
            script.PASS,
        ),
        (
            {topSystems: read_data(dir, "topSystem_controller_neg.json")},
            "5.2(3a)",
            "6.0(3d)",
            script.PASS,
        ),
        (
            {topSystems: read_data(dir, "topSystem_controller_pos.json")},
            "4.1(1a)",
            "5.2(7f)",
            script.PASS,
        ),
        (
            {topSystems: read_data(dir, "topSystem_controller_pos.json")},
            "4.2(2a)",
            "6.0(2c)",
            script.FAIL_UF,
        ),
        (
            {topSystems: read_data(dir, "topSystem_controller_pos.json")},
            "6.0(1a)",
            "6.0(2c)",
            script.FAIL_UF,
        ),
        (
            {topSystems: read_data(dir, "topSystem_controller_pos.json")},
            "6.0(2c)",
            "6.0(5c)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
