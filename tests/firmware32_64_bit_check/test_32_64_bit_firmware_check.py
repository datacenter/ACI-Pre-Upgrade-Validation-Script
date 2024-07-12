import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
firmwareFiles =	'firmwareFirmware.json'

@pytest.mark.parametrize(
	"icurl_outputs, cversion, tversion, expected_result",
	[
		##FAILING = AFFECTED VERSION + AFFECTED MO
		(
			{firmwareFiles: read_data(dir, "incorrect-firmwareFirmware.json"), 
			},
			"5.2(7f)", "6.0(2h)", script.FAIL_O,
		),
		## FAILING = AFFECTED VERSION + AFFECTED MO NON EXISTING
		(
			{firmwareFiles: read_data(dir, "NA-firmwareFirmware.json"),
			 },
			 "4.2(7f)", "6.0(2h)", script.FAIL_O,
		),
		##PASSING = AFFECTED VERSION + NON-AFFECTED MO
		(
			{firmwareFiles: read_data(dir, "correct-firmwareFirmware.json"),
			},
			"5.2(7f)", "6.0(2h)", script.PASS,
		),
		##PASSING = NON-AFFECTED VERSION + AFFECTED MO
		(
			{firmwareFiles: read_data(dir, "NA-firmwareFirmware.json"),
			},
			"5.1(1a)", "5.2(7d)", script.NA,
		),

	],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
	result = script.sixty_four_and_thirty_two_memory_image_check(1, 1, script.AciVersion(cversion), script.AciVersion(tversion))
	assert result == expected_result
	