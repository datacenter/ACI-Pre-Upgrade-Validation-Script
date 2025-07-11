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
    is_puv, tversion, cversion, debug_function = script.parse_args(args=None)
    assert is_puv is False
    assert tversion is None
    assert cversion is None
    assert debug_function is None


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], False),
        (["--puv"], True),
    ],
)
def test_puv(args, expected_result):
    is_puv, tversion, cversion, debug_function = script.parse_args(args)
    assert is_puv == expected_result


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], None),
        (["-t", "6.2(1a)"], "6.2(1a)"),
        (["-t", "16.2(1a)"], "16.2(1a)"),
        (["-t", "n9000-16.2(1a).bin"], "n9000-16.2(1a).bin"),
        (["-t", "aci-apic-dk9.6.2.1a.bin"], "aci-apic-dk9.6.2.1a.bin"),
        (["-t", "invalid_version"], "invalid_version"),
    ],
)
def test_tversion(args, expected_result):
    is_puv, tversion, cversion, debug_function = script.parse_args(args)
    if tversion is not None:
        assert isinstance(tversion, str)
    assert str(tversion) == str(expected_result)


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], None),
        (["-c", "6.2(1a)"], "6.2(1a)"),
        (["-c", "16.2(1a)"], "16.2(1a)"),
        (["-c", "n9000-16.2(1a).bin"], "n9000-16.2(1a).bin"),
        (["-c", "aci-apic-dk9.6.2.1a.bin"], "aci-apic-dk9.6.2.1a.bin"),
        (["-c", "invalid_version"], "invalid_version"),
    ],
)
def test_cversion(args, expected_result):
    is_puv, tversion, cversion, debug_function = script.parse_args(args)
    if cversion is not None:
        assert isinstance(cversion, str)
    assert str(cversion) == str(expected_result)


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], None),
        (["-d", "pbr_high_scale_check"], "pbr_high_scale_check"),
        (["-d", "made_up_func"], "made_up_func"),
    ],
)
def test_debug_func(args, expected_result):
    is_puv, tversion, cversion, debug_function = script.parse_args(args)
    if debug_function is not None:
        assert isinstance(debug_function, str)
    assert str(debug_function) == str(expected_result)
