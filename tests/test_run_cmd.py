import pytest
import importlib
from subprocess import CalledProcessError
script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.mark.parametrize(
    "cmd, splitlines, expected_output",
    [
        (["echo", "$'hello\nworld'"], True, ["hello", "world"]),
        ("echo $'hello\nworld'", True, ["hello", "world"]),
        (["echo", "$'hello\nworld'"], False, "hello\nworld\n"),
        ("echo $'hello\nworld'", False, "hello\nworld\n"),
    ],
)
def test_run_cmds(cmd, splitlines, expected_output):
    result = script.run_cmd(cmd, splitlines)
    assert result == expected_output


@pytest.mark.parametrize(
    "cmd, splitlines, expected_type",
    [
        (["ls", "-l"], True, list),
        ("ls -l", True, list),
        (["ls", "-l"], False, str),
        ("ls -l", False, str),
    ],
)
def test_run_cmd_output_type(cmd, splitlines, expected_type):
    result = script.run_cmd(cmd, splitlines)
    assert isinstance(result, expected_type)


@pytest.mark.parametrize(
    "cmd, splitlines, expected_output",
    [
        ("fake_command", True, ""),
        (["fake_command"], False, ""),
    ]
)
def test_non_existing_command(cmd, splitlines, expected_output):
    with pytest.raises(CalledProcessError):
        script.run_cmd(cmd, splitlines)
