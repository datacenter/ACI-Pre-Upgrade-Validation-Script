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
    for pathnum, versions in enumerate(upgradePaths):
        if pathnum == 0:
            assert llfc_susceptibility_check(1, 1, **versions) == "MANUAL CHECK REQUIRED"
        if pathnum == 1:
            assert llfc_susceptibility_check(1, 1, **versions) == "MANUAL CHECK REQUIRED"
        if pathnum == 2:
            assert llfc_susceptibility_check(1, 1, **versions) == "PASS"
        if pathnum == 3:
            assert llfc_susceptibility_check(1, 1, **versions) == "PASS"  


def test_get_current_version():
    script.print_title("Starting test_get_current_version\n")
    res = script.get_current_version()
    assert res == "5.2(4d)"


def test_switch_bootflash_usage_check_new():
    script.print_title("Starting test_switch_bootflash_usage_check_new\n")
    res = script.switch_bootflash_usage_check(1, 1)
    assert res == "FAIL - UPGRADE FAILURE!!"

