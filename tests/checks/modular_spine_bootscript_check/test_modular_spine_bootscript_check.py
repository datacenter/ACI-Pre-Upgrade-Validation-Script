import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "multipod_modular_spine_bootscript_check"
# Test data
fabric_nodes_with_modular_spine = read_data(dir, "fabricNode_with_modular_spine.json")
fabric_nodes_no_spine           = read_data(dir, "fabricNode_no_spine.json")
fabric_nodes_with_fixed_spine   = read_data(dir, "fabricNode_with_fixed_spine.json")
# API query
fabric_setup_count = 'fabricSetupP.json?query-target=self&rsp-subtree-include=count'
# icurl response data
not_multipod_setup = [{"moCount": {"attributes": {"count": "1"}}}]
multipod_setup     = [{"moCount": {"attributes": {"count": "2"}}}]
# SSH command
bootscript_cmd = "ls -l bootflash/ | grep boots"
# SSH command outputs
bootscript_found = """\
ls -l bootflash/ | grep boots
-rw-rw-rw- 1 root  admin             152 Jan  5 11:51 bootscript
-rw-r--r-- 1   600 admin           14119 Jan  5 11:51 bootstrap.xml
ifav42-spine1#
"""
bootscript_not_found = """\
ls -l bootflash/ | grep boots
-rw-r--r-- 1   600 admin           14119 Jan  5 11:51 bootstrap.xml
ifav42-spine1#
"""
bootstript_and_bootstrap_not_found = """\
ls -l bootflash/ | grep boots
ifav42-spine1#
"""

@pytest.mark.parametrize(
    "icurl_outputs, tversion, fabric_nodes, conn_failure, conn_cmds, expected_result, expected_data",
    [
        # Test 1: NA - Not a Multi-Pod setup (fabricSetupP count < 2)
        (
            {fabric_setup_count: not_multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_modular_spine,
            False,
            {},
            script.NA,
            [],
        ),
        # Test 2: NA - tversion not 6.1(4h) or 6.1(5e)
        (
            {fabric_setup_count: multipod_setup},
            "6.1(3a)",
            fabric_nodes_with_modular_spine,
            False,
            {},
            script.NA,
            [],
        ),
        # Test 3: NA - No modular spine found in fabric
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_no_spine,
            False,
            {},
            script.NA,
            [],
        ),
        # Test 4: PASS - bootscript present on all spine nodes (tversion 6.1(4h))
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_modular_spine,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_found,
                        "exception": None,
                    }
                ],
                "10.0.0.202": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_found,
                        "exception": None,
                    }
                ],
            },
            script.PASS,
            [
                ["1", "201", "Spine1", "N9K-C9504", "Yes", "Yes"],
                ["2", "202", "Spine2", "N9K-C9508", "Yes", "Yes"],
            ],
        ),
        # Test 5: PASS - bootscript present on all spine nodes (tversion 6.1(5e))
        (
            {fabric_setup_count: multipod_setup},
            "6.1(5e)",
            fabric_nodes_with_modular_spine,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_found,
                        "exception": None,
                    }
                ],
                "10.0.0.202": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_found,
                        "exception": None,
                    }
                ],
            },
            script.PASS,
            [
                ["1", "201", "Spine1", "N9K-C9504", "Yes", "Yes"],
                ["2", "202", "Spine2", "N9K-C9508", "Yes", "Yes"],
            ],
        ),
        # Test 6: FAIL_O - bootscript missing on all spine nodes
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_modular_spine,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_not_found,
                        "exception": None,
                    }
                ],
                "10.0.0.202": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_not_found,
                        "exception": None,
                    }
                ],
            },
            script.FAIL_O,
            [
                ["1", "201", "Spine1", "N9K-C9504", "No", "Yes"],
                ["2", "202", "Spine2", "N9K-C9508", "No", "Yes"],
            ],
        ),
        # Test 7: FAIL_O - bootscript missing on one spine node
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_modular_spine,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_found,
                        "exception": None,
                    }
                ],
                "10.0.0.202": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_not_found,
                        "exception": None,
                    }
                ],
            },
            script.FAIL_O,
            [
                ["1", "201", "Spine1", "N9K-C9504", "Yes", "Yes"],
                ["2", "202", "Spine2", "N9K-C9508", "No",  "Yes"],
            ],
        ),
        # Test 8: FAIL_UF - bootscript and bootstrap.xml missing on all spine nodes
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_modular_spine,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootstript_and_bootstrap_not_found,
                        "exception": None,
                    }
                ],
                "10.0.0.202": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootstript_and_bootstrap_not_found,
                        "exception": None,
                    }
                ],
            },
            script.FAIL_UF,
            [
                ["1", "201", "Spine1", "N9K-C9504", "No", "No"],
                ["2", "202", "Spine2", "N9K-C9508", "No", "No"],
            ],
        ),
        # Test 9: ERROR - SSH connection exception on spine node
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_modular_spine,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": bootscript_cmd,
                        "output": "",
                        "exception": Exception("SSH failed"),
                    }
                ],
                "10.0.0.202": [
                    {
                        "cmd": bootscript_cmd,
                        "output": "",
                        "exception": Exception("SSH failed"),
                    }
                ],
            },
            script.ERROR,
            [
                ["1", "201", "Spine1", "N9K-C9504", "SSH ERROR: SSH failed", "SSH ERROR: SSH failed"],
                ["2", "202", "Spine2", "N9K-C9508", "SSH ERROR: SSH failed", "SSH ERROR: SSH failed"],
            ],
        ),
        # Test 10: ERROR - SSH connection failure (login failed)
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_modular_spine,
            True,
            {},
            script.ERROR,
            [],
        ),
        # Test 11: PASS - bootscript present on fixed spine (check all spines)
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_fixed_spine,
            False,
            {
                "10.0.0.2": [
                    {
                        "cmd": bootscript_cmd,
                        "output": bootscript_found,
                        "exception": None,
                    }
                ],
            },
            script.NA,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, fabric_nodes, mock_conn, mock_run_cmd, expected_result, expected_data):
    result = run_check(tversion=script.AciVersion(tversion) if tversion else None,username="fake_username",password="fake_password",fabric_nodes=fabric_nodes,)
    assert result.result == expected_result