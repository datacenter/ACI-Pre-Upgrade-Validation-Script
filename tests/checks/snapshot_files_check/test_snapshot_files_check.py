import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "snapshot_files_check"
infraWiNode = "topology/pod-1/node-1/infraWiNode.json"

apic_ips = [
    node["fabricNode"]["attributes"]["address"]
    for node in read_data(dir, "fabricNode.json")
    if node["fabricNode"]["attributes"]["role"] == "controller"
]
apic_single_ips = [
    node["fabricNode"]["attributes"]["address"]
    for node in read_data(dir, "fabricNode_single_apic.json")
    if node["fabricNode"]["attributes"]["role"] == "controller"
]

grep_cmd = 'tail -n 1000 /var/log/dme/log/access.log | grep "GET /snapshots" | grep 404'

# Sample log output with 10+ requests within 2 minutes (issue detected)
grep_output_issue = """10.0.0.3 (-) - - [24/Dec/2025:14:30:06 +0000] "GET /snapshots/ce2_backup_policy-2025-12-24T14-30-06.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:12 +0000] "GET /snapshots/ce2_DailyAutoBackup-2025-12-24T14-30-12.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:18 +0000] "GET /snapshots/ce2_ndi_up-2025-12-24T14-30-18.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:24 +0000] "GET /snapshots/ce2_hourly_backup-2025-12-24T14-30-24.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:30 +0000] "GET /snapshots/ce2_config_export-2025-12-24T14-30-30.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:36 +0000] "GET /snapshots/ce2_NDI_EXPORT_POLICY-2025-12-24T14-30-36.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:42 +0000] "GET /snapshots/ce2_fabric_backup-2025-12-24T14-30-42.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:48 +0000] "GET /snapshots/ce2_DailyAutoBackup-2025-12-24T14-30-48.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:54 +0000] "GET /snapshots/ce2_scheduler_backup-2025-12-24T14-30-54.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:00 +0000] "GET /snapshots/ce2_ndi_up-2025-12-24T14-31-00.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:06 +0000] "GET /snapshots/ce2_NDI_EXPORT_POLICY-2025-12-24T14-31-06.tar.gz HTTP/1.1" 404 151 "-" "-"
"""

# Sample log output with less than 10 requests or spread over more than 2 minutes (no issue)
grep_output_no_issue = """10.0.0.3 (-) - - [24/Dec/2025:14:30:15 +0000] "GET /snapshots/ce2_NDI_EXPORT_POLICY-2025-12-24T14-30-05.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:35:20 +0000] "GET /snapshots/ce2_backup_policy-2025-12-24T14-35-10.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:40:30 +0000] "GET /snapshots/ce2_DailyAutoBackup-2025-12-24T14-40-20.tar.gz HTTP/1.1" 404 151 "-" "-"
"""

grep_output_no_file = """\
grep: /var/log/dme/log/access.log: No such file or directory
fabric-apic#
"""

# Edge case: Empty log output (no 404 requests found)
grep_output_empty = ""

# Edge case: Exactly 10 requests within 60 seconds 
grep_output_boundary_fail = """10.0.0.3 (-) - - [24/Dec/2025:14:30:00 +0000] "GET /snapshots/ce2_snapshot1.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:06 +0000] "GET /snapshots/ce2_snapshot2.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:12 +0000] "GET /snapshots/ce2_snapshot3.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:18 +0000] "GET /snapshots/ce2_snapshot4.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:24 +0000] "GET /snapshots/ce2_snapshot5.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:30 +0000] "GET /snapshots/ce2_snapshot6.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:36 +0000] "GET /snapshots/ce2_snapshot7.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:42 +0000] "GET /snapshots/ce2_snapshot8.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:48 +0000] "GET /snapshots/ce2_snapshot9.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:54 +0000] "GET /snapshots/ce2_snapshot10.tar.gz HTTP/1.1" 404 151 "-" "-"
"""

# Edge case: 9 requests within 60 seconds
grep_output_boundary_pass = """10.0.0.3 (-) - - [24/Dec/2025:14:30:00 +0000] "GET /snapshots/ce2_snapshot1.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:08 +0000] "GET /snapshots/ce2_snapshot2.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:16 +0000] "GET /snapshots/ce2_snapshot3.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:24 +0000] "GET /snapshots/ce2_snapshot4.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:32 +0000] "GET /snapshots/ce2_snapshot5.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:40 +0000] "GET /snapshots/ce2_snapshot6.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:48 +0000] "GET /snapshots/ce2_snapshot7.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:30:56 +0000] "GET /snapshots/ce2_snapshot8.tar.gz HTTP/1.1" 404 151 "-" "-"
10.0.0.3 (-) - - [24/Dec/2025:14:31:04 +0000] "GET /snapshots/ce2_snapshot9.tar.gz HTTP/1.1" 404 151 "-" "-"
"""

@pytest.mark.parametrize(
    "icurl_outputs, conn_failure, conn_cmds, cversion, tversion, fabric_nodes, expected_result",
    [
        # Version not affected (6.0(3d) or newer)
        (
            {},
            False,
            [],
            "6.0(3d)",
            "6.0(3e)",
            read_data(dir, "fabricNode.json"),
            script.NA,
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
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
        ),
        # Version affected, issue detected (10+ requests in 1 minutes)
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
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
        ),
        # Version affected, issue detected (10+ requests in 1 minutes)
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
                        "output": "\n".join([grep_cmd, grep_output_issue]),
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
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
        ),
        # Connection failure
        (
            {},
            True,
            [],
            "5.2(1h)",
            "6.0(3d)",
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
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.ERROR,
        ),
        # error (no such file or directory for cmd execution)
        (
            {},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_file]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "5.2(1h)",
            "6.0(3d)",
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
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.PASS,
        ),
        # fail (pre-4.0 with infraWiNode)
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_issue]),
                        "exception": None,
                    },
                ]
                for apic_ip in apic_ips
            },
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.FAIL_UF,
        ),
        # connection failure(pre-4.0 with infraWiNode)
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
            True,
            [],
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.ERROR,
        ),
        # exception during grep command execution (pre-4.0 with infraWiNode)
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
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
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.ERROR,
        ),
        # error (pre-4.0 with infraWiNode and no such file or directory for cmd execution)
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_file]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.ERROR,
        ),
        # Edge case: Single APIC with issue
        (
            {},
            False,
            {
                apic_single_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_issue]),
                        "exception": None,
                    }
                ]
            },
            "6.0(2a)",
            "6.0(3d)",
            read_data(dir, "fabricNode_single_apic.json"),
            script.FAIL_UF,
        ),
        # Edge case: Single APIC without issue
        (
            {},
            False,
            {
                apic_single_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    }
                ]
            },
            "6.0(2a)",
            "6.0(3d)",
            read_data(dir, "fabricNode_single_apic.json"),
            script.PASS,
        ),
        # Edge case: Single APIC with connection failure
        (
            {},
            True,
            [],
            "6.0(2a)",
            "6.0(3d)",
            read_data(dir, "fabricNode_single_apic.json"),
            script.ERROR,
        ),
        # Edge case: Single APIC with file not found
        (
            {},
            False,
            {
                apic_single_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_file]),
                        "exception": None,
                    }
                ]
            },
            "6.0(2a)",
            "6.0(3d)",
            read_data(dir, "fabricNode_single_apic.json"),
            script.ERROR,
        ),
        # Edge case: Multi-APIC with one file not found, others clean
        (
            {},
            False,
            {
                apic_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    }
                ],
                apic_ips[1]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_file]),
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
            "5.2(8g)",
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.ERROR,
        ),
        # Edge case: Empty log output (no 404 requests)
        (
            {},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_empty]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "6.0(2a)",
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
        ),
        # Edge case: Exactly 10 requests within 60 seconds (boundary - should fail)
        (
            {},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_boundary_fail]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "6.0(2a)",
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
        ),
        # Edge case: 9 requests within 60 seconds (boundary - should pass)
        (
            {},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_boundary_pass]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "6.0(2a)",
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
        ),
        # Edge case: Multi-APIC with all having issues
        (
            {},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_issue]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "5.2(8g)",
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
        ),
        # Edge case: Multi-APIC with mixed issues (issue + file not found + clean)
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
                        "output": "\n".join([grep_cmd, grep_output_no_file]),
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
            "6.0(3d)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_UF,
        ),
        # Edge case (pre-4.0): Single APIC with issue
        (
            {infraWiNode: read_data(dir, "infraWiNode_single_apic.json")},
            False,
            {
                apic_single_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_issue]),
                        "exception": None,
                    }
                ]
            },
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old_single_apic.json"),
            script.FAIL_UF,
        ),
        # Edge case (pre-4.0): Single APIC without issue
        (
            {infraWiNode: read_data(dir, "infraWiNode_single_apic.json")},
            False,
            {
                apic_single_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    }
                ]
            },
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old_single_apic.json"),
            script.PASS,
        ),
        # Edge case (pre-4.0): Single APIC with connection failure
        (
            {infraWiNode: read_data(dir, "infraWiNode_single_apic.json")},
            True,
            [],
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old_single_apic.json"),
            script.ERROR,
        ),
        # Edge case (pre-4.0): Single APIC with file not found
        (
            {infraWiNode: read_data(dir, "infraWiNode_single_apic.json")},
            False,
            {
                apic_single_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_file]),
                        "exception": None,
                    }
                ]
            },
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old_single_apic.json"),
            script.ERROR,
        ),
        # Edge case (pre-4.0): Multi-APIC with first APIC having issue, others clean
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
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
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.FAIL_UF,
        ),
        # Edge case (pre-4.0): Multi-APIC with one file not found, others clean
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
            False,
            {
                apic_ips[0]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_issue]),
                        "exception": None,
                    }
                ],
                apic_ips[1]: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_no_file]),
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
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.ERROR,
        ),
        # Edge case (pre-4.0): Empty log output (no 404 requests)
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_empty]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.PASS,
        ),
        # Edge case (pre-4.0): Exactly 10 requests within 60 seconds (boundary - should fail)
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_boundary_fail]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.FAIL_UF,
        ),
        # Edge case (pre-4.0): 9 requests within 60 seconds
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
            False,
            {
                apic_ip: [
                    {
                        "cmd": grep_cmd,
                        "output": "\n".join([grep_cmd, grep_output_boundary_pass]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.PASS,
        ),
        # Edge case (pre-4.0): Multi-APIC with mixed issues (issue + file not found + clean)
        (
            {infraWiNode: read_data(dir, "infraWiNode_apic1.json")},
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
                        "output": "\n".join([grep_cmd, grep_output_no_file]),
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
            "3.2(6o)",
            "6.0(3d)",
            read_data(dir, "fabricNode_old.json"),
            script.FAIL_UF,
        ),
    ],
)
def test_snapshot_files_check(run_check, mock_icurl, mock_conn, cversion, tversion, fabric_nodes, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion),
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result