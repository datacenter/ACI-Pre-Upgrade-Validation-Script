import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "inband_mgmt_zero_address_check"

# icurl queries
mgmtRsInBStNode = "mgmtRsInBStNode.json"

@pytest.mark.parametrize(
    "icurl_outputs, cver, tver, expected_result", 
    [
        # Target version missing
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode-pos.json")
            },
            "4.2(7p)",
            None,
            script.MANUAL,
        ),
        # Current Version not affected (>=6.0-1g)
        # NA  Current version not affected
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode-neg.json")
            },
            "6.1(1a)",
            "6.0(4g)",
            script.NA,
        ),
        # Target Version not affected (<=6.0-4g)
        # NA  Current version not affected
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode-neg.json")
            },
            "4.2(7a)",
            "5.0(4g)",
            script.NA,
        ),
        # Upgrade within the affected version
        # NA Affected version, No mgmtRsInBStNode MOs.
        (
            {
                mgmtRsInBStNode: []
            },
            "5.1(1g)",
            "6.0(4g)",
            script.NA,
        ),
        # PASS Affected version, mgmtRsInBStNode MOs, all with Valid addr and gw values
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode-neg.json")
            },
            "5.1(1g)",
            "6.0(4g)",
            script.PASS,
        ),
        # FAIL_O
        (
            {
                mgmtRsInBStNode: read_data(dir, "mgmtRsInBStNode-pos.json")
            },
            "5.1(1g)",
            "6.0(4g)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cver, tver, expected_result):
    result = run_check(
        cversion=script.AciVersion(cver),
        tversion=script.AciVersion(tver) if tver else None,
    )
    assert result.result == expected_result

