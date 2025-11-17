import os
import pytest
import logging
import importlib
from helpers.utils import read_data

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion

test_function = "r_leaf_compatibility_check"

# icurl queries
infraSetPol = "uni/infra/settings.json"


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, cversion, tversion, expected_result, expected_data",
    [
        # MANUAL - No TVER
        (
            {infraSetPol: read_data(dir, "infraSetPol_no_DTF.json")},
            read_data(dir, "fabricNode_with_RL.json"),
            "4.1(1a)",
            None,
            script.MANUAL,
            [],
        ),
        # FAIL - pre DTF version, yes RL
        (
            {infraSetPol: read_data(dir, "infraSetPol_no_DTF.json")},
            read_data(dir, "fabricNode_with_RL.json"),
            "4.1(1a)",
            "5.2(1a)",
            script.FAIL_O,
            [["5.2(1a)", "Present", "Not Supported"]],
        ),
        # PASS - pre DTF version, no RL
        (
            {infraSetPol: read_data(dir, "infraSetPol_no_DTF.json")},
            read_data(dir, "fabricNode_no_RL.json"),
            "4.1(1a)",
            "5.2(1a)",
            script.NA,
            [],
        ),
        # FAIL - bug version upgrade, yes RL
        (
            {infraSetPol: read_data(dir, "infraSetPol_DTF_enabled.json")},
            read_data(dir, "fabricNode_with_RL.json"),
            "4.1(2a)",
            "4.2(2a)",
            script.FAIL_O,
            [["4.2(2a)", "Present", True]],
        ),
        # PASS - bug version upgrade, no RL
        (
            {infraSetPol: read_data(dir, "infraSetPol_DTF_enabled.json")},
            read_data(dir, "fabricNode_no_RL.json"),
            "4.1(2a)",
            "4.2(2a)",
            script.NA,
            [],
        ),
        # PASS - Fix ver to 5.x, yes RL, DTF enabled
        (
            {infraSetPol: read_data(dir, "infraSetPol_DTF_enabled.json")},
            read_data(dir, "fabricNode_with_RL.json"),
            "4.2(3a)",
            "5.2(3a)",
            script.PASS,
            [],
        ),
        # FAIL - Fix ver to 5.x, yes RL, DTF disabled
        (
            {infraSetPol: read_data(dir, "infraSetPol_DTF_disabled.json")},
            read_data(dir, "fabricNode_with_RL.json"),
            "4.2(3a)",
            "5.2(3a)",
            script.FAIL_O,
            [["5.2(3a)", "Present", False]],
        ),
        # PASS - Fix ver to 5.x, no RL
        (
            {infraSetPol: read_data(dir, "infraSetPol_DTF_disabled.json")},
            read_data(dir, "fabricNode_no_RL.json"),
            "4.2(3a)",
            "5.2(3a)",
            script.NA,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, cversion, tversion, expected_result, expected_data):
    result = run_check(
        cversion=AciVersion(cversion),
        tversion=AciVersion(tversion) if tversion else None,
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
