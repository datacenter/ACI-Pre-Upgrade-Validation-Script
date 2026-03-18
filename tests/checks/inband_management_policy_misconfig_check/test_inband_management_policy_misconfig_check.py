import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "inband_management_policy_misconfig_check"
mgmtRsInBStNode = 'mgmtRsInBStNode.json?query-target-filter=or(eq(mgmtRsInBStNode.addr,"0.0.0.0"),eq(mgmtRsInBStNode.addr,"0.0.0.0/0"),eq(mgmtRsInBStNode.gw,"0.0.0.0"))'

@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result, expected_data",
    [
        # Current version is affected, Target version = 6.0(4c), valid data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_valid_config.json")
            },
            "5.2(7g)",
            "6.0(4c)",
            script.PASS,
            []
        ),
        # Current version is affected, Target version = 6.0(4c), invalid address
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_address_config.json"),
            },
            "5.2(7f)",
            "6.0(4c)",
            script.FAIL_O,
            [
                ["103", "0.0.0.0", "191.1.1.1"],
                ["104", "0.0.0.0/0", "191.1.1.1"],
            ]
        ),
        # Current version is affected, Target version = 6.0(4c), invalid gateway
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_gateway_config.json"),
            },
            "5.2(7f)",
            "6.0(4c)",
            script.FAIL_O,
            [
                ["103", "191.1.1.153/24", "0.0.0.0"],
            ]
        ),
        # Current version is affected,  Target version = 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "5.2(7f)",
            "6.0(4c)",
            script.FAIL_O,
            [
                ["103", "0.0.0.0", "0.0.0.0"],
            ]
        ),
        # Current version is affected,  Target version > 6.0(4c), valid data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_valid_config.json"),
            },
            "5.2(7f)",
            "6.0(8f)",
            script.PASS,
            []
        ),
        # Current version is affected,  Target version > 6.0(4c), invalid address
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_address_config.json"),
            },
            "5.2(7f)",
            "6.0(5h)",
            script.FAIL_O,
            [
                ["103", "0.0.0.0", "191.1.1.1"],
                ["104", "0.0.0.0/0", "191.1.1.1",]
            ]
        ),
        # Current version is affected,  Target version > 6.0(4c), invalid gateway
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_gateway_config.json"),
            },
            "5.2(7f)",
            "6.0(5j)",
            script.FAIL_O,
            [
                ["103", "191.1.1.153/24", "0.0.0.0"],
            ]
        ),
        # Current version is affected,  Target version > 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "5.2(7f)",
            "6.0(6c)",
            script.FAIL_O,
            [
                ["103", "0.0.0.0", "0.0.0.0"],
            ]
        ),
        # Current version is affected, Target version < 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "5.2(7f)",
            "6.0(3g)",
            script.NA,
            []
        ),
        #  Current version is affected, Target version < 6.0(4c), valid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_valid_config.json"),
            },
            "5.2(7f)",
            "6.0(3g)",
            script.NA,
            []
        ),
        # Current version is not affected, Target version = 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "5.3(2f)",
            "6.0(4c)",
            script.NA,
            []
        ),
        # Current version is not affected, Target version > 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "5.3(2f)",
            "6.0(6c)",
            script.NA,
            []
        ),
        # Current version is not affected, Target version < 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "5.3(2f)",
            "6.0(3g)",
            script.NA,
            []
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result, expected_data):
    result = run_check(cversion=script.AciVersion(cversion), tversion=script.AciVersion(tversion))
    assert result.result == expected_result
    assert result.data == expected_data