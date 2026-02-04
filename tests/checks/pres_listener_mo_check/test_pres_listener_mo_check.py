import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "pres_listener_mo_check"

# icurl queries
# fabricNode = "fabricNode.json"
# fabricNode += '?query-target-filter=and(eq(fabricNode.role,"leaf"),eq(fabricNode.fabricSt,"active"))'

presListener = "presListener.json"

@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, tversion, expected_result",
    [
        # No tVersion, MANUAL
        (
            {presListener: read_data(dir, "presListener-Pos.json")},
            [],
            None,
            script.MANUAL
        ),        
        # FabricNodes missing, MANUAL
        (
            {presListener: read_data(dir, "presListener-Pos.json")},
            [],
            "6.1(3a)",
            script.MANUAL
        ),
        # tVersion newer than 6.1-3f , NA
        (
            {presListener: read_data(dir, "presListener-Pos.json")},
            [],
            "6.1(4a)",
            script.NA
        ),
        # PASS TESTS
        # Version can be recovered with testapi (>=6.1-3f)
        (
            {presListener: read_data(dir, "presListener-Pos.json")},
            read_data(dir, "fabricNode.json"),
            "6.1(3a)",
            script.PASS,
        ),
        # FAIL_O TESTS
                # Version can be recovered with testapi (>=6.1-3f)
        (
            {presListener: read_data(dir, "presListener-Neg.json")},
            read_data(dir, "fabricNode.json"),
            "6.1(3a)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, tversion, expected_result):
    result = run_check(
        fabric_nodes=fabric_nodes,
         tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
