import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "fabricdomain_name_check"

# icurl queries
topSystem = 'topology/pod-1/node-1/sys.json'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, fabric_nodes, expected_result, expected_data",
    [
        # tversion missing
        (
            {topSystem: read_data(dir, "topSystem_1POS.json")},
            "5.2(3g)",
            None,
            read_data(dir, "fabricNode.json"),
            script.MANUAL,
            [],
        ),
        # APIC 1 missing in fabric_nodes (fabricNode)
        (
            {topSystem: read_data(dir, "topSystem_1POS.json")},
            "5.2(3g)",
            "6.0(2h)",
            read_data(dir, "fabricNode_no_apic1.json"),
            script.ERROR,
            [],
        ),
        # APIC 1 missing in topSystem
        (
            {topSystem: []},
            "5.2(3g)",
            "6.0(2h)",
            read_data(dir, "fabricNode.json"),
            script.ERROR,
            [],
        ),
        # `;` char test
        (
            {topSystem: read_data(dir, "topSystem_1POS.json")},
            "5.2(3g)",
            "6.0(2h)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [["fabric;4", "Contains a special character"]]
        ),
        (
            {topSystem: read_data(dir, "topSystem_1POS.json")},
            "6.0(3a)",
            "6.0(2h)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [["fabric;4", "Contains a special character"]]
        ),
        # `#` char test
        (
            {topSystem: read_data(dir, "topSystem_2POS.json")},
            "5.2(3g)",
            "6.0(2h)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [["fabric#4", "Contains a special character"]]
        ),
        (
            {topSystem: read_data(dir, "topSystem_2POS.json")},
            "6.0(3a)",
            "6.0(2h)",
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [["fabric#4", "Contains a special character"]]
        ),
        # Neither ; or # in fabricDomain
        (
            {topSystem: read_data(dir, "topSystem_NEG.json")},
            "5.2(3g)",
            "6.0(2h)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
        # only affected 6.0(2h), regardless of special chars
        (
            {topSystem: read_data(dir, "topSystem_1POS.json")},
            "5.2(3g)",
            "6.0(1j)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
        # Eventual 6.0(3) has fix
        (
            {topSystem: read_data(dir, "topSystem_1POS.json")},
            "5.2(3g)",
            "6.0(3a)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
        (
            {topSystem: read_data(dir, "topSystem_1POS.json")},
            "6.0(3a)",
            "6.0(4a)",
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, fabric_nodes, expected_result, expected_data):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
