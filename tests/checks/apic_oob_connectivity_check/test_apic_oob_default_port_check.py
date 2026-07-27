import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_oob_default_port_check"

# icurl queries
topSystem = 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, curl_exit_codes, expected_result",
    [
        # tversion not provided -> MANUAL
        (
            {topSystem: []},
            "6.0(2a)",
            None,
            [],
            script.MANUAL,
        ),
        # tversion < 6.0(2a) -> NA (version not affected)
        (
            {topSystem: []},
            "5.2(7f)",
            "5.2(7f)",
            [],
            script.NA,
        ),
        # tversion >= 6.0(2a), no controller nodes found -> NA
        (
            {topSystem: []},
            "6.0(2a)",
            "6.0(3a)",
            [],
            script.NA,
        ),
        # tversion >= 6.0(2a), all APICs have no OOB configured -> PASS
        (
            {topSystem: read_data(dir, "topSystem_no_oob.json")},
            "6.0(2a)",
            "6.0(3a)",
            [],
            script.PASS,
        ),
        # tversion >= 6.0(2a), all APICs reachable (curl returns 0) -> PASS
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob.json")},
            "6.0(2a)",
            "6.0(3a)",
            [0, 0, 0],
            script.PASS,
        ),
        # tversion >= 6.0(2a), one APIC unreachable (exit code 28 - timeout) -> FAIL_O
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob.json")},
            "6.0(2a)",
            "6.0(3a)",
            [0, 28, 0],
            script.FAIL_O,
        ),
        # tversion >= 6.0(2a), one APIC unreachable (exit code 7 - refused) -> FAIL_O
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob.json")},
            "6.0(2a)",
            "6.0(3a)",
            [0, 7, 0],
            script.FAIL_O,
        ),
        # tversion >= 6.0(2a), all APICs unreachable -> FAIL_O
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob.json")},
            "6.0(2a)",
            "6.2(3a)",
            [28, 28, 28],
            script.FAIL_O,
        ),
    ],
)
def test_logic(run_check, mock_icurl, monkeypatch, cversion, tversion, curl_exit_codes, expected_result):
    idx = [0]

    def mock_subprocess_call(cmd, shell=False):
        code = curl_exit_codes[idx[0]] if idx[0] < len(curl_exit_codes) else 0
        idx[0] += 1
        return code

    monkeypatch.setattr(script.subprocess, "call", mock_subprocess_call)
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
