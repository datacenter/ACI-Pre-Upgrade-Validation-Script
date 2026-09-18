import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "switch_group_guideline_check"

# icurl queries
upgrade_grp = "maintMaintGrp.json?rsp-subtree=children"
bgp_rr = "bgpRRNodePEp.json"
ipn_spines = 'l3extRsNodeL3OutAtt.json?query-target-filter=wcard(l3extRsNodeL3OutAtt.dn,"tn-infra/")'
apic_lldp = "lldpCtrlrAdjEp.json"
vpc_pairs = "fabricExplicitGEp.json?rsp-subtree=children&rsp-subtree-class=fabricNodePEp"


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, expected_result, expected_data",
    [
        # PASS
        # Upgrade Grp: EVEN and ODD
        # Spines:
        #   [Pod 1] 1001-1004, RR: 1001,1002, IPN 1001,1002
        #   [Pod 2] 2001-2002, RR: 2001,2002, IPN 2001,2002
        # APIC Leaves:
        #   [Pod 1] 101-102 (APIC 1, 2)
        #   [Pod 2] 201-202 (APIC 3)
        # VPC Leaves:
        #   [Pod 1] 101-102, 111-112
        #   [Pod 2] 201-202
        (
            {
                upgrade_grp: read_data(dir, "maintMaintGrp_EVEN_ODD.json"),
                bgp_rr: read_data(dir, "bgpRRNodePEp_1001_1002_2001_2002.json"),
                ipn_spines: read_data(dir, "l3extRsNodeL3OutAtt_1001_1002_2001_2002.json"),
                apic_lldp: read_data(dir, "lldpCtrlrAdjEp.json"),
                vpc_pairs: read_data(dir, "fabricExplicitGEp.json"),
            },
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
        # FAIL - All HA broken
        # Upgrade Grp: all in one
        # Spines:
        #   [Pod 1] 1001-1004, RR: 1001,1002, IPN 1001,1002
        #   [Pod 2] 2001-2002, RR: 2001,2002, IPN 2001,2002
        # APIC Leaves:
        #   [Pod 1] 101-102 (APIC 1, 2)
        #   [Pod 2] 201-202 (APIC 3)
        # VPC Leaves:
        #   [Pod 1] 101-102, 111-112
        #   [Pod 2] 201-202
        (
            {
                upgrade_grp: read_data(dir, "maintMaintGrp_ALL.json"),
                bgp_rr: read_data(dir, "bgpRRNodePEp_1001_1002_2001_2002.json"),
                ipn_spines: read_data(dir, "l3extRsNodeL3OutAtt_1001_1002_2001_2002.json"),
                apic_lldp: read_data(dir, "lldpCtrlrAdjEp.json"),
                vpc_pairs: read_data(dir, "fabricExplicitGEp.json"),
            },
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [
                ["ALL", "1", "1001,1002,1003,1004", "All spine nodes in this pod are in the same group."],
                ["ALL", "2", "2001,2002", "All spine nodes in this pod are in the same group."],
                ["ALL", "1", "1001,1002", "All RR spine nodes in this pod are in the same group."],
                ["ALL", "2", "2001,2002", "All RR spine nodes in this pod are in the same group."],
                ["ALL", "1", "1001,1002", "All IPN/ISN spine nodes in this pod are in the same group."],
                ["ALL", "2", "2001,2002", "All IPN/ISN spine nodes in this pod are in the same group."],
                ["ALL", "1", "101,102", "All leaf nodes connected to APIC 1 are in the same group."],
                ["ALL", "1", "101,102", "All leaf nodes connected to APIC 2 are in the same group."],
                ["ALL", "2", "201,202", "All leaf nodes connected to APIC 3 are in the same group."],
                ["ALL", "1", "101,102", "Both leaf nodes in the same vPC pair are in the same group."],
                ["ALL", "1", "111,112", "Both leaf nodes in the same vPC pair are in the same group."],
                ["ALL", "2", "201,202", "Both leaf nodes in the same vPC pair are in the same group."],
            ],
        ),
        # FAIL - All HA broken
        # Upgrade Grp: leaves in one group and spines in another
        # Spines:
        #   [Pod 1] 1001-1004, RR: 1001,1002, IPN 1001,1002
        #   [Pod 2] 2001-2002, RR: 2001,2002, IPN 2001,2002
        # APIC Leaves:
        #   [Pod 1] 101-102 (APIC 1, 2)
        #   [Pod 2] 201-202 (APIC 3)
        # VPC Leaves:
        #   [Pod 1] 101-102, 111-112
        #   [Pod 2] 201-202
        (
            {
                upgrade_grp: read_data(dir, "maintMaintGrp_SPINE_LEAF.json"),
                bgp_rr: read_data(dir, "bgpRRNodePEp_1001_1002_2001_2002.json"),
                ipn_spines: read_data(dir, "l3extRsNodeL3OutAtt_1001_1002_2001_2002.json"),
                apic_lldp: read_data(dir, "lldpCtrlrAdjEp.json"),
                vpc_pairs: read_data(dir, "fabricExplicitGEp.json"),
            },
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [
                ["SPINE", "1", "1001,1002,1003,1004", "All spine nodes in this pod are in the same group."],
                ["SPINE", "2", "2001,2002", "All spine nodes in this pod are in the same group."],
                ["SPINE", "1", "1001,1002", "All RR spine nodes in this pod are in the same group."],
                ["SPINE", "2", "2001,2002", "All RR spine nodes in this pod are in the same group."],
                ["SPINE", "1", "1001,1002", "All IPN/ISN spine nodes in this pod are in the same group."],
                ["SPINE", "2", "2001,2002", "All IPN/ISN spine nodes in this pod are in the same group."],
                ["LEAF", "1", "101,102", "All leaf nodes connected to APIC 1 are in the same group."],
                ["LEAF", "1", "101,102", "All leaf nodes connected to APIC 2 are in the same group."],
                ["LEAF", "2", "201,202", "All leaf nodes connected to APIC 3 are in the same group."],
                ["LEAF", "1", "101,102", "Both leaf nodes in the same vPC pair are in the same group."],
                ["LEAF", "1", "111,112", "Both leaf nodes in the same vPC pair are in the same group."],
                ["LEAF", "2", "201,202", "Both leaf nodes in the same vPC pair are in the same group."],
            ],
        ),
        # FAIL - All HA except for pod1 spine broken
        # Upgrade Grp:
        #   GRP1: 101,102,121,122,1001,1002
        #   GRP2: 111,112,201,202,1003,1004,2001,2003
        # Spines:
        #   [Pod 1] 1001-1004, RR: 1001,1002, IPN 1001,1002
        #   [Pod 2] 2001-2002, RR: 2001,2002, IPN 2001,2002
        # APIC Leaves:
        #   [Pod 1] 101-102 (APIC 1, 2)
        #   [Pod 2] 201-202 (APIC 3)
        # VPC Leaves:
        #   [Pod 1] 101-102, 111-112
        #   [Pod 2] 201-202
        (
            {
                upgrade_grp: read_data(dir, "maintMaintGrp_BAD_GRP1_GRP2.json"),
                bgp_rr: read_data(dir, "bgpRRNodePEp_1001_1002_2001_2002.json"),
                ipn_spines: read_data(dir, "l3extRsNodeL3OutAtt_1001_1002_2001_2002.json"),
                apic_lldp: read_data(dir, "lldpCtrlrAdjEp.json"),
                vpc_pairs: read_data(dir, "fabricExplicitGEp.json"),
            },
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [
                ["GRP1", "1", "1001,1002", "All RR spine nodes in this pod are in the same group."],
                ["GRP1", "1", "1001,1002", "All IPN/ISN spine nodes in this pod are in the same group."],
                ["GRP1", "1", "101,102", "All leaf nodes connected to APIC 1 are in the same group."],
                ["GRP1", "1", "101,102", "All leaf nodes connected to APIC 2 are in the same group."],
                ["GRP1", "1", "101,102", "Both leaf nodes in the same vPC pair are in the same group."],
                ["GRP2", "2", "2001,2002", "All spine nodes in this pod are in the same group."],
                ["GRP2", "2", "2001,2002", "All RR spine nodes in this pod are in the same group."],
                ["GRP2", "2", "2001,2002", "All IPN/ISN spine nodes in this pod are in the same group."],
                ["GRP2", "2", "201,202", "All leaf nodes connected to APIC 3 are in the same group."],
                ["GRP2", "1", "111,112", "Both leaf nodes in the same vPC pair are in the same group."],
                ["GRP2", "2", "201,202", "Both leaf nodes in the same vPC pair are in the same group."],
            ],
        ),
        # FAIL - Only pod1 spine RR HA is broken
        # Upgrade Grp:
        #   SPINE_GRP1: 1001-1003, 2001
        #   SPINE_GRP2: 1004, 2002
        #   EVEN: even leaves
        #   ODD: odd leaves
        # Spines:
        #   [Pod 1] 1001-1004, RR: 1001,1002, IPN 1003,1004
        #   [Pod 2] 2001-2002, RR: 2001,2002, IPN 2001,2002
        # APIC Leaves:
        #   [Pod 1] 101-102 (APIC 1, 2)
        #   [Pod 2] 201-202 (APIC 3)
        # VPC Leaves:
        #   [Pod 1] 101-102, 111-112
        #   [Pod 2] 201-202
        (
            {
                upgrade_grp: read_data(dir, "maintMaintGrp_BAD_ONLY_POD1_SPINE_RR.json"),
                bgp_rr: read_data(dir, "bgpRRNodePEp_1001_1002_2001_2002.json"),
                ipn_spines: read_data(dir, "l3extRsNodeL3OutAtt_1003_1004_2001_2002.json"),
                apic_lldp: read_data(dir, "lldpCtrlrAdjEp.json"),
                vpc_pairs: read_data(dir, "fabricExplicitGEp.json"),
            },
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [
                ["SPINE_GRP1", "1", "1001,1002", "All RR spine nodes in this pod are in the same group."],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, expected_result, expected_data):
    result = run_check(
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
