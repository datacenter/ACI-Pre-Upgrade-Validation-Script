import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "eecdh_cipher_check"

# icurl queries
commCiphers = 'commCipher.json'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, expected_result",
    [
        (
            {commCiphers: read_data(dir, "commCipher_neg.json")},
            "5.2(6d)",
            script.PASS,
        ),
        (
            {commCiphers: read_data(dir, "commCipher_neg2.json")},
            "5.2(6d)",
            script.PASS,
        ),
        (
            {commCiphers: read_data(dir, "commCipher_pos.json")},
            "5.2(6d)",
            script.FAIL_UF,
        ),
        (
            {commCiphers: ""},
            "3.2(7f)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
    )
    assert result.result == expected_result
