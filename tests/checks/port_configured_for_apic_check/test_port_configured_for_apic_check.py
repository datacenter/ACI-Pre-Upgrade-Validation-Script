import importlib

import pytest


script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "port_configured_for_apic_check"

fault_api = 'faultInst.json?&query-target-filter=wcard(faultInst.changeSet,"port-configured-for-apic")'
controller_adjacency_api = 'lldpCtrlrAdjEp.json'
path_attachment_api = 'fvRsPathAtt.json'

APIC_PORT = ("1", "101", "eth1/1")
EPG_DN = "uni/tn-example/ap-app/epg-web"
PATH_ATTACHMENT_DN = EPG_DN + "/rspathAtt-[topology/pod-1/paths-101/pathep-[eth1/1]]"


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


def apic_fault():
    return {
        "faultInst": {
            "attributes": {
                "code": "F0467",
                "dn": "topology/pod-1/node-101/local/svc-policyelem-id-0/uni/epp/fv-[{}]/node-101/stpathatt-[eth1/1]/nwissues/fault-F0467".format(EPG_DN),
            }
        }
    }


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_data",
    [
        (
            {
                fault_api: [],
                controller_adjacency_api: [controller_adjacency()],
                path_attachment_api: [path_attachment()],
            },
            script.FAIL_UF,
            [["Tenant static path attachment", *APIC_PORT, EPG_DN, "vlan-3967", PATH_ATTACHMENT_DN]],
        ),
        (
            {
                fault_api: [apic_fault()],
                controller_adjacency_api: [controller_adjacency()],
                path_attachment_api: [path_attachment()],
            },
            script.FAIL_UF,
            [["F0467", *APIC_PORT, EPG_DN, "vlan-3967", PATH_ATTACHMENT_DN]],
        ),
        (
            {
                fault_api: [],
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
    assert result.headers == ["Finding", "Pod", "Node", "Port", "EPG", "VLAN", "Configuration DN"]
