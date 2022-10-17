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
def upgradeOne():
    return {"cversion": "4.2(1a)", "tversion": "5.2(4d)"}


@pytest.fixture
def upgradeTwo():
    return {"cversion": "3.2(1a)", "tversion": "4.2(4d)"}


@pytest.fixture
def upgradeThree():
    return {"cversion": "3.2(1a)", "tversion": "5.2(6a)"}


@pytest.fixture
def upgradeFour():
    return {"cversion": "4.2(3a)", "tversion": "4.2(7d)"}


def llfc_susceptibility_check(index, total_checks, cversion=None, tversion=None, **kwargs):
    title = 'CSCvo27498 Check'
    result = script.PASS
    msg = ''
    headers = ["Current version", "Target Version", "Warning"]
    data = []
    recommended_action = ''
    doc_url = 'APIC Upgrade/Downgrade Support Matrix - http://cs.co/9005ydMQP'
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


def test_llfc_susceptibility_check_one(upgradeOne):
    assert llfc_susceptibility_check(1, 1, **upgradeOne) == "MANUAL CHECK REQUIRED"


def test_llfc_susceptibility_check_two(upgradeTwo):
    assert llfc_susceptibility_check(1, 1, **upgradeTwo) == "MANUAL CHECK REQUIRED"


def test_llfc_susceptibility_check_three(upgradeThree):
    assert llfc_susceptibility_check(1, 1, **upgradeThree) == "PASS"


def test_llfc_susceptibility_check_four(upgradeFour):
    assert llfc_susceptibility_check(1, 1, **upgradeFour) == "PASS"


def test_get_current_version_old():
    """ Returns: x.y(z) """
    firmwares = icurl('class', 'firmwareCtrlrRunning.json')
    for firmware in firmwares:
        if 'node-1' in firmware['firmwareCtrlrRunning']['attributes']['dn']:
            current_version = firmware['firmwareCtrlrRunning']['attributes']['version']
            break
    assert current_version == "5.2(4d)"


def test_get_current_version():
    res = script.get_current_version()
    print("test123")
    assert res == "5.2(4d)"


def test_switch_bootflash_usage_check_new():
    res = script.switch_bootflash_usage_check(1, 1)
    print(res)
    assert res == "FAIL - UPGRADE FAILURE!!"


def test_switch_bootflash_usage_check():
    response_json = icurl('class',
                          'eqptcapacityFSPartition.json?query-target-filter=eq(eqptcapacityFSPartition.path,"/bootflash")')
    for i, eqptcapacityFSPartition in enumerate(response_json):
        dn = re.search(script.node_regex, eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['dn'])
        pod = dn.group("pod")
        node = dn.group("node")
        avail = int(eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['avail'])
        used = int(eqptcapacityFSPartition['eqptcapacityFSPartition']['attributes']['used'])

        usage = (used / (avail + used)) * 100
        print([pod, node, usage,])
        if i == 10:
            assert pod == "1"
            assert node == "101"
            assert usage == 51.279232107240844

