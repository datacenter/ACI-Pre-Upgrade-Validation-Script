import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "fx3_breakout_port_check"

BRKOUT_QUERY = "eqptBrkoutP.json"
FCOT_QUERY = (
    'ethpmFcot.json?query-target-filter=or('
    'and(wcard(ethpmFcot.guiName,"CISCO-INNOLIGHT"),eq(ethpmFcot.guiCiscoEID,"QSFP-100G-SR4")),'
    'and(wcard(ethpmFcot.guiName,"CISCO-INNOLIGHT"),wcard(ethpmFcot.guiCiscoEID,"QSFP-100G-AOC"))'
    ')'
)

FX3_NODES = read_data(dir, "fabricNode_fx3.json")
NON_FX3_NODES = read_data(dir, "fabricNode_non_fx3.json")

# Breakout on node101/leafport49 (+ ignored brkoutport-2 leg), node101/leafport51,
# and node102/leafport50. Reused across every scenario that needs breakout config;
# ethpmFcot/l1PhysIf fixtures control which of these ports actually get flagged.
ALL_BRKOUT_PORTS = read_data(dir, "eqptBrkoutP_all_breakout_ports.json")

FAIL_MSG = "Affected breakout transceivers with FEC not disabled found. This may cause an outage during the leaf upgrade."


def l1physif_query(legs):
    """Build the exact l1PhysIf query string for the given legs.

    `legs` is a list of (pod, node_id, intf_name) tuples in the order they are
    expected to be inserted into `first_leg_per_port` (i.e. the order of their
    first occurrence in the mocked ethpmFcot data).
    """
    dn_filter = ",".join(
        'eq(l1PhysIf.dn,"topology/pod-{}/node-{}/sys/phys-[{}]")'.format(pod, node_id, intf)
        for pod, node_id, intf in legs
    )
    return (
        'l1PhysIf.json?query-target-filter=and(ne(l1PhysIf.fecMode,"disable-fec"),'
        'eq(l1PhysIf.adminSt,"up"),or({}))'
    ).format(dn_filter)


@pytest.mark.parametrize(
    "cversion, tversion, fabric_nodes, icurl_outputs, expected_result, expected_msg, expected_data",
    [
        # Target version not supplied
        (
            "5.2(8g)", None, FX3_NODES, {},
            script.MANUAL, script.TVER_MISSING, [],
        ),
        # cversion already fixed (not older than 5.2(8h))
        (
            "5.2(8h)", "5.3(2a)", FX3_NODES, {},
            script.NA, script.VER_NOT_AFFECTED, [],
        ),
        # tversion not newer than 5.3(1a)
        (
            "5.2(8g)", "5.3(1a)", FX3_NODES, {},
            script.NA, script.VER_NOT_AFFECTED, [],
        ),
        # tversion at/after the fixed 6.1(6a) release, and not the 6.2(1g) exception
        (
            "5.2(8g)", "6.1(6a)", FX3_NODES, {},
            script.NA, script.VER_NOT_AFFECTED, [],
        ),
        # tversion exactly 6.2(1g) is still affected despite being newer than 6.1(6a)
        (
            "5.2(8g)", "6.2(1g)",
            FX3_NODES,
            {BRKOUT_QUERY: read_data(dir, "eqptBrkoutP_none.json")},
            script.PASS, "No breakout configuration found on ports 49-52 of YC-FX3/TC-FX3 switches.", [],
        ),
        # Affected versions, no YC-FX3/TC-FX3 switches in the fabric
        (
            "5.2(8g)", "5.3(2a)", NON_FX3_NODES, {},
            script.NA, "No YC-FX3/TC-FX3 switches found. Skipping.", [],
        ),
        # Affected versions, FX3 switches present, but no breakout config on ports 49-52
        (
            "5.2(8g)", "5.3(2a)",
            FX3_NODES,
            {BRKOUT_QUERY: read_data(dir, "eqptBrkoutP_none.json")},
            script.PASS, "No breakout configuration found on ports 49-52 of YC-FX3/TC-FX3 switches.", [],
        ),
        # Breakout configured, but not on ports 49-52
        (
            "5.2(8g)", "5.3(2a)",
            FX3_NODES,
            {BRKOUT_QUERY: read_data(dir, "eqptBrkoutP_port_not_in_range.json")},
            script.PASS, "No breakout configuration found on ports 49-52 of YC-FX3/TC-FX3 switches.", [],
        ),
        # Breakout on port 49, but no matching Innolight SR4/AOC transceiver found
        (
            "5.2(8g)", "5.3(2a)",
            FX3_NODES,
            {
                BRKOUT_QUERY: ALL_BRKOUT_PORTS,
                FCOT_QUERY: read_data(dir, "ethpmFcot_none.json"),
            },
            script.PASS, "No affected breakout transceivers found on ports 49-52 of YC-FX3/TC-FX3 switches.", [],
        ),
        # Matching transceiver on brkoutport-1, but FEC is already disabled
        (
            "5.2(8g)", "5.3(2a)",
            FX3_NODES,
            {
                BRKOUT_QUERY: ALL_BRKOUT_PORTS,
                FCOT_QUERY: read_data(dir, "ethpmFcot_node101_port49_sr4.json"),
                l1physif_query([(1, 101, "eth1/49/1")]): read_data(dir, "l1PhysIf_none.json"),
            },
            script.PASS, "", [],
        ),
        # Matching transceiver, FEC not disabled -> outage risk.
        (
            "5.2(8g)", "5.3(2a)",
            FX3_NODES,
            {
                BRKOUT_QUERY: ALL_BRKOUT_PORTS,
                FCOT_QUERY: read_data(dir, "ethpmFcot_node101_port49_sr4.json"),
                l1physif_query([(1, 101, "eth1/49/1")]): read_data(dir, "l1PhysIf_node101_port49_fec_enabled.json"),
            },
            script.FAIL_O, FAIL_MSG,
            [["1", "101", "leaf101", "N9K-C93180YC-FX3", "eth1/49/1", "QSFP-100G-SR4", "cl91-fec"]],
        ),
        # Matching transceiver, FEC not disabled, but the interface is admin down
        # -> the adminSt="up" filter excludes it from the (mocked) API response.
        (
            "5.2(8g)", "5.3(2a)",
            FX3_NODES,
            {
                BRKOUT_QUERY: ALL_BRKOUT_PORTS,
                FCOT_QUERY: read_data(dir, "ethpmFcot_node101_port49_sr4.json"),
                l1physif_query([(1, 101, "eth1/49/1")]): read_data(dir, "l1PhysIf_admin_down.json"),
            },
            script.PASS, "", [],
        ),
        # AOC transceiver variant (guiCiscoEID prefix match) is also flagged
        (
            "5.2(8g)", "5.3(2a)",
            FX3_NODES,
            {
                BRKOUT_QUERY: ALL_BRKOUT_PORTS,
                FCOT_QUERY: read_data(dir, "ethpmFcot_node101_port51_aoc.json"),
                l1physif_query([(1, 101, "eth1/51/1")]): read_data(dir, "l1PhysIf_node101_port51_fec_enabled.json"),
            },
            script.FAIL_O, FAIL_MSG,
            [["1", "101", "leaf101", "N9K-C93180YC-FX3", "eth1/51/1", "QSFP-100G-AOC3M", "cl91-fec"]],
        ),
        # Two breakout ports (49, 51) on the same node, plus a second node (50)
        # -- this single case also covers the "multiple nodes both affected" scenario,
        # -> each port reported once; the extra brkoutport-2 leg on node 101's
        # port 49 is ignored, since only brkoutport-1 is affected.
        (
            "5.2(8g)", "5.3(2a)",
            FX3_NODES,
            {
                BRKOUT_QUERY: ALL_BRKOUT_PORTS,
                FCOT_QUERY: read_data(dir, "ethpmFcot_same_node_two_ports.json"),
                l1physif_query([(1, 101, "eth1/49/1"), (1, 101, "eth1/51/1"), (1, 102, "eth1/50/1")]): read_data(
                    dir, "l1PhysIf_same_node_two_ports.json"
                ),
            },
            script.FAIL_O, FAIL_MSG,
            [
                ["1", "101", "leaf101", "N9K-C93180YC-FX3", "eth1/49/1", "QSFP-100G-SR4", "cl91-fec"],
                ["1", "101", "leaf101", "N9K-C93180YC-FX3", "eth1/51/1", "QSFP-100G-AOC3M", "cl74-fec"],
                ["1", "102", "leaf102", "N9K-C93108TC-FX3", "eth1/50/1", "QSFP-100G-SR4", "cl91-fec"],
            ],
        ),
    ],
)
def test_logic(
    run_check, mock_icurl, cversion, tversion, fabric_nodes, expected_result, expected_msg, expected_data
):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.msg == expected_msg
    assert result.data == expected_data
