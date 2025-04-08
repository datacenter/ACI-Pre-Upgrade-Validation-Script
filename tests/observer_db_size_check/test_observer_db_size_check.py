import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

topSystem_api = 'topSystem.json'
topSystem_api += '?query-target-filter=eq(topSystem.role,"controller")'

topSystem = read_data(dir, "topSystem.json")
apic_ips = [
    mo["topSystem"]["attributes"]["address"]
    for mo in topSystem["imdata"]
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
12.2G observer_9.db
999M observer_10.db
11M observer_template.db
apic1#
"""
ls_output_no_such_file = """\
ls: cannot access /data2/dbstats: No such file or directory
apic1#
"""

@pytest.mark.parametrize(
    "icurl_outputs, conn_failure, conn_cmds, expected_result",
    [
        # Connection failure
        (
            {topSystem_api: read_data(dir, "topSystem.json")},
            True,
            [],
            script.ERROR,
        ),
        # Simulatated exception at `ls` command
        (
            {topSystem_api: read_data(dir, "topSystem.json")},
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
            script.FAIL_UF,
        ),
        # dbstats dir not found/not accessible
        (
            {topSystem_api: read_data(dir, "topSystem.json")},
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
            script.FAIL_UF,
        ),
        # dbstats dir found, all DBs under 1G
        (
            {topSystem_api: read_data(dir, "topSystem.json")},
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
        ),
        # dbstats dir found, found DBs over 1G
        (
            {topSystem_api: read_data(dir, "topSystem.json")},
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
        ),
        # ERROR, topsystem failure
        (
            {topSystem_api: read_data(dir, "topSystem_empty.json")},
            False,
            [],
            script.ERROR,
        ),
    ],
)
def test_logic(mock_icurl, mock_conn, expected_result):
    result = script.observer_db_size_check(1, 1, "fake_username", "fake_password")
    assert result == expected_result
