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
compatRsSuppHwM4_531_api = 'uni/fabric/compcat-default/ctlrfw-apic-5.3(1)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicm4].json'
compatRsSuppHwL4_531_api = 'uni/fabric/compcat-default/ctlrfw-apic-5.3(1)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicl4].json'

release_note_supported_615_outputs = {
    eqptCh_api: read_data(dir, "eqptCh_615_supported_423e.json"),
    compatRsSuppHwL3_api: read_data(dir, "compatRsSuppHw_615_M5.json"),
    compatRsSuppHwM3_api: read_data(dir, "compatRsSuppHw_615_M5.json"),
    compatRsSuppHwL4_api: read_data(dir, "compatRsSuppHw_615_M6.json"),
    compatRsSuppHwM4_api: read_data(dir, "compatRsSuppHw_615_M6.json"),
    compatRsSuppHwL4_531_api: [{"compatRsSuppHw": {"attributes": {"cimcVersion": "4.0(2g)"}}}],
    compatRsSuppHwM4_531_api: [{"compatRsSuppHw": {"attributes": {"cimcVersion": "4.0(2g)"}}}],
}

def release_note_supported_outputs(model, cimc_version):
    apic_model = "APIC-SERVER-{}".format(model[4:].upper())
    compat_api = (
        "uni/fabric/compcat-default/ctlrfw-apic-6.1(5)"
        "/rssuppHw-[uni/fabric/compcat-default/ctlrhw-{}].json".format(model)
    )
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
        compat_api: [
            {
                "compatRsSuppHw": {
                    "attributes": {
                        "cimcVersion": "9.9(9z)",
                        "dn": compat_api[:-5],
                    }
                }
            }
        ],
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
        # Issue #435: CIMC 4.1(1g) is release-note supported on APIC-L3/M3.
        (
            release_note_supported_outputs("apicl3", "4.1(1g)"),
            "6.1(5e)",
            "5.2(8g)",
            script.PASS,
        ),
        # The release-note exception avoids a required CIMC upgrade, but still warns about CSCwo74485.
        (
            release_note_supported_615_outputs,
            "6.1(5e)",
            "5.3(1d)",
            script.MANUAL,
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


def m4l4_compatibility_outputs(model="M4", cimc_version="4.3(4.241063)",
                               target_recommendation="4.0(2g)", current_recommendation="4.0(2g)"):
    model_key = "apic" + model.lower()
    target_api = ('uni/fabric/compcat-default/ctlrfw-apic-6.2(3)/rssuppHw-'
                  '[uni/fabric/compcat-default/ctlrhw-{}].json').format(model_key)
    current_api = ('uni/fabric/compcat-default/ctlrfw-apic-5.3(1)/rssuppHw-'
                   '[uni/fabric/compcat-default/ctlrhw-{}].json').format(model_key)
    return {
        eqptCh_api: [{"eqptCh": {"attributes": {
            "cimcVersion": cimc_version,
            "descr": "APIC-SERVER-" + model,
            "dn": "topology/pod-1/node-1/sys/ch",
        }}}],
        target_api: [{"compatRsSuppHw": {"attributes": {"cimcVersion": target_recommendation}}}],
        current_api: [{"compatRsSuppHw": {"attributes": {"cimcVersion": current_recommendation}}}],
    }


@pytest.mark.parametrize("icurl_outputs, model", [
    (m4l4_compatibility_outputs("M4"), "M4"),
    (m4l4_compatibility_outputs("L4"), "L4"),
])
def test_cscwo74485_supported_on_current_and_target(run_check, mock_icurl, model, icurl_outputs):
    result = run_check(tversion=script.AciVersion("6.2(3f)"), cversion=script.AciVersion("5.3(1d)"))
    assert result.result == script.MANUAL
    assert result.data == [["node-1", "APIC-SERVER-" + model, "4.3(4.241063)", "4.0(2g)",
                            "CSCwo74485 advisory"]]
    assert result.recommended_action == (
        "The current CIMC is supported; a CIMC upgrade is not required. If you choose to "
        "upgrade CIMC, upgrade APICs to a release fixed for CSCwo74485 "
        "[6.0(9e)+ or 6.1(4h)+] BEFORE upgrading CIMC."
    )


@pytest.mark.parametrize("icurl_outputs, expected_result, expected_action", [
    (m4l4_compatibility_outputs(target_recommendation="4.3(5)"), script.FAIL_UF, "BEFORE upgrading CIMC"),
    (m4l4_compatibility_outputs(current_recommendation="4.3(5)"), script.MANUAL, "Review the current APIC/CIMC"),
    (m4l4_compatibility_outputs(cimc_version="4.3(5)"), script.PASS, "Check Release note"),
])
def test_cscwo74485_compatibility_boundaries(run_check, mock_icurl, expected_result, expected_action):
    result = run_check(tversion=script.AciVersion("6.2(3f)"), cversion=script.AciVersion("5.3(1d)"))
    assert result.result == expected_result
    assert expected_action in result.recommended_action


@pytest.mark.parametrize("icurl_outputs", [m4l4_compatibility_outputs(target_recommendation="4.3(5)")])
def test_cscwo74485_required_upgrade_action(run_check, mock_icurl):
    result = run_check(tversion=script.AciVersion("6.2(3f)"), cversion=script.AciVersion("5.3(1d)"))
    assert result.result == script.FAIL_UF
    assert result.recommended_action == (
        "The current CIMC is below the target recommendation; a CIMC upgrade is required. "
        "Upgrade APICs to a release fixed for CSCwo74485 [6.0(9e)+ or 6.1(4h)+] "
        "BEFORE upgrading CIMC, then follow the target catalog recommendation."
    )


@pytest.mark.parametrize("icurl_outputs", [dict(m4l4_compatibility_outputs(), **{compatRsSuppHwM4_531_api: []})])
def test_cscwo74485_missing_current_compatibility(run_check, mock_icurl):
    result = run_check(tversion=script.AciVersion("6.2(3f)"), cversion=script.AciVersion("5.3(1d)"))
    assert result.result == script.MANUAL
    assert result.data[0][-1] == "Current APIC/CIMC compatibility information unavailable."


def mixed_m4l4_outputs():
    outputs = m4l4_compatibility_outputs()
    l4_outputs = m4l4_compatibility_outputs("L4", target_recommendation="4.3(5)")
    l4_node = l4_outputs[eqptCh_api][0]
    l4_node["eqptCh"]["attributes"]["dn"] = "topology/pod-1/node-2/sys/ch"
    outputs[eqptCh_api].append(l4_node)
    for key, value in l4_outputs.items():
        if key != eqptCh_api:
            outputs[key] = value
    return outputs


@pytest.mark.parametrize("icurl_outputs", [mixed_m4l4_outputs()])
def test_cscwo74485_required_and_optional_upgrades(run_check, mock_icurl):
    result = run_check(tversion=script.AciVersion("6.2(3f)"), cversion=script.AciVersion("5.3(1d)"))
    assert result.result == script.FAIL_UF
    assert [row[0] for row in result.data] == ["node-1", "node-2"]
    assert result.data[0][-1] == "CSCwo74485 advisory"
    assert result.data[1][-1] == ""
    assert result.recommended_action == (
        "For nodes marked CSCwo74485 advisory, the current CIMC is supported; a CIMC "
        "upgrade is not required. If you choose to upgrade CIMC on those nodes, upgrade "
        "APICs to a release fixed for CSCwo74485 [6.0(9e)+ or 6.1(4h)+] BEFORE upgrading "
        "CIMC. For affected M4/L4 nodes below the target CIMC recommendation, a CIMC "
        "upgrade is required; upgrade APICs to a CSCwo74485 fixed release first, then "
        "follow the target catalog recommendation."
    )


def mixed_non_bug_outputs():
    outputs = m4l4_compatibility_outputs()
    outputs[eqptCh_api].append({"eqptCh": {"attributes": {
        "cimcVersion": "4.0(1a)",
        "descr": "APIC-SERVER-M3",
        "dn": "topology/pod-1/node-2/sys/ch",
    }}})
    m3_api = ('uni/fabric/compcat-default/ctlrfw-apic-6.2(3)/rssuppHw-'
              '[uni/fabric/compcat-default/ctlrhw-apicm3].json')
    outputs[m3_api] = [{"compatRsSuppHw": {"attributes": {"cimcVersion": "4.3(2.250016)"}}}]
    return outputs


@pytest.mark.parametrize("icurl_outputs", [mixed_non_bug_outputs()])
def test_cscwo74485_advisory_with_unaffected_model_failure(run_check, mock_icurl):
    result = run_check(tversion=script.AciVersion("6.2(3f)"), cversion=script.AciVersion("5.3(1d)"))
    assert result.result == script.FAIL_UF
    assert [row[1] for row in result.data] == ["APIC-SERVER-M4", "APIC-SERVER-M3"]
    assert result.recommended_action == (
        "For nodes marked CSCwo74485 advisory, the current CIMC is supported; a CIMC "
        "upgrade is not required. If you choose to upgrade CIMC on those nodes, upgrade "
        "APICs to a release fixed for CSCwo74485 [6.0(9e)+ or 6.1(4h)+] BEFORE upgrading "
        "CIMC. For other nodes below the target CIMC recommendation, check the APIC model "
        "and target version release notes to plan the required CIMC upgrade."
    )


@pytest.mark.parametrize("icurl_outputs", [
    {eqptCh_api: [{"eqptCh": {"attributes": {
        "cimcVersion": "4.0(1a)",
        "descr": "APIC-SERVER-M3",
        "dn": "topology/pod-1/node-2/sys/ch",
    }}}],
     'uni/fabric/compcat-default/ctlrfw-apic-6.2(3)/rssuppHw-[uni/fabric/compcat-default/ctlrhw-apicm3].json':
         [{"compatRsSuppHw": {"attributes": {"cimcVersion": "4.3(2.250016)"}}}]}
])
def test_unaffected_model_failure_keeps_general_action(run_check, mock_icurl):
    result = run_check(tversion=script.AciVersion("6.2(3f)"), cversion=script.AciVersion("5.3(1d)"))
    assert result.result == script.FAIL_UF
    assert result.recommended_action == 'Check Release note of APIC Model/version for latest recommendations.'
