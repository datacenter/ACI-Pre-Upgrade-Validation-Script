# content of test_class_demo.py
import pytest
import json
import re

import importlib  
script = importlib.import_module("aci-preupgrade-validation-script")


def icurl(apitype, query):
    if apitype not in ['class', 'mo']:
        print('invalid API type - %s' % apitype)
        return []

    with open("tests/"+query,"r") as file:
        imdata = json.loads(file.read())['imdata']
        
    if imdata and "error" in imdata[0].keys():
        raise Exception('API call failed! Check debug log')
    else:
        return imdata


# Overwrite to local for file test
script.icurl = icurl


@pytest.fixture
def upgradePaths():
    return [{"cversion": "4.2(1a)", "tversion": "5.2(4d)"},
            {"cversion": "3.2(1a)", "tversion": "4.2(4d)"},
            {"cversion": "3.2(1a)", "tversion": "5.2(6a)"},
            {"cversion": "4.2(3a)", "tversion": "4.2(7d)"}]


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
            assert llfc_susceptibility_check(pathnum, pathlen, **testdata) == "MANUAL CHECK REQUIRED"
        if pathnum == 2:
            assert llfc_susceptibility_check(pathnum, pathlen, **testdata) == "MANUAL CHECK REQUIRED"
        if pathnum == 3:
            assert llfc_susceptibility_check(pathnum, pathlen, **testdata) == "PASS"
        if pathnum == 4:
            assert llfc_susceptibility_check(pathnum, pathlen, **testdata) == "PASS"  



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
    # POS - with affected object in json
    for i, testdata in enumerate(upgradePaths):
        pathnum = i+1
        if pathnum == 1:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == "FAIL - OUTAGE WARNING!!"
        if pathnum == 2:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == "PASS"
        if pathnum == 3:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == "FAIL - OUTAGE WARNING!!"
        if pathnum == 4:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == "PASS"  


def test_neg_stale_nir_object_check(upgradePaths):
    script.print_title("Starting Negative stale_nir_object_check\n")
    pathlen = len(upgradePaths)
    # NEG - without affected object in json

    for i, testdata in enumerate(upgradePaths):
        neg_json = {"totalCount":"0","imdata":[]}
        testdata.update({"telemetryStatsServerP.json": neg_json['imdata']})
        
        pathnum = i+1

        if pathnum == 1:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == "PASS"
        if pathnum == 2:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == "PASS"
        if pathnum == 3:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == "PASS"
        if pathnum == 4:
            assert stale_nir_object_check(pathnum, pathlen, **testdata) == "PASS"  

def test_get_current_version():
    script.print_title("Starting test_get_current_version\n")
    res = script.get_current_version()
    assert res == "5.2(4d)"


def test_switch_bootflash_usage_check_new():
    script.print_title("Starting test_switch_bootflash_usage_check_new\n")
    res = script.switch_bootflash_usage_check(1, 1)
    assert res == "FAIL - UPGRADE FAILURE!!"

