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
            {"cversion": "5.2(1a)", "tversion": None},
            {"cversion": "4.1(1a)", "tversion": "5.2(7f)"}]


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


def test_get_vpc_nodes():
    script.prints("=====Starting test_get_vpc_nodes\n")

    with open("tests/fabricNodePEp.json_pos","r") as file:
        testdata = {"fabricNodePEp.json": json.loads(file.read())['imdata']}

    assert set(script.get_vpc_nodes(**testdata)) == set(["101", "103", "204", "206"])


@pytest.mark.parametrize(
    "cversion,tversion,expected_fail_type",
    [
        # Non-affected version combination
        ("3.2(5e)", "4.2(4r)", script.PASS),
        ("3.2(10g)", "4.2(4r)", script.PASS),
        ("4.1(2a)", "4.2(7a)", script.PASS),
        # Affected versio combination
        ("3.2(4a)", "5.2(2a)", script.FAIL_UF),
        ("4.0(1a)", "5.2(3a)", script.FAIL_UF),
    ],
)
def test_defect_eventmgr_db(cversion, tversion, expected_fail_type):
    script.prints("=====Starting test_defect_eventmgr_db\n")
    testdata = {
        "cversion": cversion,
        "tversion": tversion
    }
    assert script.eventmgr_db_defect_check(1, 1, **testdata) == expected_fail_type




@pytest.mark.parametrize(
    "faultInst,fvIfConn,expected_fail_type",
    [
        # FAIL - certreq returns error
        ( "faultInst-encap-pos.json", "fvIfConn.json", script.FAIL_O),
        # PASS - certreq returns cert info
        ("faultInst-encap-neg.json", "fvIfConn.json", script.PASS)
    ],
)
def test_encap_already_in_use_check(faultInst, fvIfConn, expected_fail_type):
    script.prints("=====Starting encap_already_in_use_check\n")
    testdata = {
        "faultInst": faultInst,
        "fvIfConn": fvIfConn,
    }
    with open("tests/"+faultInst,"r") as file:
        testdata.update({"faultInst": json.loads(file.read())['imdata']})
    with open("tests/"+fvIfConn,"r") as file:
        testdata.update({"fvIfConn": json.loads(file.read())['imdata']})
    assert script.encap_already_in_use_check(1, 1, **testdata) == expected_fail_type



@pytest.mark.parametrize(
    "cversion,tversion,certreq_resp,expected_fail_type",
    [
        # FAIL - certreq returns error
        ("4.2(5e)", "5.2(6e)", "POS_certreq.txt", script.FAIL_O),
        # PASS - certreq returns cert info
        ("4.2(4a)", "5.2(2a)", "NEG_certreq.txt",script.PASS)
    ],
)
def test_apic_ca_cert_validation(cversion, tversion, certreq_resp, expected_fail_type):
    script.prints("=====Starting apic_ca_cert_validation\n")
    testdata = {
        "cversion": cversion,
        "tversion": tversion
    }
    with open("tests/"+certreq_resp,"r") as file:
        testdata.update({"certreq_out": file.read()})
    assert script.apic_ca_cert_validation(1, 1, **testdata) == expected_fail_type


def test_vpc_paired_switches_check(upgradePaths):
    script.prints("=====Starting vpc_paired_switches_check\n")
    pathlen = len(upgradePaths)

    for i, testdata in enumerate(upgradePaths):
        with open("tests/topSystem.json_pos","r") as file:
            testdata.update({"topSystem.json": json.loads(file.read())['imdata']})
        pathnum = i+1
        if pathnum == 1:
            testdata.update({"vpc_node_ids": ["101", "102", "103", "204", "206"]})
            assert script.vpc_paired_switches_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            testdata.update({"vpc_node_ids": ["101", "103", "204", "206"]})
            assert script.vpc_paired_switches_check(pathnum, pathlen, **testdata) == script.MANUAL


def test_llfc_susceptibility_check(upgradePaths):
    script.print_title("Starting test_llfc_susceptibility_check\n")
    pathlen = len(upgradePaths)

    for i, testdata in enumerate(upgradePaths):
        testdata.update({"vpc_node_ids": ["101", "103", "204", "206"]})

        with open("tests/ethpmFcot.json_pos","r") as file:
            testdata.update({"ethpmFcot.json": json.loads(file.read())['imdata']})

        pathnum = i+1
        if pathnum == 1:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 2:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 3:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 4:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 5:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 6:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 7:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL


def test_pos_telemetryStatsServerP_object_check(upgradePaths):
    script.prints("=====Starting test_pos_telemetryStatsServerP_object_check\n")
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
    script.prints("=====Starting Negative stale_nir_object_check\n")
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
    script.prints("=====Starting test_pos_isis_redis_metric_mpod_msite_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/isisDomP-default.json_pos","r") as file:
            testdata.update({"uni/fabric/isisDomP-default.json": json.loads(file.read())['imdata']})

        pathnum = i+1
        if pathnum == 1:
            with open("tests/fvFabricExtConnP.json_pos1","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 2:
            with open("tests/fvFabricExtConnP.json_pos2","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 3:
            with open("tests/fvFabricExtConnP.json_pos3","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 4:
            with open("tests/fvFabricExtConnP.json_pos1","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O


def test_neg_isis_redis_metric_mpod_msite_check(upgradePaths):
    script.prints("=====Starting test_neg_isis_redis_metric_mpod_msite_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):

        with open("tests/isisDomP-default.json_neg","r") as file:
            testdata.update({"uni/fabric/isisDomP-default.json": json.loads(file.read())['imdata']})
        with open("tests/fvFabricExtConnP.json_pos1","r") as file:
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
    script.prints("=====Starting test_missing_isis_redis_metric_mpod_msite_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):

        with open("tests/isisDomP-default.json_missing","r") as file:
            testdata.update({"uni/fabric/isisDomP-default.json": json.loads(file.read())['imdata']})
        with open("tests/fvFabricExtConnP.json_pos1","r") as file:
            testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            
        pathnum = i+1
        if pathnum == 5:
            assert script.isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O 


def test_switch_bootflash_usage_check_new():
    script.prints("=====Starting test_switch_bootflash_usage_check_new\n")
    with open("tests/eqptcapacityFSPartition.json_pos","r") as file:
        testdata = {"eqptcapacityFSPartition.json": json.loads(file.read())['imdata']}
    res = script.switch_bootflash_usage_check(1, 1, **testdata)
    assert res == script.FAIL_UF


def test_contract_22_defect_check(upgradePaths):
    script.prints("=====Starting test_llfc_susceptibility_check\n")
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


def test_pos_internal_vlanpool_check(upgradePaths):
    script.prints("=====Starting Positive internal_vlanpool_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/fvnsVlanInstP.json_pos","r") as file:
            testdata.update({"fvnsVlanInstP.json": json.loads(file.read())['imdata']})
        with open("tests/vmmDomP.json_pos","r") as file:
            testdata.update({"vmmDomP.json": json.loads(file.read())['imdata']})
        pathnum = i+1
        if pathnum == 1:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 2:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 4:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 5:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS


def test_neg_internal_vlanpool_check(upgradePaths):
    script.prints("=====Starting Negative internal_vlanpool_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/fvnsVlanInstP.json_neg","r") as file:
            testdata.update({"fvnsVlanInstP.json": json.loads(file.read())['imdata']})
        with open("tests/vmmDomP.json_neg","r") as file:
            testdata.update({"vmmDomP.json": json.loads(file.read())['imdata']})
        pathnum = i+1

        if pathnum == 1:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 5:
            assert script.internal_vlanpool_check(pathnum, pathlen, **testdata) == script.PASS


def test_bgp_golf_route_target_type_check(upgradePaths):
    script.prints("=====Starting bgp_golf_route_target_type_check tests\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/fvCtx.json_pos","r") as file:
            testdata.update({"fvCtx.json": json.loads(file.read())['imdata']})
        pathnum = i+1
        if pathnum == 1:
            assert script.bgp_golf_route_target_type_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            assert script.bgp_golf_route_target_type_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 3:
            assert script.bgp_golf_route_target_type_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 4:
            assert script.bgp_golf_route_target_type_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 5:
            assert script.bgp_golf_route_target_type_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 6:
            assert script.bgp_golf_route_target_type_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 7:
            assert script.bgp_golf_route_target_type_check(pathnum, pathlen, **testdata) == script.FAIL_O