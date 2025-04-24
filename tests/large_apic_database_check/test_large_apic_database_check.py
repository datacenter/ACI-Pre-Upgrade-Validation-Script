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

dme_svc_list = ['vmmmgr','policymgr','eventmgr','policydist']

@pytest.mark.parametrize(
    "icurl_outputs, top_class_stats_file, top_db_stats_file, cversion, expected_result",
    [
        # Failure when version older than 6.1(3a) but top Mo counter exceed 1.5M
        (
            {apic_node_api:read_data(dir,'infraWiNode.json'),},
            "top_class_stats_file_above_threshold.txt",
            None,
            "5.3(2a)",
            script.FAIL_O,
        ),
        # pass when version older than 6.1(3a) but top Mo counter exceed 1.5M
        (
            {apic_node_api:read_data(dir,'infraWiNode.json'),},
            "top_class_stats_file_below_threshold.txt",
            None,
            "5.3(2a)",
            script.PASS,
        ),
        # pass when version newer than 6.1(3a) and top DB counter less than 5G
        (
            {apic_node_api:read_data(dir,'infraWiNode.json'),},
            None,
            "top_db_stats_file_below_threshold.txt",
            "6.1(3f)",
            script.PASS,
        ),
        # pass when version newer than 6.1(3a) and top DB counter above than 5G
        (
            {apic_node_api:read_data(dir,'infraWiNode.json'),},
            None,
            "top_db_stats_file_above_threshold.txt",
            "6.1(3f)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(mock_icurl, cversion, top_class_stats_file, top_db_stats_file, expected_result):
    cver = script.AciVersion(cversion) if cversion else None
    top_class_stats = None
    top_db_stats = None
    if top_class_stats_file:
        data_path = os.path.join("tests", dir, top_class_stats_file)
        with open(data_path, "r") as file:
            top_class_stats = file.read()
    if top_db_stats_file:
        data_path = os.path.join("tests", dir, top_db_stats_file)
        with open(data_path, "r") as file:
            top_db_stats = json.loads(file.read())

    result = script.large_apic_database_check(1, 1, cver, top_class_stats =top_class_stats,top_db_stats = top_db_stats  )
    assert result == expected_result
