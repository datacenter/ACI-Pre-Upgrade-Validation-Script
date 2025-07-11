import importlib
import logging

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion


def check_builder(func_name, title, result):
    def _check(index, total_checks, **kwargs):
        _check.__name__ = func_name
        script.print_title(title, index, total_checks)
        if result == script.ERROR:
            raise Exception("This is a test exception to result in `script.ERROR`.")
        else:
            script.print_result(title, result)
            return result

    return _check


fake_checks = [
    check_builder(func_name, title, result)
    for func_name, title, result in [
        ("check1", "Test Check 1", script.PASS),
        ("check2", "Test Check 2", script.FAIL_O),
        ("check3", "Test Check 3", script.FAIL_UF),
        ("check4", "Test Check 4", script.MANUAL),
        ("check5", "Test Check 5", script.POST),
        ("check6", "Test Check 6", script.NA),
        ("check7", "Test Check 7", script.ERROR),
        ("check8", "Test Check 8", script.PASS),
    ]
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
[Check  2/8] Test Check 2...                                                                                      FAIL - OUTAGE WARNING!!
[Check  3/8] Test Check 3...                                                                                     FAIL - UPGRADE FAILURE!!
[Check  4/8] Test Check 4...                                                                                        MANUAL CHECK REQUIRED
[Check  5/8] Test Check 5...                                                                                  POST UPGRADE CHECK REQUIRED
[Check  6/8] Test Check 6...                                                                                                          N/A
[Check  7/8] Test Check 7... 
                    ... Unexpected Error: This is a test exception to result in `script.ERROR`.                                   ERROR !!
[Check  8/8] Test Check 8...                                                                                                         PASS

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
