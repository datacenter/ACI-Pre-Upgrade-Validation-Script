import os
import pytest
import logging
import importlib
from helpers.utils import read_data

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "rogue_ep_coop_exception_mac_check"

exception_mac_api = "fvRogueExceptionMac.json?rsp-subtree-include=count"

presListener_api = "presListener.json"
presListener_api += '?query-target-filter=and(eq(presListener.lstDn,"exceptcont"))&rsp-subtree-include=count'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, cversion, expected_result, expected_data",
    [
        # NA cases (not affected)
        # tversion (affected source)
        ({}, "5.3(2f)", "5.2(3e)", script.NA, []),  # cversion (affected source)
        ({}, "6.0(2h)", "5.2(3e)", script.NA, []),  # cversion (affected source)
        ({}, "5.3(2f)", "5.2(1a)", script.NA, []),  # cversion (too old)
        ({}, "6.0(2h)", "5.2(1a)", script.NA, []),  # cversion (too old)
        # tversion (affected target)
        ({}, "6.0(3e)", "5.2(1a)", script.NA, []),  # cversion (too old)
        ({}, "6.1(3g)", "5.2(1a)", script.NA, []),  # cversion (too old)
        ({}, "6.0(9d)", "6.0(3e)", script.NA, []),  # cversion (affected target, but different than tversion))
        ({}, "6.1(3g)", "6.0(3e)", script.NA, []),  # cversion (affected target, but different than tversion))
        ({}, "6.1(3g)", "6.1(1f)", script.NA, []),  # cversion (affected target, but different than tversion))
        ({}, "6.1(3g)", "6.0(9e)", script.NA, []),  # cversion (fixed)
        # tversion (fixed)
        ({}, "6.0(9e)", "5.2(1a)", script.NA, []),  # cversion (too old)
        ({}, "6.1(4h)", "5.2(1a)", script.NA, []),  # cversion (too old)
        ({}, "6.0(9e)", "5.2(3e)", script.NA, []),  # cversion (affected source)
        ({}, "6.1(4h)", "5.2(3e)", script.NA, []),  # cversion (affected source)
        ({}, "6.0(9e)", "6.0(3e)", script.NA, []),  # cversion (affected target)
        ({}, "6.1(4h)", "6.0(3e)", script.NA, []),  # cversion (affected target)
        ({}, "6.1(4h)", "6.1(1f)", script.NA, []),  # cversion (affected target)
        ({}, "6.0(9f)", "6.0(9e)", script.NA, []),  # cversion (fixed)
        ({}, "6.1(4h)", "6.0(9e)", script.NA, []),  # cversion (fixed)
        ({}, "6.2(1a)", "6.1(4h)", script.NA, []),  # cversion (fixed)
        # Affected (pre-APIC upgrade) cases
        # tversion (affected target), cversion (affected source), no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json")},
            "6.0(3e)",
            "5.2(3e)",
            script.PASS,
            [],
        ),
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json")},
            "6.1(3g)",
            "5.2(3e)",
            script.PASS,
            [],
        ),
        # tversion (affected target), cversion (affected source), exception MACs
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json")},
            "6.0(3e)",
            "5.2(3e)",
            script.FAIL_O,
            [[5, "N/A"]],
        ),
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json")},
            "6.1(3g)",
            "5.2(3e)",
            script.FAIL_O,
            [[5, "N/A"]],
        ),
        # Affected (post-APIC upgrade, pre-switch upgrade) cases
        # tversion == cversion (affected target), no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json")},
            "6.0(3e)",
            "6.0(3e)",
            script.PASS,
            [],
        ),
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json")},
            "6.1(3g)",
            "6.1(3g)",
            script.PASS,
            [],
        ),
        # tversion == cversion (affected target), exception MACs, presListener entries present
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont.json"),
            },
            "6.0(3e)",
            "6.0(3e)",
            script.PASS,
            [],
        ),
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont.json"),
            },
            "6.1(3g)",
            "6.1(3g)",
            script.PASS,
            [],
        ),
        # tversion == cversion (affected target), exception MACs, presListener entries missing (one, many, 31, or 32(all) missing)
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont_one_missing.json"),
            },
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_O,
            [[5, "only 31 found out of 32"]],
        ),
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont_one_missing.json"),
            },
            "6.1(3g)",
            "6.1(3g)",
            script.FAIL_O,
            [[5, "only 31 found out of 32"]],
        ),
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont_many_missing.json"),
            },
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_O,
            [[5, "only 27 found out of 32"]],
        ),
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont_many_missing.json"),
            },
            "6.1(3g)",
            "6.1(3g)",
            script.FAIL_O,
            [[5, "only 27 found out of 32"]],
        ),
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont_31_missing.json"),
            },
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_O,
            [[5, "only 1 found out of 32"]],
        ),
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont_31_missing.json"),
            },
            "6.1(3g)",
            "6.1(3g)",
            script.FAIL_O,
            [[5, "only 1 found out of 32"]],
        ),
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont_32_missing.json"),
            },
            "6.0(3e)",
            "6.0(3e)",
            script.FAIL_O,
            [[5, "only 0 found out of 32"]],
        ),
        (
            {
                exception_mac_api: read_data(dir, "rogue_mac_response.json"),
                presListener_api: read_data(dir, "presListener_exceptcont_32_missing.json"),
            },
            "6.1(3g)",
            "6.1(3g)",
            script.FAIL_O,
            [[5, "only 0 found out of 32"]],
        ),
    ],
)
def test_rogue_ep_coop_exception_mac_check(run_check, mock_icurl, tversion, cversion, expected_result, expected_data):
    """Test rogue_ep_coop_exception_mac_check with various scenarios."""
    result = run_check(cversion=script.AciVersion(cversion), tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result
    assert result.data == expected_data
