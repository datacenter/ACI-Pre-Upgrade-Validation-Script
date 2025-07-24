import os
import pytest
import logging
import importlib
import json
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

apic_node_api = 'infraWiNode.json'

apic1_pm_cat = "cat /debug/apic1/policymgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic1_pd_cat = "cat /debug/apic1/policydist/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic1_vmm_cat = "cat /debug/apic1/vmmmgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic1_evm_cat = "cat /debug/apic1/eventmgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"

apic2_pm_cat = "cat /debug/apic2/policymgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic2_pd_cat = "cat /debug/apic2/policydist/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic2_vmm_cat = "cat /debug/apic2/vmmmgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic2_evm_cat = "cat /debug/apic2/eventmgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"

apic3_pm_cat = "cat /debug/apic3/policymgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic3_pd_cat = "cat /debug/apic3/policydist/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic3_vmm_cat = "cat /debug/apic3/vmmmgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic3_evm_cat = "cat /debug/apic3/eventmgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"

apic4_pm_cat = "cat /debug/apic4/policymgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic4_pd_cat = "cat /debug/apic4/policydist/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic4_vmm_cat = "cat /debug/apic4/vmmmgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"
apic4_evm_cat = "cat /debug/apic4/eventmgr/mitmocounters/mo | grep -v ALL | sort -rn -k3"

apic1_acidiag = "acidiag dbsize --topshard --apic 1 -f json"
apic2_acidiag = "acidiag dbsize --topshard --apic 2 -f json"
apic3_acidiag = "acidiag dbsize --topshard --apic 3 -f json"
apic4_acidiag = "acidiag dbsize --topshard --apic 4 -f json"

mitcounters_policymgr_pos = """
vzCreatedBy                                : 312748
vzRsRFltAtt                                : 312047
vzToEPg                                    : 65140
"""

mitcounters_policydist_pos = """
l3extSubnet                                : 21926
validatorConsumedPolicy                    : 14207
validatorScopeHop                          : 12242
"""

mitcounters_vmmmgr_pos = """
compProv                 : 1800000
compatCtlrFw             : 1700000
aaaIRbacRule             : 1600000
"""

mitcounters_eventmgr_pos = """
statsColl                        : 21846
statsReportable                  : 18183
statsThrDoubleP                  : 6006
"""

mitcounters_neg = """compProv                 : 264
compatCtlrFw             : 178
aaaIRbacRule             : 128
"""

acidiag_pos = """{
    "dbs": [
        {
            "name": "ifc_eventmgr-1.db",
            "apic": "2",
            "dme": "ifc_eventmgr",
            "shard_replica": "S11_R0",
            "type": "Regular",
            "size_b": 5368709121,
            "size_h": "5120.8M"
        },
        {
            "name": "ifc_policymgr.db",
            "apic": "2",
            "dme": "ifc_policymgr",
            "shard_replica": "S32_R1",
            "type": "Regular",
            "size_b": 59133952,
            "size_h": "56.4M"
        },
        {
            "name": "ifc_ae.db",
            "apic": "2",
            "dme": "ifc_ae",
            "shard_replica": "S255_R127",
            "type": "Regular",
            "size_b": 52435968,
            "size_h": "50.0M"
        },
        {
            "name": "ifc_eventmgr-1.db",
            "apic": "2",
            "dme": "ifc_eventmgr",
            "shard_replica": "S17_R0",
            "type": "Regular",
            "size_b": 46935040,
            "size_h": "44.8M"
        },
        {
            "name": "ifc_dhcpd.db",
            "apic": "2",
            "dme": "ifc_dhcpd",
            "shard_replica": "S255_R127",
            "type": "Regular",
            "size_b": 46110720,
            "size_h": "44.0M"
        }
    ]
}"""

acidiag_neg = """{
    "dbs": [
        {
            "name": "ifc_eventmgr-1.db",
            "apic": "2",
            "dme": "ifc_eventmgr",
            "shard_replica": "S11_R0",
            "type": "Regular",
            "size_b": 75320320,
            "size_h": "71.8M"
        },
        {
            "name": "ifc_policymgr.db",
            "apic": "2",
            "dme": "ifc_policymgr",
            "shard_replica": "S32_R1",
            "type": "Regular",
            "size_b": 59133952,
            "size_h": "56.4M"
        },
        {
            "name": "ifc_ae.db",
            "apic": "2",
            "dme": "ifc_ae",
            "shard_replica": "S255_R127",
            "type": "Regular",
            "size_b": 52435968,
            "size_h": "50.0M"
        },
        {
            "name": "ifc_eventmgr-1.db",
            "apic": "2",
            "dme": "ifc_eventmgr",
            "shard_replica": "S17_R0",
            "type": "Regular",
            "size_b": 46935040,
            "size_h": "44.8M"
        },
        {
            "name": "ifc_dhcpd.db",
            "apic": "2",
            "dme": "ifc_dhcpd",
            "shard_replica": "S255_R127",
            "type": "Regular",
            "size_b": 46110720,
            "size_h": "44.0M"
        }
    ]
}"""

@pytest.mark.parametrize(
    "icurl_outputs, cmd_outputs, cversion, expected_result",
    [
        ## 3 APIC cluster
        # Failure when version older than 6.1(3a) but top Mo counter exceed 1.5M
        (
            {apic_node_api: read_data(dir, 'infraWiNode_3.json')},
            {
                apic2_pm_cat: {"splitlines": True, "output": mitcounters_policymgr_pos},
                apic2_pd_cat: {"splitlines": True, "output": mitcounters_policydist_pos},
                apic2_vmm_cat: {"splitlines": True, "output": mitcounters_vmmmgr_pos},
                apic2_evm_cat: {"splitlines": True, "output": mitcounters_eventmgr_pos},
            },
            "5.3(2a)",
            script.FAIL_UF,
        ),
        # pass when version older than 6.1(3a) but top Mo counter less than 1.5M
        (
            {apic_node_api: read_data(dir, 'infraWiNode_3.json')},
            {
                apic2_pm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic2_pd_cat: {"splitlines": True, "output": mitcounters_neg},
                apic2_vmm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic2_evm_cat: {"splitlines": True, "output": mitcounters_neg},
            },
            "5.3(2a)",
            script.PASS,
        ),
        # pass when version newer than 6.1(3a) and top DB counter less than 5G
        (
            {apic_node_api: read_data(dir, 'infraWiNode_3.json')},
            {
                apic1_acidiag: {"splitlines": False, "output": acidiag_neg},
                apic2_acidiag: {"splitlines": False, "output": acidiag_neg},
                apic3_acidiag: {"splitlines": False, "output": acidiag_neg},
            },
            "6.1(3f)",
            script.PASS,
        ),
        # pass when version newer than 6.1(3a) and top DB counter above than 5G
        (
            {apic_node_api: read_data(dir, 'infraWiNode_3.json')},
            {
                apic1_acidiag: {"splitlines": False, "output": acidiag_pos},
                apic2_acidiag: {"splitlines": False, "output": acidiag_pos},
                apic3_acidiag: {"splitlines": False, "output": acidiag_pos},
            },
            "6.1(3f)",
            script.FAIL_UF,
        ),

        ## 4 APIC cluster
        # Failure when version older than 6.1(3a) but top Mo counter exceed 1.5M
        (
            {apic_node_api: read_data(dir, 'infraWiNode_4.json')},
            {
                apic1_pm_cat: {"splitlines": True, "output": mitcounters_policymgr_pos},
                apic1_pd_cat: {"splitlines": True, "output": mitcounters_policydist_pos},
                apic1_vmm_cat: {"splitlines": True, "output": mitcounters_vmmmgr_pos},
                apic1_evm_cat: {"splitlines": True, "output": mitcounters_eventmgr_pos},
                apic2_pm_cat: {"splitlines": True, "output": mitcounters_policymgr_pos},
                apic2_pd_cat: {"splitlines": True, "output": mitcounters_policydist_pos},
                apic2_vmm_cat: {"splitlines": True, "output": mitcounters_vmmmgr_pos},
                apic2_evm_cat: {"splitlines": True, "output": mitcounters_eventmgr_pos},
                apic3_pm_cat: {"splitlines": True, "output": mitcounters_policymgr_pos},
                apic3_pd_cat: {"splitlines": True, "output": mitcounters_policydist_pos},
                apic3_vmm_cat: {"splitlines": True, "output": mitcounters_vmmmgr_pos},
                apic3_evm_cat: {"splitlines": True, "output": mitcounters_eventmgr_pos},
                apic4_pm_cat: {"splitlines": True, "output": mitcounters_policymgr_pos},
                apic4_pd_cat: {"splitlines": True, "output": mitcounters_policydist_pos},
                apic4_vmm_cat: {"splitlines": True, "output": mitcounters_vmmmgr_pos},
                apic4_evm_cat: {"splitlines": True, "output": mitcounters_eventmgr_pos},
            },
            "5.3(2a)",
            script.FAIL_UF,
        ),
        # pass when version older than 6.1(3a) but top Mo counter less than 1.5M
        (
            {apic_node_api: read_data(dir, 'infraWiNode_4.json')},
            {
                apic1_pm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic1_pd_cat: {"splitlines": True, "output": mitcounters_neg},
                apic1_vmm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic1_evm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic2_pm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic2_pd_cat: {"splitlines": True, "output": mitcounters_neg},
                apic2_vmm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic2_evm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic3_pm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic3_pd_cat: {"splitlines": True, "output": mitcounters_neg},
                apic3_vmm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic3_evm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic4_pm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic4_pd_cat: {"splitlines": True, "output": mitcounters_neg},
                apic4_vmm_cat: {"splitlines": True, "output": mitcounters_neg},
                apic4_evm_cat: {"splitlines": True, "output": mitcounters_neg},
            },
            "5.3(2a)",
            script.PASS,
        ),
        # pass when version newer than 6.1(3a) and top DB counter less than 5G
        (
            {apic_node_api: read_data(dir, 'infraWiNode_4.json')},
            {
                apic1_acidiag: {"splitlines": False, "output": acidiag_neg},
                apic2_acidiag: {"splitlines": False, "output": acidiag_neg},
                apic3_acidiag: {"splitlines": False, "output": acidiag_neg},
                apic4_acidiag: {"splitlines": False, "output": acidiag_neg},
            },
            "6.1(3f)",
            script.PASS,
        ),
        # pass when version newer than 6.1(3a) and top DB counter above than 5G
        (
            {apic_node_api: read_data(dir, 'infraWiNode_4.json')},
            {
                apic1_acidiag: {"splitlines": False, "output": acidiag_pos},
                apic2_acidiag: {"splitlines": False, "output": acidiag_pos},
                apic3_acidiag: {"splitlines": False, "output": acidiag_pos},
                apic4_acidiag: {"splitlines": False, "output": acidiag_pos},
            },
            "6.1(3f)",
            script.FAIL_UF,
        ),
    ],
)
def test_logic(mock_icurl, mock_run_cmd, cversion, expected_result):
    cver = script.AciVersion(cversion) if cversion else None
    result = script.apic_database_size_check(1, 1, cver)
    assert result == expected_result
