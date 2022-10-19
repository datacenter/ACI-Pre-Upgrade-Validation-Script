# content of test_class_demo.py
import pytest
import json
import re

import importlib  
script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.fixture
def upgradePaths():
    return [{"cversion": "4.2(1a)", "tversion": "5.2(4d)"},
            {"cversion": "3.2(1a)", "tversion": "4.2(4d)"},
            {"cversion": "3.2(1a)", "tversion": "5.2(6a)"},
            {"cversion": "4.2(3a)", "tversion": "4.2(7d)"},
            {"cversion": "2.2(3a)", "tversion": "2.2(4r)"}]


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



# New Check, migrate to script once logic confirmed
def stale_nir_object_check(index, total_checks, cversion=None, tversion=None, **kwargs):
    title = 'NIR App Stale Object Check'
    result = script.PASS
    msg = ''
    headers = ["Current version", "Target Version", "Warning"]
    data = []
    recommended_action = 'Manually delete the telemetryStatsServerP object prior to switch upgrade'
    doc_url = 'https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvt47850'
    script.print_title(title, index, total_checks)

    telemetryStatsServerP_json = kwargs.get("telemetryStatsServerP.json", None)
    if not cversion:
        cversion = kwargs.get("cversion", None)
    if not tversion:
        tversion = kwargs.get("tversion", None)
    cfw = script.AciVersion(cversion)
    tfw = script.AciVersion(tversion)

    if cfw and tfw:
        if cfw.older_than("4.2(4d)") and tfw.newer_than("5.2(2d)"):
            if not isinstance(telemetryStatsServerP_json, list):
                telemetryStatsServerP_json = icurl('class', 'telemetryStatsServerP.json')
            if len(telemetryStatsServerP_json) > 0:
                result = script.FAIL_O
                data.append([cversion, tversion, 'telemetryStatsServerP Found'])

    script.print_result(title, result, msg, headers, data, recommended_action=recommended_action, doc_url=doc_url)
    return result


def test_pos_stale_nir_object_check(upgradePaths):
    script.print_title("Starting Positive stale_nir_object_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        with open("tests/telemetryStatsServerP.json_pos","r") as file:
            testdata.update({"telemetryStatsServerP.json": json.loads(file.read())['imdata']})
        pathnum = i+1
        if pathnum == 1:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 2:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 4:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == script.PASS


def test_neg_stale_nir_object_check(upgradePaths):
    script.print_title("Starting Negative stale_nir_object_check\n")
    pathlen = len(upgradePaths)
    for i, testdata in enumerate(upgradePaths):
        neg_json = {"totalCount":"0","imdata":[]}
        testdata.update({"telemetryStatsServerP.json": neg_json['imdata']})
        
        pathnum = i+1

        if pathnum == 1:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == script.PASS


def isis_redis_metric_mpod_msite_check(index, total_checks, **kwargs):
    title = 'ISIS Redistribution metric for MPod/MSite'
    result = script.FAIL_O
    msg = ''
    headers = ["ISIS Redistribution Metric", "MPod Deployment", "MSite Deployment","Recommendation" ]
    data = []
    recommended_action = None
    doc_url = '"ISIS Redistribution Metric" from ACI Best Practices Quick Summary - http://cs.co/9001zNNr7'
    script.print_title(title, index, total_checks)

    isis_mo = kwargs.get("uni/fabric/isisDomP-default.json", None)
    mpod_msite_mo = kwargs.get("fvFabricExtConnP.json?query-target=children", None)

    if not isis_mo:
        isis_mo = icurl('mo', 'uni/fabric/isisDomP-default.json')
    redistribMetric = isis_mo[0]['isisDomPol']['attributes'].get('redistribMetric')

    msite = False
    mpod = False

    if not redistribMetric:
        recommended_action = 'Upgrade to 2.2(4f)+ or 3.0(1k)+ to support configurable ISIS Redistribution Metric'
    else:
        if int(redistribMetric) >= 63:
            recommended_action = 'Change ISIS Redistribution Metric to less than 63'

    if recommended_action:
        if not mpod_msite_mo:
            mpod_msite_mo = icurl('class','fvFabricExtConnP.json?query-target=children')
        if mpod_msite_mo:
            pods_list = []

            for mo in mpod_msite_mo:
                if mo.get('fvSiteConnP'):
                    msite = True
                elif mo.get('fvPodConnP'):
                    podid = mo['fvPodConnP']['attributes'].get('id')
                    if podid and podid not in pods_list:
                        pods_list.append(podid)
            mpod = (len(pods_list) > 1)
    if mpod or msite:
        data.append([redistribMetric, mpod, msite, recommended_action])
    if not data:
        result = script.PASS
    script.print_result(title, result, msg, headers, data, doc_url=doc_url)
    return result


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
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 2:
            with open("tests/fvFabricExtConnP.json?query-target=children_pos2","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 3:
            with open("tests/fvFabricExtConnP.json?query-target=children_pos3","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O
        if pathnum == 4:
            with open("tests/fvFabricExtConnP.json?query-target=children_pos1","r") as file:
                testdata.update({"fvFabricExtConnP.json?query-target=children": json.loads(file.read())['imdata']})
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O


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
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 2:
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 3:
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.PASS
        if pathnum == 4:
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.PASS


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
            assert isis_redis_metric_mpod_msite_check(pathnum, pathlen, **testdata) == script.FAIL_O 


def test_switch_bootflash_usage_check_new():
    script.print_title("Starting test_switch_bootflash_usage_check_new\n")
    with open("tests/eqptcapacityFSPartition.json_pos","r") as file:
        testdata = {"eqptcapacityFSPartition.json": json.loads(file.read())['imdata']}
    res = script.switch_bootflash_usage_check(1, 1, **testdata)
    assert res == script.FAIL_UF

