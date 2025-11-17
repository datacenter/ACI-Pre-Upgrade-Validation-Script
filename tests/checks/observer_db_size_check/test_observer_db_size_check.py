import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "observer_db_size_check"

fabricNodes = read_data(dir, "fabricNode.json")
apic_ips = [
    mo["fabricNode"]["attributes"]["address"]
    for mo in fabricNodes
    if mo["fabricNode"]["attributes"]["role"] == "controller"
]

ls_cmd = "ls -lh /data2/dbstats | awk '{print $5, $9}'"
ls_output_neg = """\

11M observer_8.db
11M observer_9.db
11M observer_10.db
11M observer_template.db
apic1#
"""
ls_output_pos = """\

1.0G observer_8.db
12G observer_9.db
999M observer_10.db
11M observer_template.db
apic1#
"""
ls_output_no_such_file = """\
ls: cannot access /data2/dbstats: No such file or directory
apic1#
"""


@pytest.mark.parametrize(
    "fabric_nodes, conn_failure, conn_cmds, expected_result, expected_data",
    [
        # Connection failure
        (
            fabricNodes,
            True,
            [],
            script.ERROR,
            [
                ["1", "apic1", "Simulated exception at connect()"],
                ["2", "apic2", "Simulated exception at connect()"],
                ["3", "apic3", "Simulated exception at connect()"],
            ],
        ),
        # Simulatated exception at `ls` command
        (
            fabricNodes,
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "",
                        "exception": Exception("Simulated exception at `ls` command"),
                    }
                ]
                for apic_ip in apic_ips
            },
            script.ERROR,
            [
                ["1", "apic1", "Simulated exception at `ls` command"],
                ["2", "apic2", "Simulated exception at `ls` command"],
                ["3", "apic3", "Simulated exception at `ls` command"],
            ],
        ),
        # dbstats dir not found/not accessible
        (
            fabricNodes,
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output_no_such_file]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            script.ERROR,
            [
                ["1", "/data2/dbstats/ not found", "Check user permissions or retry as 'apic#fallback\\\\admin'"],
                ["2", "/data2/dbstats/ not found", "Check user permissions or retry as 'apic#fallback\\\\admin'"],
                ["3", "/data2/dbstats/ not found", "Check user permissions or retry as 'apic#fallback\\\\admin'"],
            ],
        ),
        # dbstats dir found, all DBs under 1G
        (
            fabricNodes,
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output_neg]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            script.PASS,
            [],
        ),
        # dbstats dir found, found DBs over 1G
        (
            fabricNodes,
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output_pos]),
                        "exception": None,
                    }
                ]
                for apic_ip in apic_ips
            },
            script.FAIL_UF,
            [
                ["1", "/data2/dbstats/observer_8.db", "1.0G"],
                ["1", "/data2/dbstats/observer_9.db", "12G"],
                ["2", "/data2/dbstats/observer_8.db", "1.0G"],
                ["2", "/data2/dbstats/observer_9.db", "12G"],
                ["3", "/data2/dbstats/observer_8.db", "1.0G"],
                ["3", "/data2/dbstats/observer_9.db", "12G"],
            ],
        ),
        # ERROR, fabricNode failure
        (
            read_data(dir, "fabricNode_no_apic.json"),
            False,
            [],
            script.ERROR,
            [],
        ),
    ],
)
def test_logic(run_check, fabric_nodes, mock_conn, expected_result, expected_data):
    result = run_check(
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
