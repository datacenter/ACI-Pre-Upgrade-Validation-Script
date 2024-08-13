import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
eqptSpCmnBlk = 'eqptSpCmnBlk.json?&query-target-filter=wcard(eqptSpromSupBlk.dn,"sup")'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # Affected Sups and on 5.2
        (
            {eqptSpCmnBlk: read_data(dir, "eqptSpCmnBlk_POS.json")},
            "5.2(1g)",
            "5.2(8e)",
            script.FAIL_O,
        ),
        # Affected Sups, going to fixed version
        (
            {eqptSpCmnBlk: read_data(dir, "eqptSpCmnBlk_POS.json")},
            "5.2(1g)",
            "5.2(8f)",
            script.PASS,
        ),
        # Affected sups, going to fixed version
        (
            {eqptSpCmnBlk: read_data(dir, "eqptSpCmnBlk_POS.json")},
            "6.0(1a)",
            "6.0(3d)",
            script.PASS,
        ),
        # affected sups, not yet on 5.2
        (
            {eqptSpCmnBlk: read_data(dir, "eqptSpCmnBlk_POS.json")},
            "4.2(3g)",
            "5.2(2h)",
            script.PASS,
        ),
        # no affected sups
        (
            {eqptSpCmnBlk: read_data(dir, "eqptSpCmnBlk_NEG.json")},
            "5.2(1g)",
            "5.2(8e)",
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.sup_hwrev_check(
        1, 1, script.AciVersion(cversion), script.AciVersion(tversion)
    )
    assert result == expected_result
