import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
topSystems = 'topSystem.json'
topSystems += '?rsp-subtree=children&rsp-subtree-class=l1PhysIf,eqptCh'
topSystems += '&rsp-subtree-filter=or(eq(l1PhysIf.fecMode,"ieee-rs-fec"),eq(l1PhysIf.fecMode,"cons16-rs-fec"),eq(eqptCh.model,"N9K-C93180YC-EX"))'
topSystems += '&rsp-subtree-include=required'

@pytest.mark.parametrize(
    "icurl_outputs, sw_cversion, tversion, expected_result",
    [
        (
            {topSystems: read_data(dir, "topSystem_pos.json")},
            "4.2(3d)",
            "4.2(7f)",
            script.PASS,
        ),
        (
            {topSystems: read_data(dir, "topSystem_pos.json")},
            "5.2(6d)",
            "6.0(3c)",
            script.PASS,
        ),
        (
            {topSystems: read_data(dir, "topSystem_pos.json")},
            "4.2(7f)",
            "5.2(5c)",
            script.FAIL_O,
        ),
        (
            {topSystems: read_data(dir, "topSystem_neg.json")},
            "4.2(7f)",
            "5.2(5c)",
            script.PASS,
        ),
        (
            {topSystems: []},
            "4.2(7f)",
            "5.2(5c)",
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, sw_cversion, tversion, expected_result):
    result = script.unsupported_fec_configuration_ex_check(
        1,
        1,
        script.AciVersion(sw_cversion),
        script.AciVersion(tversion),
    )
    assert result == expected_result