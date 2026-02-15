import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_disk_space_faults_check"

# icurl queries
faultInst_api = 'faultInst.json?query-target-filter=or(eq(faultInst.code,"F1527"),eq(faultInst.code,"F1528"),eq(faultInst.code,"F1529"))'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # ===== AFFECTED VERSIONS (< 6.1(4a)) =====
        # Older 4.x version, no /tmp faults
        (
            {faultInst_api: []},
            "4.2(7f)",
            script.PASS,
        ),
        # 5.x version, no /tmp faults
        (
            {faultInst_api: []},
            "5.2(8f)",
            script.PASS,
        ),
        # 6.0.x version, no /tmp faults
        (
            {faultInst_api: []},
            "6.0(5a)",
            script.PASS,
        ),
        # Just before fix version 6.1(3z), no /tmp faults
        (
            {faultInst_api: []},
            "6.1(3z)",
            script.PASS,
        ),
        # 4.x version with /tmp faults
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "4.2(7t)",
            script.FAIL_UF,
        ),
        # 5.x version with /tmp faults
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "5.2(8f)",
            script.FAIL_UF,
        ),
        # 6.0.x version with /tmp faults
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "6.0(2h)",
            script.FAIL_UF,
        ),
        # Just before fix version 6.1(3z) with /tmp faults
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "6.1(3z)",
            script.FAIL_UF,
        ),
        # Affected version with only non-/tmp faults (should FAIL_UF)
        (
            {faultInst_api: read_data(dir, "faultInst_non_tmp.json")},
            "5.2(6a)",
            script.FAIL_UF,
        ),
        # Affected version with mixed /tmp and non-/tmp faults (should FAIL_UF)
        (
            {faultInst_api: read_data(dir, "faultInst_mixed.json")},
            "6.0(3a)",
            script.FAIL_UF,
        ),
        # 3.x version with /tmp faults
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "3.2(10e)",
            script.FAIL_UF,
        ),
        # 4.x version with only non-/tmp faults (should FAIL_UF)
        (
            {faultInst_api: read_data(dir, "faultInst_non_tmp.json")},
            "4.2(7f)",
            script.FAIL_UF,
        ),
        # 6.0.x version with mixed faults
        (
            {faultInst_api: read_data(dir, "faultInst_mixed.json")},
            "6.0(5h)",
            script.FAIL_UF,
        ),
        # ===== FIXED VERSIONS (>= 6.1(4a)) =====
        # Exact fix version 6.1(4a) with /tmp faults (should be NA - CSCwo96334 doesn't apply)
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "6.1(4a)",
            script.NA,
        ),
        # Exact fix version 6.1(4a) without faults (should PASS)
        (
            {faultInst_api: []},
            "6.1(4a)",
            script.PASS,
        ),
        # Later 6.1.x version with /tmp faults (should be NA - CSCwo96334 doesn't apply)
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "6.1(5a)",
            script.NA,
        ),
        # 6.2.x version with /tmp faults (should be NA - CSCwo96334 doesn't apply)
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "6.2(1a)",
            script.NA,
        ),
        # Future 7.x version with /tmp faults (should be NA - CSCwo96334 doesn't apply)
        (
            {faultInst_api: read_data(dir, "faultInst_tmp_pos.json")},
            "7.0(1a)",
            script.NA,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion("5.2(1a)"),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
