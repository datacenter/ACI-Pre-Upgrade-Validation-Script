import pytest
import importlib
import logging
import json

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion


# ------------------------------
# Data and fixtures
# ------------------------------


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

output_error = [{"error": {"attributes": {"code": "400", "text": "Request failed, unresolved class for dummyClass"}}}]


@pytest.fixture(scope="function")
def icurl_outputs(request):
    param = getattr(request, "param", {})
    data = {
        "firmwareCtrlrRunning.json": outputs["cversion"],
        "firmwareRunning.json": outputs["switch_version"],
        "fabricNodePEp.json": outputs["vpc_nodes"],
    }
    for key in data:
        if param.get(key, "non_falsy_default") != "non_falsy_default":
            data[key] = param[key]
    return data


@pytest.fixture(scope="function")
def fake_args(request):
    data = {
        "api_only": False,
        "cversion": None,
        "tversion": None,
    }
    for key in data:
        if request.param.get(key, "non_falsy_default") != "non_falsy_default":
            data[key] = request.param[key]
    return data


# ------------------------------
# Tests
# ------------------------------


@pytest.mark.parametrize(
    "fake_args, expected_common_data",
    [
        # Default, no argparse arguments
        pytest.param(
            {},
            {},
            id="default_no_args",
        ),
        # `api_only` is True.
        # No `get_credentials()`, no username nor password
        pytest.param(
            {
                "api_only": True,
            },
            {"username": None, "password": None},
            id="api_only",
        ),
        # `arg_tversion` is provided (i.e. -t 6.1(4a))
        pytest.param(
            {
                "tversion": "6.1(4a)",
            },
            {
                "tversion": AciVersion("6.1(4a)"),
            },
            id="tversion",
        ),
        # `arg_tversion` and `arg_cversion` are both provided (i.e. -t 6.1(4a))
        pytest.param(
            {
                "cversion": "6.0(8d)",
                "tversion": "6.1(4a)",
            },
            {
                "cversion": AciVersion("6.0(8d)"),
                "tversion": AciVersion("6.1(4a)"),
            },
            id="cversion_tversion",
        ),
        # versions are switch syntax
        pytest.param(
            {
                "cversion": "16.0(4d)",
                "tversion": "16.1(4a)",
            },
            {
                "cversion": AciVersion("6.0(4d)"),
                "tversion": AciVersion("6.1(4a)"),
            },
            id="cversion_tversion_with_switch_version_syntax",
        ),
        # versions are APIC image name syntax
        pytest.param(
            {
                "cversion": "aci-apic-dk9.6.0.1a.bin",
                "tversion": "aci-apic-dk9.6.2.1a.bin",
            },
            {
                "cversion": AciVersion("6.0(1a)"),
                "tversion": AciVersion("6.2(1a)"),
            },
            id="cversion_tversion_with_apic_image_name_syntax",
        ),
        # versions are Switch image name syntax
        pytest.param(
            {
                "cversion": "n9000-16.0(1a).bin",
                "tversion": "n9000-16.2(1a).bin",
            },
            {
                "cversion": AciVersion("6.0(1a)"),
                "tversion": AciVersion("6.2(1a)"),
            },
            id="cversion_tversion_with_switch_image_name_syntax",
        ),
    ],
    indirect=["fake_args", "expected_common_data"],
)
def test_common_data(mock_icurl, icurl_outputs, fake_args, expected_common_data):
    """test query_common_data and write_script_metadata"""
    # --- test for `query_common_data()`
    common_data = script.query_common_data(
        api_only=fake_args["api_only"], arg_cversion=fake_args["cversion"], arg_tversion=fake_args["tversion"]
    )
    for key in common_data:
        if isinstance(common_data[key], AciVersion):
            assert str(common_data[key]) == str(expected_common_data[key])
        else:
            assert common_data[key] == expected_common_data[key]

    # --- test for `write_script_metadata()`
    script.write_script_metadata(
        api_only=fake_args["api_only"], timeout=1200, total_checks=100, common_data=expected_common_data
    )
    with open(script.META_FILE, "r") as f:
        meta = json.load(f)
        assert meta["name"] == "PreupgradeCheck"
        assert meta["method"] == "standalone script"
        assert meta["datetime"] == script.ts + script.tz
        assert meta["script_version"] == script.SCRIPT_VERSION
        assert meta["cversion"] == str(expected_common_data["cversion"])
        assert meta["tversion"] == str(expected_common_data["tversion"])
        assert meta["sw_cversion"] == str(expected_common_data["sw_cversion"])
        assert meta["api_only"] == fake_args["api_only"]
        assert meta["timeout"] == 1200
        assert meta["total_checks"] == 100


def test_tversion_invald():
    with pytest.raises(SystemExit):
        with pytest.raises(ValueError):
            script.query_common_data(arg_cversion="6.0(1a)", arg_tversion="invalid_version")


def test_cversion_invald():
    with pytest.raises(SystemExit):
        with pytest.raises(ValueError):
            script.query_common_data(arg_cversion="invalid_version", arg_tversion="6.0(1a)")


@pytest.mark.parametrize(
    "icurl_outputs, print_output",
    [
        # `get_cversion()` failure
        ({"firmwareCtrlrRunning.json": output_error}, "Checking current APIC version..."),
        # `get_switch_version()` failure
        ({"firmwareRunning.json": output_error}, "Gathering Lowest Switch Version from Firmware Repository..."),
        # `get_vpc_nodes()` failure
        ({"fabricNodePEp.json": output_error}, "Collecting VPC Node IDs..."),
    ],
    indirect=["icurl_outputs"],
)
def test_icurl_failure_in_query_common_data(capsys, caplog, mock_icurl, print_output):
    caplog.set_level(logging.CRITICAL)
    with pytest.raises(SystemExit):
        with pytest.raises(Exception):
            script.query_common_data()
    captured = capsys.readouterr()
    expected_output = (
        print_output
        + """

Error: Your current ACI version does not have requested class
Initial query failed. Ensure APICs are healthy. Ending script run.
"""
    )
    assert captured.out.endswith(expected_output), "captured.out is:\n{}".format(captured.out)
