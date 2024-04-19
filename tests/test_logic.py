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
    return [{"cversion": script.AciVersion("4.2(1b)"), "tversion": script.AciVersion("5.2(2a)")},
            {"cversion": script.AciVersion("3.2(1a)"), "tversion": script.AciVersion("4.2(4d)")},
            {"cversion": script.AciVersion("3.2(1a)"), "tversion": script.AciVersion("5.2(6a)")},
            {"cversion": script.AciVersion("4.2(3a)"), "tversion": script.AciVersion("4.2(7d)")},
            {"cversion": script.AciVersion("2.2(3a)"), "tversion": script.AciVersion("2.2(4r)")},
            {"cversion": script.AciVersion("5.2(1a)"), "tversion": None},
            {"cversion": script.AciVersion("4.1(1a)"), "tversion": script.AciVersion("5.2(7f)")}]


def test_aciversion(upgradePaths):
    for i, testdata in enumerate(upgradePaths):
        cfw = testdata.get("cversion", None)
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
