import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
telemetryStatsServerPs = "telemetryStatsServerP.json"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
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
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.telemetryStatsServerP_object_check(
        1,
        1,
        script.AciVersion(cversion),
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result
