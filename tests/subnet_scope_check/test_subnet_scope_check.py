import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
subnets =  'fvSubnet.json' 
ip_scopes = 'fvSubnet.json?query-target-filter=and(eq(fvSubnet.ip,"10.66.178.1/26"))'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {subnets: read_data(dir, "fvSubnet-incorrect.json"), ip_scopes: read_data(dir, "fvSubnet-incorrect.json")},
            script.FAIL_O,
        ),
        (
            {subnets: read_data(dir, "fvSubnet-correct.json"), ip_scopes: read_data(dir, "fvSubnet-correct.json")},
            script.PASS,
        ),

    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.subnet_scope_check(1, 1)
    assert result == expected_result
