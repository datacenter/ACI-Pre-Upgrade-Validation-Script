import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "inband_management_policy_misconfig_check"

# icurl query
mgmtRsInBStNode = 'mgmtRsInBStNode.json?query-target-filter=or(eq(mgmtRsInBStNode.addr,"0.0.0.0"),eq(mgmtRsInBStNode.addr,"0.0.0.0/0"),eq(mgmtRsInBStNode.gw,"0.0.0.0"))'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # Target version missing
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "5.2(5c)",
            None,
            script.MANUAL,
        ),
        # Current version < 6.0(4c), target version = 6.0(4c), valid data
        (
            {
                mgmtRsInBStNode: [],
            },
            "6.0(3g)",
            "6.0(4c)",
            script.PASS,
        ),
        # Current version < 6.0(4c), target version > 6.0(4c), valid data
        (
            {
                mgmtRsInBStNode: [],
            },
            "6.0(3e)",
            "6.0(8f)",
            script.PASS,
        ),
        # Current version > 6.0(4c), target version >= 6.0(4c), invalid address
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_address_config.json"),
            },
            "6.0(4c)",
            "6.0(5h)",
            script.NA,
        ),
        
        # Current version > 6.0(4c), target version >= 6.0(4c), invalid gateway
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_gateway_config.json"),
            },
            "6.0(5h)",
            "6.0(5j)",
            script.NA,
        ),
        # Current version > 6.0(4c), target version >= 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "6.0(5j)",
            "6.0(6c)",
            script.NA,
        ),
        # Current version < 6.0(4c), target version < 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "6.0(3g)",
            "6.0(3f)",
            script.NA,
        ),
        # Current version < 6.0(4c), target version >= 6.0(4c), invalid address
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_address_config.json"),
            },
            "6.0(3g)",
            "6.0(4c)",
            script.FAIL_O,
        ),
        # Current version < 6.0(4c), target version >= 6.0(4c), invalid gateway
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_gateway_config.json"),
            },
            "5.3(2c)",
            "6.1(4h)",
            script.FAIL_O,
        ),
        # Current version < 6.0(4c), target version >= 6.0(4c), invalid both data
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode_invalid_addr_and_gw_config.json"),
            },
            "5.2(8h)",
            "6.1(3f)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion = script.AciVersion(cversion),
        tversion = script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result