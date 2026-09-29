import importlib

import pytest


script = importlib.import_module("aci-preupgrade-validation-script")
test_function = "nxos_ipn_multicast_rpf_defect_check"

OSPF_QUERY = 'ospfAdjEp.json?query-target-filter=wcard(ospfAdjEp.dn,"/dom-overlay-1/")'
LLDP_QUERY = 'lldpAdjEp.json?query-target-filter=wcard(lldpAdjEp.dn,"topology/pod-1/node-201/sys/lldp/inst/if-")'
CDP_QUERY = 'cdpAdjEp.json?query-target-filter=wcard(cdpAdjEp.dn,"topology/pod-1/node-201/sys/cdp/inst/if-")'


def spine(pod, node):
    return {"fabricNode": {"attributes": {
        "dn": "topology/pod-{}/node-{}".format(pod, node),
        "role": "spine", "fabricSt": "active", "name": "spine-{}".format(node),
    }}}


def ospf(port="eth1/31.31", pod=1, node=201, domain="overlay-1"):
    return {"ospfAdjEp": {"attributes": {
        "dn": "topology/pod-{}/node-{}/sys/ospf/inst-default/dom-{}/if-[{}]/adj-22.22.22.21".format(
            pod, node, domain, port),
    }}}


def lldp(version, port="eth1/31", name="ipn-1"):
    description = "Cisco Nexus Operating System (NX-OS) Software {}".format(version)
    return {"lldpAdjEp": {"attributes": {
        "dn": "topology/pod-1/node-201/sys/lldp/inst/if-[{}]/adj-1".format(port),
        "sysName": name, "sysDesc": description,
    }}}


def cdp(version, port="eth1/31", platform="N9K-C9504", name="ipn-1"):
    description = "Cisco Nexus Operating System (NX-OS) Software, Version {}".format(version)
    return {"cdpAdjEp": {"attributes": {
        "dn": "topology/pod-1/node-201/sys/cdp/inst/if-[{}]/adj-1".format(port),
        "sysName": name, "platId": platform, "ver": description,
    }}}


@pytest.fixture
def fabric_nodes():
    return [spine(1, 201), spine(2, 202)]


@pytest.fixture
def icurl_outputs():
    return {OSPF_QUERY: [ospf()], LLDP_QUERY: [], CDP_QUERY: []}


def test_affected_lldp_release_is_manual(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[LLDP_QUERY] = [lldp("10.5(4)")]

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.MANUAL
    assert result.data == [["1", "spine-201", "eth1/31", "ipn-1", "-", "10.5(4)",
                            "LLDP", "Listed as unpatched in CSCwt59437"]]


def test_affected_106_release_from_cdp_is_manual(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[CDP_QUERY] = [cdp("10.6(2s)")]

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.MANUAL
    assert result.data[0][4:7] == ["N9K-C9504", "10.6(2s)", "CDP"]


@pytest.mark.parametrize("version, expected, assessment", [
    ("10.5(2)", script.MANUAL, "10.5(2) is not listed as unpatched in CSCwt59437; verify manually"),
    ("10.5(4a)", script.MANUAL, "Release variant is not individually listed in CSCwt59437"),
    ("10.5(4)SMU(1)", script.MANUAL, "Release variant is not individually listed in CSCwt59437"),
    ("10.5(4)SMU(16)", script.PASS, None),
    ("10.5(5.28)", script.PASS, None),
    ("10.6(2n)", script.MANUAL, "Listed as unpatched in CSCwt59437"),
    ("10.6(3)", script.PASS, None),
    ("10.5(6)", script.PASS, None),
    ("10.3(1)", script.PASS, None),
])
def test_release_classification(run_check, mock_icurl, fabric_nodes, icurl_outputs,
                                version, expected, assessment):
    icurl_outputs[LLDP_QUERY] = [lldp(version)]

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == expected
    assert (result.data[0][-1] if result.data else None) == assessment


def test_lldp_and_cdp_are_deduplicated(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[LLDP_QUERY] = [lldp("10.5(5)")]
    icurl_outputs[CDP_QUERY] = [cdp("10.5(5)")]

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.MANUAL
    assert len(result.data) == 1
    assert result.data[0][4:7] == ["N9K-C9504", "10.5(5)", "CDP/LLDP"]


def test_only_ospf_facing_physical_port_is_used(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[LLDP_QUERY] = [lldp("10.5(4)", port="eth1/32"), lldp("10.6(3)")]

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.PASS
    assert result.data == []


def test_missing_neighbor_data_is_inconclusive(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.MANUAL
    assert "No LLDP/CDP neighbor data" in result.data[0][-1]


def test_missing_nxos_version_is_inconclusive(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[LLDP_QUERY] = [lldp("")]

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.MANUAL
    assert result.data[0][5] == "-"
    assert "version could not be read" in result.data[0][-1]


def test_blank_lldp_description_is_inconclusive(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[LLDP_QUERY] = [lldp("")]
    icurl_outputs[LLDP_QUERY][0]["lldpAdjEp"]["attributes"]["sysDesc"] = ""

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.MANUAL
    assert "version could not be read" in result.data[0][-1]


def test_conflicting_neighbor_versions_are_reported(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[LLDP_QUERY] = [lldp("10.5(4)")]
    icurl_outputs[CDP_QUERY] = [cdp("10.5(6)")]

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.MANUAL
    assert any("conflicting" in row[-1] for row in result.data)
    assert any("10.5(4)" in row[5] for row in result.data)


def test_non_n9k_cdp_peer_does_not_trigger(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[CDP_QUERY] = [cdp("10.5(4)", platform="N3K-C3172")]

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.PASS


def test_no_ospf_adj_is_inconclusive(run_check, mock_icurl, fabric_nodes, icurl_outputs):
    icurl_outputs[OSPF_QUERY] = []

    result = run_check(fabric_nodes=fabric_nodes)

    assert result.result == script.MANUAL
    assert "No spine overlay OSPF adjacency" in result.msg


def test_single_pod_is_not_applicable(run_check, mock_icurl, icurl_outputs):
    result = run_check(fabric_nodes=[spine(1, 201), spine(1, 202)])

    assert result.result == script.NA
    assert result.data == []
