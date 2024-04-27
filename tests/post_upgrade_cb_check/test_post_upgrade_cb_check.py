import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
mo1_new = "infraAssocEncapInstDef.json?rsp-subtree-include=count"
mo1_old = "infraRsToEncapInstDef.json?rsp-subtree-include=count"
mo2_new = "infraRsConnectivityProfileOpt.json?rsp-subtree-include=count"
mo2_old = "infraRsConnectivityProfile.json?rsp-subtree-include=count"
mo3_new = "fvSlaDef.json?rsp-subtree-include=count"
mo3_old = "fvIPSLAMonitoringPol.json?rsp-subtree-include=count"
mo4_new = "infraImplicitSetPol.json?rsp-subtree-include=count"
mo5_new = "infraRsToImplicitSetPol.json?rsp-subtree-include=count"
mo5_old = "infraImplicitSetPol.json?rsp-subtree-include=count"

# icurl output sets
mo_count_same = {
    mo1_new: read_data(dir, "moCount_10.json"),
    mo1_old: read_data(dir, "moCount_10.json"),
    mo2_new: read_data(dir, "moCount_10.json"),
    mo2_old: read_data(dir, "moCount_10.json"),
    mo3_new: read_data(dir, "moCount_10.json"),
    mo3_old: read_data(dir, "moCount_10.json"),
    mo4_new: read_data(dir, "moCount_10.json"),
    mo5_new: read_data(dir, "moCount_10.json"),
    mo5_old: read_data(dir, "moCount_10.json"),
}
mo_count_diff = {
    mo1_new: read_data(dir, "moCount_8.json"),
    mo1_old: read_data(dir, "moCount_10.json"),
    mo2_new: read_data(dir, "moCount_8.json"),
    mo2_old: read_data(dir, "moCount_10.json"),
    mo3_new: read_data(dir, "moCount_8.json"),
    mo3_old: read_data(dir, "moCount_10.json"),
    mo4_new: read_data(dir, "moCount_8.json"),
    mo5_new: read_data(dir, "moCount_8.json"),
    mo5_old: read_data(dir, "moCount_10.json"),
}


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # Target Version not supplied
        (mo_count_diff, "3.2(8f)", None, script.MANUAL),
        # Target Version newer than current (i.e. APIC upgrade not done yet)
        (mo_count_diff, "4.2(7v)", "5.2(8g)", script.MANUAL),
        # No new class
        (mo_count_diff, "3.2(9h)", "3.2(9h)", script.PASS),
        # New classes
        # infraRsToImplicitSetPol, infraImplicitSetPol
        (mo_count_same, "3.2(10g)", "3.2(10g)", script.PASS),
        (mo_count_diff, "3.2(10g)", "3.2(10g)", script.FAIL_O),
        # New classes
        # infraRsToImplicitSetPol, infraImplicitSetPol, fvSlaDef
        (mo_count_same, "4.2(7v)", "4.2(7v)", script.PASS),
        (mo_count_diff, "4.2(7v)", "4.2(7v)", script.FAIL_O),
        # New classes
        # infraRsToImplicitSetPol, infraImplicitSetPol, fvSlaDef, infraRsConnectivityProfileOpt, infraAssocEncapInstDef
        (mo_count_same, "5.2(8g)", "5.2(8g)", script.PASS),
        (mo_count_diff, "5.2(8g)", "5.2(8g)", script.FAIL_O),
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
