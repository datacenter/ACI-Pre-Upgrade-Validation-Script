import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))




# icurl queries
#eqptFC = 'eqptFC.json?&query-target-filter=or(wcard(eqptFC.model,"N9K-C9504-FM-E"),wcard(eqptFC.model,"N9K-C9508-FM-E"))'
eqptLC = 'eqptLC.json?&query-target-filter=wcard(eqptLC.model,"N9K-X9732C-EX")'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {
		eqptLC: read_data(dir, "eqptLC_POS.json")
	    },
            script.MANUAL,
        ),
        (
            {
		eqptLC: read_data(dir, "eqptLC_NEG.json")
	    },
            script.PASS,
        )
    ],
)
def test_logic(mock_icurl,expected_result):
    result = script.clock_signal_component_failure(1, 1)
    assert result == expected_result
