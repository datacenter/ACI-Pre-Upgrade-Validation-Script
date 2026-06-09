import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "cimc_compatibilty_check"

# icurl queries
eqptCh_api = 'eqptCh.json?query-target-filter=wcard(eqptCh.descr,"APIC")'

compatRsSuppHwL2_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.0(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicl2].json'
compatRsSuppHwM1_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.0(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicm1].json'

compatRsSuppHwL4_605_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.0(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicl4].json'
compatRsSuppHwM4_605_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.0(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicm4].json'
compatRsSuppHwL4_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.1(6)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicl4].json'
compatRsSuppHwM4_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.1(6)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicm4].json'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, cversion, expected_result",
    [
        #m4/l4 model check and targeting affected version and cversion affected and cimc < 4.3.5
        (
            {eqptCh_api: read_data(dir, "eqptCh_m4l4_model_old_cimc.json"),
            compatRsSuppHwL4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json"),
            compatRsSuppHwM4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json")},
            "6.0(5a)",
            "5.3(1a)",
            script.FAIL_UF,
        ),
        #m4/l4 with other apic server model and check targeting affect version and cversion affected and cimc < 4.3.5
        (
            {
            eqptCh_api: read_data(dir, "eqptCh_m4l4_mixed_models.json"),
            compatRsSuppHwL4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json"),
            compatRsSuppHwM4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json"),
            compatRsSuppHwL2_api: read_data(dir, "compatRsSuppHw_605_L2.json"),
            compatRsSuppHwM1_api: read_data(dir, "compatRsSuppHw_605_M1.json")},
            "6.0(5a)",
            "5.3(1a)",
            script.FAIL_UF,
        ),
        # current cimc > 3.4.5 (known issue) but APIC current version is not affected
        (
            {eqptCh_api: read_data(dir, "eqptCh_m4l4_model_new_cimc.json"),
            compatRsSuppHwL4_api: read_data(dir, "compatRsSuppHw_616_M4L4.json"),
            compatRsSuppHwM4_api: read_data(dir, "compatRsSuppHw_616_M4L4.json")},
            "6.1(6a)",
            "6.1(5a)",
            script.PASS,
        ),
        #version affected and cimc version > 4.3.5
        (
            {eqptCh_api: read_data(dir, "eqptCh_m4l4_model_new_cimc.json"),
            compatRsSuppHwL4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json"),
            compatRsSuppHwM4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json")},
            "6.0(5a)",
            "5.3(1a)",
            script.PASS,
        ),
        (
            {eqptCh_api: read_data(dir, "eqptCh_reallyoldver.json"),
             compatRsSuppHwL2_api: read_data(dir, "compatRsSuppHw_605_L2.json"),
             compatRsSuppHwM1_api: read_data(dir, "compatRsSuppHw_605_M1.json")},
            "6.0(5a)",
            None,
            script.FAIL_UF,
        ),
        (
            {eqptCh_api: read_data(dir, "eqptCh_oldver.json"),
             compatRsSuppHwL2_api: read_data(dir, "compatRsSuppHw_605_L2.json"),
             compatRsSuppHwM1_api: read_data(dir, "compatRsSuppHw_605_M1.json")},
            "6.0(5a)",
            None,
            script.FAIL_UF,
        ),
        (
            {eqptCh_api: read_data(dir, "eqptCh_newver.json"),
             compatRsSuppHwL2_api: read_data(dir, "compatRsSuppHw_605_L2.json"),
             compatRsSuppHwM1_api: read_data(dir, "compatRsSuppHw_605_M1.json")},
            "6.0(5a)",
            None,
            script.PASS,
        ),
        # Seen in QA testing where version + model does not have catalog entry
        (
            {eqptCh_api: read_data(dir, "eqptCh_newver.json"),
             compatRsSuppHwL2_api: read_data(dir, "compatRsSuppHw_605_L2.json"),
             compatRsSuppHwM1_api: read_data(dir, "compatRsSuppHw_empty.json")},
            "6.0(5a)",
            None,
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, cversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion), cversion=script.AciVersion(cversion) if cversion is not None else None)
    assert result.result == expected_result
