import os
import pytest
import logging
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_ca_cert_validation"


@pytest.mark.parametrize(
    "certreq_out_file, expected_result",
    [
        # FAIL - certreq returns error
        (
            "POS_certreq.txt",
            script.FAIL_O,
        ),
        # PASS - certreq returns cert info
        (
            "NEG_certreq.txt",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, certreq_out_file, expected_result):
    data_path = os.path.join("tests", "checks", dir, certreq_out_file)
    with open(data_path, "r") as file:
        certreq_out = file.read()
    result = run_check(certreq_out=certreq_out)
    assert result.result == expected_result
