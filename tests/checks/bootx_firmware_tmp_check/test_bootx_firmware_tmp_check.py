import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

# API query for fabricNode (get_fabric_nodes() uses 'fabricNode.json' without filter)
fabricNode_api = 'fabricNode.json'

# Commands that will be executed via SSH
ls_firmware_tmp_cmd = '[ -d /firmware/tmp ] && ls -1 /firmware/tmp 2>/dev/null | wc -l || echo 0'
grep_fatal_bootx_cmd = '[ -d /var/log/bootx/logs ] && grep -Ri "fatal" /var/log/bootx/logs/* 2>/dev/null | wc -l || echo 0'

test_function = "bootx_firmware_tmp_check"

@pytest.mark.parametrize(
    "icurl_outputs, conn_cmds, cversion, expected_result",
    [
        # Test 1: Version not provided (cversion is None)
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {},
            None,
            script.MANUAL,
        ),
        # Test 2: Version not affected (below 6.0(2f))
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {},
            "6.0(1a)",
            script.PASS,
        ),
        # Test 3: Version not affected (above 6.0(8f))
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {},
            "6.0(9a)",
            script.PASS,
        ),
        # Test 4: Version not affected (between 6.0(8f) and 6.1(1f))
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {},
            "6.0(9h)",
            script.PASS,
        ),
        # Test 5: Version not affected (above 6.1(2f))
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {},
            "6.1(3a)",
            script.PASS,
        ),
        # Test 6: Affected version 6.0(2f), no issues found
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "0\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "0\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "0\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            "6.0(2f)",
            script.PASS,
        ),
        # Test 7: Affected version 6.0(5a), file count >= 1000 on one APIC
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "1500\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "100\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "50\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            "6.0(5a)",
            script.FAIL_UF,
        ),
        # Test 8: Affected version 6.0(8f), fatal errors found on one APIC
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "50\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "5\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "30\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "20\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            "6.0(8f)",
            script.MANUAL,
        ),
        # Test 9: Affected version 6.1(1f), both high file count and fatal errors
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "2000\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "10\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "500\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "100\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            "6.1(1f)",
            script.FAIL_UF,
        ),
        # Test 10: Affected version 6.1(2f), multiple APICs with issues
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "1200\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "1500\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "2\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "100\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            "6.1(2f)",
            script.FAIL_UF,
        ),
        # Test 11: Affected version, file count exactly 1000 (boundary test)
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "1000\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "100\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "50\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            "6.0(3a)",
            script.FAIL_UF,
        ),
        # Test 12: Affected version, file count just below 1000 (boundary test)
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "999\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "100\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "50\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            "6.0(4a)",
            script.PASS,
        ),
        # Test 13: Affected version, only fatal errors (no high file count)
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "10\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "20\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "3\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "15\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "7\napic3#", "exception": None},
                ],
            },
            "6.1(2a)",
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check, mock_icurl, mock_conn, icurl_outputs, cversion, expected_result):
    cver = script.AciVersion(cversion) if cversion else None
    fabric_nodes = icurl_outputs.get(fabricNode_api, [])
    result = run_check(fabric_nodes=fabric_nodes, cversion=cver, username="admin", password="password")
    assert result.result == expected_result


@pytest.mark.parametrize(
    "icurl_outputs, conn_cmds, conn_failure, cversion, expected_result",
    [
        # Test 14: SSH connection failure on one APIC
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {},
            True,
            "6.0(5a)",
            script.ERROR,
        ),
        # Test 15: SSH command execution error on one APIC
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "", "exception": Exception("Command failed")},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "100\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "50\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            False,
            "6.0(7a)",
            script.ERROR,
        ),
    ],
)
def test_connection_errors(run_check, mock_icurl, mock_conn, icurl_outputs, cversion, expected_result):
    cver = script.AciVersion(cversion) if cversion else None
    fabric_nodes = icurl_outputs.get(fabricNode_api, [])
    result = run_check(fabric_nodes=fabric_nodes, cversion=cver, username="admin", password="password")
    assert result.result == expected_result


@pytest.mark.parametrize(
    "icurl_outputs, conn_cmds, cversion, expected_result",
    [
        # Test 16: Empty topSystem response (unhealthy cluster)
        (
            {fabricNode_api: []},
            {},
            "6.0(5a)",
            script.ERROR,
        ),
        # Test 17: Non-numeric output from commands (edge case)
        (
            {fabricNode_api: read_data(dir, "fabricNode.json")},
            {
                "10.0.0.1": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "error\napic1#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic1#", "exception": None},
                ],
                "10.0.0.2": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "0\napic2#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "invalid\napic2#", "exception": None},
                ],
                "10.0.0.3": [
                    {"cmd": ls_firmware_tmp_cmd, "output": "50\napic3#", "exception": None},
                    {"cmd": grep_fatal_bootx_cmd, "output": "0\napic3#", "exception": None},
                ],
            },
            "6.0(6a)",
            script.PASS,
        ),
    ],
)
def test_edge_cases(run_check, mock_icurl, mock_conn, icurl_outputs, cversion, expected_result):
    cver = script.AciVersion(cversion) if cversion else None
    fabric_nodes = icurl_outputs.get(fabricNode_api, [])
    result = run_check(fabric_nodes=fabric_nodes, cversion=cver, username="admin", password="password")
    assert result.result == expected_result