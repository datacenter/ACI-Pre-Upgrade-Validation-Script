import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "ssd_firmware_version_check"

# icurl queries
eqptFlash_api = 'eqptFlash.json'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # TVERSION not supplied
        (
            {eqptFlash_api: read_data(dir, "eqptFlash_unaffected_models.json")},
            None,
            script.MANUAL,
        ),

        # No eqptFlash objects
        (
            {eqptFlash_api: []},
            "5.2(5e)",
            script.FAIL_UF,
        ),

        # eqptFlash objects present, going to affected apic version and affected firmware models
        (
            {eqptFlash_api: read_data(dir, "eqptFlash_affected_models.json")},
            "5.2(6a)",
            script.FAIL_O,
        ),

        # eqptFlash objects present, going to affected apic version and unaffected firmware models
        (
            {eqptFlash_api: read_data(dir, "eqptFlash_unaffected_models.json")},
            "5.2(6a)",
            script.PASS,
        ),
        
        # Fixed Target Version
        (
            {eqptFlash_api: read_data(dir, "eqptFlash_unaffected_models.json")},
            "6.2(1a)",
            script.NA,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
