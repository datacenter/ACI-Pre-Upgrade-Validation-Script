import pytest
import importlib
import logging

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

    def _mock_get_target_version():
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
    "icurl_outputs, is_puv, arg_tversion, expected_result",
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
            {"username": "admin", "password": "mypassword", "cversion": AciVersion("6.1(1a)"), "tversion": AciVersion("6.2(1a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
        # `is_puv` is True (i.e. --puv)
        # No `get_credentials()`, no username nor password
        (
            {
                "firmwareCtrlrRunning.json": outputs["cversion"],
                "firmwareRunning.json": outputs["switch_version"],
                "fabricNodePEp.json": outputs["vpc_nodes"],
            },
            True,
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
            AciVersion("6.1(4a)"),
            {"username": "admin", "password": "mypassword", "cversion": AciVersion("6.1(1a)"), "tversion": AciVersion("6.1(4a)"), "sw_cversion": AciVersion("6.0(9d)"), "vpc_node_ids": ["101", "102"]},
        ),
    ],
)
def test_prepare(mock_icurl, is_puv, arg_tversion, expected_result):
    inputs, json_log = script.prepare(is_puv, arg_tversion)
    for key, value in expected_result.items():
        if "version" in key:
            assert isinstance(inputs[key], AciVersion)
            assert str(inputs[key]) == str(value)
        else:
            assert inputs[key] == value


@pytest.mark.parametrize(
    "icurl_outputs, is_puv, arg_tversion, expected_result",
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
            """\
Collecting VPC Node IDs...

Error: Your current ACI version does not have requested class
Initial query failed. Ensure APICs are healthy. Ending script run.
""",
        ),
    ],
)
def test_prepare_exception(capsys, caplog, mock_icurl, is_puv, arg_tversion, expected_result):
    caplog.set_level(logging.CRITICAL)
    with pytest.raises(SystemExit):
        with pytest.raises(Exception):
            script.prepare(is_puv, arg_tversion)
    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out.endswith(expected_result)
