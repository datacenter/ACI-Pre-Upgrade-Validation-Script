import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "clock_signal_component_failure_check"

eqptFC_api = 'eqptFC.json'
eqptFC_api += '?query-target-filter=or(eq(eqptFC.model,"N9K-C9504-FM-E"),eq(eqptFC.model,"N9K-C9508-FM-E"))'

eqptLC_api = 'eqptLC.json'
eqptLC_api += '?query-target-filter=eq(eqptLC.model,"N9K-X9732C-EX")'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_serials",
    # Positive cases, one or both classes return an affected model
    [
        (
            {
		eqptFC_api: read_data(dir, "eqptFC_POS.json"),
		eqptLC_api: read_data(dir, "eqptLC_POS.json")
	    },
            script.MANUAL,
            ["FOC235053QS", "FOC23506V60", "FOC23506V3J", "FOC235053QU", "FOC235053MR", "FDO23260QX5"],
        ),
        (
            {
		eqptFC_api: read_data(dir, "eqptFC_POS.json"),
		eqptLC_api: read_data(dir, "eqptLC_NEG.json")
	    },
            script.MANUAL,
            ["FOC235053QS", "FOC23506V60", "FOC23506V3J", "FOC235053QU", "FOC235053MR"],
        ),
        (
            {
		eqptFC_api: read_data(dir, "eqptFC_NEG.json"),
		eqptLC_api: read_data(dir, "eqptLC_POS.json")
	    },
            script.MANUAL,
            ["FDO23260QX5"],
        ),
        # Both classes return empty
        (
            {
		eqptFC_api: read_data(dir, "eqptFC_NEG.json"),
		eqptLC_api: read_data(dir, "eqptLC_NEG.json")
	    },
            script.PASS,
            [],
        )
    ],
)
def test_logic(run_check, mock_icurl, expected_result, expected_serials):
    result = run_check()
    assert result.result == expected_result
    if expected_result == script.MANUAL:
        assert "shipped after December 5, 2016 are not affected" in result.recommended_action
        assert "on or before December 5, 2016" in result.recommended_action
        assert "contact Cisco TAC" in result.recommended_action
        assert "V01 Version ID (VID) is only possibly affected" in result.recommended_action
        assert all(serial in result.recommended_action for serial in expected_serials)
        assert "chat interface" not in result.recommended_action
        assert "Serial Number Validation tool" not in result.recommended_action
