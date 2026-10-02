import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "post_upgrade_cb_check"


# icurl queries
mo1_new = "infraRsToImplicitSetPol.json?rsp-subtree-include=count"
mo1_old = "infraImplicitSetPol.json?rsp-subtree-include=count"

mo2_new = "fvSlaDef.json"
mo2_old = "fvIPSLAMonitoringPol.json"

mo3_new = "infraRsConnectivityProfileOpt.json?rsp-subtree-include=count"
mo3_old = "infraRsConnectivityProfile.json?rsp-subtree-include=count"

mo4_new = "infraAssocEncapInstDef.json?rsp-subtree-include=count"
mo4_old = "infraRsToEncapInstDef.json?rsp-subtree-include=count"

mo5_new = "infraRsToInterfacePolProfileOpt.json?rsp-subtree-include=count"
mo5_old = "infraRsToInterfacePolProfile.json?rsp-subtree-include=count"

mo6_new = 'compatSwitchHw.json?rsp-subtree-include=count&query-target-filter=eq(compatSwitchHw.suppBit,"32")'


# icurl output sets
ipsla_new = read_data(dir, "fvSlaDef.json")
ipsla_old = read_data(dir, "fvIPSLAMonitoringPol.json")

mo_count_pass = {
    mo1_new: read_data(dir, "moCount_10.json"),
    mo1_old: read_data(dir, "moCount_10.json"),
    mo2_new: ipsla_new,
    mo2_old: ipsla_old,
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
    mo2_new: ipsla_new[:-1],
    mo2_old: ipsla_old,
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
        # Current Version not affected
        (mo_count_fail, "6.0(6b)", None, script.NA),
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
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result


def assert_ipsla_result(run_check, expected_result):
    result = run_check(
        cversion=script.AciVersion("4.2(7v)"),
        tversion=script.AciVersion("4.2(7v)"),
    )
    assert result.result == expected_result
    expected_headers = [] if expected_result == script.ERROR else ["Missed Objects", "Impact"]
    assert result.headers == expected_headers
    expected_data = []
    if expected_result == script.FAIL_O:
        expected_data = [["fvSlaDef", "IPSLA monitor policy will not be deployed"]]
    assert result.data == expected_data
    return result


@pytest.mark.parametrize(
    "new_objects, old_objects, expected_result",
    [
        pytest.param(ipsla_new[:1] * 2, ipsla_old[:1], script.PASS,
                     id="issue-344-duplicate-default"),
        pytest.param(ipsla_new + [ipsla_new[1]], ipsla_old, script.PASS,
                     id="duplicate-non-default"),
        pytest.param(ipsla_new + [ipsla_new[0]], ipsla_old + [ipsla_old[2]], script.PASS,
                     id="duplicates-in-both-classes"),
        pytest.param([ipsla_new[0], ipsla_new[0], ipsla_new[1]], ipsla_old, script.FAIL_O,
                     id="duplicate-masks-missing-object"),
        pytest.param(ipsla_new[:-1], ipsla_old, script.FAIL_O, id="missing-new-object"),
        pytest.param(ipsla_new, ipsla_old[:-1], script.FAIL_O, id="extra-new-object"),
        pytest.param([], [], script.PASS, id="both-classes-empty"),
        pytest.param([], ipsla_old[:1], script.FAIL_O, id="new-class-empty"),
        pytest.param(ipsla_new[:1], [], script.FAIL_O, id="old-class-empty"),
        pytest.param(ipsla_new[1:], ipsla_old[1:2], script.FAIL_O,
                     id="same-name-in-distinct-tenants"),
    ],
)
def test_ipsla_unique_counts(run_check, mock_icurl, icurl_outputs,
                            new_objects, old_objects, expected_result):
    icurl_outputs.update(mo_count_pass)
    icurl_outputs.update({mo2_new: new_objects, mo2_old: old_objects})
    assert_ipsla_result(run_check, expected_result)


@pytest.mark.parametrize("missing_object", [False, True])
def test_ipsla_pagination(run_check, mock_icurl, icurl_outputs, monkeypatch, missing_object):
    # The default DN is repeated across pages. Raw lengths must drive pagination.
    first_new_page = ipsla_new[:2]
    second_new_page = [ipsla_new[0]] + ([] if missing_object else ipsla_new[2:])
    new_total = str(len(first_new_page) + len(second_new_page))
    icurl_outputs.update(mo_count_pass)
    icurl_outputs.update({
        mo2_new: [
            {"totalCount": new_total, "imdata": first_new_page},
            {"totalCount": new_total, "imdata": second_new_page},
        ],
        mo2_old: [
            {"totalCount": "3", "imdata": ipsla_old[:1]},
            {"totalCount": "3", "imdata": ipsla_old[1:]},
        ],
    })
    mocked_query = script._icurl
    queried_pages = []

    def track_pages(apitype, query, page=0, page_size=100000):
        queried_pages.append((query, page))
        return mocked_query(apitype, query, page, page_size)

    monkeypatch.setattr(script, "_icurl", track_pages)
    expected_result = script.FAIL_O if missing_object else script.PASS
    assert_ipsla_result(run_check, expected_result)
    for query in (mo2_new, mo2_old):
        assert (query, 0) in queried_pages
        assert (query, 1) in queried_pages


@pytest.mark.parametrize("query, classname", [(mo2_new, "fvSlaDef"), (mo2_old, "fvIPSLAMonitoringPol")])
@pytest.mark.parametrize("failure", ["missing-dn", "api-error", "incomplete-response"])
def test_ipsla_query_errors(run_check, mock_icurl, icurl_outputs, query, classname, failure):
    icurl_outputs.update(mo_count_pass)
    if failure == "missing-dn":
        icurl_outputs[query] = [{classname: {"attributes": {"name": "default"}}}]
    elif failure == "api-error":
        icurl_outputs[query] = [{"error": {"attributes": {
            "code": "503", "text": "Unable to deliver the message, Resolve timeout",
        }}}]
    else:
        icurl_outputs[query] = [
            {"totalCount": "2", "imdata": icurl_outputs[query][:1]},
            {"totalCount": "2", "imdata": []},
        ]
    result = assert_ipsla_result(run_check, script.ERROR)
    assert result.msg.startswith("Unexpected Error:")
    if failure == "missing-dn":
        assert "dn" in result.msg
    elif failure == "api-error":
        assert "API Timeout" in result.msg
    else:
        assert "API response empty with totalCount:2" in result.msg
