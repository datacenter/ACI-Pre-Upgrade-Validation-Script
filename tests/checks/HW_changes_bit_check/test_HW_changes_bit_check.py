import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "HW_changes_bit_check"

# Define API endpoints
fabricNode_api = 'fabricNode.json'
fabricNode_api += '?query-target-filter=or(eq(fabricNode.model,"N9K-C9316D-GX"),eq(fabricNode.model,"N9K-C93600CD-GX"))'


fabricNode = read_data(dir, "FabricNodes_matching.json")

node_names = [
    mo["fabricNode"]["attributes"]["name"]
    for mo in fabricNode
]

ifconfig_cmd = "ifconfig | grep 255.255.255.255"

ifconfig_output = "inet 10.0.0.1  netmask 255.255.255.255  broadcast 0.0.0.0"

hw_changes_bit_cmd = "vsh -c 'show sprom cpu-info' | grep \"HW Changes Bits\""

hw_changes_lower_bit_output = """\
vsh -c 'show sprom cpu-info' | grep 'HW Changes Bits'
 HW Changes Bits : 0x0
leaf12#"""

hw_changes_higher_bit_output = """\
vsh -c 'show sprom cpu-info' | grep 'HW Changes Bits'
 HW Changes Bits : 0x3
leaf12#"""

hw_changes_no_output = """\
vsh -c 'show sprom cpu-info' | grep 'HW Changes Bits'

leaf12#"""


@pytest.mark.parametrize(
    "fabric_nodes, conn_failure, conn_cmds, cmd_outputs, tversion, expected_result",
    [   
        # tversion not given 
        (
            [],
            False,
            {},
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            None,
            script.MANUAL,
        ),
    
        # Connection failure
        (
            read_data(dir, "FabricNodes_matching.json"),
            True,
            {},
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            "14.2(5a)",
            script.ERROR,
        ),

        # No Matching model nodes found
        (
            [],
            False,
            {},
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            "14.2(5a)",
            script.PASS,
        ),

        # All nodes with HW Changes Bits = 0x0
        (
            read_data(dir, "FabricNodes_matching.json"),
            False,
            {
                node_name: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_lower_bit_output,
                        "exception": None,
                    }
                ]
                for node_name in node_names
            },
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            "14.2(5a)",
            script.FAIL_O,
        ),

        # All nodes with HW Changes Bits = 0x3
        (
            read_data(dir, "FabricNodes_matching.json"),
            False,
            {
                node_name: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_higher_bit_output,
                        "exception": None,
                    }
                ]
                for node_name in node_names
            },
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            "14.2(5a)",
            script.PASS,
        ),

        # One node fails (0x0), another node pass (0x3)
        (
            read_data(dir, "FabricNodes_matching.json"),
            False,
            {
                node_names[0]: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_lower_bit_output,
                        "exception": None,
                    }
                ],
                node_names[1]: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_higher_bit_output,
                        "exception": None,
                    }
                ],
                node_names[2]: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_lower_bit_output,
                        "exception": None,
                    }
                ],
                node_names[3]: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_higher_bit_output,
                        "exception": None,
                    }
                ]
            },
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            "14.2(5a)",
            script.FAIL_O,
        ),

        # No output from command execution
        (
            read_data(dir, "FabricNodes_matching.json"),
            False,
            {
                node_name: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_no_output,
                        "exception": None,
                    }
                ]
                for node_name in node_names
            },
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            "14.2(5a)",
            script.ERROR,
        ),

        # One node connection fails, others succeed
        (
            read_data(dir, "FabricNodes_matching.json"),
            False,
            {
                node_names[0]: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_lower_bit_output,
                        "exception": None,
                    }
                ],
                node_names[1]: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": "",
                        "exception": Exception("connection_failure"),
                    }
                ],
                node_names[2]: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_lower_bit_output,
                        "exception": None,
                    }
                ],
                node_names[3]: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": hw_changes_higher_bit_output,
                        "exception": None,
                    }
                ]
            },
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            "14.2(5a)",
            script.FAIL_O,
        ),

        # Command execution exception
        (
            read_data(dir, "FabricNodes_matching.json"),
            False,
            {
                node_name: [
                    {
                        "cmd": hw_changes_bit_cmd,
                        "output": "",
                        "exception": Exception("Command execution failed"),
                    }
                ]
                for node_name in node_names
            },
            {ifconfig_cmd: {"splitlines": True, "output": ifconfig_output}},
            "14.2(5a)",
            script.ERROR,
        ),

        # ERROR when APIC IP cannot be determined (empty ifconfig output)
        (
            read_data(dir, "FabricNodes_matching.json"),
            False,
            {},
            {ifconfig_cmd: {"splitlines": True, "output": ""}},
            "14.2(5a)",
            script.ERROR,
        ),
    ],
)

def test_logic(run_check, fabric_nodes, mock_conn, mock_run_cmd, tversion, expected_result):

    result = run_check(tversion=script.AciVersion(tversion) if tversion else None, username=None, password=None, fabric_nodes=fabric_nodes)
    assert result.result == expected_result