import pytest
import importlib
import logging
import json
import sys

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
            script.prints("Target APIC version is overridden to %s\n" % arg_tversion)
            try:
                target_version = AciVersion(arg_tversion)
            except ValueError as e:
                script.prints(e)
                sys.exit(1)
            return target_version
        return AciVersion("6.2(1a)")

    monkeypatch.setattr(script, "get_target_version", _mock_get_target_version)


_icurl_outputs = {
    "fabricNode.json": [
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.1",
                    "dn": "topology/pod-1/node-1",
                    "fabricSt": "commissioned",
                    "id": "1",
                    "model": "APIC-SERVER-L2",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "apic1",
                    "nodeType": "unspecified",
                    "role": "controller",
                    "version": "6.1(1a)",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.2",
                    "dn": "topology/pod-1/node-2",
                    "fabricSt": "commissioned",
                    "id": "2",
                    "model": "APIC-SERVER-L2",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "apic2",
                    "nodeType": "unspecified",
                    "role": "controller",
                    "version": "6.1(1a)",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.3",
                    "dn": "topology/pod-2/node-3",
                    "fabricSt": "commissioned",
                    "id": "3",
                    "model": "APIC-SERVER-L2",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "apic3",
                    "nodeType": "unspecified",
                    "role": "controller",
                    "version": "6.1(1a)",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.101",
                    "dn": "topology/pod-1/node-101",
                    "fabricSt": "active",
                    "id": "101",
                    "model": "N9K-C93180YC-FX",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "leaf101",
                    "nodeType": "unspecified",
                    "role": "leaf",
                    "version": "n9000-16.1(1a)",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.102",
                    "dn": "topology/pod-1/node-102",
                    "fabricSt": "active",
                    "id": "102",
                    "model": "N9K-C93180YC-FX",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "leaf102",
                    "nodeType": "unspecified",
                    "role": "leaf",
                    "version": "n9000-16.1(1a)",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.111",
                    "dn": "topology/pod-1/node-1001",
                    "fabricSt": "active",
                    "id": "1001",
                    "model": "N9K-C9504",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "spine1001",
                    "nodeType": "unspecified",
                    "role": "spine",
                    "version": "n9000-16.1(1a)",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.201",
                    "dn": "topology/pod-2/node-201",
                    "fabricSt": "active",
                    "id": "201",
                    "model": "N9K-C93180YC-FX3",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "leaf201",
                    "nodeType": "unspecified",
                    "role": "leaf",
                    "version": "n9000-16.0(9d)",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.211",
                    "dn": "topology/pod-2/node-2001",
                    "fabricSt": "active",
                    "id": "2001",
                    "model": "N9K-C9504",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "spine2001",
                    "nodeType": "unspecified",
                    "role": "spine",
                    "version": "n9000-16.1(1a)",
                }
            }
        },
    ],
    "fabricNodePEp.json": [
        {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-101-102/nodepep-101", "id": "101"}}},
        {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-101-102/nodepep-102", "id": "102"}}},
    ],
}

_icurl_outputs_old = {
    # fabricNode.version in older versions like 3.2 shows an invalid version like "A"
    # for controller and empty for active switches.
    "fabricNode.json": [
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.1",
                    "dn": "topology/pod-1/node-1",
                    "fabricSt": "commissioned",
                    "id": "1",
                    "model": "APIC-SERVER-L2",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "apic1",
                    "nodeType": "unspecified",
                    "role": "controller",
                    "version": "A",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.2",
                    "dn": "topology/pod-1/node-2",
                    "fabricSt": "commissioned",
                    "id": "2",
                    "model": "APIC-SERVER-L2",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "apic2",
                    "nodeType": "unspecified",
                    "role": "controller",
                    "version": "A",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.3",
                    "dn": "topology/pod-2/node-3",
                    "fabricSt": "commissioned",
                    "id": "3",
                    "model": "APIC-SERVER-L2",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "apic3",
                    "nodeType": "unspecified",
                    "role": "controller",
                    "version": "A",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.101",
                    "dn": "topology/pod-1/node-101",
                    "fabricSt": "active",
                    "id": "101",
                    "model": "N9K-C93180YC-FX",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "leaf101",
                    "nodeType": "unspecified",
                    "role": "leaf",
                    "version": "",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.102",
                    "dn": "topology/pod-1/node-102",
                    "fabricSt": "active",
                    "id": "102",
                    "model": "N9K-C93180YC-FX",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "leaf102",
                    "nodeType": "unspecified",
                    "role": "leaf",
                    "version": "",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.111",
                    "dn": "topology/pod-1/node-1001",
                    "fabricSt": "active",
                    "id": "1001",
                    "model": "N9K-C9504",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "spine1001",
                    "nodeType": "unspecified",
                    "role": "spine",
                    "version": "",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.201",
                    "dn": "topology/pod-2/node-201",
                    "fabricSt": "active",
                    "id": "201",
                    "model": "N9K-C93180YC-FX3",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "leaf201",
                    "nodeType": "unspecified",
                    "role": "leaf",
                    "version": "",
                }
            }
        },
        {
            "fabricNode": {
                "attributes": {
                    "address": "10.0.0.211",
                    "dn": "topology/pod-2/node-2001",
                    "fabricSt": "active",
                    "id": "2001",
                    "model": "N9K-C9504",
                    "monPolDn": "uni/fabric/monfab-default",
                    "name": "spine2001",
                    "nodeType": "unspecified",
                    "role": "spine",
                    "version": "",
                }
            }
        },
    ],
    "fabricNodePEp.json": _icurl_outputs["fabricNodePEp.json"],
    "topology/pod-1/node-1/sys/ctrlrfwstatuscont/ctrlrrunning.json": [
        {
            "firmwareCtrlrRunning": {
                "attributes": {
                    "dn": "topology/pod-1/node-1/sys/ctrlrfwstatuscont/ctrlrrunning",
                    "type": "controller",
                    "version": "3.2(7f)"
                }
            }
        }
    ],
    "firmwareRunning.json": [
        {
            "firmwareRunning": {
                "attributes": {
                    "dn": "topology/pod-1/node-101/sys/fwstatuscont/running",
                    "peVer": "3.1(2u)",
                    "type": "switch",
                    "version": "n9000-13.1(2u)"
                }
            }
        },
        {
            "firmwareRunning": {
                "attributes": {
                    "dn": "topology/pod-1/node-102/sys/fwstatuscont/running",
                    "peVer": "3.2(7f)",
                    "type": "switch",
                    "version": "n9000-13.2(7f)"
                }
            }
        },
        {
            "firmwareRunning": {
                "attributes": {
                    "dn": "topology/pod-1/node-1001/sys/fwstatuscont/running",
                    "peVer": "3.2(7f)",
                    "type": "switch",
                    "version": "n9000-13.2(7f)"
                }
            }
        },
        {
            "firmwareRunning": {
                "attributes": {
                    "dn": "topology/pod-2/node-201/sys/fwstatuscont/running",
                    "peVer": "3.2(7f)",
                    "type": "switch",
                    "version": "n9000-13.2(7f)"
                }
            }
        },
        {
            "firmwareRunning": {
                "attributes": {
                    "dn": "topology/pod-2/node-2001/sys/fwstatuscont/running",
                    "peVer": "3.2(7f)",
                    "type": "switch",
                    "version": "n9000-13.2(7f)"
                }
            }
        },

    ],
}


@pytest.fixture(scope="function")
def fake_args(request):
    data = {
        "api_only": False,
        "cversion": None,
        "tversion": None,
    }
    # update data contents when parametrize provides non-falsy values
    for key in data:
        if request.param.get(key, "non_falsy_default") != "non_falsy_default":
            data[key] = request.param[key]
    return data


# ------------------------------
# Tests
# ------------------------------


@pytest.mark.parametrize(
    "icurl_outputs, fake_args, expected_common_data",
    [
        # Default, no argparse arguments
        pytest.param(
            _icurl_outputs,
            {},
            {
                "cversion": AciVersion("6.1(1a)"),
                "sw_cversion": AciVersion("6.0(9d)"),
                "tversion": AciVersion("6.2(1a)"),
                "fabric_nodes": _icurl_outputs["fabricNode.json"],
                "vpc_node_ids": ["101", "102"],
            },
            id="default_no_args",
        ),
        # Default, no argparse arguments, old ACI version
        pytest.param(
            _icurl_outputs_old,
            {},
            {
                "cversion": AciVersion("3.2(7f)"),
                "sw_cversion": AciVersion("3.1(2u)"),
                "tversion": AciVersion("6.2(1a)"),
                "fabric_nodes": _icurl_outputs_old["fabricNode.json"],
                "vpc_node_ids": ["101", "102"],
            },
            id="default_no_args_old_aci",
        ),
        # `api_only` is True.
        # No `get_credentials()`, no username nor password
        pytest.param(
            _icurl_outputs,
            {
                "api_only": True,
            },
            {
                "username": None,
                "password": None,
                "cversion": AciVersion("6.1(1a)"),
                "sw_cversion": AciVersion("6.0(9d)"),
                "tversion": AciVersion("6.2(1a)"),
                "fabric_nodes": _icurl_outputs["fabricNode.json"],
                "vpc_node_ids": ["101", "102"],
            },
            id="api_only",
        ),
        # `arg_tversion` is provided (i.e. -t 6.1(4a))
        pytest.param(
            _icurl_outputs,
            {
                "tversion": "6.1(4a)",
            },
            {
                "cversion": AciVersion("6.1(1a)"),
                "sw_cversion": AciVersion("6.0(9d)"),
                "tversion": AciVersion("6.1(4a)"),
                "fabric_nodes": _icurl_outputs["fabricNode.json"],
                "vpc_node_ids": ["101", "102"],
            },
            id="tversion",
        ),
        # `arg_tversion` and `arg_cversion` are both provided (i.e. -t 6.1(4a))
        pytest.param(
            _icurl_outputs,
            {
                "cversion": "6.0(8d)",
                "tversion": "6.1(4a)",
            },
            {
                "cversion": AciVersion("6.0(8d)"),
                "sw_cversion": AciVersion("6.0(8d)"),
                "tversion": AciVersion("6.1(4a)"),
                "fabric_nodes": _icurl_outputs["fabricNode.json"],
                "vpc_node_ids": ["101", "102"],
            },
            id="cversion_tversion",
        ),
        # versions are switch syntax
        pytest.param(
            _icurl_outputs,
            {
                "cversion": "16.0(4d)",
                "tversion": "16.1(4a)",
            },
            {
                "cversion": AciVersion("6.0(4d)"),
                "sw_cversion": AciVersion("6.0(4d)"),
                "tversion": AciVersion("6.1(4a)"),
                "fabric_nodes": _icurl_outputs["fabricNode.json"],
                "vpc_node_ids": ["101", "102"],
            },
            id="cversion_tversion_with_switch_version_syntax",
        ),
        # versions are APIC image name syntax
        pytest.param(
            _icurl_outputs,
            {
                "cversion": "aci-apic-dk9.6.0.1a.bin",
                "tversion": "aci-apic-dk9.6.2.1a.bin",
            },
            {
                "cversion": AciVersion("6.0(1a)"),
                "sw_cversion": AciVersion("6.0(1a)"),
                "tversion": AciVersion("6.2(1a)"),
                "fabric_nodes": _icurl_outputs["fabricNode.json"],
                "vpc_node_ids": ["101", "102"],
            },
            id="cversion_tversion_with_apic_image_name_syntax",
        ),
        # versions are Switch image name syntax
        pytest.param(
            _icurl_outputs,
            {
                "cversion": "n9000-16.0(1a).bin",
                "tversion": "n9000-16.2(1a).bin",
            },
            {
                "cversion": AciVersion("6.0(1a)"),
                "sw_cversion": AciVersion("6.0(1a)"),
                "tversion": AciVersion("6.2(1a)"),
                "fabric_nodes": _icurl_outputs["fabricNode.json"],
                "vpc_node_ids": ["101", "102"],
            },
            id="cversion_tversion_with_switch_image_name_syntax",
        ),
    ],
    indirect=["fake_args", "expected_common_data"],
)
def test_common_data(mock_icurl, fake_args, expected_common_data):
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


@pytest.mark.parametrize("icurl_outputs", [_icurl_outputs])
def test_tversion_invald(capsys, mock_icurl):
    with pytest.raises(SystemExit):
        script.query_common_data(arg_cversion="6.0(1a)", arg_tversion="invalid_version")

    captured = capsys.readouterr()
    expected_output = """\
Gathering Node Information...

Current version is overridden to 6.0(1a)

Target APIC version is overridden to invalid_version

Parsing failure of ACI version `invalid_version`
"""
    assert captured.out.endswith(expected_output), "captured.out is:\n{}".format(captured.out)


@pytest.mark.parametrize("icurl_outputs", [_icurl_outputs])
def test_cversion_invald(capsys, mock_icurl):
    with pytest.raises(SystemExit):
        script.query_common_data(arg_cversion="invalid_version", arg_tversion="6.0(1a)")

    captured = capsys.readouterr()
    expected_output = """\
Gathering Node Information...

Current version is overridden to invalid_version

Parsing failure of ACI version `invalid_version`
"""
    assert captured.out.endswith(expected_output), "captured.out is:\n{}".format(captured.out)


@pytest.mark.parametrize(
    "icurl_outputs, print_output",
    [
        # `get_fabric_nodes()` failure
        (
            {
                "fabricNode.json": [{"error": {"attributes": {"code": "400", "text": "Request failed, unresolved class for dummyClass"}}}],
                "fabricNodePEp.json": _icurl_outputs["fabricNodePEp.json"],
            },
            "Gathering Node Information...\n\n",
        ),
        # `get_vpc_nodes()` failure
        (
            {
                "fabricNode.json": _icurl_outputs["fabricNode.json"],
                "fabricNodePEp.json": [{"error": {"attributes": {"code": "400", "text": "Request failed, unresolved class for dummyClass"}}}],
            },
            "Collecting VPC Node IDs...",
        ),
    ],
)
def test_icurl_failure_in_query_common_data(capsys, caplog, mock_icurl, print_output):
    caplog.set_level(logging.CRITICAL)
    with pytest.raises(SystemExit):
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
