import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

# icurl queries
firmware_60_api =	'firmwareFirmware.json'
firmware_60_api +=	'?query-target-filter=eq(firmwareFirmware.fullVersion,"n9000-16.0(3e)")'

# icurl queries
firmware_52_api =	'firmwareFirmware.json'
firmware_52_api +=	'?query-target-filter=eq(firmwareFirmware.fullVersion,"n9000-15.2(7d)")'

@pytest.mark.parametrize(
	"icurl_outputs, tversion, expected_result",
	[
		##FAILING = AFFECTED VERSION + AFFECTED MO
		(
			{firmware_60_api: read_data(dir, "firmwareFirmware_pos.json"), 
			},
			"6.0(3e)", script.FAIL_UF,
		),
		## FAILING = AFFECTED VERSION + AFFECTED MO NON EXISTING
		(
			{firmware_60_api: read_data(dir, "firmwareFirmware_empty.json"),
			 },
			 "6.0(3e)", script.FAIL_UF,
		),
		##PASSING = AFFECTED VERSION + NON-AFFECTED MO
		(
			{firmware_60_api: read_data(dir, "firmwareFirmware_neg.json"),
			},
			"6.0(3e)", script.PASS,
		),
		##PASSING = NON-AFFECTED VERSION + AFFECTED MO
		(
			{firmware_52_api: read_data(dir, "firmwareFirmware_empty.json"),
			},
			"5.2(7d)", script.NA,
		),

	],
)
def test_logic(mock_icurl, tversion, expected_result):
	result = script.validate_32_64_bit_image_check(1, 1, script.AciVersion(tversion))
	assert result == expected_result
	