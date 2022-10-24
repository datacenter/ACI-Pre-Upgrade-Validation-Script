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


def test_llfc_susceptibility_check(upgradePaths):
    script.print_title("Starting test_llfc_susceptibility_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        pathnum = i+1
        if pathnum == 1:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 2:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.MANUAL
        if pathnum == 3:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert script.llfc_susceptibility_check(pathnum, pathlen, **testdata) == script.PASS


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
