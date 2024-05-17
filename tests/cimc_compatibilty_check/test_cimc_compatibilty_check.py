import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
eqptCh_api =  'eqptCh.json?query-target-filter=wcard(eqptCh.descr,"APIC")'

compatRsSuppHwL2_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.0(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicl2].json'
compatRsSuppHwM1_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.0(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicm1].json'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            {eqptCh_api: read_data(dir, "eqptCh_reallyoldver.json"),
            compatRsSuppHwL2_api: read_data(dir, "compatRsSuppHw_605_L2.json"),
            compatRsSuppHwM1_api: read_data(dir, "compatRsSuppHw_605_M1.json")},
            "6.0(5a)",
            script.FAIL_UF,
        ),
        (
            {eqptCh_api: read_data(dir, "eqptCh_oldver.json"),
            compatRsSuppHwL2_api: read_data(dir, "compatRsSuppHw_605_L2.json"),
            compatRsSuppHwM1_api: read_data(dir, "compatRsSuppHw_605_M1.json")},
            "6.0(5a)",
            script.FAIL_UF,
        ),
        (
            {eqptCh_api: read_data(dir, "eqptCh_newver.json"),
            compatRsSuppHwL2_api: read_data(dir, "compatRsSuppHw_605_L2.json"),
            compatRsSuppHwM1_api: read_data(dir, "compatRsSuppHw_605_M1.json")},
            "6.0(5a)",
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.cimc_compatibilty_check(1, 1, script.AciVersion(tversion))
    assert result == expected_result
