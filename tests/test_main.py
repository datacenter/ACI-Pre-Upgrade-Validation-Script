import pytest
import importlib
import os
import json

script = importlib.import_module("aci-preupgrade-validation-script")
AciResult = script.AciResult
CheckManager = script.CheckManager


# ----------------------------
# Fixtures
# ----------------------------
@pytest.fixture
def mock_query_common_data(monkeypatch, expected_common_data):
    def _mock_query_common_data(api_only, args_cversion, args_tversion):
        return expected_common_data

    monkeypatch.setattr(script, "query_common_data", _mock_query_common_data)


@pytest.fixture
def expected_result_objects(result_objects_factory):
    return (
        result_objects_factory("pass")
        + result_objects_factory("fail_full", script.FAIL_O)
        + result_objects_factory("fail_simple", script.FAIL_UF)
        + result_objects_factory("only_msg")
        + result_objects_factory("pass")
        + result_objects_factory("only_long_msg")
    )


@pytest.fixture
def mock_CheckManager_get_check_funcs(monkeypatch, check_funcs_factory, expected_result_objects):
    check_funcs = check_funcs_factory(expected_result_objects)

    def _mock_CheckManager_get_check_funcs(self):
        return check_funcs

    monkeypatch.setattr(script.CheckManager, "get_check_funcs", _mock_CheckManager_get_check_funcs)


# ----------------------------
# Tests
# ----------------------------
def test_args_version(capsys):
    script.main(["--version"])
    captured = capsys.readouterr()
    assert "{}\n".format(script.SCRIPT_VERSION) == captured.out, "captured.out is =\n{}".format(captured.out)


@pytest.mark.parametrize("api_only", [False, True])
def test_args_total_checks(capsys, api_only):
    args = ["--total-checks", "--api-only"] if api_only else ["--total-checks"]

    cm = CheckManager(api_only)
    expected_output = "Total Number of Checks: {}\n".format(cm.total_checks)

    script.main(args)
    captured = capsys.readouterr()
    assert captured.out == expected_output, "captured.out is =\n{}".format(captured.out)


def test_main(capsys, mock_query_common_data, mock_CheckManager_get_check_funcs, expected_result_objects):
    script.main(["--no-cleanup"])

    for idx, result_obj in enumerate(expected_result_objects):
        check_id = "fake_{}_check".format(idx)
        check_title = "Fake Check {}".format(idx)
        expected_aci_result_obj = AciResult(check_id, check_title, result_obj)
        expected_aci_result = expected_aci_result_obj.as_dict()
        # Err msg from try/except in `check_wrapper()`
        if result_obj.result == script.ERROR:
            expected_aci_result["reason"] = "Unexpected Error: {}".format(expected_aci_result["reason"])

        with open(os.path.join(script.JSON_DIR, check_id + ".json")) as f:
            aci_result = json.load(f)
        assert aci_result == expected_aci_result

    captured = capsys.readouterr()
    assert captured.out.startswith(
        """\
    ==== {ts}{tz}, Script Version {version}  ====

!!!! Check https://github.com/datacenter/ACI-Pre-Upgrade-Validation-Script for Latest Release !!!!

Progress:""".format(
            ts=script.ts,
            tz=script.tz,
            version=script.SCRIPT_VERSION,
        )
    ), "captured.out is =\n{}".format(captured.out)

    assert captured.out.endswith(
        """\
11/11 checks completed\r


=== Check Result (failed only) ===

[Check  2/11] Fake Check 1... test msg                                                                             FAIL - OUTAGE WARNING!!
  H1               H2     H3
  --               --     --
  Data1            Data2  Data3
  Data4            Data5  Data6
  Loooooong Data7  Data8  Data9

  Unformatted_H1
  --------------
  Data1
  Data2

  Recommended Action: This is your recommendation to remediate the issue
  Reference Document: https://fake_doc_url.local/path1/#section1


[Check  3/11] Fake Check 2...                                                                                     FAIL - UPGRADE FAILURE!!
  H1               H2     H3
  --               --     --
  Data1            Data2  Data3
  Data4            Data5  Data6
  Loooooong Data7  Data8  Data9

  Recommended Action: This is your recommendation to remediate the issue
  Reference Document: https://fake_doc_url.local/path1/#section1


[Check  6/11] Fake Check 5... test msg                                                                               MANUAL CHECK REQUIRED
[Check  7/11] Fake Check 6... test msg                                                                         POST UPGRADE CHECK REQUIRED
[Check  8/11] Fake Check 7... Unexpected Error: test msg                                                                          ERROR !!
[Check 11/11] Fake Check 10... Unexpected Error: long test msg xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx ERROR !!

=== Summary Result ===

PASS                        :  3
FAIL - OUTAGE WARNING!!     :  1
FAIL - UPGRADE FAILURE!!    :  1
MANUAL CHECK REQUIRED       :  1
POST UPGRADE CHECK REQUIRED :  1
N/A                         :  2
ERROR !!                    :  2
TOTAL                       : 11

    Pre-Upgrade Check Complete.
    Next Steps: Address all checks flagged as FAIL, ERROR or MANUAL CHECK REQUIRED

    Result output and debug info saved to below bundle for later reference.
    Attach this bundle to Cisco TAC SRs opened to address the flagged checks.

      Result Bundle: {bundle_loc}

==== Script Version {version} FIN ====
""".format(
            version=script.SCRIPT_VERSION,
            bundle_loc="/".join([os.getcwd(), script.BUNDLE_NAME]),
        )
    ), "captured.out is =\n{}".format(captured.out)
