import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries

fcEntitys = 'fcEntity.json'
fabricNodes = 'fabricNode.json'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            {fcEntitys: read_data(dir, "fcEntity_POS.json"),
            fabricNodes: read_data(dir, "fabricNode_POS.json")},
            "6.1(1f)",
            script.FAIL_O,
        ),
        (
            {fcEntitys: read_data(dir, "fcEntity_POS.json"),
            fabricNodes: read_data(dir, "fabricNode_POS.json")},
            "6.0(7e)",
            script.FAIL_O,
        ),
        (
            {fcEntitys: read_data(dir, "fcEntity_POS.json"),
            fabricNodes: read_data(dir, "fabricNode_POS.json")},
            "6.0(1f)",
            script.NA,
        ),
        (
            {fcEntitys: read_data(dir, "fcEntity_NEG.json"),
            fabricNodes: read_data(dir, "fabricNode_NEG.json")},
            "6.1(1f)",
            script.NA,
        ),
        (
            {fcEntitys: read_data(dir, "fcEntity_NEG.json"),
            fabricNodes: read_data(dir, "fabricNode_NEG.json")},
            "6.0(7e)",
            script.NA,
        ),
        (
            {fcEntitys: read_data(dir, "fcEntity_POS.json"),
            fabricNodes: read_data(dir, "fabricNode_NEG.json")},
            "6.0(7e)",
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.fc_ex_model_check(1, 1, script.AciVersion(tversion))
    assert result == expected_result
