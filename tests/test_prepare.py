import pytest
import importlib
import logging
import json

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion


@pytest.fixture(autouse=True)
def mock_get_credentials(monkeypatch):
    """Mock the get_credentials function to return a fixed username and password."""

    def _mock_get_credentials():
        return ("admin", "mypassword")

    monkeypatch.setattr(script, "get_credentials", _mock_get_credentials)


@pytest.fixture(autouse=True)
def mock_get_target_version(monkeypatch):
    """
    Mock `get_target_version()` to return a fixed target version.
    Used when the script is run without the `-t` option which is simulated by
    `arg_tversion`.
    Not using `mock_icurl` because this function involves a user interaction to
    select a version.
    """

    def _mock_get_target_version(arg_tversion):
        if arg_tversion:
            try:
                return AciVersion(arg_tversion)
            except ValueError as e:
                script.prints(e)
                raise SystemExit(1)
        return AciVersion("6.2(1a)")

    monkeypatch.setattr(script, "get_target_version", _mock_get_target_version)


outputs = {
    "cversion": [
        {
            "firmwareCtrlrRunning": {
                "attributes": {
                    "dn": "topology/pod-1/node-1/sys/ctrlrfwstatuscont/ctrlrrunning",
                    "version": "6.1(1a)",
                }
            }
        }
    ],
    "switch_version": [
        {"firmwareRunning": {"attributes": {"peVer": "6.1(1a)", "version": "n9000-16.1(1a)"}}},
        {"firmwareRunning": {"attributes": {"peVer": "6.0(9d)", "version": "n9000-16.0(9d)"}}},
    ],
    "vpc_nodes": [
        {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-101-102/nodepep-101", "id": "101"}}},
        {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-101-102/nodepep-102", "id": "102"}}},
    ],
}


@pytest.mark.parametrize(
    "icurl_outputs, api_only, arg_tversion, arg_cversion, debug_function, expected_result",
    [
        # Default, no argparse arguments
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            False,
            None,
            None,
            None,
            {"username": "admin", "password": "mypassword", "cversion": AciVersion("6.1(1a)"), "tversion": AciVersion("6.2(1a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
        # `api_only` is True (i.e. --puv)
        # No `get_credentials()`, no username nor password
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            True,
            None,
            None,
            None,
            {"username": None, "password": None, "cversion": AciVersion("6.1(1a)"), "tversion": AciVersion("6.2(1a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
        # `arg_tversion` is provided (i.e. -t 6.1(4a))
        # The version `get_target_version()` is ignored.
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            False,
            "6.1(4a)",
            None,
            None,
            {"username": "admin", "password": "mypassword", "cversion": AciVersion("6.1(1a)"), "tversion": AciVersion("6.1(4a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
        # `arg_tversion` and `arg_cversion` are both provided (i.e. -t 6.1(4a))
        # The version `get_target_version()` is ignored.
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            False,
            "6.1(4a)",
            "6.0(8d)",
            None,
            {"username": "admin", "password": "mypassword", "cversion": AciVersion("6.0(8d)"), "tversion": AciVersion("6.1(4a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
        # `arg_tversion`, `arg_cversion` and 'debug_function' are all provided
        # The version `get_target_version()` is ignored.
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            False,
            "6.1(4a)",
            "6.0(4d)",
            "ave_eol_check",
            {"username": "admin", "password": "mypassword", "cversion": AciVersion("6.0(4d)"), "tversion": AciVersion("6.1(4a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
        # veresions are switch syntax
        # The version `get_target_version()` is ignored.
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            False,
            "16.1(4a)",
            "16.0(4d)",
            "ave_eol_check",
            {"username": "admin", "password": "mypassword", "cversion": AciVersion("6.0(4d)"), "tversion": AciVersion("6.1(4a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
        # veresions are switch or APIC syntax
        # The version `get_target_version()` is ignored.
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            False,
            "n9000-16.2(1a).bin",
            "aci-apic-dk9.6.0.1a.bin",
            "ave_eol_check",
            {"username": "admin", "password": "mypassword", "cversion": AciVersion("6.0(1a)"), "tversion": AciVersion("6.2(1a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
    ],
)
def test_prepare(mock_icurl, api_only, arg_tversion, arg_cversion, debug_function, expected_result):
    checks = script.get_checks(api_only, debug_function)
    inputs = script.prepare(api_only, arg_tversion, arg_cversion, len(checks))
    for key, value in expected_result.items():
        if "version" in key:
            assert isinstance(inputs[key], AciVersion)
            assert str(inputs[key]) == str(value)
        else:
            assert inputs[key] == value

    with open(script.META_FILE, "r") as f:
        meta = json.load(f)
        assert meta["name"] == "PreupgradeCheck"
        assert meta["method"] == "standalone script"
        assert meta.get("datetime") is not None
        assert meta["script_version"] == script.SCRIPT_VERSION
        assert meta["cversion"] == str(expected_result["cversion"])
        assert meta["tversion"] == str(expected_result["tversion"])
        assert meta["sw_cversion"] == str(expected_result["sw_cversion"])
        assert meta["api_only"] == api_only
        assert meta["total_checks"] == len(checks)
        if debug_function:
            assert meta["total_checks"] == 1


def test_tversion_invald():
    with pytest.raises(SystemExit):
        with pytest.raises(ValueError):
            script.prepare(False, "invalid_version", "6.0(1a)", 1)


def test_cversion_invald():
    with pytest.raises(SystemExit):
        with pytest.raises(ValueError):
            script.prepare(False, "6.0(1a)", "invalid_version", 1)


@pytest.mark.parametrize(
    "icurl_outputs, api_only, arg_tversion, arg_cversion, debug_function, expected_result",
    [
        # `get_cversion()` failure
        (
            {
                "firmwareCtrlrRunning.json": [{"error": {"attributes": {"code": "400", "text": "Request failed, unresolved class for firmwareCtrlrRunning_fake"}}}],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            False,
            None,
            None,
            None,
            """\
Checking current APIC version...

Error: Your current ACI version does not have requested class
Initial query failed. Ensure APICs are healthy. Ending script run.
""",
        ),
        # `get_switch_version()` failure
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": [{"error": {"attributes": {"code": "400", "text": "Request failed, unresolved class for firmwareRunning_fake"}}}],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            False,
            None,
            None,
            None,
            """\
Gathering Lowest Switch Version from Firmware Repository...

Error: Your current ACI version does not have requested class
Initial query failed. Ensure APICs are healthy. Ending script run.
""",
        ),
        # `get_vpc_nodes()` failure
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": [{"error": {"attributes": {"code": "400", "text": "Request failed, unresolved class for fabricNodePEp_fake"}}}],
            },
            False,
            None,
            None,
            None,
            """\
Collecting VPC Node IDs...

Error: Your current ACI version does not have requested class
Initial query failed. Ensure APICs are healthy. Ending script run.
""",
        ),
    ],
)
def test_prepare_exception(capsys, caplog, mock_icurl, api_only, arg_tversion, arg_cversion, debug_function, expected_result):
    caplog.set_level(logging.CRITICAL)
    with pytest.raises(SystemExit):
        with pytest.raises(Exception):
            checks = script.get_checks(api_only, debug_function)
            script.prepare(api_only, arg_tversion, arg_cversion, len(checks))
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out.endswith(expected_result)
