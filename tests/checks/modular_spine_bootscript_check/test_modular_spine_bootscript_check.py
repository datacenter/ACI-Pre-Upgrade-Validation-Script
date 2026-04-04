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
fabric_nodes_with_fixed_spine = read_data(dir, "fabricNode_with_fixed_spine.json")
# API query
fabric_setup_count = "fabricSetupP.json?rsp-subtree-include=count"
# icurl response data
not_multipod_setup = [{"moCount": {"attributes": {"count": "1"}}}]
multipod_setup = [{"moCount": {"attributes": {"count": "2"}}}]
# SSH command
bootscript_cmd = "ls -l /bootflash/ | grep boots"
# SSH command outputs
bootscript_found = """\
ls -l /bootflash/ | grep boots
-rw-rw-rw- 1 root  admin             152 Jan  5 11:51 bootscript
-rw-r--r-- 1   600 admin           14119 Jan  5 11:51 bootstrap.xml
spine201#
"""
bootscript_not_found = """\
ls -l /bootflash/ | grep boots
-rw-r--r-- 1   600 admin           14119 Jan  5 11:51 bootstrap.xml
spine201#
"""


@pytest.mark.parametrize(
    "icurl_outputs, tversion, fabric_nodes, conn_failure, conn_cmds, expected_result, expected_data",
    [
        # Test 1: NA - tversion not 6.1(4h)
        (
            {fabric_setup_count: multipod_setup},
            "6.1(3a)",
            fabric_nodes_with_modular_spine,
            False,
            {},
            script.NA,
            [],
        ),
        # Test 2: PASS - Not a Multi-Pod setup (fabricSetupP count < 2)
        (
            {fabric_setup_count: not_multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_modular_spine,
            False,
            {},
            script.PASS,
            [],
        ),
        # Test 3: PASS - No modular spine found in fabric
        (
            {fabric_setup_count: multipod_setup},
            "6.1(4h)",
            fabric_nodes_with_fixed_spine,
            False,
            {},
            script.PASS,
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
            [],
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
                ["1", "201", "spine201", "N9K-C9504", "No"],
                ["2", "202", "spine202", "N9K-C9508", "No"],
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
            [["2", "202", "spine202", "N9K-C9508", "No"]],
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
                ["1", "201", "spine201", "N9K-C9504", "SSH ERROR: SSH failed"],
                ["2", "202", "spine202", "N9K-C9508", "SSH ERROR: SSH failed"],
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
            [
                ["1", "201", "spine201", "N9K-C9504", "SSH ERROR: Simulated exception at connect()"],
                ["2", "202", "spine202", "N9K-C9508", "SSH ERROR: Simulated exception at connect()"],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, fabric_nodes, mock_conn, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
