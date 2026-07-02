import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "infravlan_overlap_access_policy_check"

# icurl queries
lldpInst_api = "lldpInst.json"
fvnsEncapBlk_api = "fvnsEncapBlk.json"


@pytest.mark.parametrize(
	"icurl_outputs, tversion, expected_result",
	[
		# Case 1 : infraVlan overlapping in user configured vlan pool range
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap.json"),
			},
			"6.2(1g)",
			script.FAIL_O,
		),
		# Case 2 : infraVlan not overlapping in user configured vlan pool range
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_no_overlap.json"),
			},
			"6.2(1g)",
			script.PASS,
		),
		# case 3 : version not impacting the check, so result should be NA
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap.json"),
			},
			"6.0(9f)",
			script.NA,
		),
		# case 3 : tversion missing check
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap.json"),
			},
			None,
			script.MANUAL,
		),
	],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
	result = run_check(tversion=script.AciVersion(tversion)if tversion else None)
	assert result.result == expected_result
	


