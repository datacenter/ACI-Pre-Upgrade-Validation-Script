import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
commCiphers = 'commCipher.json'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {commCiphers: read_data(dir, "commCipher_neg.json")},
            script.PASS,
        ),
        (
            {commCiphers: read_data(dir, "commCipher_pos.json")},
            script.FAIL_UF,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.eecdh_cipher_check(
        1,
        1,
    )
    assert result == expected_result