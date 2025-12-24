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
        #  Non affected tversion, affected cversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(3g)",
            "5.2(8e)",
            script.PASS,
        ),
        # Non affected cversion, affected tversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(8h)",
            "3.1(2v)",
            script.PASS,
        ),
        # non affected cversion and tversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(4h)",
            "3.1(2s)",
            script.PASS,
        ),
        # non affected cversion and tversion, with exception MACs
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(4h)",
            "3.1(2s)",
            script.PASS,
        ),
        # affected edge cversion and tversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(3f)",
            "5.2(7f)",
            script.PASS,
        ),
        # affected cversion and tversion, no exception MACs
        (
            {exception_mac_api: read_data(dir, "no_rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(2f)",
            "5.2(8g)",
            script.PASS,
        ),
        # affected version, exception MACs present but exceptcont listeners present
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.0(3e)",
            "5.2(8g)E",
            script.PASS,
        ),
        # affected edge version, exception MACs present but exceptcont listeners present
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont.json")},
            "6.1(3f)",
            "5.2(7f)",
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
        # affected edge version, exception MACs present, one missing exceptcont presListeners
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_one_missing.json")},
            "6.1(3f)",
            "5.2(7f)",
            script.FAIL_O,
        ),
        # affected version, exception MACs present, 31 exceptcont presListeners missing
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_31_missing.json")},
            "6.0(3e)",
            "5.2(8g)E",
            script.FAIL_O,
        ),
        # affected version, exception MACs present, many exceptcont presListeners missing
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: read_data(dir, "presListener_exceptcont_many_missing.json")},
            "6.1(2f)",
            "5.2(8g)",
            script.FAIL_O,
        ),
        # affected version, exception MACs present, no exceptcont presListeners missing
        (
            {exception_mac_api: read_data(dir, "rogue_mac_response.json"),
             presListener_api: []},
            "6.1(2f)",
            "5.2(8g)",
            script.FAIL_O,
        ),
    ],
    ids=[
        "PASS_non_affected_tversion_affected_cversion_no_exception_MACs",
        "PASS_non_affected_cversion_affected_tversion_no_exception_MACs",
        "PASS_non_affected_cversion_tversion_no_exception_MACs",
        "PASS_non_affected_cversion_tversion_with_exception_MACs",
        "PASS_affected_edge_cversion_tversion_no_exception_MACs",
        "PASS_affected_cversion_tversion_no_exception_MACs",
        "PASS_affected_cversion_tversion_exception_MACs_with_exceptcont_listeners",
        "PASS_affected_edge_cversion_tversion_exception_MACs_with_exceptcont_listeners",
        "MANUAL_tversion_not_provided",
        "FAIL_affected_edge_cversion_tversion_exception_MACs_one_missing_exceptcont_listener",
        "FAIL_affected_cversion_tversion_exception_MACs_31_missing_exceptcont_listeners",
        "FAIL_affected_cversion_tversion_exception_MACs_many_missing_exceptcont_listeners",
        "FAIL_affected_cversion_tversion_exception_MACs_no_exceptcont_listeners",
    ],
)
def test_rogue_ep_coop_exception_mac_check(run_check, mock_icurl, tversion, cversion, expected_result):
    """Test rogue_ep_coop_exception_mac_check with various scenarios."""
    result = run_check(cversion=script.AciVersion(cversion), tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result