import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "ntp_server_bd_svi_check"

# icurl queries
fabric_time_pol = "fabricRsTimePol.json"
datetime_pol = "datetimePol.json"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # MANUAL - Tversion not found.
        (
            {
                fabric_time_pol: read_data(dir, "fabricRsTimePol.json"),
                datetime_pol: read_data(dir, "datetimePol-pos.json"),
            },
            "6.1(1f)",
            None,
            script.MANUAL,
        ),
        # NA Versions not affected
        # NA Cversion not affected OLD.
        (
            {

                fabric_time_pol: read_data(dir, "fabricRsTimePol.json"),
                datetime_pol: read_data(dir, "datetimePol-pos.json"),
            },
            "6.0(1g)",
            "6.0(9f)",
            script.NA,
        ),
        # NA Cversion not affected. NEW
        (
            {

                fabric_time_pol: read_data(dir, "fabricRsTimePol.json"),
                datetime_pol: read_data(dir, "datetimePol-pos.json"),
            },
            "6.1(5g)",
            "6.0(9f)",
            script.NA,
        ),
        # NA Tversion not affected OLD.
        (
            {

                fabric_time_pol: read_data(dir, "fabricRsTimePol.json"),
                datetime_pol: read_data(dir, "datetimePol-pos.json"),
            },
            "6.1(4g)",
            "6.0(9f)",
            script.NA,
        ),
        # NA Tversion not affected. NEW. 
        (
            {

                fabric_time_pol: read_data(dir, "fabricRsTimePol.json"),
                datetime_pol: read_data(dir, "datetimePol-pos.json"),
            },
            "6.1(3g)",
            "6.1(9f)",
            script.NA,
        ),
        # PASS - Versions affected, negative datetimePol MO.
        (
            {

                fabric_time_pol: read_data(dir, "fabricRsTimePol.json"),
                datetime_pol: read_data(dir, "datetimePol-neg.json"),
            },
            "6.1(2g)",
            "6.1(5d)",
            script.PASS,
        ), 
        # FAIL_UF - Versions affected, positive datetimePol MO.
        (
            {

                fabric_time_pol: read_data(dir, "fabricRsTimePol.json"),
                datetime_pol: read_data(dir, "datetimePol-pos.json"),
            },
            "6.1(2g)",
            "6.1(5d)",
            script.FAIL_UF,
        ),        
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
