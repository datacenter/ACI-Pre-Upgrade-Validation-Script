import os
import copy
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "apic_oob_connectivity_check"

# icurl queries
topSystem = 'topSystem.json?query-target-filter=eq(topSystem.role,"controller")'
commHttps = "commHttps.json"
podPolicyGroups = 'fabricPodPGrp.json?rsp-subtree=children&rsp-subtree-class=fabricRsCommPol'
podProfiles = 'fabricPodP.json?rsp-subtree=full'
defaultHttps = 'uni/fabric/comm-default/https.json'

# headers returned only when the check reaches its final return (early MANUAL/NA/ERROR returns have no headers)
HEADERS = ["Node ID", "OOB IP", "Port", "Status"]

DEFAULT_POLICY_OUTPUTS = {
    podPolicyGroups: [
        {
            "fabricPodPGrp": {
                "attributes": {"dn": "uni/fabric/funcprof/podpgrp-default"},
                "children": [
                    {"fabricRsCommPol": {"attributes": {"tDn": "uni/fabric/comm-default"}}}
                ]
            }
        }
    ],
    defaultHttps: [
        {"commHttps": {"attributes": {"dn": "uni/fabric/comm-default/https", "port": "443"}}}
    ],
}


def custom_policy_outputs(port="8443"):
    outputs = {
        podPolicyGroups: [
            {
                "fabricPodPGrp": {
                    "attributes": {"dn": "uni/fabric/funcprof/podpgrp-default"},
                    "children": [
                        {"fabricRsCommPol": {"attributes": {"tDn": "uni/fabric/comm-default"}}}
                    ]
                }
            },
            {
                "fabricPodPGrp": {
                    "attributes": {"dn": "uni/fabric/funcprof/podpgrp-custom"},
                    "children": [
                        {"fabricRsCommPol": {"attributes": {"tDn": "uni/fabric/comm-custom"}}}
                    ]
                }
            },
        ],
        podProfiles: [
            {
                "fabricPodP": {
                    "attributes": {"dn": "uni/fabric/podprof-default"},
                    "children": [
                        {
                            "fabricPodS": {
                                "attributes": {"type": "ALL"},
                                "children": [
                                    {"fabricRsPodPGrp": {"attributes": {"tDn": "uni/fabric/funcprof/podpgrp-custom"}}}
                                ]
                            }
                        }
                    ]
                }
            }
        ],
        commHttps: [
            {"commHttps": {"attributes": {"dn": "uni/fabric/comm-default/https", "port": "443"}}},
            {"commHttps": {"attributes": {"dn": "uni/fabric/comm-custom/https", "port": port}}},
        ],
    }
    return outputs


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, connect_exit_codes, expected_result, expected_headers, expected_data",
    [
        # tversion not provided -> MANUAL
        (
            {topSystem: [], commHttps: []},
            "6.0(2a)",
            None,
            [],
            script.MANUAL,
            [],
            [],
        ),
        # Current version < 6.0(2a), even when the target is newer -> NA
        (
            {topSystem: [], commHttps: []},
            "5.2(7f)",
            "6.0(3a)",
            [],
            script.NA,
            [],
            [],
        ),
        # tversion = 6.0(1h), immediately below the 6.0(2a) gate -> NA
        (
            {topSystem: [], commHttps: []},
            "6.0(1h)",
            "6.0(1h)",
            [],
            script.NA,
            [],
            [],
        ),
        # Current version >= 6.0(2a), no controller nodes found -> ERROR
        (
            {topSystem: [], commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [],
            script.ERROR,
            HEADERS,
            [],
        ),
        # Missing OOB inventory must be investigated manually, not treated as reachable.
        (
            {topSystem: read_data(dir, "topSystem_no_oob.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [],
            script.MANUAL,
            HEADERS,
            [["1", "N/A", "443", "OOB address is not reported by APIC inventory"]],
        ),
        # The local APIC probe passes, but a multi-APIC mesh requires manual peer probes.
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 0, 0],
            script.MANUAL,
            HEADERS,
            [],
        ),
        # Default-policy local probes pass, but the peer mesh still requires manual probes.
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                commHttps: read_data(dir, "commHttps_default_port.json"),
            },
            "6.2(1g)",
            "6.2(2a)",
            [0, 0, 0],
            script.MANUAL,
            HEADERS,
            [],
        ),
        # A custom Pod Policy Group resolves each APIC to port 8443; peer probes are manual.
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                "_policy_outputs": custom_policy_outputs(),
            },
            "6.2(1g)",
            "6.2(2a)",
            [0, 0, 0],
            script.MANUAL,
            HEADERS,
            [],
        ),
        # commHttps is resolved regardless of its pre-6.x availability; peer probes are manual.
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                "_policy_outputs": custom_policy_outputs(),
            },
            "6.2(1f)",
            "6.2(2a)",
            [0, 0, 0],
            script.MANUAL,
            HEADERS,
            [],
        ),
        # tversion >= 6.0(2a), one APIC unreachable on port 443 (exit 28) -> FAIL_UF
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 28, 0],
            script.FAIL_UF,
            HEADERS,
            [["2", "10.30.10.191", "443", "Unreachable"]],
        ),
        # Default policy port 443, one APIC unreachable (exit 7) -> FAIL_UF
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
            },
            "6.2(1g)",
            "6.2(2a)",
            [0, 7, 0],
            script.FAIL_UF,
            HEADERS,
            [["2", "10.30.10.191", "443", "Unreachable"]],
        ),
        # Custom policy port 8443, all APICs unreachable -> FAIL_UF
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                "_policy_outputs": custom_policy_outputs(),
            },
            "6.2(1g)",
            "6.2(2a)",
            [28, 28, 28],
            script.FAIL_UF,
            HEADERS,
            [
                ["1", "10.30.10.189", "8443", "Unreachable"],
                ["2", "10.30.10.191", "8443", "Unreachable"],
                ["3", "10.30.10.193", "8443", "Unreachable"],
            ],
        ),
        # Resolved commHttps with an invalid port value -> ERROR
        (
            {
                topSystem: read_data(dir, "topSystem_3apics_oob.json"),
                "_policy_outputs": custom_policy_outputs("invalid"),
            },
            "6.2(1g)",
            "6.2(2a)",
            [],
            script.ERROR,
            HEADERS,
            [],
        ),
        # IPv6 OOB local probes pass, with manual mesh commands required.
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob_ipv6.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 0, 0],
            script.MANUAL,
            HEADERS,
            [],
        ),
        # IPv6 OOB, one APIC unreachable (exit 28) -> FAIL_UF
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob_ipv6.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 28, 0],
            script.FAIL_UF,
            HEADERS,
            [["2", "2001:db8::2", "443", "Unreachable"]],
        ),
        # Both IPv4 and IPv6 configured: IPv4 is used, with manual mesh commands required.
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob_both.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 0, 0],
            script.MANUAL,
            HEADERS,
            [],
        ),
        # Both IPv4 and IPv6 configured, one unreachable -> FAIL_UF (IPv4 should be used)
        (
            {topSystem: read_data(dir, "topSystem_3apics_oob_both.json"), commHttps: []},
            "6.0(2a)",
            "6.0(3a)",
            [0, 28, 0],
            script.FAIL_UF,
            HEADERS,
            [["2", "10.30.10.191", "443", "Unreachable"]],
        ),
    ],
)
def test_logic(run_check, mock_icurl, monkeypatch, icurl_outputs, cversion, tversion, connect_exit_codes, expected_result, expected_headers, expected_data):
    policy_outputs = icurl_outputs.pop("_policy_outputs", DEFAULT_POLICY_OUTPUTS)
    for query, output in policy_outputs.items():
        icurl_outputs[query] = copy.deepcopy(output)
    idx = [0]

    class FakeSocket:
        def __init__(self, family, type_):
            self.family = family

        def settimeout(self, timeout):
            pass

        def connect_ex(self, address):
            host, port = address
            # IPv6 addresses must be passed raw (no brackets) to socket.connect_ex
            assert not host.startswith('['), "IPv6 address must not be bracketed for connect_ex, got: {}".format(host)
            expected_family = script.socket.AF_INET6 if ':' in host else script.socket.AF_INET
            assert self.family == expected_family
            if idx[0] >= len(connect_exit_codes):
                raise AssertionError("Unexpected connection attempt to {}:{}".format(host, port))
            code = connect_exit_codes[idx[0]]
            idx[0] += 1
            return code

        def close(self):
            pass

    monkeypatch.setattr(script.socket, "socket", lambda family, type_: FakeSocket(family, type_))
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.headers == expected_headers
    assert result.data == expected_data
    assert idx[0] == len(connect_exit_codes)


def test_manual_mesh_commands(run_check, mock_icurl, monkeypatch, icurl_outputs):
    icurl_outputs[topSystem] = read_data(dir, "topSystem_3apics_oob.json")
    icurl_outputs.update(copy.deepcopy(DEFAULT_POLICY_OUTPUTS))

    class FakeSocket:
        def __init__(self, family, type_):
            pass

        def settimeout(self, timeout):
            pass

        def connect_ex(self, address):
            return 0

        def close(self):
            pass

    monkeypatch.setattr(script.socket, "socket", lambda family, type_: FakeSocket(family, type_))

    result = run_check(
        cversion=script.AciVersion("6.0(2a)"),
        tversion=script.AciVersion("6.0(3a)"),
    )

    assert result.result == script.MANUAL
    assert "On APIC node 1: curl --max-time 5 -k -s -o /dev/null https://10.30.10.191:443" in result.msg
    assert "On APIC node 3: curl --max-time 5 -k -s -o /dev/null https://10.30.10.191:443" in result.msg
