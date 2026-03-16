import os
import pytest
import logging
import importlib
from helpers.utils import read_data

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "rogue_ep_coop_exception_mac_check"

exception_mac_api = 'fvRogueExceptionMac.json?rsp-subtree-include=count'

presListener_api = 'presListener.json'
presListener_api += '?query-target-filter=and(eq(presListener.lstDn,"exceptcont"))&rsp-subtree-include=count'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, cversion, expected_result",
    [
        # PASS cases
        # Non affected tversion (fixed 6.1(4h)), affected cversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(4h)",
            "5.2(5e)",
            script.PASS,
        ),
        # Non affected tversion (fixed 6.0(9e)), affected cversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(9e)",
            "6.0(1h)",
            script.PASS,
        ),
        # Non affected cversion (too old), affected tversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(5h)",
            "5.2(1a)",
            script.PASS,
        ),
        # Non affected cversion (too new), affected tversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(5h)",
            "6.0(5h)",
            script.PASS,
        ),
        # Non affected cversion and tversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(4h)",
            "5.2(1a)",
            script.PASS,
        ),
        # Non affected cversion and tversion, with exception MACs
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(4h)",
            "5.2(1a)",
            script.PASS,
        ),
        # Non affected cversion and tversion corner case, with exception MACs
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(8h)",
            "6.0(3e)",
            script.PASS,
        ),
        # Affected edge cversion (5.2(3e)) and tversion (6.1(3f)), no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(3f)",
            "5.2(3e)",
            script.PASS,
        ),
        # Affected edge cversion (6.0(2j)) and tversion (6.0(8h)), no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(8h)",
            "6.0(2j)",
            script.PASS,
        ),
        # Affected cversion and tversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(2f)",
            "5.2(8g)",
            script.PASS,
        ),
        # Affected cversion and tversion, exception MACs present but 32 exceptcont listeners present
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(3e)",
            "5.2(8g)",
            script.PASS,
        ),
        # Affected edge cversion and tversion, exception MACs present but 32 exceptcont listeners present
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(3f)",
            "5.2(3e)",
            script.PASS,
        ),
        # FAIL cases
        # Affected edge cversion (5.2(3e)) and tversion (6.1(3f)), exception MACs present, one missing exceptcont presListener
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_one_missing.json")},
            "6.1(3f)",
            "5.2(3e)",
            script.FAIL_O,
        ),
        # Affected cversion and tversion, exception MACs present, 31 exceptcont presListeners (missing 1)
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_31_missing.json")},
            "6.0(3e)",
            "5.2(8g)",
            script.FAIL_O,
        ),
        # Affected cversion and tversion, exception MACs present, many exceptcont presListeners missing
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_many_missing.json")},
            "6.1(2f)",
            "5.2(8g)",
            script.FAIL_O,
        ),
        # Affected cversion and tversion, exception MACs present, no exceptcont presListeners
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_32_missing.json")},
            "6.1(2f)",
            "5.2(8g)",
            script.FAIL_O,
        ),
        # Affected edge cversion (6.0(2j)) and tversion (6.0(8h)), exception MACs present, no exceptcont presListeners
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_32_missing.json")},
            "6.0(8h)",
            "6.0(2j)",
            script.FAIL_O,
        ),
        # After APIC upgrade.
        # Same cversion and tversion, exception MACs present, no exceptcont presListeners
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_32_missing.json")},
            "6.1(2f)",
            "6.1(2f)",
            script.FAIL_O,
        ),
        # Same cversion and tversion, exception MACs present, exceptcont listeners missing
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_31_missing.json")},
            "6.1(2f)",
            "6.1(2f)",
            script.FAIL_O,
        ),
        # Same cversion and tversion, exception MACs present, 32 exceptcont presListeners present
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(2f)",
            "6.1(2f)",
            script.PASS,
        ),
    ],
)
def test_rogue_ep_coop_exception_mac_check(run_check, mock_icurl, tversion, cversion, expected_result):
    """Test rogue_ep_coop_exception_mac_check with various scenarios."""
    result = run_check(cversion=script.AciVersion(cversion), tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result