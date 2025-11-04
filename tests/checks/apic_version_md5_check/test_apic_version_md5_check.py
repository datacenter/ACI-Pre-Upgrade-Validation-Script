import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_version_md5_check"

api_firmware = "fwrepo/fw-aci-apic-dk9.6.0.5h.json"
api_topSystem = "topSystem.json"

topSystems = read_data(dir, "topSystem.json")
apic_ips = [
    mo["topSystem"]["attributes"]["address"]
    for mo in topSystems["imdata"]
    if mo["topSystem"]["attributes"]["role"] == "controller"
]

ls_cmd = "ls -aslh /firmware/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin"
ls_output = """\
6.1G -rwxr-xr-x 1 root root 6.1G Apr  3 16:36 /firmware/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin
apic1#
"""
ls_output_no_such_file = """\
ls: cannot access '/firmware/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin': No such file or directory
apic1#
"""

cat_cmd = "cat /firmware/fwrepos/fwrepo/md5sum/aci-apic-dk9.6.0.5h.bin"
cat_output = """\
d5afca58fce2018495d068c44eb4a547  /var/run/mgmt/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin
f2-apic1#
"""
cat_output2 = """\
d5afca58fce2018495d068c000000000  /var/run/mgmt/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin
f2-apic2#
"""
cat_output_no_such_file = """\
cat: /firmware/fwrepos/fwrepo/md5sum/aci-apic-dk9.6.0.5h.bin: No such file or directory
f2-apic1#
"""
cat_output_unexpected = """\
Something unexpected
f2-apic1#
"""


@pytest.mark.parametrize(
    "icurl_outputs, conn_failure, conn_cmds, tversion, expected_result",
    [
        # tversion missing
        ({}, False, [], None, script.MANUAL),
        # Image signing failure shown in firmwareFirmware
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h_image_sign_fail.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
            False,
            [],
            "6.0(5h)",
            script.FAIL_UF,
        ),
        # Exception failure at the very first connection()
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
            True,
            [],
            "6.0(5h)",
            script.ERROR,
        ),
        # Exception failure at the ls command
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
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
            "6.0(5h)",
            script.ERROR,
        ),
        # No such file output from the ls command
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
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
            "6.0(5h)",
            script.FAIL_UF,
        ),
        # Exception failure at the cat command
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output]),
                        "exception": None,
                    },
                    {
                        "cmd": cat_cmd,
                        "output": "",
                        "exception": Exception("Simulated exception at `cat` command"),
                    },
                ]
                for apic_ip in apic_ips
            },
            "6.0(5h)",
            script.ERROR,
        ),
        # No such file output from the cat command
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output]),
                        "exception": None,
                    },
                    {
                        "cmd": cat_cmd,
                        "output": "\n".join([cat_cmd, cat_output_no_such_file]),
                        "exception": None,
                    },
                ]
                for apic_ip in apic_ips
            },
            "6.0(5h)",
            script.FAIL_UF,
        ),
        # Unexpected output from the cat command
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output]),
                        "exception": None,
                    },
                    {
                        "cmd": cat_cmd,
                        "output": "\n".join([cat_cmd, cat_output_unexpected]),
                        "exception": None,
                    },
                ]
                for apic_ip in apic_ips
            },
            "6.0(5h)",
            script.ERROR,
        ),
        # Failure because md5sum on each APIC do not match
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
            False,
            {
                apic_ips[0]: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output]),
                        "exception": None,
                    },
                    {
                        "cmd": cat_cmd,
                        "output": "\n".join([cat_cmd, cat_output]),
                        "exception": None,
                    },
                ],
                apic_ips[1]: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output]),
                        "exception": None,
                    },
                    {
                        "cmd": cat_cmd,
                        "output": "\n".join([cat_cmd, cat_output2]),
                        "exception": None,
                    },
                ],
                apic_ips[2]: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output]),
                        "exception": None,
                    },
                    {
                        "cmd": cat_cmd,
                        "output": "\n".join([cat_cmd, cat_output]),
                        "exception": None,
                    },
                ],
            },
            "6.0(5h)",
            script.FAIL_UF,
        ),
        # Pass
        (
            {
                api_firmware: read_data(dir, "firmwareFirmware_6.0.5h.json"),
                api_topSystem: read_data(dir, "topSystem.json"),
            },
            False,
            {
                apic_ip: [
                    {
                        "cmd": ls_cmd,
                        "output": "\n".join([ls_cmd, ls_output]),
                        "exception": None,
                    },
                    {
                        "cmd": cat_cmd,
                        "output": "\n".join([cat_cmd, cat_output]),
                        "exception": None,
                    },
                ]
                for apic_ip in apic_ips
            },
            "6.0(5h)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, mock_conn, tversion, expected_result):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        username="fake_username",
        password="fake_password",
    )
    assert result.result == expected_result
