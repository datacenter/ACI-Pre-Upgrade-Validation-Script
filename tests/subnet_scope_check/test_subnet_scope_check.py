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

bd_api =  'fvBD.json'
bd_api += '?rsp-subtree=children&rsp-subtree-class=fvSubnet&rsp-subtree-include=required'

epg_api =  'fvAEPg.json?' 
epg_api += 'rsp-subtree=children&rsp-subtree-class=fvSubnet&rsp-subtree-include=required'

@pytest.mark.parametrize(
    "icurl_outputs, cversion, expected_result",
    [
        (
            {bd_api: read_data(dir, "fvBD.json"), 
            epg_api: read_data(dir, "fvAEPg_empty.json"),
            "fvRsBd.json": read_data(dir, "fvRsBd.json")},
            "4.2(6a)",
            script.NA,
        ),
        (
            {bd_api: read_data(dir, "fvBD.json"), 
            epg_api: read_data(dir, "fvAEPg_pos.json"),
            "fvRsBd.json": read_data(dir, "fvRsBd.json")},
            "4.2(6a)",
            script.FAIL_O,
        ),
        (
            {bd_api: read_data(dir, "fvBD.json"), 
            epg_api: read_data(dir, "fvAEPg_pos.json"),
            "fvRsBd.json": read_data(dir, "fvRsBd.json")},
            "5.1(1a)",
            script.FAIL_O,
        ),
        (
            {bd_api: read_data(dir, "fvBD.json"), 
            epg_api: read_data(dir, "fvAEPg_neg.json"),
            "fvRsBd.json": read_data(dir, "fvRsBd.json")},
            "5.2(8h)",
            script.PASS,
        ),

    ],
)
def test_logic(mock_icurl, cversion, expected_result):
    result = script.subnet_scope_check(1, 1, script.AciVersion(cversion))
    assert result == expected_result
