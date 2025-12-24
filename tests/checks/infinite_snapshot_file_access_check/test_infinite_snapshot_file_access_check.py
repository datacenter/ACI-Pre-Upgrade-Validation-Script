import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "infinite_snapshot_file_access_check"
infraWiNode = "topology/pod-1/node-1/infraWiNode.json"

apic_ips = [
    node["fabricNode"]["attributes"]["address"]
    for node in read_data(dir, "fabricNode.json")
    if node["fabricNode"]["attributes"]["role"] == "controller"
]

grep_cmd = 'tail -n 1000 /data/techsupport/snapshotfile.txt | grep "GET /snapshots" | grep 404'

# Sample log output with 10+ requests within 2 minutes (issue detected)
grep_output_issue = """10.0.0.3 (-) - - [24/Dec/2025:14:30:15 +0000]"GET /snapshots/ce2_NDI_EXPORT_POLICY-2025-12-24T14-30-05.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:25 +0000]"GET /snapshots/ce2_backup_policy-2025-12-24T14-30-15.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:35 +0000]"GET /snapshots/ce2_DailyAutoBackup-2025-12-24T14-30-25.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:45 +0000]"GET /snapshots/ce2_ndi_up-2025-12-24T14-30-35.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:55 +0000]"GET /snapshots/ce2_hourly_backup-2025-12-24T14-30-45.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:05 +0000]"GET /snapshots/ce2_config_export-2025-12-24T14-30-55.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:15 +0000]"GET /snapshots/ce2_NDI_EXPORT_POLICY-2025-12-24T14-31-05.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:25 +0000]"GET /snapshots/ce2_fabric_backup-2025-12-24T14-31-15.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:35 +0000]"GET /snapshots/ce2_DailyAutoBackup-2025-12-24T14-31-25.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:45 +0000]"GET /snapshots/ce2_scheduler_backup-2025-12-24T14-31-35.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:55 +0000]"GET /snapshots/ce2_ndi_up-2025-12-24T14-31-45.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:32:05 +0000]"GET /snapshots/ce2_NDI_EXPORT_POLICY-2025-12-24T14-31-55.tar.gz HTTP/1.1" 404 151 "-" "-"
"""

# Sample log output with less than 10 requests or spread over more than 2 minutes (no issue)
grep_output_no_issue = """10.0.0.3 (-) - - [24/Dec/2025:14:30:15 +0000]"GET /snapshots/ce2_NDI_EXPORT_POLICY-2025-12-24T14-30-05.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:35:20 +0000]"GET /snapshots/ce2_backup_policy-2025-12-24T14-35-10.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:40:30 +0000]"GET /snapshots/ce2_DailyAutoBackup-2025-12-24T14-40-20.tar.gz HTTP/1.1" 404 151 "-" "-"
"""

@pytest.mark.parametrize(
    "icurl_outputs, conn_failure, conn_cmds, cversion, fabric_nodes, expected_result",
    [
        # Version not affected (6.0(3d) or newer)
        (
            {},
            False,
            [],
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
        ),
        # Version affected, but no issues found
        (
            {},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "5.2(1h)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
        ),
        # Version affected, issue detected (10+ requests in 2 minutes)
        (
            {},
            False,
            {
                apic_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_issue]),
                        "exception": None,
                    }
                ],
                apic_ips[1]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    }
                ],
                apic_ips[2]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    }
                ],
            },
            "6.0(2a)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
        ),
        # Connection failure
        (
            {},
            True,
            [],
            "5.2(1h)",
            read_data(dir, "fabricNode.json"),
            script.ERROR,
        ),
        # Exception during grep command execution
        (
            {},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "",
                        "exception": Exception("Simulated exception at grep command"),
                    }
                ]
                for apic_ip in apic_ips
            },
            "6.0(2a)",
            read_data(dir, "fabricNode.json"),
            script.ERROR,
        ),
        # Pass (pre-4.0 with infraWiNode)
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    },
                ]
                for apic_ip in apic_ips
            },
            "3.2(6o)",
            read_data(dir, "fabricNode_old.json"),
            script.PASS,
        ),
        (
            {},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    },
                ]
                for apic_ip in apic_ips
            },
            "3.2(6o)",
            read_data(dir, "fabricNode_no_apic.json"),
            script.ERROR,
        )
    ],
)
def test_infinite_snapshot_file_access_check(run_check, mock_icurl, mock_conn, cversion, fabric_nodes, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result