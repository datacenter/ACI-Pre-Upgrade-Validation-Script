import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
mo1_new = "infraRsToImplicitSetPol.json?rsp-subtree-include=count"
mo1_old = "infraImplicitSetPol.json?rsp-subtree-include=count"

mo2_new = "fvSlaDef.json?rsp-subtree-include=count"
mo2_old = "fvIPSLAMonitoringPol.json?rsp-subtree-include=count"

mo3_new = "infraRsConnectivityProfileOpt.json?rsp-subtree-include=count"
mo3_old = "infraRsConnectivityProfile.json?rsp-subtree-include=count"

mo4_new = "infraAssocEncapInstDef.json?rsp-subtree-include=count"
mo4_old = "infraRsToEncapInstDef.json?rsp-subtree-include=count"

mo5_new = "infraRsToInterfacePolProfileOpt.json?rsp-subtree-include=count"
mo5_old = "infraRsToInterfacePolProfile.json?rsp-subtree-include=count"

mo6_new = 'compatSwitchHw.json?rsp-subtree-include=count&query-target-filter=eq(compatSwitchHw.suppBit,"32")'



# icurl output sets
mo_count_pass = {
    mo1_new: read_data(dir, "moCount_10.json"),
    mo1_old: read_data(dir, "moCount_10.json"),
    mo2_new: read_data(dir, "moCount_10.json"),
    mo2_old: read_data(dir, "moCount_10.json"),
    mo3_new: read_data(dir, "moCount_10.json"),
    mo3_old: read_data(dir, "moCount_10.json"),
    mo4_new: read_data(dir, "moCount_10.json"),
    mo4_old: read_data(dir, "moCount_10.json"),
    mo5_new: read_data(dir, "moCount_10.json"),
    mo5_old: read_data(dir, "moCount_10.json"),
    mo6_new: read_data(dir, "moCount_10.json"),
}
mo_count_fail = {
    # Both infraImplicitSetPol and infraRsToImplicitSetPol are brand new classes.
    # When postUpgradeCb failed, MO counts are zero as those are newly created
    # instead of converted from the old class.
    mo1_new: read_data(dir, "moCount_0.json"),
    mo1_old: read_data(dir, "moCount_0.json"),
    # Others are number mismatch
    mo2_new: read_data(dir, "moCount_8.json"),
    mo2_old: read_data(dir, "moCount_10.json"),
    mo3_new: read_data(dir, "moCount_8.json"),
    mo3_old: read_data(dir, "moCount_10.json"),
    mo4_new: read_data(dir, "moCount_8.json"),
    mo4_old: read_data(dir, "moCount_10.json"),
    mo5_new: read_data(dir, "moCount_8.json"),
    mo5_old: read_data(dir, "moCount_10.json"),
    # suppBit is a new attribute in 6.0.2 that can be either 32 or 64.
    # When postUpgradeCb failed, there may be no compatSwitch with suppBit being 32.
    mo6_new: read_data(dir, "moCount_0.json"),
}


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # Target Version not supplied
        (mo_count_fail, "3.2(8f)", None, script.POST),
        # Target Version newer than current (i.e. APIC upgrade not done yet)
        (mo_count_fail, "4.2(7v)", "5.2(8g)", script.POST),
        # No new class
        (mo_count_fail, "3.2(9h)", "3.2(9h)", script.PASS),

        # New classes
        # infraRsToImplicitSetPol, infraImplicitSetPol
        (mo_count_pass, "3.2(10g)", "3.2(10g)", script.PASS),
        (mo_count_fail, "3.2(10g)", "3.2(10g)", script.FAIL_O),

        # New classes
        # infraRsToImplicitSetPol, infraImplicitSetPol, fvSlaDef
        (mo_count_pass, "4.2(7v)", "4.2(7v)", script.PASS),
        (mo_count_fail, "4.2(7v)", "4.2(7v)", script.FAIL_O),

        # New classes
        # infraRsToImplicitSetPol, infraImplicitSetPol, fvSlaDef, infraRsConnectivityProfileOpt, infraAssocEncapInstDef
        (mo_count_pass, "5.2(8g)", "5.2(8g)", script.PASS),
        (mo_count_fail, "5.2(8g)", "5.2(8g)", script.FAIL_O),

        # New classes
        # infraRsToImplicitSetPol, infraImplicitSetPol, fvSlaDef, infraRsConnectivityProfileOpt, infraAssocEncapInstDef, compatSwitchHw.suppBit
        (mo_count_pass, "6.0(3e)", "6.0(3e)", script.PASS),
        (mo_count_fail, "6.0(3e)", "6.0(3e)", script.FAIL_O),
    ]
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.post_upgrade_cb_check(
        1,
        1,
        script.AciVersion(cversion),
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result
