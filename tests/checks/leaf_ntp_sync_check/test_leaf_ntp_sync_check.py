import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "leaf_ntp_sync_check"
datetimeClkPol_api = 'datetimeClkPol.json?query-target-filter=and(eq(datetimeClkPol.serverState,"enabled"))&rsp-prop-include=naming-only'
ipv4Addr_api = 'ipv4Addr.json?query-target-filter=or(wcard(ipv4Addr.dn,":"))&rsp-prop-include=naming-only'
ipv6Addr_api = 'ipv6Addr.json?&rsp-prop-include=naming-only'

@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # no pod group scenario
        ( { datetimeClkPol_api: read_data(dir, "datetimeClkPol_no_podgroup.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_issue.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_issue.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.PASS,
        ),
        # single pod scenario
        # Version not affected
        ( { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_1pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_issue.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_issue.json")},
            "6.1(3f)",
            "6.1(5e)",
            script.NA,
        ),
        # Affected version, no NTP sync issue
        ( { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_1pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_no_issue.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_no_issue.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.PASS,
        ),
        # Affected version, NTP sync issue
        ( { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_1pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_issue.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_issue.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.FAIL_O,
        ),
        # Affected version, only ipv4 NTP sync issue
        ( { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_1pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_issue.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_no_issue.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.FAIL_O,
        ),
        # Affected version, only ipv6 NTP sync issue
        ( { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_1pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_no_issue.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_issue.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.FAIL_O,
        ),
        # multi pod scenario
        # Version not affected
        (
            { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_2pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_issue_2.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_issue_2.json")},
            "6.1(3f)",
            "6.1(5e)",
            script.NA,
        ),
        # Affected version, no NTP sync issue
        (
            { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_2pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_no_issue_2.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_no_issue_2.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.PASS,
        ),
        # Affected version, one pod NTP sync issue
        (
            { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_2pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_issue_1.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_issue_1.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.FAIL_O,
        ),
        # Affected version, multiple pod NTP sync issues
        (
            { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_2pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_issue_2.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_issue_2.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.FAIL_O,
        ),
        # Affected version, only ipv4 NTP sync issues
        (
            { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_2pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_issue_2.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_no_issue_2.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.FAIL_O,
        ),
        # Affected version, only ipv6 NTP sync issues
        (
            { datetimeClkPol_api: read_data(dir, "datetimeClkPol_ntp_sync_2pod.json"),
            ipv4Addr_api: read_data(dir, "ipv4_ntp_sync_no_issue_2.json"),
            ipv6Addr_api: read_data(dir, "ipv6_ntp_sync_issue_2.json")},
            "6.1(3f)",
            "6.1(4b)",
            script.FAIL_O,
        ),
    ],
)
def test_leaf_ntp_sync_check(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion) if cversion else None,
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result 