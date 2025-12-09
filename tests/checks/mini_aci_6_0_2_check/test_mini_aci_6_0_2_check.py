import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "mini_aci_6_0_2_check"


@pytest.mark.parametrize(
    "cversion, tversion, fabric_nodes, expected_result, expected_data",
    [
        # tversion missing
        (
            "5.2(3a)",
            None,
            read_data(dir, "fabricNode_mini_aci.json"),
            script.MANUAL,
            [],
        ),
        # Version Not Affected (not crossing 6.0.2)
        (
            "3.2(1a)",
            "5.2(6a)",
            read_data(dir, "fabricNode_mini_aci.json"),
            script.NA,
            [],
        ),
        # Version Not Affected (not crossing 6.0.2)
        (
            "6.0(2e)",
            "6.0(5d)",
            read_data(dir, "fabricNode_mini_aci.json"),
            script.NA,
            [],
        ),
        # Version Affected, Not mini ACI
        (
            "5.2(3a)",
            "6.0(3d)",
            read_data(dir, "fabricNode_all_phys_apic.json"),
            script.PASS,
            [],
        ),
        # Version Affected, mini ACI
        (
            "4.2(2a)",
            "6.0(2c)",
            read_data(dir, "fabricNode_mini_aci.json"),
            script.FAIL_UF,
            [["2", "apic2", "virtual"], ["3", "apic3", "virtual"]],
        ),
        # Version Affected, mini ACI
        (
            "6.0(1a)",
            "6.0(2c)",
            read_data(dir, "fabricNode_mini_aci.json"),
            script.FAIL_UF,
            [["2", "apic2", "virtual"], ["3", "apic3", "virtual"]],
        ),
    ],
)
def test_logic(run_check, cversion, tversion, fabric_nodes, expected_result, expected_data):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
