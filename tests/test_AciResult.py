import pytest
import importlib
from six import string_types

script = importlib.import_module("aci-preupgrade-validation-script")
AciResult = script.AciResult
Result = script.Result


@pytest.mark.parametrize(
    "func_name, name, result_obj, expected_show, expected_criticality, expected_passed",
    [
        # Check 1: NA
        (
            "fake_func_name_NA_test",
            "NA",
            Result(
                result=script.NA,
                recommended_action="",
                msg="",
                doc_url="",
                headers=["col1", "col2"],
                data=[["row1", "row2"], ["row3", "row4"]],
                unformatted_headers=["col1", "col2"],
                unformatted_data=[["row1", "row2"], ["row3", "row4"]],
            ),
            False,
            "informational",
            "passed"
        ),
        # Check 2: PASS
        (
            "fake_func_name_PASS_test",
            "PASS",
            Result(
                result=script.PASS,
                recommended_action="",
                msg="",
                doc_url="",
                headers=[],
                data=[],
                unformatted_headers=[],
                unformatted_data=[],
            ),
            True,
            "informational",
            "passed"
        ),
        # Check 3: POST
        (
            "fake_func_name_POST_test",
            "POST",
            Result(
                result=script.POST,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=["col1", "col2"],
                data=[["row1", "row2"], ["row3", "row4"]],
                unformatted_headers=["col1", "col2"],
                unformatted_data=[["row1", "row2"], ["row3", "row4"]],
            ),
            False,
            "informational",
            "failed"
        ),
        # Check 4: MANUAL
        (
            "fake_func_name_MANUAL_test",
            "MANUAL",
            Result(
                result=script.MANUAL,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=["col1", "col2"],
                data=[["row1", "row2"], ["row3", "row4"]],
                unformatted_headers=["col1", "col2"],
                unformatted_data=[["row1", "row2"], ["row3", "row4"]],
            ),
            True,
            "warning",
            "failed"
        ),
        # Check 5: ERROR
        (
            "fake_func_name_ERROR_test",
            "ERROR",
            Result(
                result=script.ERROR,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=["col1", "col2"],
                data=[["row1", "row2"], ["row3", "row4"]],
                unformatted_headers=["col1", "col2"],
                unformatted_data=[["row1", "row2"], ["row3", "row4"]],
            ),
            True,
            "major",
            "failed"
        ),
        # Check 6: FAIL_UF
        (
            "fake_func_name_FAIL_UF_test",
            "FAIL_UF",
            Result(
                result=script.FAIL_UF,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=["col1", "col2"],
                data=[["row1", "row2"], ["row3", "row4"]],
                unformatted_headers=["col1", "col2"],
                unformatted_data=[["row1", "row2"], ["row3", "row4"]],
            ),
            True,
            "critical",
            "failed"
        ),
        # Check 7: FAIL_O
        (
            "fake_func_name_FAIL_O_test",
            "FAIL_O",
            Result(
                result=script.FAIL_O,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=["col1", "col2", "col3"],
                data=[["row1", "row2", "row3"], ["row4", "row5", "row6"]],
                unformatted_headers=["col4", "col5"],
                unformatted_data=[["row1", "row2"], ["row3", "row4"]],
            ),
            True,
            "critical",
            "failed"
        ),
        # Check 8: FAIL_O Formatted only
        (
            "fake_func_name_FAIL_O_formatted_only_test",
            "FAIL_O Formatted only",
            Result(
                result=script.FAIL_O,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=["col1", "col2", "col3"],
                data=[["row1", None, 3], ["row4", None, 3]],
                unformatted_headers=[],
                unformatted_data=[],
            ),
            True,
            "critical",
            "failed"
        ),
        # Check 9: FAIL_O unformatted only
        (
            "fake_func_name_FAIL_O_unformatted_only_test",
            "FAIL_O Unformatted only",
            Result(
                result=script.FAIL_O,
                recommended_action="reboot",
                msg="test reason",
                doc_url="https://test_doc_url.html",
                headers=[],
                data=[],
                unformatted_headers=["col1", "col2", "col3"],
                unformatted_data=[["row1", None, 3], ["row4", None, 3]],
            ),
            True,
            "critical",
            "failed"
        ),
    ],
)
def test_AciResult(
    func_name,
    name,
    result_obj,
    expected_show,
    expected_criticality,
    expected_passed,
):
    synth = AciResult(func_name, name, result_obj)
    assert synth.ruleId == func_name
    assert synth.showValidation == expected_show
    assert synth.severity == expected_criticality
    assert synth.ruleStatus == expected_passed
    for entry in synth.failureDetails["data"]:
        for vals in entry.values():
            assert isinstance(vals, string_types)
    for entry in synth.failureDetails["unformatted_data"]:
        for vals in entry.values():
            assert isinstance(vals, string_types)


@pytest.mark.parametrize(
    "headers, data",
    [
        ("", []),  # invalid headers (columns)
        ([], {}),  # invalid data (rows)
        ("", {}),  # invalid headers and data
    ]
)
def test_invalid_headers_or_data(headers, data):
    with pytest.raises(TypeError):
        synth = AciResult("func_name", "Check Title")
        synth.convert_data(
            column=headers,
            rows=data,
        )


@pytest.mark.parametrize(
    "headers, data",
    [
        # Rows are shorter
        (
            ["col1", "col2"],
            [
                ["row1"],
                ["row2"]
            ]
        ),
        # columns are shorter
        (
            ["col1"],
            [
                ["row1", "row2"],
                ["row3", "row4"]
            ]
        ),
    ]
)
def test_mismatched_lengths(headers, data):
    with pytest.raises(ValueError):
        synth = AciResult("func_name", "Check Title")
        synth.convert_data(
            column=headers,
            rows=data,
        )
