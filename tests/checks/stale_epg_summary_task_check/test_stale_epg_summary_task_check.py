import os
import pytest
import importlib
from datetime import datetime
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

dir = os.path.dirname(os.path.abspath(__file__))

test_function = "stale_epg_summary_task_check"

# icurl query key
task_api = 'dbgacEpgSummaryTask.json?query-target-filter=eq(dbgacEpgSummaryTask.operSt,"processing")'

# Fixed "now" used by mock_datetime fixture: 2026-01-15 12:00:00 UTC
# Stale threshold = 2026-01-14 12:00:00 UTC (24h before fixed now)
# dbgacEpgSummaryTask_stale.json  -> startTs 2024-01-01 (way before threshold) -> FAIL_O
# dbgacEpgSummaryTask_recent.json -> startTs 2026-01-15 11:30 UTC (30 min before fixed now) -> PASS
FIXED_NOW = datetime(2026, 1, 15, 12, 0, 0)


class MockDatetime:
    """Replaces datetime class in script to return a fixed 'now' for deterministic tests."""
    @staticmethod
    def utcnow():
        return FIXED_NOW

    @staticmethod
    def strptime(date_string, format):
        return datetime.strptime(date_string, format)

    def __new__(cls, *args, **kwargs):
        return datetime(*args, **kwargs)


@pytest.fixture
def mock_datetime(monkeypatch):
    """Monkeypatches script.datetime so utcnow() returns a fixed timestamp."""
    monkeypatch.setattr(script, "datetime", MockDatetime)


@pytest.mark.parametrize(
    "tversion, icurl_outputs, expected_result, expected_data",
    [
        # Case 1: Target version 6.2(2a) is beyond both affected ranges (6.1(5e) and 6.2(1g)).
        # The target binary has the fix so version gate fails. Expected: NA without any API calls.
        (
            "6.2(2a)",
            {},
            script.NA,
            [],
        ),
        # Case 2: Target version 6.1(5e) is affected, no dbgacEpgSummaryTask objects found.
        # No stale tasks present — system is safe. Expected: PASS.
        (
            "6.1(5e)",
            {
                task_api: read_data(dir, "dbgacEpgSummaryTask_empty.json"),
            },
            script.PASS,
            [],
        ),
        # Case 3: Target version 6.1(5e) is affected, one task in processing state but startTs is
        # only 30 minutes old (within 24-hour threshold). Not considered stale.
        # Expected: PASS.
        (
            "6.1(5e)",
            {
                task_api: read_data(dir, "dbgacEpgSummaryTask_recent.json"),
            },
            script.PASS,
            [],
        ),
        # Case 4: Target version 6.1(5e) is affected, one task stuck in processing with startTs
        # from 2024 (way older than 24 hours). Stale task detected.
        # Expected: FAIL_O with the offending DN and startTs reported.
        (
            "6.1(5e)",
            {
                task_api: read_data(dir, "dbgacEpgSummaryTask_stale.json"),
            },
            script.FAIL_O,
            [
                [
                    "action/policymgrsubj-[uni/tn-TN_PROD/epgToEpg-EPG_PROD_FE_TO_EPG_PROD_BE/dstepg-[uni/tn-TN_PROD/ap-AP_PROD/epg-EPG_PROD_BE]]/dbgacEpgSummaryTask-ReportODACDef",
                    "2024-01-01T00:00:00.000+00:00",
                ]
            ],
        ),
        # Case 5: Target version 6.2(1g) is affected, two tasks — one stale (2024), one recent.
        # Only the stale task should be reported. Expected: FAIL_O with one row.
        (
            "6.2(1g)",
            {
                task_api: read_data(dir, "dbgacEpgSummaryTask_mixed.json"),
            },
            script.FAIL_O,
            [
                [
                    "action/policymgrsubj-[uni/tn-TN_PROD/epgToEpg-EPG_PROD_FE_TO_EPG_PROD_BE/dstepg-[uni/tn-TN_PROD/ap-AP_PROD/epg-EPG_PROD_BE]]/dbgacEpgSummaryTask-ReportODACDef",
                    "2024-01-01T00:00:00.000+00:00",
                ]
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, mock_datetime, tversion, icurl_outputs, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion),
    )
    assert result.result == expected_result
    assert result.data == expected_data
