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
compatRsSuppHwL4_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.1(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicl4].json'
compatRsSuppHwM4_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.1(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicm4].json'
compatRsSuppHwL3_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.1(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicl3].json'
compatRsSuppHwM3_api = 'uni/fabric/compcat-default/ctlrfw-apic-6.1(5)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicm3].json'

release_note_supported_615_outputs = {
    eqptCh_api: read_data(dir, "eqptCh_615_supported_423e.json"),
    compatRsSuppHwL3_api: read_data(dir, "compatRsSuppHw_615_M5.json"),
    compatRsSuppHwM3_api: read_data(dir, "compatRsSuppHw_615_M5.json"),
    compatRsSuppHwL4_api: read_data(dir, "compatRsSuppHw_615_M6.json"),
    compatRsSuppHwM4_api: read_data(dir, "compatRsSuppHw_615_M6.json"),
}

release_note_model_data = {
    "apicl3": ("APIC-SERVER-L3", compatRsSuppHwL3_api, "compatRsSuppHw_615_M5.json"),
    "apicm3": ("APIC-SERVER-M3", compatRsSuppHwM3_api, "compatRsSuppHw_615_M5.json"),
    "apicl4": ("APIC-SERVER-L4", compatRsSuppHwL4_api, "compatRsSuppHw_615_M6.json"),
    "apicm4": ("APIC-SERVER-M4", compatRsSuppHwM4_api, "compatRsSuppHw_615_M6.json"),
}


def release_note_supported_outputs(model, cimc_version):
    apic_model, compat_api, compat_fixture = release_note_model_data[model]
    return {
        eqptCh_api: [
            {
                "eqptCh": {
                    "attributes": {
                        "cimcVersion": cimc_version,
                        "descr": apic_model,
                        "dn": "topology/pod-1/node-1/sys/ch",
                        "model": apic_model,
                    }
                }
            }
        ],
        compat_api: read_data(dir, compat_fixture),
    }


release_note_supported_cases = [
    release_note_supported_outputs(model, cimc_version)
    for (target, model), cimc_versions in script.CIMC_RELEASE_NOTE_SUPPORT.items()
    if target == "6.1(5)"
    for cimc_version in cimc_versions
]

@pytest.mark.parametrize(
    "icurl_outputs, tversion, cversion, expected_result",
    [
        # CIMC 4.2(3e) is explicitly supported for M5/M6 APICs by the 6.1(5) release notes.
        (
            release_note_supported_615_outputs,
            "6.1(5e)",
            "5.2(8g)",
            script.PASS,
        ),
        # The release-note exception must not bypass the CSCwo74485 upgrade ordering check.
        (
            release_note_supported_615_outputs,
            "6.1(5e)",
            "5.3(1d)",
            script.FAIL_UF,
        ),
        # Other CIMC versions below the catalog recommendation remain unsupported.
        (
            {
                eqptCh_api: read_data(dir, "eqptCh_615_unsupported_423d.json"),
                compatRsSuppHwM3_api: read_data(dir, "compatRsSuppHw_615_M5.json"),
                compatRsSuppHwM4_api: read_data(dir, "compatRsSuppHw_615_M6.json"),
            },
            "6.1(5e)",
            "5.2(8g)",
            script.FAIL_UF,
        ),
        #m4/l4 model check and targeting affected version and cversion affected and cimc < 4.3.5
        (
            {eqptCh_api: read_data(dir, "eqptCh_m4l4_model_old_cimc.json"),
            compatRsSuppHwL4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json"),
            compatRsSuppHwM4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json")},
            "6.0(5h)",
            "5.3(1d)",
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
            "6.0(5h)",
            "5.3(1d)",
            script.FAIL_UF,
        ),
        # current cimc > 3.4.5 (known issue) but APIC current version is not affected
        (
            {eqptCh_api: read_data(dir, "eqptCh_m4l4_model_new_cimc.json"),
            compatRsSuppHwL4_api: read_data(dir, "compatRsSuppHw_615_M4L4.json"),
            compatRsSuppHwM4_api: read_data(dir, "compatRsSuppHw_615_M4L4.json")},
            "6.1(5e)",
            "6.1(4h)",
            script.PASS,
        ),
        #version affected and cimc version > 4.3.5
        (
            {eqptCh_api: read_data(dir, "eqptCh_m4l4_model_new_cimc.json"),
            compatRsSuppHwL4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json"),
            compatRsSuppHwM4_605_api: read_data(dir, "compatRsSuppHw_605_M4L4.json")},
            "6.0(5h)",
            "5.3(1d)",
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


@pytest.mark.parametrize("icurl_outputs", release_note_supported_cases)
def test_release_note_supported_versions(run_check, mock_icurl):
    result = run_check(
        tversion=script.AciVersion("6.1(5e)"),
        cversion=script.AciVersion("5.2(8g)"),
    )
    assert result.result == script.PASS
