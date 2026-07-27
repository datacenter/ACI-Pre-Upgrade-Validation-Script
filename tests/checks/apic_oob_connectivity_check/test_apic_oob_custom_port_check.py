import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_oob_custom_port_check"

# icurl queries
topSystem = 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")'
commHttps = "commHttps.json"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, curl_exit_codes, expected_result",
    [
        # tversion not provided -> MANUAL
        (
            {topSystem: [], commHttps: []},
            "6.2(1a)",
            None,
            [],
            script.MANUAL,
        ),
        # cversion < 6.2(1a) -> NA (version not affected)
        (
            {topSystem: [], commHttps: []},
            "6.0(3a)",
            "6.2(1a)",
            [],
            script.NA,
        ),
        # tversion < 6.2(1a) -> NA (version not affected)
        (
            {topSystem: [], commHttps: []},
            "6.2(1a)",
            "6.0(3a)",
            [],
            script.NA,
        ),
        # Both >= 6.2, no controller nodes found -> NA
        (
            {topSystem: [], commHttps: read_data(dir, "commHttps_default_port.json")},
            "6.2(1a)",
            "6.2(2a)",
            [],
            script.NA,
        ),
        # Both >= 6.2, all APICs have no OOB configured -> PASS
        (
            {
                topSystem: read_data(dir, "topSystem_no_oob.json"),
                commHttps: read_data(dir, "commHttps_default_port.json"),
            },
            "6.2(1a)",
            "6.2(2a)",
            [],
            script.PASS,
        ),
        # Both >= 6.2, default port 443, all APICs reachable -> PASS
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_default_port.json"),
            },
            "6.2(1a)",
            "6.2(2a)",
            [0, 0, 0],
            script.PASS,
        ),
        # Both >= 6.2, default port 443, one APIC unreachable (exit code 28) -> FAIL_UF
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_default_port.json"),
            },
            "6.2(1a)",
            "6.2(2a)",
            [0, 28, 0],
            script.FAIL_UF,
        ),
        # Both >= 6.2, custom port 8443, one APIC unreachable (exit code 7) -> FAIL_UF
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_custom_port.json"),
            },
            "6.2(1a)",
            "6.2(2a)",
            [0, 7, 0],
            script.FAIL_UF,
        ),
        # Both >= 6.2, custom port 8443, all APICs unreachable -> FAIL_UF
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_custom_port.json"),
            },
            "6.2(1a)",
            "6.2(2a)",
            [28, 28, 28],
            script.FAIL_UF,
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
