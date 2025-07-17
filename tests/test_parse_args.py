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
    args = script.parse_args(args=None)
    assert args.api_only is False
    assert args.tversion is None
    assert args.cversion is None
    assert args.debug_function is None
    assert args.no_cleanup is False
    assert args.version is False
    assert args.total_checks is False


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], False),
        (["-a"], True),
        (["--api-only"], True),
    ],
)
def test_api_only(args, expected_result):
    args = script.parse_args(args)
    assert args.api_only == expected_result


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], None),
        (["-t", "6.2(1a)"], "6.2(1a)"),
        (["-t", "16.2(1a)"], "16.2(1a)"),
        (["-t", "n9000-16.2(1a).bin"], "n9000-16.2(1a).bin"),
        (["-t", "aci-apic-dk9.6.2.1a.bin"], "aci-apic-dk9.6.2.1a.bin"),
        (["-t", "invalid_version"], "invalid_version"),
        (["--tversion", "6.2(1a)"], "6.2(1a)"),
    ],
)
def test_tversion(args, expected_result):
    args = script.parse_args(args)
    if args.tversion is not None:
        assert isinstance(args.tversion, str)
    assert str(args.tversion) == str(expected_result)


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], None),
        (["-c", "6.2(1a)"], "6.2(1a)"),
        (["-c", "16.2(1a)"], "16.2(1a)"),
        (["-c", "n9000-16.2(1a).bin"], "n9000-16.2(1a).bin"),
        (["-c", "aci-apic-dk9.6.2.1a.bin"], "aci-apic-dk9.6.2.1a.bin"),
        (["-c", "invalid_version"], "invalid_version"),
        (["--cversion", "6.2(1a)"], "6.2(1a)"),
    ],
)
def test_cversion(args, expected_result):
    args = script.parse_args(args)
    if args.cversion is not None:
        assert isinstance(args.cversion, str)
    assert str(args.cversion) == str(expected_result)


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], None),
        (["-d", "pbr_high_scale_check"], "pbr_high_scale_check"),
        (["-d", "made_up_func"], "made_up_func"),
        (["--debug-func", "pbr_high_scale_check"], "pbr_high_scale_check"),
    ],
)
def test_debug_func(args, expected_result):
    args = script.parse_args(args)
    if args.debug_function is not None:
        assert isinstance(args.debug_function, str)
    assert str(args.debug_function) == str(expected_result)


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], False),
        (["-n"], True),
        (["--no-cleanup"], True),
    ],
)
def test_no_cleanup(args, expected_result):
    args = script.parse_args(args)
    assert args.no_cleanup == expected_result


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], False),
        (["-v"], True),
        (["--version"], True),
    ],
)
def test_version(args, expected_result):
    args = script.parse_args(args)
    assert args.version == expected_result


@pytest.mark.parametrize(
    "args, expected_result",
    [
        ([], False),
        (["--total-checks"], True),
    ],
)
def test_total_checks(args, expected_result):
    args = script.parse_args(args)
    assert args.total_checks == expected_result
