import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "leaf_ntp_sync_check"

fabricRsTimePol_api = "fabricRsTimePol.json"
datetimePol_mo1 = "uni/fabric/time-default.json"
datetimePol_mo2 = "uni/fabric/time-NEW1.json"

@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # no pod group scenario
        ( { fabricRsTimePol_api: read_data(dir, "fabricRsTimePol_no_podgroup.json"),
            datetimePol_mo1: read_data(dir, "datetimePol_ntp_sync_issue.json")},
            "6.1(4.10)",
            "6.1(4.15)",
            script.PASS,
        ),
        # single pod scenario
        # Version not affected
        ( { fabricRsTimePol_api: read_data(dir, "fabricRsTimePol_ntp_sync_1pod.json"),
            datetimePol_mo1: read_data(dir, "datetimePol_ntp_sync_issue.json")},
            "6.1(4.28)",
            "6.1(4.30)",
            script.NA,
        ),
        # Affected version, no NTP sync issue
        ( { fabricRsTimePol_api: read_data(dir, "fabricRsTimePol_ntp_sync_1pod.json"),
            datetimePol_mo1: read_data(dir, "datetimePol_ntp_sync_no_issue.json")},
            "6.1(4.10)",
            "6.1(4.15)",
            script.PASS,
        ),
        # Affected version, NTP sync issue
        ( { fabricRsTimePol_api: read_data(dir, "fabricRsTimePol_ntp_sync_1pod.json"),
            datetimePol_mo1: read_data(dir, "datetimePol_ntp_sync_issue.json")},
            "6.1(4.10)",
            "6.1(4.15)",
            script.FAIL_O,
        ),
        # multi pod scenario
        # Version not affected
        (
            { fabricRsTimePol_api: read_data(dir, "fabricRsTimePol_ntp_sync_2pod.json"),
            datetimePol_mo1: read_data(dir, "datetimePol_ntp_sync_issue.json"),
            datetimePol_mo2: read_data(dir, "datetimePol_ntp_sync_issue_2.json")},
            "6.1(4.28)",
            "6.1(4.30)",
            script.NA,
        ),
        # Affected version, no NTP sync issue
        (
            { fabricRsTimePol_api: read_data(dir, "fabricRsTimePol_ntp_sync_2pod.json"),
            datetimePol_mo1: read_data(dir, "datetimePol_ntp_sync_no_issue.json"),
            datetimePol_mo2: read_data(dir, "datetimePol_ntp_sync_no_issue_2.json")},
            "6.1(4.10)",
            "6.1(4.15)",
            script.PASS,
        ),
        # Affected version, one NTP sync issue
        (
            { fabricRsTimePol_api: read_data(dir, "fabricRsTimePol_ntp_sync_2pod.json"),
            datetimePol_mo1: read_data(dir, "datetimePol_ntp_sync_issue.json"),
            datetimePol_mo2: read_data(dir, "datetimePol_ntp_sync_no_issue_2.json")},
            "6.1(4.10)",
            "6.1(4.15)",
            script.FAIL_O,
        ),
        # Affected version, multiple NTP sync issues
        (
            { fabricRsTimePol_api: read_data(dir, "fabricRsTimePol_ntp_sync_2pod.json"),
            datetimePol_mo1: read_data(dir, "datetimePol_ntp_sync_issue.json"),
            datetimePol_mo2: read_data(dir, "datetimePol_ntp_sync_issue_2.json")},
            "6.1(4.10)",
            "6.1(4.15)",
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