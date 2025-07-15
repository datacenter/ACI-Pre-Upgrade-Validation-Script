import pytest
import importlib
import sys

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion


def test_args_version(capsys):
    script.main(["--version"])
    captured = capsys.readouterr()
    print(captured.out)
    assert "{}\n".format(script.SCRIPT_VERSION) == captured.out


@pytest.mark.parametrize("api_only", [False, True])
def test_args_total_checks(capsys, api_only):
    args = ["--total-checks", "--api-only"] if api_only else ["--total-checks"]
    checks = script.get_checks(api_only=api_only, debug_function=None)
    script.main(args)
    captured = capsys.readouterr()
    print(captured.out)
    assert "Total Number of Checks: {}\n".format(len(checks)) == captured.out
