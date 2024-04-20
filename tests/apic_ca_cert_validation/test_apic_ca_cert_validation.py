import os
import pytest
import logging
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


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
def test_logic(certreq_out_file, expected_result):
    data_path = os.path.join("tests", dir, certreq_out_file)
    with open(data_path, "r") as file:
        certreq_out = file.read()
    result = script.apic_ca_cert_validation(1, 1, certreq_out=certreq_out)
    assert result == expected_result
