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
lldpInst_api = "lldpInst.json?query-target-filter=wcard(lldpInst.dn,\"/node-1/\")"
fvnsEncapBlk_api = "fvnsEncapBlk.json?query-target-filter=eq(fvnsEncapBlk.role,\"external\")"


@pytest.mark.parametrize(
	"icurl_outputs, tversion, expected_result, expected_data, expected_unformatted_data",
	[
		# Case 1: tversion missing. Expected: MANUAL.
		(
			{},
			None,
			script.MANUAL,
			[],
			[],
		),
		# Case 2: Version not affected (6.0(9f) is below 6.1(3f)). Expected: NA.
		(
			{},
			"6.0(9f)",
			script.NA,
			[],
			[],
		),
		# Case 3: Version not affected (6.1(3e) is just below lower boundary 6.1(3f)). Expected: NA.
		(
			{},
			"6.1(3e)",
			script.NA,
			[],
			[],
		),
		# Case 4: Version not affected (6.1(6a) is above upper boundary 6.1(5e) and not 6.2(1g)). Expected: NA.
		(
			{},
			"6.1(6a)",
			script.NA,
			[],
			[],
		),
		# Case 5: lldpInst returns no data so infraVlan cannot be determined. Expected: ERROR.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_empty.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap_single_vlan_pool.json"),
			},
			"6.2(1g)",
			script.ERROR,
			[],
			[],
		),
		# Case 6: InfraVLAN overlaps on lower boundary version 6.1(3f). Expected: FAIL_UF.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap_single_vlan_pool.json"),
			},
			"6.1(3f)",
			script.FAIL_UF,
			[["4093", "vlan-100 to vlan-4094", "uni/infra/vlanns-[vlan_pool]-static/from-[vlan-100]-to-[vlan-4094]"]],
			[],
		),
		# Case 7: InfraVLAN overlaps on a mid-range version 6.1(4a). Expected: FAIL_UF.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap_single_vlan_pool.json"),
			},
			"6.1(4a)",
			script.FAIL_UF,
			[["4093", "vlan-100 to vlan-4094", "uni/infra/vlanns-[vlan_pool]-static/from-[vlan-100]-to-[vlan-4094]"]],
			[],
		),
		# Case 8: InfraVLAN overlaps on upper boundary version 6.1(5e). Expected: FAIL_UF.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap_single_vlan_pool.json"),
			},
			"6.1(5e)",
			script.FAIL_UF,
			[["4093", "vlan-100 to vlan-4094", "uni/infra/vlanns-[vlan_pool]-static/from-[vlan-100]-to-[vlan-4094]"]],
			[],
		),
		# Case 9: InfraVLAN overlaps on standalone affected version 6.2(1g). Expected: FAIL_UF.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap_single_vlan_pool.json"),
			},
			"6.2(1g)",
			script.FAIL_UF,
			[["4093", "vlan-100 to vlan-4094", "uni/infra/vlanns-[vlan_pool]-static/from-[vlan-100]-to-[vlan-4094]"]],
			[],
		),
		# Case 10: InfraVLAN does not overlap on affected version 6.2(1g). Expected: PASS.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_no_overlap.json"),
			},
			"6.2(1g)",
			script.PASS,
			[],
			[],
		),
		# Case 11: Single lldpInst entry with overlap on affected version 6.2(1g). Expected: FAIL_UF.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_single_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap_single_vlan_pool.json"),
			},
			"6.2(1g)",
			script.FAIL_UF,
			[["4093", "vlan-100 to vlan-4094", "uni/infra/vlanns-[vlan_pool]-static/from-[vlan-100]-to-[vlan-4094]"]],
			[],
		),
		# Case 12: InfraVLAN overlaps on multiple VLAN pools including VMM domain blocks on 6.2(1g). Expected: FAIL_UF.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap_multiple_vlan_pool.json"),
			},
			"6.2(1g)",
			script.FAIL_UF,
			[
				["4093", "vlan-100 to vlan-4094", "uni/infra/vlanns-[vlan_pool1]-static/from-[vlan-100]-to-[vlan-4094]"],
				["4093", "vlan-100 to vlan-4094", "uni/infra/vlanns-[vlan_pool2]-static/from-[vlan-200]-to-[vlan-4094]"],
				["4093", "vlan-4000 to vlan-4094", "uni/infra/vlanns-[vlan_pool3]-static/from-[vlan-4000]-to-[vlan-4094]"],
				["4093", "vlan-1751 to vlan-4094", "uni/vmmp-VMware/dom-k8s-scale-vmm/usrcustomaggr-k8srkesetup1/from-[vlan-1751]-to-[vlan-4094]"],
				["4093", "vlan-1752 to vlan-4094", "uni/vmmp-VMware/dom-k8s-scale-vmm/usrcustomaggr-k8srkesetup1/from-[vlan-1752]-to-[vlan-4094]"],
			],
			[],
		),
		# Case 13: InfraVLAN exists and empty fvnsEncapBlk for vlan pools on standalone affected version 6.2(1g). Expected: PASS.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_empty.json"),
			},
			"6.2(1g)",
			script.PASS,
			[],
			[],
		),
		# Case 14: Overlap found with malformed DN format. Expected: FAIL_UF with row captured in unformatted_data.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_overlap_malformed_dn.json"),
			},
			"6.2(1g)",
			script.ERROR,
			[],
			[["4093", "vlan-4000 to vlan-4094", "uni/infra/vlanpool/vlan-4000-4094"]],
		),
		# Case 15: Missing dn/from/to attributes in fvnsEncapBlk. Expected: ERROR.
		(
			{
				lldpInst_api: read_data(dir, "lldpInst_infra_vlan_multiple_entry.json"),
				fvnsEncapBlk_api: read_data(dir, "fvnsEncapBlk_missing_attrs.json"),
			},
			"6.2(1g)",
			script.ERROR,
			[],
			[],
		),
	],
)
def test_logic(run_check, mock_icurl, tversion, expected_result, expected_data, expected_unformatted_data):
	result = run_check(tversion=script.AciVersion(tversion) if tversion else None)
	assert result.result == expected_result
	assert result.data == expected_data
	assert result.unformatted_data == expected_unformatted_data
