import pytest
import importlib
import sys

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion


def test_no_args():
    # When `None` or nothing is passed to `ArgumentParser.parse_args()`, the `argparse`
    # module reads `sys.argv[1:]` which should return an empty list when a script is
    # run without any command-line arguments. However, in pytest, `sys.argv[1:]` is
    # the arguments to the pytest command which may not be empty.
    # To simulate the script being run without any command-line arguments,
    # we set `sys.argv[1:]` to an empty list when `args` is `None`.
    sys.argv[1:] = []
    is_puv, tversion = script.parse_args(args=None)
    assert is_puv is False
    assert tversion is None


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], False),
        (["--puv"], True),
    ],
)
def test_puv(args, expected_result):
    is_puv, tversion = script.parse_args(args)
    assert is_puv == expected_result


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], None),
        (["-t", "6.2(1a)"], AciVersion("6.2(1a)")),
        (["-t", "16.2(1a)"], AciVersion("6.2(1a)")),
        (["-t", "n9000-16.2(1a).bin"], AciVersion("6.2(1a)")),
        (["-t", "aci-apic-dk9.6.2.1a.bin"], AciVersion("6.2(1a)")),
    ],
)
def test_tversion(args, expected_result):
    is_puv, tversion = script.parse_args(args)
    if tversion is not None:
        assert isinstance(tversion, AciVersion)
    assert str(tversion) == str(expected_result)


def test_tversion_invald():
    with pytest.raises(SystemExit):
        with pytest.raises(RuntimeError):
            script.parse_args(args=["-t", "invalid_version"])
