import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "sup_sysmgr_log_size_check"

# Version test data
version_affected = "15.2(1a)"
version_unaffected = "16.1(4a)"

# API query filter for eqptSupC
sup_query = 'eqptSupC.json?query-target-filter=and(wcard(eqptSupC.model,"N9K-SUP-A"))'

# SSH command for checking sysmgr.log size
sysmgr_log_cmd = "find /mnt/pss/bootlogs -mindepth 2 -maxdepth 2 -name 'sysmgr.log' -type f -exec ls -l {} \\; | awk '{sum+=$5} END {print sum}'"
hostname_cmd = "bash -c \"hostname\""

# Test data: eqptSupC responses
eqptSupC_single_node = read_data(dir, "eqptSupC_single_node.json")
eqptSupC_multi_nodes = read_data(dir, "eqptSupC_multi_nodes.json")
eqptSupC_empty = []

# Test data: SSH outputs for sysmgr.log size
sysmgr_log_small = """\
find /mnt/pss/bootlogs -mindepth 2 -maxdepth 2 -name 'sysmgr.log' -type f -exec ls -l {} \\; | awk '{sum+=$5} END {print sum}'
1024
spine1#
"""

sysmgr_log_large = """\
find /mnt/pss/bootlogs -mindepth 2 -maxdepth 2 -name 'sysmgr.log' -type f -exec ls -l {} \\; | awk '{sum+=$5} END {print sum}'
33554432
spine1#
"""

sysmgr_log_30mib = """\
find /mnt/pss/bootlogs -mindepth 2 -maxdepth 2 -name 'sysmgr.log' -type f -exec ls -l {} \\; | awk '{sum+=$5} END {print sum}'
31457280
spine1#
"""

sysmgr_log_zero = """\
find /mnt/pss/bootlogs -mindepth 2 -maxdepth 2 -name 'sysmgr.log' -type f -exec ls -l {} \\; | awk '{sum+=$5} END {print sum}'
0
spine1#
"""

# Fabric node data
fabricNode_with_spines = read_data(dir, "fabricNode_with_spines.json")
fabricNode_no_spines = read_data(dir, "fabricNode_no_spines.json")

# Hostname output
hostname_output = "apic1"

cmd_outputs_base = {
    hostname_cmd: {
        "splitlines": True,
        "output": hostname_output
    }
}


@pytest.mark.parametrize(
    "icurl_outputs, tversion, fabric_nodes, conn_failure, conn_cmds, cmd_outputs, expected_result",
    [
        # Test 1: PASS - Small sysmgr.log files within 30MiB threshold
        (
            {sup_query: eqptSupC_single_node},
            version_affected,
            fabricNode_with_spines,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": sysmgr_log_cmd,
                        "output": sysmgr_log_small,
                        "exception": None,
                    }
                ]
            },
            cmd_outputs_base,
            script.PASS,
        ),
        
        # Test 2: FAIL_O - Single spine node with large file exceeding 30MiB
        (
            {sup_query: eqptSupC_single_node},
            version_affected,
            fabricNode_with_spines,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": sysmgr_log_cmd,
                        "output": sysmgr_log_large,
                        "exception": None,
                    }
                ]
            },
            cmd_outputs_base,
            script.FAIL_O,
        ),
        
        # Test 3: FAIL_O - Multiple spine nodes with one exceeding threshold
        (
            {sup_query: eqptSupC_multi_nodes},
            version_affected,
            fabricNode_with_spines,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": sysmgr_log_cmd,
                        "output": sysmgr_log_small,
                        "exception": None,
                    }
                ],
                "10.0.0.202": [
                    {
                        "cmd": sysmgr_log_cmd,
                        "output": sysmgr_log_large,
                        "exception": None,
                    }
                ]
            },
            cmd_outputs_base,
            script.FAIL_O,
        ),
        
        # Test 4: NA - No SUP nodes found
        (
            {sup_query: eqptSupC_empty},
            version_affected,
            fabricNode_with_spines,
            False,
            {},
            cmd_outputs_base,
            script.NA,
        ),
        
        # Test 5: NA - Target version not affected (>= 16.1(4x))
        (
            {sup_query: eqptSupC_single_node},
            version_unaffected,
            fabricNode_with_spines,
            False,
            {},
            cmd_outputs_base,
            script.NA,
        ),
        
        # Test 6: MANUAL - No target version supplied
        (
            {sup_query: eqptSupC_single_node},
            None,
            fabricNode_with_spines,
            False,
            {},
            cmd_outputs_base,
            script.MANUAL,
        ),
        
        # Test 7: ERROR - SSH connection timeout
        (
            {sup_query: eqptSupC_single_node},
            version_affected,
            fabricNode_with_spines,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": sysmgr_log_cmd,
                        "output": "",
                        "exception": __import__('pexpect').TIMEOUT("Connection timeout"),
                    }
                ]
            },
            cmd_outputs_base,
            script.ERROR,
        ),
        
        # Test 8: ERROR - SSH connection EOF
        (
            {sup_query: eqptSupC_single_node},
            version_affected,
            fabricNode_with_spines,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": sysmgr_log_cmd,
                        "output": "",
                        "exception": __import__('pexpect').EOF("Connection closed"),
                    }
                ]
            },
            cmd_outputs_base,
            script.ERROR,
        ),
        
        # Test 9: PASS - Zero byte sysmgr.log file (no logs found)
        (
            {sup_query: eqptSupC_single_node},
            version_affected,
            fabricNode_with_spines,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": sysmgr_log_cmd,
                        "output": sysmgr_log_zero,
                        "exception": None,
                    }
                ]
            },
            cmd_outputs_base,
            script.PASS,
        ),
        
        # Test 10: FAIL_O - File at exactly 30MiB threshold (31457280 bytes > 30*1024*1024)
        (
            {sup_query: eqptSupC_single_node},
            version_affected,
            fabricNode_with_spines,
            False,
            {
                "10.0.0.201": [
                    {
                        "cmd": sysmgr_log_cmd,
                        "output": sysmgr_log_30mib,
                        "exception": None,
                    }
                ]
            },
            cmd_outputs_base,
            script.FAIL_O,
        ),
        
        # Test 11: ERROR - SSH connection failure (login failed)
        (
            {sup_query: eqptSupC_single_node},
            version_affected,
            fabricNode_with_spines,
            True,
            {},
            cmd_outputs_base,
            script.ERROR,
        ),
        
        # Test 12: ERROR - No fabric nodes (unable to determine APIC IP)
        (
            {sup_query: eqptSupC_single_node},
            version_affected,
            fabricNode_no_spines,
            False,
            {},
            cmd_outputs_base,
            script.ERROR,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, fabric_nodes, mock_conn, mock_run_cmd, expected_result):
    # import pdb; pdb.set_trace()
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result