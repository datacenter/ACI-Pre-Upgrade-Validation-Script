import importlib
import logging
import json
import os

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion
JSON_DIR = script.JSON_DIR
ApicResult = script.syntheticMaintPValidate
Result = script.Result
check_wrapper = script.check_wrapper


ERROR_REASON = "This is a test exception to result in `script.ERROR`."


def check_builder(func_name, title, result, others):
    @check_wrapper(check_title=title)
    def _check(**kwargs):
        _check.__name__ = func_name  # Set the function name for the check
        if result == script.ERROR:
            raise Exception(ERROR_REASON)
        else:
            return Result(result=result, **others)
    return _check


fake_data_full = {
    "msg": "test msg",
    "headers": ["H1", "H2", "H3"],
    "data": [["Data1", "Data2", "Data3"], ["Data4", "Data5", "Data6"], ["Loooooong Data7", "Data8", "Data9"]],
    "unformatted_headers": ["Unformatted_H1"],
    "unformatted_data": [["Data1"], ["Data2"]],
    "recommended_action": "This is your recommendation to remediate the issue",
    "doc_url": "https://fake_doc_url.local/path1/#section1",
}

fake_data_no_msg_no_unform = {
    "headers": ["H1", "H2", "H3"],
    "data": [["Data1", "Data2", "Data3"], ["Data4", "Data5", "Data6"], ["Loooooong Data7", "Data8", "Data9"]],
    "recommended_action": "This is your recommendation to remediate the issue",
    "doc_url": "https://fake_doc_url.local/path1/#section1",
}

fake_data_error = {
    "msg": "Error msg. This should not be printed",
}

fake_data_only_msg = {
    "msg": "test msg",
}

fake_checks_meta = [
    ("fake_check1", "Test Check 1", script.PASS, {}),
    ("fake_check2", "Test Check 2", script.FAIL_O, fake_data_full),
    ("fake_check3", "Test Check 3", script.FAIL_UF, fake_data_no_msg_no_unform),
    ("fake_check4", "Test Check 4", script.MANUAL, fake_data_only_msg),
    ("fake_check5", "Test Check 5", script.POST, fake_data_only_msg),
    ("fake_check6", "Test Check 6", script.NA, fake_data_only_msg),
    ("fake_check7", "Test Check 7", script.ERROR, fake_data_error),
    ("fake_check8", "Test Check 8", script.PASS, fake_data_only_msg),
]

fake_checks = [
    check_builder(func_name, title, result, others)
    for func_name, title, result, others in fake_checks_meta
]

fake_result_filenames = [
    "{}.json".format(func_name) for func_name, _, _, _ in fake_checks_meta
]

fake_inputs = {
    "username": "admin",
    "password": "mypassword",
    "cversion": AciVersion("6.1(1a)"),
    "tversion": AciVersion("6.2(1a)"),
    "sw_cversion": AciVersion("6.1(1a)"),
    "vpc_node_ids": ["101", "102"],
}


def test_run_checks(capsys, caplog):
    caplog.set_level(logging.CRITICAL)  # Skip logging.exceptions in pytest output as it is expected.
    script.run_checks(fake_checks, fake_inputs)
    captured = capsys.readouterr()
    print(captured.out)
    assert (
        captured.out
        == """\
[Check  1/8] Test Check 1...                                                                                                         PASS
[Check  2/8] Test Check 2... test msg                                                                             FAIL - OUTAGE WARNING!!
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


[Check  3/8] Test Check 3...                                                                                     FAIL - UPGRADE FAILURE!!
  H1               H2     H3
  --               --     --
  Data1            Data2  Data3
  Data4            Data5  Data6
  Loooooong Data7  Data8  Data9

  Recommended Action: This is your recommendation to remediate the issue
  Reference Document: https://fake_doc_url.local/path1/#section1


[Check  4/8] Test Check 4... test msg                                                                               MANUAL CHECK REQUIRED
[Check  5/8] Test Check 5... test msg                                                                         POST UPGRADE CHECK REQUIRED
[Check  6/8] Test Check 6... test msg                                                                                                 N/A
[Check  7/8] Test Check 7... Unexpected Error: This is a test exception to result in `script.ERROR`.                             ERROR !!
[Check  8/8] Test Check 8... test msg                                                                                                PASS

=== Summary Result ===

PASS                        :  2
FAIL - OUTAGE WARNING!!     :  1
FAIL - UPGRADE FAILURE!!    :  1
MANUAL CHECK REQUIRED       :  1
POST UPGRADE CHECK REQUIRED :  1
N/A                         :  1
ERROR !!                    :  1
TOTAL                       :  8
"""  # noqa: W291
    )

    json_files = [f for f in os.listdir(JSON_DIR) if f in fake_result_filenames]
    assert json_files, "Result JSON file not created"

    for json_file in json_files:
        with open(os.path.join(JSON_DIR, json_file)) as f:
            data = json.load(f)

        for func_name, title, result, others, in fake_checks_meta:
            if data["ruleId"] == func_name:
                assert data["name"] == title
                # reason
                if result == script.ERROR:
                    assert data["reason"].endswith(ERROR_REASON)
                elif others.get("unformatted_data"):
                    assert data["reason"] == others.get("msg", "") + (
                        "\n"
                        "Parse failure occurred, the provided data may not be complete. "
                        "Please contact Cisco TAC to identify the missing data."
                    )
                else:
                    assert data["reason"] == others.get("msg", "")
                # failureDetails.failType
                if result not in [script.PASS, script.NA]:
                    assert data["failureDetails"]["failType"] == result
                else:
                    assert data["failureDetails"]["failType"] == ""
                # failureDetails.data
                assert data["failureDetails"]["data"] == ApicResult.craftData(
                    others.get("headers", []), others.get("data", [])
                )
                assert data["failureDetails"]["unformatted_data"] == ApicResult.craftData(
                    others.get("unformatted_headers", []), others.get("unformatted_data", [])
                )
                # other fields
                assert data["recommended_action"] == others.get("recommended_action", "")
                assert data["docUrl"] == others.get("doc_url", "")
                assert data["description"] == ""
                assert data["sub_reason"] == ""
