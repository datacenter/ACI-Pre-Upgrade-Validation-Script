import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
api = 'fabricNode.json?query-target-filter=or(eq(fabricNode.model,"N9K-C93108TC-FX3P"),eq(fabricNode.model,"N9K-C93108TC-FX3H"))'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # Version not supplied
        ({api: []}, None, script.MANUAL),
        # Version not affected
        ({api: read_data(dir, "fabricNode_FX3P3H.json")}, "5.2(8h)", script.PASS),
        ({api: read_data(dir, "fabricNode_FX3P3H.json")}, "5.3(2b)", script.PASS),
        ({api: read_data(dir, "fabricNode_FX3P3H.json")}, "6.0(4c)", script.PASS),
        # Affected version, no FX3P or FX3H
        ({api: []}, "5.2(8g)", script.PASS),
        ({api: []}, "5.3(1d)", script.PASS),
        ({api: []}, "6.0(2h)", script.PASS),
        # Affected version, FX3P
        ({api: read_data(dir, "fabricNode_FX3P.json")}, "5.2(8g)", script.FAIL_O),
        ({api: read_data(dir, "fabricNode_FX3P.json")}, "5.3(1d)", script.FAIL_O),
        ({api: read_data(dir, "fabricNode_FX3P.json")}, "6.0(2h)", script.FAIL_O),
        # Affected version, FX3H
        ({api: read_data(dir, "fabricNode_FX3H.json")}, "5.2(8g)", script.FAIL_O),
        ({api: read_data(dir, "fabricNode_FX3H.json")}, "5.3(1d)", script.FAIL_O),
        ({api: read_data(dir, "fabricNode_FX3H.json")}, "6.0(2h)", script.FAIL_O),
        # Affected version, FX3P and FX3H
        ({api: read_data(dir, "fabricNode_FX3P3H.json")}, "5.2(8g)", script.FAIL_O),
        ({api: read_data(dir, "fabricNode_FX3P3H.json")}, "5.3(1d)", script.FAIL_O),
        ({api: read_data(dir, "fabricNode_FX3P3H.json")}, "6.0(2h)", script.FAIL_O),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.n9k_c93108tc_fx3p_interface_down_check(
        1,
        1,
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result
