import os
import pytest
import logging
import importlib
from datetime import datetime
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "aes_encryption_check"


# icurl queries
exportcryptkey = "uni/exportcryptkey.json"
export_history = (
    'configJob.json?query-target-filter=and(eq(configJob.type,"export"),eq(configJob.operSt,"success"))'
    '&order-by=configJob.lastStepTime|desc'
)


@pytest.fixture(autouse=True)
def default_export_history(icurl_outputs):
    icurl_outputs.setdefault(export_history, [])


@pytest.fixture
def fixed_time(monkeypatch):
    class FixedDatetime(datetime):
        @classmethod
        def utcnow(cls):
            return cls(2026, 10, 2, 14, 0, 0)

    monkeypatch.setattr(script, "datetime", FixedDatetime)


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # AES enabled (tversion > 6.1.2a)
        (
            {exportcryptkey: read_data(dir, "exportcryptkey.json")},
            "6.1(3b)",
            script.PASS,
        ),
        # AES enabled (tversion < 6.1.2a)
        (
            {exportcryptkey: read_data(dir, "exportcryptkey.json")},
            "5.2(8g)",
            script.PASS,
        ),
        # AES disabled (tversion > 6.1.2a)
        (
            {exportcryptkey: read_data(dir, "exportcryptkey_disabled.json")},
            "6.1(3b)",
            script.FAIL_UF,
        ),
        # Exact mandatory-encryption boundary
        (
            {exportcryptkey: read_data(dir, "exportcryptkey_disabled.json")},
            "6.1(2a)",
            script.FAIL_UF,
        ),
        (
            {exportcryptkey: read_data(dir, "exportcryptkey.json")},
            "6.1(2a)",
            script.PASS,
        ),
        # AES disabled (tversion < 6.1.2a)
        (
            {exportcryptkey: read_data(dir, "exportcryptkey_disabled.json")},
            "5.2(8g)",
            script.MANUAL,
        ),
        # AES MO not found (tversion > 6.1.2a)
        (
            {exportcryptkey: []},
            "6.1(3b)",
            script.MANUAL,
        ),
        # AES MO not found (tversion < 6.1.2a)
        (
            {exportcryptkey: []},
            "5.2(8g)",
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion))
    assert result.result == expected_result
    assert "No successful export found in retained history" in result.data[0]
    assert "It cannot be retrieved from APIC" in result.recommended_action
    assert "without the original passphrase" in result.recommended_action


@pytest.mark.parametrize("enabled, expected", [("yes", script.PASS), ("no", script.FAIL_UF), (None, script.ERROR), ("unknown", script.ERROR)])
def test_encryption_attribute(run_check, mock_icurl, icurl_outputs, enabled, expected):
    attributes = {} if enabled is None else {"strongEncryptionEnabled": enabled}
    # No keyConfigured attribute is needed to evaluate encryption status.
    icurl_outputs[exportcryptkey] = [{"pkiExportEncryptionKey": {"attributes": attributes}}]
    result = run_check(tversion=script.AciVersion("6.1(3b)"))
    assert result.result == expected


@pytest.mark.parametrize("enabled, expected", [("yes", script.PASS), ("no", script.FAIL_UF)])
def test_latest_export_details(run_check, mock_icurl, icurl_outputs, monkeypatch, fixed_time, enabled, expected):
    icurl_outputs[exportcryptkey] = [{"pkiExportEncryptionKey": {"attributes": {"strongEncryptionEnabled": enabled}}}]
    icurl_outputs[export_history] = {
        "totalCount": "20",
        "imdata": [{"configJob": {"attributes": {
            "dn": "uni/backupst/jobs-[uni/fabric/configexp-DailyAutoBackup]/run-2026-10-02T09-00-15",
            "executeTime": "2026-10-02T09:00:15.685-04:00",
            "lastStepTime": "2026-10-02T09:00:48.102-04:00",
            "type": "export",
            "operSt": "success",
        }}}],
    }
    calls = []
    original_icurl = script._icurl

    def track_query(apitype, query, page=0, page_size=100000):
        calls.append((apitype, query, page, page_size))
        return original_icurl(apitype, query, page=page, page_size=page_size)

    monkeypatch.setattr(script, "_icurl", track_query)
    result = run_check(tversion=script.AciVersion("6.1(3b)"))
    assert result.result == expected
    assert result.data[0][3:] == ["DailyAutoBackup", "2026-10-02T09:00:48.102-04:00", "0d 0h 59m"]
    assert len(result.headers) == len(result.data[0])
    assert calls == [("mo", exportcryptkey, 0, 100000), ("class", export_history, 0, 1)]

    output = []
    monkeypatch.setattr(script, "prints", output.append)
    script.print_result(1, 1, "Global AES Encryption", **result.as_dict())
    assert "DailyAutoBackup" in output[0]
    assert "0d 0h 59m" in output[0]
    assert "WARNING:" in output[0]
    payload = script.AciResult(test_function, "Global AES Encryption", result).as_dict()
    assert "DailyAutoBackup" in payload["recommended_action"]
    assert "2026-10-02T09:00:48.102-04:00" in payload["recommended_action"]
    assert "without the original passphrase" in payload["recommended_action"]


@pytest.mark.parametrize("response", [
    {"totalCount": "1", "imdata": []},
    {"totalCount": "1", "imdata": [{"configJob": {"attributes": {"lastStepTime": "invalid"}}}]},
    {"totalCount": "1", "imdata": [{"configJob": {"attributes": {}}}]},
    {"totalCount": "1", "imdata": [{"error": {"attributes": {"text": "unresolved class for configJob"}}}]},
    {"totalCount": "1", "imdata": [{"error": {"attributes": {"text": "Unable to deliver the message, Resolve timeout"}}}]},
])
def test_export_history_errors_are_informational(run_check, mock_icurl, icurl_outputs, response):
    icurl_outputs[exportcryptkey] = read_data(dir, "exportcryptkey.json")
    icurl_outputs[export_history] = response
    result = run_check(tversion=script.AciVersion("6.1(3b)"))
    assert result.result == script.PASS
    assert "Unable to determine latest successful export" in result.data[0]
    assert "Unable to determine latest successful export" in result.recommended_action
    assert "No successful export found" not in result.recommended_action


@pytest.mark.parametrize("timestamp, expected", [
    ("2026-10-01T09:00:00.000-04:00", "1d 1h 0m"),
    ("2026-10-02T18:30:00.000+05:30", "0d 1h 0m"),
    ("2026-10-02T13:00:00Z", "0d 1h 0m"),
    ("2026-10-02T15:00:00.000+00:00", "In the future (check APIC clock)"),
])
def test_export_age_handles_timezone_offsets(fixed_time, timestamp, expected):
    assert script._config_export_age(timestamp) == expected


def test_missing_target_does_not_query_apic(run_check, monkeypatch):
    def unexpected_query(*args, **kwargs):
        pytest.fail("Missing target version must skip APIC queries")

    monkeypatch.setattr(script, "_icurl", unexpected_query)
    result = run_check(tversion=None)
    assert result.result == script.MANUAL
    assert result.msg == script.TVER_MISSING
