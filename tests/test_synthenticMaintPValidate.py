import pytest
import importlib
import json

script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.mark.parametrize(
    "name, description, result, recommended_action, reason, header, footer, column, row, unformatted_column, unformatted_rows, expected_show, expected_criticality, expected_passed",
    [
        # Check 1: NA
        (
            "NA",
            "",
            script.NA,
            "",
            "",
            "",
            "",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            False,
            "informational",
            True
        ),
        # Check 2: PASS
        (
            "PASS",
            "",
            script.PASS,
            "",
            "",
            "",
            "",
            [],
            [],
            [],
            [],
            True,
            "informational",
            True
        ),
        # Check 3: POST
        (
            "POST",
            "",
            script.POST,
            "reboot",
            "test reason",
            "test header",
            "test footer",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            False,
            "informational",
            False
        ),
        # Check 4: MANUAL
        (
            "MANUAL",
            "",
            script.MANUAL,
            "reboot",
            "test reason",
            "test header",
            "test footer",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            True,
            "warning",
            False
        ),
        # Check 5: ERROR
        (
            "ERROR",
            "",
            script.ERROR,
            "reboot",
            "test reason",
            "test header",
            "test footer",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            True,
            "major",
            False
        ),
        # Check 6: FAIL_UF
        (
            "FAIL_UF",
            "",
            script.FAIL_UF,
            "reboot",
            "test reason",
            "test header",
            "test footer",
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            ["col1", "col2"],
            [["row1", "row2"], ["row3", "row4"]],
            True,
            "critical",
            False
        ),
        # Check 7: FAIL_O
        (
            "FAIL_O",
            "",
            script.FAIL_O,
            "reboot",
            "test reason",
            "test header",
            "test footer",
            ["col1", "col2", "col3"],
            [["row1", "row2", "row3"], ["row4", "row5", "row6"]],
            ["col4", "col5"],
            [["row1", "row2"], ["row3", "row4"]],
            True,
            "critical",
            False
        ),
        # Check 8: FAIL_O Formatted only
        (
            "FAIL_O Formatted only",
            "",
            script.FAIL_O,
            "reboot",
            "test reason",
            "test header",
            "test footer",
            ["col1", "col2", "col3"],
            [["row1", "row2", "row3"], ["row4", "row5", "row6"]],
            [],
            [],
            True,
            "critical",
            False
        ),
        # Check 9: FAIL_O
        (
            "FAIL_O Unformatted only",
            "",
            script.FAIL_O,
            "reboot",
            "test reason",
            "test header",
            "test footer",
            [],
            [],
            ["col1", "col2", "col3"],
            [["row1", "row2", "row3"], ["row4", "row5", "row6"]],
            True,
            "critical",
            False
        ),
    ],
)
def test_syntheticMaintPValidate(
    name,
    description,
    result,
    recommended_action,
    reason,
    header,
    footer,
    column,
    row,
    unformatted_column,
    unformatted_rows,
    expected_show,
    expected_criticality,
    expected_passed,
):
    synth = script.syntheticMaintPValidate(name, description)
    synth.updateWithResults(result, recommended_action, reason, header, footer, column, row, unformatted_column, unformatted_rows)
    file = synth.writeResult()
    with open(file, "r") as f:
        data = json.load(f)
    assert data["syntheticMaintPValidate"]["attributes"]["showValidation"] == expected_show
    assert data["syntheticMaintPValidate"]["attributes"]["criticality"] == expected_criticality
    assert data["syntheticMaintPValidate"]["attributes"]["passed"] == expected_passed
