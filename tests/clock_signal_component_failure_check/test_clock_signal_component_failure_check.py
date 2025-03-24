import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


eqptFC_api = 'eqptFC.json'
eqptFC_api += '?query-target-filter=or(eq(eqptFC.model,"N9K-C9504-FM-E"),eq(eqptFC.model,"N9K-C9508-FM-E"))'

eqptLC_api = 'eqptLC.json'
eqptLC_api += '?query-target-filter=eq(eqptLC.model,"N9K-X9732C-EX")'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    # Positive cases, one or both classes return an affected model
    [
        (
            {
		eqptFC_api: read_data(dir, "eqptFC_POS.json"),
		eqptLC_api: read_data(dir, "eqptLC_POS.json")
	    },
            script.MANUAL,
        ),
        (
            {
		eqptFC_api: read_data(dir, "eqptFC_POS.json"),
		eqptLC_api: read_data(dir, "eqptLC_NEG.json")
	    },
            script.MANUAL,
        ),
        (
            {
		eqptFC_api: read_data(dir, "eqptFC_NEG.json"),
		eqptLC_api: read_data(dir, "eqptLC_POS.json")
	    },
            script.MANUAL,
        ),
        # Both classes return empty
        (
            {
		eqptFC_api: read_data(dir, "eqptFC_NEG.json"),
		eqptLC_api: read_data(dir, "eqptLC_NEG.json")
	    },
            script.PASS,
        )
    ],
)
def test_logic(mock_icurl,expected_result):
    result = script.clock_signal_component_failure_check(1, 1)
    assert result == expected_result
