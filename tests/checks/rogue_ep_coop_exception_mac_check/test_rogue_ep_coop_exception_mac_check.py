import os
import pytest
import logging
import importlib
from helpers.utils import read_data

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "rogue_ep_coop_exception_mac_check"

# icurl queries
exception_mac_api = 'fvRogueExceptionMac.json'
exception_mac_api += '?query-target-filter=and(wcard(fvRogueExceptionMac.dn,"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}"))'

presListener_api = 'presListener.json'
presListener_api += '?query-target-filter=and(wcard(presListener.dn,"exceptcont"))'


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
        # Affected edge cversion (5.2(3e)) and tversion (6.1(3f)), no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(3f)",
            "5.2(3e)",
            script.PASS,
        ),
        # Affected edge cversion (6.0(3g)) and tversion (6.0(8h)), no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(8h)",
            "6.0(3g)",
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
        # Affected cversion and tversion, exception MACs present but 32+ exceptcont listeners present
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(3e)",
            "5.2(8g)",
            script.PASS,
        ),
        # Affected edge cversion and tversion, exception MACs present but 32+ exceptcont listeners present
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(3f)",
            "5.2(3e)",
            script.PASS,
        ),
        # MANUAL cases
        # tversion is not provided
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "",
            "5.2(8g)",
            script.MANUAL,
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
             presListener_api: []},
            "6.1(2f)",
            "5.2(8g)",
            script.FAIL_O,
        ),
        # Affected edge cversion (6.0(3g)) and tversion (6.0(8h)), exception MACs present, no exceptcont presListeners
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: []},
            "6.0(8h)",
            "6.0(3g)",
            script.FAIL_O,
        ),
    ],
    ids=[
        "PASS_non_affected_tversion_6.1(4h)_fixed_affected_cversion_no_exception_MACs",
        "PASS_non_affected_tversion_6.0(9e)_fixed_affected_cversion_no_exception_MACs",
        "PASS_non_affected_cversion_too_old_affected_tversion_no_exception_MACs",
        "PASS_non_affected_cversion_too_new_affected_tversion_no_exception_MACs",
        "PASS_non_affected_cversion_tversion_no_exception_MACs",
        "PASS_non_affected_cversion_tversion_with_exception_MACs",
        "PASS_affected_edge_cversion_5.2(3e)_tversion_6.1(3f)_no_exception_MACs",
        "PASS_affected_edge_cversion_6.0(3g)_tversion_6.0(8h)_no_exception_MACs",
        "PASS_affected_cversion_tversion_no_exception_MACs",
        "PASS_affected_cversion_tversion_exception_MACs_with_32plus_exceptcont_listeners",
        "PASS_affected_edge_cversion_tversion_exception_MACs_with_32plus_exceptcont_listeners",
        "MANUAL_tversion_not_provided",
        "FAIL_affected_edge_cversion_tversion_exception_MACs_one_missing_exceptcont_listener",
        "FAIL_affected_cversion_tversion_exception_MACs_31_exceptcont_listeners",
        "FAIL_affected_cversion_tversion_exception_MACs_many_missing_exceptcont_listeners",
        "FAIL_affected_cversion_tversion_exception_MACs_no_exceptcont_listeners",
        "FAIL_affected_edge_cversion_6.0(3g)_tversion_6.0(8h)_exception_MACs_no_exceptcont_listeners",
    ],
)
def test_rogue_ep_coop_exception_mac_check(run_check, mock_icurl, tversion, cversion, expected_result):
    """Test rogue_ep_coop_exception_mac_check with various scenarios."""
    result = run_check(cversion=script.AciVersion(cversion), tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result