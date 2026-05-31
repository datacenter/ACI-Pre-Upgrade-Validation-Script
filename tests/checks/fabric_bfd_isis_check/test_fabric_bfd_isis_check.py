import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "fabric_bfd_isis_check"

# icurl queries
api = 'l3IfPol.json'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # No l3IfPol MOs returned
        ({api: read_data(dir, "no_l3IfPol.json")}, script.PASS),
        # bfdIsis disabled on the default policy
        ({api: read_data(dir, "bfd_isis_disabled.json")}, script.PASS),
        # bfdIsis enabled on the default policy
        ({api: read_data(dir, "bfd_isis_enabled.json")}, script.FAIL_O),
        # Multiple l3IfPol MOs - some enabled, some disabled
        ({api: read_data(dir, "bfd_isis_mixed.json")}, script.FAIL_O),
    ],
)
def test_logic(run_check, mock_icurl, expected_result):
    result = run_check()
    assert result.result == expected_result
