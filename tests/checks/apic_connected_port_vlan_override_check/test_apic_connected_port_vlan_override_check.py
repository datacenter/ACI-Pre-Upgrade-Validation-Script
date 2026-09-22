import importlib

import pytest


script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "apic_connected_port_vlan_override_check"

lldp_inst_api = 'lldpInst.json?query-target-filter=wcard(lldpInst.dn,"/node-1/")'
controller_adjacency_api = 'lldpCtrlrAdjEp.json'
path_attachment_api = 'fvRsPathAtt.json'

APIC_PORT = ("1", "101", "eth1/1")
EPG_DN = "uni/tn-example/ap-app/epg-web"
PATH_ATTACHMENT_DN = EPG_DN + "/rspathAtt-[topology/pod-1/paths-101/pathep-[eth1/1]]"


def lldp_inst(infra_vlan="vlan-3967"):
    return {
        "lldpInst": {
            "attributes": {
                "dn": "topology/pod-1/node-1/sys/lldp/inst",
                "infraVlan": infra_vlan,
            }
        }
    }


def controller_adjacency(pod="1", node="101", port="eth1/1"):
    return {
        "lldpCtrlrAdjEp": {
            "attributes": {
                "dn": "topology/pod-{}/node-{}/sys/lldp/inst/if-[{}]/ctrlrAdj-1".format(pod, node, port),
                "id": "1",
            }
        }
    }


def path_attachment(dn=PATH_ATTACHMENT_DN, tdn="topology/pod-1/paths-101/pathep-[eth1/1]", encap="vlan-3967"):
    return {
        "fvRsPathAtt": {
            "attributes": {
                "dn": dn,
                "tDn": tdn,
                "encap": encap,
            }
        }
    }


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_data",
    [
        (
            {
                lldp_inst_api: [lldp_inst()],
                controller_adjacency_api: [controller_adjacency()],
                path_attachment_api: [path_attachment()],
            },
            script.FAIL_UF,
            [list(APIC_PORT) + [EPG_DN, "vlan-3967", "3967", PATH_ATTACHMENT_DN]],
        ),
        (
            {
                lldp_inst_api: [lldp_inst()],
                controller_adjacency_api: [controller_adjacency()],
                path_attachment_api: [path_attachment(tdn="topology/pod-1/paths-102/pathep-[eth1/1]")],
            },
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, icurl_outputs, expected_result, expected_data):
    result = run_check()

    assert result.result == expected_result
    assert result.data == expected_data
    assert result.headers == ["Pod", "Node", "Port", "EPG", "Configured VLAN", "InfraVLAN", "Configuration DN"]


@pytest.mark.parametrize("icurl_outputs", [{lldp_inst_api: []}])
def test_returns_error_when_infravlan_cannot_be_determined(run_check, mock_icurl, icurl_outputs):
    result = run_check()

    assert result.result == script.ERROR
    assert result.msg == "Unable to determine InfraVLAN from lldpInst."
