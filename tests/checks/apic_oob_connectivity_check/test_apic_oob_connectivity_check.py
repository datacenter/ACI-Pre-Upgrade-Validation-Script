import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_oob_connectivity_check"

# icurl queries
topSystem = 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")'
commHttps = "commHttps.json"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, curl_exit_codes, expected_result",
    [
        # tversion not provided -> MANUAL
        (
            {topSystem: [], commHttps: []},
            "6.0(2a)",
            None,
            [],
            script.MANUAL,
        ),
        # tversion < 6.0(2a) -> NA (version not affected)
        (
            {topSystem: [], commHttps: []},
            "5.2(7f)",
            "5.2(7f)",
            [],
            script.NA,
        ),
        # tversion >= 6.0(2a), no controller nodes found -> NA
        (
            {topSystem: [], commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [],
            script.NA,
        ),
        # tversion >= 6.0(2a), all APICs have no OOB configured -> PASS
        (
            {topSystem: read_data(dir, "topSystem_no_oob.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [],
            script.PASS,
        ),
        # tversion >= 6.0(2a), all APICs reachable on port 443 -> PASS
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 0, 0],
            script.PASS,
        ),
        # cversion >= 6.2(1g), default port 443, all APICs reachable -> PASS
        # (custom port check skipped since commHttps port == 443)
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_default_port.json"),
            },
            "6.2(1g)",
            "6.2(2a)",
            [0, 0, 0],
            script.PASS,
        ),
        # cversion >= 6.2(1g), custom port 8443, all APICs reachable on both ports -> PASS
        # (default port 443: [0,0,0], custom port 8443: [0,0,0])
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_custom_port.json"),
            },
            "6.2(1g)",
            "6.2(2a)",
            [0, 0, 0, 0, 0, 0],
            script.PASS,
        ),
        # tversion >= 6.0(2a), one APIC unreachable on port 443 (exit 28) -> FAIL_UF
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 28, 0],
            script.FAIL_UF,
        ),
        # cversion >= 6.2(1g), one APIC unreachable on default port 443 (exit 7) -> FAIL_UF
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_default_port.json"),
            },
            "6.2(1g)",
            "6.2(2a)",
            [0, 7, 0],
            script.FAIL_UF,
        ),
        # cversion >= 6.2(1g), custom port 8443, all unreachable on custom port -> FAIL_UF
        # (default port 443 all pass: [0,0,0], custom port 8443 all fail: [28,28,28])
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_custom_port.json"),
            },
            "6.2(1g)",
            "6.2(2a)",
            [0, 0, 0, 28, 28, 28],
            script.FAIL_UF,
        ),
        # cversion >= 6.2(1g), commHttps returns invalid port value -> ERROR
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_invalid_port.json"),
            },
            "6.2(1g)",
            "6.2(2a)",
            [0, 0, 0],
            script.ERROR,
        ),
        # IPv6 OOB, all APICs reachable -> PASS
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob_ipv6.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 0, 0],
            script.PASS,
        ),
        # IPv6 OOB, one APIC unreachable (exit 28) -> FAIL_UF
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob_ipv6.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 28, 0],
            script.FAIL_UF,
        ),
        # Both IPv4 and IPv6 configured, all reachable -> PASS (IPv4 should be used)
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob_both.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 0, 0],
            script.PASS,
        ),
        # Both IPv4 and IPv6 configured, one unreachable -> FAIL_UF (IPv4 should be used)
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob_both.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 28, 0],
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
