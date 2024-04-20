# content of test_class_demo.py
import os
import sys
import json

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
sys.path.append(PROJECT_DIR)

import importlib
script = importlib.import_module("aci-preupgrade-validation-script")


def test_get_vpc_nodes():
    script.prints("=====Starting test_get_vpc_nodes\n")

    with open("tests/fabricNodePEp.json_pos","r") as file:
        testdata = {"fabricNodePEp.json": json.loads(file.read())['imdata']}

    assert set(script.get_vpc_nodes(**testdata)) == set(["101", "103", "204", "206"])
