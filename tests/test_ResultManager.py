import importlib
import json

script = importlib.import_module("aci-preupgrade-validation-script")
AciResult = script.AciResult
Result = script.Result


def _test_init_result(rm, fake_checks):
    for fake_check in fake_checks:
        rm.init_result(**fake_check)

    assert len(rm.titles) == len(fake_checks)

    for check_id in rm.titles:
        expected_title = [check["check_title"] for check in fake_checks if check["check_id"] == check_id][0]
        assert rm.titles[check_id] == expected_title

        filepath = rm.get_result_filepath(check_id)
        with open(filepath, "r") as f:
            aci_result = json.load(f)
            assert aci_result["ruleId"] == check_id
            assert aci_result["name"] == rm.titles[check_id]
            assert aci_result["ruleStatus"] == AciResult.IN_PROGRESS
            assert aci_result["severity"] == "informational"
            assert aci_result["recommended_action"] == ""
            assert aci_result["docUrl"] == ""
            assert aci_result["failureDetails"]["failType"] == ""
            assert aci_result["failureDetails"]["header"] == []
            assert aci_result["failureDetails"]["data"] == []
            assert aci_result["failureDetails"]["unformatted_header"] == []
            assert aci_result["failureDetails"]["unformatted_data"] == []


def _test_update_result(rm, fake_checks):
    for fake_check in fake_checks:
        rm.update_result(**fake_check)

    inited_fake_checks = [check for check in fake_checks if check["check_id"] in rm.titles]
    assert len(rm.results) == len(inited_fake_checks)

    for check_id in rm.results:
        expected_result_obj = [check["result_obj"] for check in fake_checks if check["check_id"] == check_id][0]
        r = rm.results[check_id]
        assert r == expected_result_obj

        filepath = rm.get_result_filepath(check_id)
        with open(filepath, "r") as f:
            aci_result = json.load(f)
            assert aci_result["ruleId"] == check_id
            assert aci_result["name"] == rm.titles[check_id]
            assert aci_result["ruleStatus"] in (AciResult.PASS, AciResult.FAIL)
            if r.unformatted_data:
                assert aci_result["recommended_action"].startswith(r.recommended_action)
            else:
                assert aci_result["recommended_action"] == r.recommended_action
            assert aci_result["docUrl"] == r.doc_url
            assert aci_result["failureDetails"]["failType"] == "" if r.result == script.PASS else r.result
            assert aci_result["failureDetails"]["header"] == r.headers
            assert aci_result["failureDetails"]["data"] == AciResult.convert_data(r.headers, r.data)
            assert aci_result["failureDetails"]["unformatted_header"] == r.unformatted_headers
            assert aci_result["failureDetails"]["unformatted_data"] == AciResult.convert_data(r.unformatted_headers, r.unformatted_data)


def test_ResultManager():
    rm = script.ResultManager()
    fake_checks_for_init = [
        {"check_id": "puv_1_check", "check_title": "PUV 1"},
        {"check_id": "puv_2_check", "check_title": "PUV 2"},
    ]
    fake_checks_for_update = [
        {
            "check_id": "puv_1_check",
            "result_obj": Result(
                result=script.PASS,
                recommended_action="",
                msg="",
                doc_url="",
                headers=[],
                data=[],
                unformatted_headers=[],
                unformatted_data=[],
            ),
        },
        {
            "check_id": "puv_2_check",
            "result_obj": Result(
                result=script.FAIL_UF,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=["col1", "col2"],
                data=[["row1", "row2"], ["row3", "row4"]],
                unformatted_headers=["col1", "col2"],
                unformatted_data=[["row1", "row2"], ["row3", "row4"]],
            ),
        },
        {
            "check_id": "no_init_check",
            "result_obj": Result(
                result=script.FAIL_UF,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=["col1", "col2"],
                data=[["row1", "row2"], ["row3", "row4"]],
                unformatted_headers=["col1", "col2"],
                unformatted_data=[["row1", "row2"], ["row3", "row4"]],
            ),
        },
    ]
    _test_init_result(rm, fake_checks_for_init)
    _test_update_result(rm, fake_checks_for_update)

    summary = rm.get_summary()
    assert len(summary) == 8  # [PASS, FAIL_O, FAIL_UF, MANUAL, POST, NA, ERROR, 'TOTAL']
    for key in summary:
        if key == "TOTAL":
            expected_num = len([c for c in fake_checks_for_update if c["check_id"] != "no_init_check"])
        else:
            expected_num = len([c for c in fake_checks_for_update if c["result_obj"].result == key and c["check_id"] != "no_init_check"])

        assert summary[key] == expected_num
