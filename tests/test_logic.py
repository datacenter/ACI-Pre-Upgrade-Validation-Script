# content of test_class_demo.py
import os
import sys
import pytest
import json
import re

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
sys.path.append(PROJECT_DIR)

import importlib  
script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.fixture
def upgradePaths():
    return [{"cversion": "4.2(1b)", "tversion": "5.2(2a)"},
            {"cversion": "3.2(1a)", "tversion": "4.2(4d)"},
            {"cversion": "3.2(1a)", "tversion": "5.2(6a)"},
            {"cversion": "4.2(3a)", "tversion": "4.2(7d)"},
            {"cversion": "2.2(3a)", "tversion": "2.2(4r)"},
            {"cversion": "5.2(1a)", "tversion": None}]


def test_aciversion(upgradePaths):
    for i, testdata in enumerate(upgradePaths):
        cversion = testdata.get("cversion", None)
        cfw = script.AciVersion(cversion)
        pathnum = i+1
        if pathnum == 1: # cfw = 4.2(1a)
            assert cfw.older_than("4.1(10b)") == False
            assert cfw.older_than("4.2(1a)") == False
            assert cfw.older_than("4.2(1b)") == False # Same
            assert cfw.older_than("4.2(3b)") == True
            assert cfw.older_than("5.0(1b)") == True
            assert cfw.older_than("5.1(1b)") == True
            assert cfw.older_than("5.2(1b)") == True

            assert cfw.newer_than("4.1(10b)") == True
            assert cfw.newer_than("4.2(1a)") == True 
            assert cfw.newer_than("4.2(1b)") == False # Same
            assert cfw.newer_than("4.2(3b)") == False
            assert cfw.newer_than("5.0(1b)") == False
            assert cfw.newer_than("5.1(1b)") == False
            assert cfw.newer_than("5.2(1b)") == False

            assert cfw.same_as("4.2(1b)") == True # Same


# New Check, migrate to script once logic confirmed
def llfc_susceptibility_check(index, total_checks, cversion=None, tversion=None, **kwargs):
    title = 'CSCvo27498 Check'
    result = script.PASS
    msg = ''
    headers = ["Current version", "Target Version", "Warning"]
    data = []
    recommended_action = 'Manually change Transmit(send) Flow Control to off prior to switch Upgrade'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvo27498'
    script.print_title(title, index, total_checks)

    if not cversion:
        cversion = kwargs.get("cversion", None)
    if not tversion:
        tversion = kwargs.get("tversion", None)
    cfw = script.AciVersion(cversion)
    tfw = script.AciVersion(tversion)

    if cfw and tfw:
        if (cfw.newer_than("2.2(10a)") and cfw.older_than("4.2(2a)")) and (tfw.older_than("5.2(5a)")):
            result = script.MANUAL
            data.append([cversion, tversion, 'Affected Path Found, Check Bug RNE'])

    script.print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def test_llfc_susceptibility_check(upgradePaths):
    script.print_title("Starting test_llfc_susceptibility_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        pathnum = i+1
        if pathnum == 1:
            assert llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 2:
            assert llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 3:
            assert llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.PASS


def test_pos_telemetryStatsServerP_object_check(upgradePaths):
    script.print_title("Starting test_pos_telemetryStatsServerP_object_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/telemetryStatsServerP.json_pos","r") as file:
            testdata.update({"telemetryStatsServerP.json": json.loads(file.read())['imdata']})
        pathnum = i+1
        if pathnum == 1:
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 4:
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.PASS


def test_neg_telemetryStatsServerP_object_check(upgradePaths):
    script.print_title("Starting Negative stale_nir_object_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        pathnum = i+1
        if pathnum == 1:
            neg_json = {"totalCount":"0","imdata":[]}
            testdata.update({"telemetryStatsServerP.json": neg_json['imdata']})
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            with open("tests/telemetryStatsServerP.json_neg","r") as file:
                testdata.update({"telemetryStatsServerP.json": json.loads(file.read())['imdata']})
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 5:
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 6:
            assert script.telemetryStatsServerP_object_check(pathnum, pathlen, **testdata) == script.MANUAL


def test_pos_isis_redis_metric_mpod_msite_check(upgradePaths):
    script.print_title("Starting test_pos_isis_redis_metric_mpod_msite_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/isisDomP-default.json_pos","r") as file:
            testdata.update({"uni/fabric/isisDomP-default.json": json.loads(file.read())['imdata']})

        pathnum = i+1
        if pathnum == 1:
            with open("tests/fvFabricExtConnP.json?query-target=children_pos1","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 2:
            with open("tests/fvFabricExtConnP.json?query-target=children_pos2","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 3:
            with open("tests/fvFabricExtConnP.json?query-target=children_pos3","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 4:
            with open("tests/fvFabricExtConnP.json?query-target=children_pos1","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O


def test_neg_isis_redis_metric_mpod_msite_check(upgradePaths):
    script.print_title("Starting test_neg_isis_redis_metric_mpod_msite_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):

        with open("tests/isisDomP-default.json_neg","r") as file:
            testdata.update({"uni/fabric/isisDomP-default.json": json.loads(file.read())['imdata']})
        with open("tests/fvFabricExtConnP.json?query-target=children_pos1","r") as file:
            testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})

        pathnum = i+1
        if pathnum == 1:
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.PASS


def test_missing_isis_redis_metric_mpod_msite_check(upgradePaths):
    script.print_title("Starting test_missing_isis_redis_metric_mpod_msite_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):

        with open("tests/isisDomP-default.json_missing","r") as file:
            testdata.update({"uni/fabric/isisDomP-default.json": json.loads(file.read())['imdata']})
        with open("tests/fvFabricExtConnP.json?query-target=children_pos1","r") as file:
            testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            
        pathnum = i+1
        if pathnum == 5:
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O 


def test_switch_bootflash_usage_check_new():
    script.print_title("Starting test_switch_bootflash_usage_check_new\n")
    with open("tests/eqptcapacityFSPartition.json_pos","r") as file:
        testdata = {"eqptcapacityFSPartition.json": json.loads(file.read())['imdata']}
    res = script.switch_bootflash_usage_check(1, 1, **testdata)
    assert res == script.FAIL_UF


def test_contract_22_defect_check(upgradePaths):
    script.print_title("Starting test_llfc_susceptibility_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        pathnum = i+1
        if pathnum == 1:
            assert script.contract_22_defect_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 2:
            assert script.contract_22_defect_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert script.contract_22_defect_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert script.contract_22_defect_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 5:
            assert script.contract_22_defect_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 6:
            assert script.contract_22_defect_check(pathnum, pathlen, **testdata) == script.MANUAL
            
               
# New Check, migrate to script once logic confirmed
def internal_vlanpool_check(index, total_checks, tversion=None, **kwargs):
    title = 'Internal VLAN Pool Check'
    result = script.PASS
    msg = ''
    headers = ["Target Version", "VLAN Pool", "Warning"]
    data = []
    recommended_action = 'Ensure any VLAN Encap blocks explicitly used for leaf front panel VLAN programming are set to "external (on the wire)"'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvw33061'
    script.print_title(title, index, total_checks)

    fvnsVlanInstP_json = kwargs.get("fvnsVlanInstP.json", None)
    vmmDomP_json = kwargs.get("vmmDomP.json", None)
    if not tversion:
        tversion = kwargs.get("tversion", None)
    tfw = script.AciVersion(tversion)

    if tfw:
        if tfw.newer_than("4.2(6a)"):
            if not isinstance(fvnsVlanInstP_json, list):
                fvnsVlanInstP_json = icurl('class', 'fvnsVlanInstP.json?rsp-subtree=children&rsp-subtree-class=fvnsRtVlanNs,fvnsEncapBlk&rsp-subtree-include=required')
            # Dict with key = vlan pool name, values = list of associated domains
            dom_rel = {}
            # List of vlanInstP which contain fvnsEncapBlk.role = "internal"
            encap_list = []
            for vlanInstP in fvnsVlanInstP_json:
                vlanInstP_name = vlanInstP['fvnsVlanInstP']["attributes"]["name"]
                dom_list = []
                for vlan_child in vlanInstP['fvnsVlanInstP']['children']:
                    if vlan_child.get('fvnsRtVlanNs'):
                        dom_list.append({"dn":vlan_child['fvnsRtVlanNs']['attributes']['tDn'], "tCl":vlan_child['fvnsRtVlanNs']['attributes']['tCl']})
                    elif vlan_child.get('fvnsEncapBlk'):
                        if vlan_child['fvnsEncapBlk']['attributes']['role'] == "internal":
                            encap_list.append(vlanInstP_name)
                dom_rel[vlanInstP_name] = dom_list
            if len(encap_list) > 0:
                # Check if internal vlan pool is associated to a domain which isnt AVE
                # List of domains which are associated to a vlan pool that contains an encap block with role "internal"
                assoc_doms = []
                for vlanInstP_name in encap_list:
                    for dom in dom_rel[vlanInstP_name]:
                        if dom["tCl"] != "vmmDomP":
                            result = script.FAIL_O
                            data.append([tversion, vlanInstP_name, 'VLAN Pool contains an encap block with role "internal" and is associated to a non-AVE domain'])
                        assoc_doms.append(dom["dn"])
                if not isinstance(vmmDomP_json, list):
                    vmmDomP_json = icurl('class', 'vmmDomP.json')
                for vmmDomP in vmmDomP_json:
                    if vmmDomP["vmmDomP"]["attributes"]["dn"] in assoc_doms:
                        if vmmDomP["vmmDomP"]["attributes"]["enableAVE"] != "yes":
                            result = script.FAIL_O
                            data.append([tversion, vlanInstP_name, 'VLAN Pool contains an encap block with role "internal" and is associated to a non-AVE domain'])

    script.print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result
    
def test_pos_internal_vlanpool_check(upgradePaths):
    script.print_title("Starting Positive internal_vlanpool_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/fvnsVlanInstP.json_pos","r") as file:
            testdata.update({"fvnsVlanInstP.json": json.loads(file.read())['imdata']})
        with open("tests/vmmDomP.json_pos","r") as file:
            testdata.update({"vmmDomP.json": json.loads(file.read())['imdata']})
        pathnum = i+1
        if pathnum == 1:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 2:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 4:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 5:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
            
def test_neg_internal_vlanpool_check(upgradePaths):
    script.print_title("Starting Negative internal_vlanpool_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/fvnsVlanInstP.json_neg","r") as file:
            testdata.update({"fvnsVlanInstP.json": json.loads(file.read())['imdata']})
        with open("tests/vmmDomP.json_neg","r") as file:
            testdata.update({"vmmDomP.json": json.loads(file.read())['imdata']})
        pathnum = i+1

        if pathnum == 1:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 5:
            assert internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
