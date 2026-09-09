import importlib

script = importlib.import_module("aci-preupgrade-validation-script")


def test_print_result_handles_mixed_type_rows_without_error():
    # Verify that Result stringifies all cell values, so data.sort() in print_result never fails.
    r = script.Result(
        result=script.FAIL_O,
        headers=["col1"],
        data=[[1], ["2"]],
        unformatted_headers=["col1"],
        unformatted_data=[[3], ["4"]],
    )
    # All values must already be strings after construction.
    assert r.data == [["1"], ["2"]]
    assert r.unformatted_data == [["3"], ["4"]]
    # print_result must not raise.
    script.print_result(
        index=1,
        total=1,
        title="Mixed type table",
        result=script.FAIL_O,
        headers=r.headers,
        data=r.data,
        unformatted_headers=r.unformatted_headers,
        unformatted_data=r.unformatted_data,
    )
