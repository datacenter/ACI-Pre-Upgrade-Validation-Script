import pytest
import importlib
import json
from six import string_types

script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.mark.parametrize(
    "func_name, name, description, result, recommended_action, reason, doc_url, column, row, unformatted_column, unformatted_rows, expected_show, expected_criticality, expected_passed",
    [
        # Check 1: NA
        (
            "fake_func_name_NA_test",
            "NA",
            "",
            script.NA,
            "",
            "",
            "",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            False,
            "informational",
            "passed"
        ),
        # Check 2: PASS
        (
            "fake_func_name_PASS_test",
            "PASS",
            "",
            script.PASS,
            "",
            "",
            "",
            [],
            [],
            [],
            [],
            True,
            "informational",
            "passed"
        ),
        # Check 3: POST
        (
            "fake_func_name_POST_test",
            "POST",
            "",
            script.POST,
            "reboot",
            "test reason",
            "https://test_doc_url.html",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            False,
            "informational",
            "failed"
        ),
        # Check 4: MANUAL
        (
            "fake_func_name_MANUAL_test",
            "MANUAL",
            "",
            script.MANUAL,
            "reboot",
            "test reason",
            "https://test_doc_url.html",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            True,
            "warning",
            "failed"
        ),
        # Check 5: ERROR
        (
            "fake_func_name_ERROR_test",
            "ERROR",
            "",
            script.ERROR,
            "reboot",
            "test reason",
            "https://test_doc_url.html",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            True,
            "major",
            "failed"
        ),
        # Check 6: FAIL_UF
        (
            "fake_func_name_FAIL_UF_test",
            "FAIL_UF",
            "",
            script.FAIL_UF,
            "reboot",
            "test reason",
            "https://test_doc_url.html",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            True,
            "critical",
            "failed"
        ),
        # Check 7: FAIL_O
        (
            "fake_func_name_FAIL_O_test",
            "FAIL_O",
            "",
            script.FAIL_O,
            "reboot",
            "test reason",
            "https://test_doc_url.html",
            ["col1", "col2", "col3"],
            [["row1", "row2", "row3"], ["row4", "row5", "row6"]],
            ["col4", "col5"],
            [["row1", "row2"], ["row3", "row4"]],
            True,
            "critical",
            "failed"
        ),
        # Check 8: FAIL_O Formatted only
        (
            "fake_func_name_FAIL_O_formatted_only_test",
            "FAIL_O Formatted only",
            "",
            script.FAIL_O,
            "reboot",
            "test reason",
            "https://test_doc_url.html",
            ["col1", "col2", "col3"],
            [["row1", None, 3], ["row4", None, 3]],
            [],
            [],
            True,
            "critical",
            "failed"
        ),
        # Check 9: FAIL_O unformatted only
        (
            "fake_func_name_FAIL_O_unformatted_only_test",
            "FAIL_O Unformatted only",
            "",
            script.FAIL_O,
            "reboot",
            "test reason",
            "https://test_doc_url.html",
            [],
            [],
            ["col1", "col2", "col3"],
            [["row1", None, 3], ["row4", None, 3]],
            True,
            "critical",
            "failed"
        ),
    ],
)
def test_AciResult(
    func_name,
    name,
    description,
    result,
    recommended_action,
    reason,
    doc_url,
    column,
    row,
    unformatted_column,
    unformatted_rows,
    expected_show,
    expected_criticality,
    expected_passed,
):
    synth = script.AciResult(func_name, name, description)
    synth.updateWithResults(result, recommended_action, reason, doc_url, column, row, unformatted_column, unformatted_rows)
    file = synth.writeResult()
    with open(file, "r") as f:
        data = json.load(f)
    assert data["ruleId"] == func_name
    assert data["showValidation"] == expected_show
    assert data["severity"] == expected_criticality
    assert data["ruleStatus"] == expected_passed
    for entry in data["failureDetails"]["data"]:
        for vals in entry.values():
            assert isinstance(vals, string_types)
    for entry in data["failureDetails"]["unformatted_data"]:
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
        synth = script.AciResult("func_name", "Check Title", "A Description")
        synth.craftData(
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
        synth = script.AciResult("func_name", "Check Title", "A Description")
        synth.craftData(
            column=headers,
            rows=data,
        )
