import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "oob_mgmt_security_check"

# icurl queries
mgmtOoB = "mgmtOoB.json?rsp-subtree=children"
mgmtInstP = "mgmtInstP.json?rsp-subtree=children"


@pytest.mark.parametrize(
    "icurl_outputs, cver, tver, expected_result",
    [
        # Target version missing
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB.json"),
                mgmtInstP: read_data(dir, "mgmtInstP.json"),
            },
            "4.2(7f)",
            None,
            script.MANUAL,
        ),
        # Upgrade within the affected version
        # (after CSCvx29282 and before CSCvz96117)
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB.json"),
                mgmtInstP: read_data(dir, "mgmtInstP.json"),
            },
            "4.2(7f)",
            "5.2(1g)",
            script.NA,
        ),
        # Both current and target versions are after CSCvz96117
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB.json"),
                mgmtInstP: read_data(dir, "mgmtInstP.json"),
            },
            "5.2(3g)",
            "6.0(2h)",
            script.NA,
        ),
        # Both current and target versions are before CSCvz96117
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB.json"),
                mgmtInstP: read_data(dir, "mgmtInstP.json"),
            },
            "3.2(10g)",
            "4.2(6a)",
            script.NA,
        ),
        # Upgrading to an affected version
        # (after CSCvx29282 and before CSCvz96117)
        # Security becomes loose but nobody will lose access to APICs after an
        # upgrade. Hence, marking this as PASS.
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB.json"),
                mgmtInstP: read_data(dir, "mgmtInstP.json"),
            },
            "4.2(5j)",
            "5.2(1g)",
            script.NA,
        ),
        # Upgrading to a fixed version and the security becomes tight again.
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB.json"),
                mgmtInstP: read_data(dir, "mgmtInstP.json"),
            },
            "5.2(1g)",
            "5.2(7f)",
            script.MANUAL,
        ),
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB_no_contracts.json"),
                mgmtInstP: read_data(dir, "mgmtInstP.json"),
            },
            "5.2(1g)",
            "5.2(7f)",
            script.PASS,
        ),
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB.json"),
                mgmtInstP: read_data(dir, "mgmtInstP_no_contracts.json"),
            },
            "5.2(1g)",
            "5.2(7f)",
            script.PASS,
        ),
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB_no_contracts.json"),
                mgmtInstP: read_data(dir, "mgmtInstP_no_contracts.json"),
            },
            "5.2(1g)",
            "5.2(7f)",
            script.PASS,
        ),
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB.json"),
                mgmtInstP: read_data(dir, "mgmtInstP_no_subnets.json"),
            },
            "5.2(1g)",
            "5.2(7f)",
            script.PASS,
        ),
        (
            {
                mgmtOoB: read_data(dir, "mgmtOoB_no_contracts.json"),
                mgmtInstP: read_data(dir, "mgmtInstP_no_subnets.json"),
            },
            "5.2(1g)",
            "5.2(7f)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cver, tver, expected_result):
    result = run_check(
        cversion=script.AciVersion(cver),
        tversion=script.AciVersion(tver) if tver else None,
    )
    assert result.result == expected_result
