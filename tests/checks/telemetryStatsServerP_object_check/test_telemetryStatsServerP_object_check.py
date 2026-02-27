import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "telemetryStatsServerP_object_check"

# icurl queries
telemetryStatsServerPs = "telemetryStatsServerP.json"


@pytest.mark.parametrize(
    "icurl_outputs, sw_cversion, tversion, expected_result",
    [
        (
            {telemetryStatsServerPs: []},
            "4.2(1b)",
            "5.2(2a)",
            script.PASS,
        ),
        (
            {telemetryStatsServerPs: []},
            "3.2(1a)",
            "4.2(4d)",
            script.PASS,
        ),
        (
            {telemetryStatsServerPs: read_data(dir, "telemetryStatsServerP_neg.json")},
            "3.2(1a)",
            "5.2(6a)",
            script.PASS,
        ),
        (
            {telemetryStatsServerPs: read_data(dir, "telemetryStatsServerP_neg.json")},
            "4.2(3a)",
            "4.2(7d)",
            script.PASS,
        ),
        (
            {telemetryStatsServerPs: read_data(dir, "telemetryStatsServerP_neg.json")},
            "2.2(3a)",
            "2.2(4r)",
            script.PASS,
        ),
        (
            {telemetryStatsServerPs: read_data(dir, "telemetryStatsServerP_neg.json")},
            "5.2(1a)",
            None,
            script.MANUAL,
        ),
        (
            {telemetryStatsServerPs: read_data(dir, "telemetryStatsServerP_pos.json")},
            "4.2(1b)",
            "5.2(2a)",
            script.PASS,
        ),
        (
            {telemetryStatsServerPs: read_data(dir, "telemetryStatsServerP_pos.json")},
            "3.2(1a)",
            "4.2(4d)",
            script.PASS,
        ),
        (
            {telemetryStatsServerPs: read_data(dir, "telemetryStatsServerP_pos.json")},
            "3.2(1a)",
            "5.2(6a)",
            script.FAIL_O,
        ),
        (
            {telemetryStatsServerPs: read_data(dir, "telemetryStatsServerP_pos.json")},
            "4.2(3a)",
            "4.2(7d)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, sw_cversion, tversion, expected_result):
    result = run_check(
        sw_cversion=script.AciVersion(sw_cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
