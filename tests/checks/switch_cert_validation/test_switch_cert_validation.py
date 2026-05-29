import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "switch_cert_validation"

# icurl queries
pki_certs_api = "pkiFabricNodeSSLCertificate.json"


@pytest.mark.parametrize(
    "icurl_outputs, fabric_nodes, expected_result, expected_data",
    [
        # FAIL - Only expired certs on spine/leaf are flagged.
        # The positive fixture contains 4 certs: an expired APIC controller cert
        # (must be ignored - controllers are out of scope), a valid leaf cert
        # (not expired), an expired spine cert (must be flagged), and a cert for
        # an unknown nodeId (must be ignored).
        (
            {pki_certs_api: read_data(dir, "pkiFabricNodeSSLCertificate_positive.json")},
            read_data(dir, "fabricNode.json"),
            script.FAIL_O,
            [
                [
                    "1",
                    "102",
                    "spine102",
                    "spine",
                    "2020-01-01T00:00:00.000+00:00",
                ],
            ],
        ),
        # PASS - All certificates are valid and unexpired.
        (
            {pki_certs_api: read_data(dir, "pkiFabricNodeSSLCertificate_negative.json")},
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
        # PASS - pkiFabricNodeSSLCertificate class returns no objects.
        (
            {pki_certs_api: []},
            read_data(dir, "fabricNode.json"),
            script.PASS,
            [],
        ),
        # PASS - fabric_nodes contains controllers only; even with an expired
        # controller cert in the response, the check must return PASS because
        # it is scoped to spine/leaf nodes only.
        (
            {pki_certs_api: read_data(dir, "pkiFabricNodeSSLCertificate_positive.json")},
            [
                fn for fn in read_data(dir, "fabricNode.json")
                if fn["fabricNode"]["attributes"].get("role") == "controller"
            ],
            script.PASS,
            [],
        ),
        # PASS - fabric_nodes is empty (no APIC data at all).
        (
            {pki_certs_api: read_data(dir, "pkiFabricNodeSSLCertificate_positive.json")},
            [],
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, fabric_nodes, expected_result, expected_data):
    result = run_check(
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
