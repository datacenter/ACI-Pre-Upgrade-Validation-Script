import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "l3out_route_map_missing_target_check"

# icurl queries
profiles = 'rtctrlProfile.json'
profiles += '?query-target-filter=eq(rtctrlProfile.type,"combinable")'
profiles += '&rsp-subtree=full&rsp-subtree-filter=eq(rtctrlRsCtxPToSubjP.state,"missing-target")'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # Version not affected
        (
            {profiles: read_data(dir, "rtctrlProfile_missing_target.json")},
            "5.2(8f)",
            "5.3(2d)",
            script.NA,
        ),
        # Version not affected
        (
            {profiles: read_data(dir, "rtctrlProfile_missing_target.json")},
            "6.0(2h)",
            "6.0(5h)",
            script.NA,
        ),
        # Affected version, no missing_target
        (
            {profiles: read_data(dir, "rtctrlProfile_no_missing_target.json")},
            "4.2(7s)",
            "5.2(8f)",
            script.PASS,
        ),
        # Affected version, one missing_target
        (
            {profiles: read_data(dir, "rtctrlProfile_missing_target.json")},
            "4.2(7s)",
            "5.2(8f)",
            script.FAIL_O,
        ),
        # Affected version, multiple missing_target in the same route map
        (
            {profiles: read_data(dir, "rtctrlProfile_multiple_missing_target.json")},
            "4.2(7s)",
            "5.2(8f)",
            script.FAIL_O,
        ),
        # Affected version, multiple missing_target in the different L3Out/route map
        (
            {profiles: read_data(dir, "rtctrlProfile_multiple_l3out_multiple_missing_target.json")},
            "4.2(7s)",
            "5.2(8f)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion),
    )
    assert result.result == expected_result
