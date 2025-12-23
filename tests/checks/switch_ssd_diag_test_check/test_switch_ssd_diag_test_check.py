import os
import pytest
import logging
import importlib
from helpers.utils import read_data
import pexpect

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "switch_ssd_diag_test_check"

# ---- Test Command & Query Constants ----
diag_cmd = "show diagnostic result module 1 test 24 detail"
fault_query = 'faultInst.json?query-target-filter=eq(faultInst.code,"F2421")'
hostname_cmd = "bash -c \"hostname\""

# ---- Test Data Outputs ----
output_success_leaf101 = "show diagnostic result module 1 test 24 detail\n\nDiagnostic module 1, test 24:\n\nError code ---------> DIAG TEST SUCCESS\nTotal run count ---------> 2915\nTotal failure count ---------> 0\nLast test execution time ---------> 2023-11-15 10:30:45\n\nleaf101#"

output_success_leaf102 = "show diagnostic result module 1 test 24 detail\n\nDiagnostic module 1, test 24:\n\nError code ---------> DIAG TEST SUCCESS\nTotal run count ---------> 3100\nTotal failure count ---------> 0\nLast test execution time ---------> 2023-11-15 10:31:12\n\nleaf102#"

output_fail_leaf101 = "show diagnostic result module 1 test 24 detail\n\nDiagnostic module 1, test 24:\n\nError code ---------> DIAG TEST FAIL\nTotal run count ---------> 1500\nTotal failure count ---------> 1500\nLast test execution time ---------> 2023-11-15 09:15:22\n\nleaf101#"

output_fail_leaf102 = "show diagnostic result module 1 test 24 detail\n\nDiagnostic module 1, test 24:\n\nError code ---------> DIAG TEST FAIL\nTotal run count ---------> 500\nTotal failure count ---------> 500\nLast test execution time ---------> 2023-11-15 10:25:33\n\nleaf102#"

output_100pct_failure_leaf102 = "show diagnostic result module 1 test 24 detail\n\nDiagnostic module 1, test 24:\n\nError code ---------> DIAG TEST SUCCESS\nTotal run count ---------> 850\nTotal failure count ---------> 850\nLast test execution time ---------> 2023-11-15 08:45:33\n\nleaf102#"

output_high_failure_leaf101 = "show diagnostic result module 1 test 24 detail\n\nDiagnostic module 1, test 24:\n\nError code ---------> DIAG TEST SUCCESS\nTotal run count ---------> 1000\nTotal failure count ---------> 150\nLast test execution time ---------> 2023-11-15 07:20:11\n\nleaf101#"

output_invalid_format = "show diagnostic result module 1 test 24 detail\n\nDiagnostic module 1, test 24:\n\nInvalid output format\nNo error code or counts\n\nleaf101#"

# ---- Mock Fault Data ----
no_faults = []
f2421_fault_leaf101 = [
    {
        "faultInst": {
            "attributes": {
                "dn": "topology/pod-1/node-101/faultInst",
                "code": "F2421",
                "severity": "critical",
            }
        }
    }
]

# ---- Mock cmd_outputs (hostname) ----
cmd_outputs_apic1 = {
    hostname_cmd: {
        "splitlines": True,
        "output": "apic1",
    }
}

# ---- Mock icurl_outputs (faults) ----
icurl_no_faults = {fault_query: no_faults}
icurl_with_f2421 = {fault_query: f2421_fault_leaf101}

# ---- Mock conn_cmds (SSH commands) ----
conn_leaf101_success = {
    "leaf101": [
        {
            "cmd": diag_cmd,
            "output": output_success_leaf101,
            "exception": None,
        }
    ]
}

conn_leaf102_success = {
    "leaf102": [
        {
            "cmd": diag_cmd,
            "output": output_success_leaf102,
            "exception": None,
        }
    ]
}

conn_leaf101_fail = {
    "leaf101": [
        {
            "cmd": diag_cmd,
            "output": output_fail_leaf101,
            "exception": None,
        }
    ]
}

conn_leaf102_fail = {
    "leaf102": [
        {
            "cmd": diag_cmd,
            "output": output_fail_leaf102,
            "exception": None,
        }
    ]
}

conn_leaf102_100pct_failure = {
    "leaf102": [
        {
            "cmd": diag_cmd,
            "output": output_100pct_failure_leaf102,
            "exception": None,
        }
    ]
}

conn_leaf101_timeout = {
    "leaf101": [
        {
            "cmd": diag_cmd,
            "output": "",
            "exception": pexpect.TIMEOUT("SSH connection timeout"),
        }
    ]
}

conn_leaf101_eof = {
    "leaf101": [
        {
            "cmd": diag_cmd,
            "output": "",
            "exception": pexpect.EOF("Connection closed"),
        }
    ]
}

conn_leaf101_invalid_output = {
    "leaf101": [
        {
            "cmd": diag_cmd,
            "output": output_invalid_format,
            "exception": None,
        }
    ]
}

conn_both_switches_success = {
    "leaf101": [
        {
            "cmd": diag_cmd,
            "output": output_success_leaf101,
            "exception": None,
        }
    ],
    "leaf102": [
        {
            "cmd": diag_cmd,
            "output": output_success_leaf102,
            "exception": None,
        }
    ],
}

conn_mixed_results = {
    "leaf101": [
        {
            "cmd": diag_cmd,
            "output": output_success_leaf101,
            "exception": None,
        }
    ],
    "leaf102": [
        {
            "cmd": diag_cmd,
            "output": output_fail_leaf102,
            "exception": None,
        }
    ],
}

# ---- Fabric Node Data ----
fabric_with_switches = read_data(dir, "fabricNode_with_switches.json")
fabric_single_leaf101 = read_data(dir, "fabricNode_single_switch.json")
fabric_single_leaf102 = read_data(dir, "fabricNode_single_switch2.json")
fabric_no_switches = read_data(dir, "fabricNode_no_switches.json")

# ---- Expected Results Data ----
data_pass_all = []

data_fail_leaf101_explicit = [["leaf101", "DIAG TEST FAIL", 1500, "N/A"]]

data_fail_leaf102_100pct = [["leaf102", "DIAG TEST SUCCESS", 850, "N/A"]]

data_error_conn_failure = [["leaf101", "Error: Simulated exception at connect()", "N/A", "N/A"]]

data_error_timeout = [["leaf101", "SSH Timeout", "N/A", "N/A"]]

data_error_eof = [["leaf101", "SSH Connection Closed", "N/A", "N/A"]]

data_error_invalid_output = [["leaf101", "SSD Diag Test results are not available", "N/A", "N/A"]]

data_fail_leaf102_mixed = [["leaf102", "DIAG TEST FAIL", 500, "N/A"]]


@pytest.mark.parametrize(
    "icurl_outputs, conn_failure, conn_cmds, cmd_outputs, fabric_nodes, expected_result, expected_data",
    [
        # Test 1: PASS - All switches have SUCCESS status and no failures
        (
            icurl_no_faults,
            False,
            conn_both_switches_success,
            cmd_outputs_apic1,
            fabric_with_switches,
            script.PASS,
            data_pass_all,
        ),
        
        # Test 2: FAIL_O - Error code shows DIAG TEST FAIL
        (
            icurl_no_faults,
            False,
            conn_leaf101_fail,
            cmd_outputs_apic1,
            fabric_single_leaf101,
            script.FAIL_O,
            data_fail_leaf101_explicit,
        ),
        
        # Test 3: FAIL_O - 100% failure rate (run_count == failure_count)
        (
            icurl_no_faults,
            False,
            conn_leaf102_100pct_failure,
            cmd_outputs_apic1,
            fabric_single_leaf102,
            script.FAIL_O,
            data_fail_leaf102_100pct,
        ),
        
        # Test 4: ERROR - SSH connection failure
        (
            icurl_no_faults,
            True,
            {},
            cmd_outputs_apic1,
            fabric_single_leaf101,
            script.ERROR,
            data_error_conn_failure,
        ),
        
        # Test 5: ERROR - SSH timeout
        (
            icurl_no_faults,
            False,
            conn_leaf101_timeout,
            cmd_outputs_apic1,
            fabric_single_leaf101,
            script.ERROR,
            data_error_timeout,
        ),
        
        # Test 6: ERROR - SSH EOF (connection closed)
        (
            icurl_no_faults,
            False,
            conn_leaf101_eof,
            cmd_outputs_apic1,
            fabric_single_leaf101,
            script.ERROR,
            data_error_eof,
        ),
        
        # Test 7: NA - No active switches in fabric
        (
            icurl_no_faults,
            False,
            {},
            cmd_outputs_apic1,
            fabric_no_switches,
            script.NA,
            [],
        ),
        
        # Test 8: FAIL_O - Mixed results (some switches pass, some fail)
        (
            icurl_no_faults,
            False,
            conn_mixed_results,
            cmd_outputs_apic1,
            fabric_with_switches,
            script.FAIL_O,
            data_fail_leaf102_mixed,
        ),
        
        # Test 9: ERROR - Cannot parse diagnostic output (missing fields)
        (
            icurl_no_faults,
            False,
            conn_leaf101_invalid_output,
            cmd_outputs_apic1,
            fabric_single_leaf101,
            script.ERROR,
            data_error_invalid_output,
        ),
    ],
)

def test_logic(run_check, mock_icurl, mock_conn, mock_run_cmd, fabric_nodes, expected_result, expected_data):
    
    result = run_check(username="test_user", password="test_pass", fabric_nodes=fabric_nodes)
    assert result.result == expected_result
    assert result.data == expected_data