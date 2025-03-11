import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))




# icurl queries
eqptFC = 'eqptFC.json'
eqptLC = 'eqptLC.json'

commCiphers = 'commCipher.json'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {
		eqptFC: read_data(dir, "eqptFC_POS.json"),
		eqptLC: read_data(dir, "eqptLC_POS.json")
	    },
            script.MANUAL,
        ),
        (
            {
		eqptFC: read_data(dir, "eqptFC_NEG.json"),
		eqptLC: read_data(dir, "eqptLC_NEG.json")
	    },
            script.PASS,
        )
    ],
)
def test_logic(mock_icurl,expected_result):
    result = script.clock_signal_component_failure(1, 1)
    assert result == expected_result
