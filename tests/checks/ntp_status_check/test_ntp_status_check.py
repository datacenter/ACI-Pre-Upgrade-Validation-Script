import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "ntp_status_check"

# icurl queries
apic_ntp = "datetimeNtpq.json"
switch_ntp = "datetimeClkPol.json"


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_data",
    [
        # FAIL - APIC is not Synced
        (
            {
                apic_ntp: read_data(dir, "POS_datetimeNtpq.json"),
                switch_ntp: read_data(dir, "NEG_datetimeClkPol.json"),
            },
            script.FAIL_UF,
            [["1", "1"]],
        ),
        # FAIL - Switch is not Synced
        (
            {
                apic_ntp: read_data(dir, "NEG_datetimeNtpq.json"),
                switch_ntp: read_data(dir, "POS_datetimeClkPol.json"),
            },
            script.FAIL_UF,
            [["1", "201"]],
        ),
        # FAIL - APIC and Switch are not Synced
        (
            {
                apic_ntp: read_data(dir, "POS_datetimeNtpq.json"),
                switch_ntp: read_data(dir, "POS_datetimeClkPol.json"),
            },
            script.FAIL_UF,
            [["1", "1"], ["1", "201"]],
        ),
        # PASS - Both are synced
        (
            {
                apic_ntp: read_data(dir, "NEG_datetimeNtpq.json"),
                switch_ntp: read_data(dir, "NEG_datetimeClkPol.json"),
            },
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, expected_result, expected_data):
    result = run_check(
        fabric_nodes=read_data(dir, "fabricNode.json"),
    )
    assert result.result == expected_result
    assert result.data == expected_data
