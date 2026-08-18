import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "out_of_service_ports_check"

# operSt: '2' = 'up'
# usage: '32' = 'blacklist', '34' = 'blacklist,epg',
#        '36' = 'blacklist,fabric', '292' = 'blacklist,fabric,fabric-ext'
ethpmPhysIf_api = 'ethpmPhysIf.json'
ethpmPhysIf_api += (
    '?query-target-filter=and(eq(ethpmPhysIf.operSt,"2"),'
    'or(eq(ethpmPhysIf.usage,"32"),eq(ethpmPhysIf.usage,"34"),'
    'eq(ethpmPhysIf.usage,"36"),eq(ethpmPhysIf.usage,"292")))'
)


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_usages",
    [
        (
            # Four 'up' access and fabric ports with supported blacklist masks
            {ethpmPhysIf_api: read_data(dir, "ethpmPhysIf-pos.json")},
            script.FAIL_O,
            [
                "blacklist",
                "blacklist,epg",
                "blacklist,fabric",
                "blacklist,fabric,fabric-ext",
            ],
        ),
        (
            # 0 ports returned
            {ethpmPhysIf_api: read_data(dir, "ethpmPhysIf-neg.json")},
            script.PASS,
            [],
        )
    ],
)
def test_logic(run_check, mock_icurl, expected_result, expected_usages):
    result = run_check()
    assert result.result == expected_result
    assert [row[4] for row in result.data] == expected_usages


@pytest.mark.parametrize("usage_mask", ["32", "34", "36", "292"])
def test_requested_usage_masks_are_queried(usage_mask):
    usage_filter = 'eq(ethpmPhysIf.usage,"{}")'.format(usage_mask)
    assert usage_filter in ethpmPhysIf_api


@pytest.mark.parametrize("usage_mask", ["31", "33", "35", "37", "291", "293"])
def test_unrelated_usage_masks_are_not_queried(usage_mask):
    usage_filter = 'eq(ethpmPhysIf.usage,"{}")'.format(usage_mask)
    assert usage_filter not in ethpmPhysIf_api
