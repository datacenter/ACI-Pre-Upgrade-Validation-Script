import os
import logging
import importlib
import yaml
from jinja2 import Environment, FileSystemLoader

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

j2_env = Environment(loader=FileSystemLoader("/".join([dir, "templates"])))
tmpl = j2_env.get_template("access_policy.j2")

params = {
    "nodes": [
        {"name": "L101", "ifp_name": "L101", "from": "101", "to": "101"},
        {"name": "L102", "ifp_name": "L102", "from": "102", "to": "102"},
        {"name": "L103", "ifp_name": "L103", "from": "103", "to": "103"},
        {"name": "L104", "ifp_name": "L104", "from": "104", "to": "104"},
        {"name": "L101-102", "ifp_name": "L101-102", "from": "101", "to": "102"},
        {"name": "L103-104", "ifp_name": "L103-104", "from": "103", "to": "104"},
    ],
    "ports": [
        {
            "ifp": "L101",
            "card": "1",
            "port": "1",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG1",
        },
        {
            "ifp": "L101",
            "card": "1",
            "port": "2",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG1",
        },
        {
            "ifp": "L101",
            "card": "1",
            "port": "3",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG2",
        },
        {
            "ifp": "L101",
            "card": "1",
            "port": "20",
            "ifpg_class": "infraAccBndlGrp",
            "ifpg_name": "IFPG_PC1",
        },
        {
            "ifp": "L101",
            "card": "1",
            "port": "30",
            "ifpg_class": "infraAccBndlGrp",
            "ifpg_name": "IFPG_VPC1",
        },
        {
            "ifp": "L102",
            "card": "1",
            "port": "1",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG1",
        },
        {
            "ifp": "L102",
            "card": "1",
            "port": "2",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG1",
        },
        {
            "ifp": "L102",
            "card": "1",
            "port": "3",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG2",
        },
        {
            "ifp": "L102",
            "card": "1",
            "port": "20",
            "ifpg_class": "infraAccBndlGrp",
            "ifpg_name": "IFPG_PC1",
        },
        {
            "ifp": "L102",
            "card": "1",
            "port": "21",
            "ifpg_class": "infraAccBndlGrp",
            "ifpg_name": "IFPG_PC2",
        },
        {
            "ifp": "L102",
            "card": "1",
            "port": "30",
            "ifpg_class": "infraAccBndlGrp",
            "ifpg_name": "IFPG_VPC1",
        },
        {
            "ifp": "L103",
            "card": "1",
            "port": "5",
            "ifpg_class": "infraBrkoutPortGrp",
            "ifpg_name": "system-breakout-25g-4x",
        },
        {
            "ifp": "L103",
            "card": "1",
            "port": "5",
            "subport": "1",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG2",
        },
        {
            "ifp": "L103",
            "card": "1",
            "port": "10",
            "ifpg_class": "infraFexBndlGrp",
            "ifpg_name": "FEX110",
            "fex": "110",
        },
        {
            "ifp": "L104",
            "card": "1",
            "port": "1",
            "ifpg_class": "infraAccBndlGrp",
            "ifpg_name": "IFPG_PC1",
        },
        {
            "fexp": "FEX110",
            "card": "1",
            "port": "20",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG1",
        },
        {
            "ifp": "L101-102",
            "card": "1",
            "port": "11",
            "ifpg_class": "infraAccBndlGrp",
            "ifpg_name": "IFPG_VPC2",
        },
        {
            "ifp": "L103-104",
            "card": "1",
            "port": "11",
            "ifpg_class": "infraAccBndlGrp",
            "ifpg_name": "IFPG_VPC3",
        },
    ],
    "override_ports": [
        {
            "node": "102",
            "path": "eth1/2",
            "ifpg_class": "infraAccPortGrp",
            "ifpg_name": "IFPG2",
        },
        {
            "node": "102",
            "path": "IFPG_PC2",
            "ifpg_class": "infraAccBndlPolGrp",
            "ifpg_name": "IFPG_PC_Override",
        },
    ],
    "ifpgs": [
        {
            "class": "infraAccPortGrp",
            "name": "IFPG1",
            "aep": "AEP1",
            "l2if": "default",
        },
        {
            "class": "infraAccPortGrp",
            "name": "IFPG2",
            "aep": "AEP2",
            "l2if": "VLAN_SCOPE_LOCAL",
        },
        {
            "class": "infraAccBndlGrp",
            "name": "IFPG_PC1",
            "aep": "AEP1",
            "lagT": "link",
            "l2if": "default",
        },
        {
            "class": "infraAccBndlGrp",
            "name": "IFPG_PC2",
            "aep": "AEP2",
            "lagT": "link",
            "l2if": "VLAN_SCOPE_LOCAL",
        },
        {
            "class": "infraAccBndlGrp",
            "name": "IFPG_VPC1",
            "aep": "AEP1",
            "lagT": "node",
            "l2if": "default",
        },
        {
            "class": "infraAccBndlGrp",
            "name": "IFPG_VPC2",
            "aep": "AEP2",
            "lagT": "node",
            "l2if": "VLAN_SCOPE_LOCAL",
        },
        {
            "class": "infraAccBndlGrp",
            "name": "IFPG_VPC3",
            "aep": "AEP2",
            "lagT": "node",
            "l2if": "VLAN_SCOPE_LOCAL",
        },
        {
            "class": "infraAccBndlPolGrp",
            "name": "IFPG_PC_Override",
            "aep": "AEP1",
            "l2if": "default",
        },
        {
            "class": "infraBrkoutPortGrp",
            "name": "system-breakout-25g-4x",
        },
        {
            "class": "infraFexBndlGrp",
            "name": "FEX110",
            "lagT": "link",
        },
    ],
    "aeps": ["AEP1", "AEP2"],
    "domains": [
        {"name": "PHYDOM1", "aeps": ["AEP1"]},
        {"name": "PHYDOM2", "aeps": ["AEP2"]},
        {"name": "PHYDOM3", "aeps": ["AEP1", "AEP2"]},
        {"name": "L3DOM1", "aeps": ["AEP1"], "class": "l3extDomP"},
        {"name": "VMMDOM1", "aeps": ["AEP1"], "class": "vmmDomP"},
    ],
    "vpools": [
        {
            "name": "VLANPool1",
            "mode": "dynamic",
            "vlan_ranges": [{"from": "2000", "to": "2010"}],
            "domains": [{"name": "PHYDOM1"}, {"name": "VMMDOM1", "class": "vmmDomP"}],
        },
        {
            "name": "VLANPool2",
            "mode": "static",
            "vlan_ranges": [{"from": "203", "to": "207"}],
            "domains": [{"name": "PHYDOM2"}],
        },
        {
            "name": "VLANPool3",
            "mode": "static",
            "vlan_ranges": [
                {"from": "200", "to": "205"},
                {"from": "2000", "to": "2010"},
            ],
            "domains": [{"name": "PHYDOM3"}, {"name": "L3DOM1", "class": "l3extDomP"}],
        },
        {
            "name": "VLANPool4",
            "mode": "dynamic",
            "vlan_ranges": [{"from": "410", "to": "415"}],
            "domains": [{"name": "PHYDOM4"}, {"name": "VMMDOM4", "class": "vmmDomP"}],
        },
    ],
}


def test_get_classes():
    all_classes = script.AciAccessPolicyParser.get_classes()
    assert sorted(all_classes) == sorted(
        [
            "fvnsVlanInstP",
            "fvnsEncapBlk",
            "infraAttEntityP",
            "infraAccPortP",
            "infraHPortS",
            "infraPortBlk",
            "infraSubPortBlk",
            "infraHPathS",
            "infraNodeP",
            "infraLeafS",
            "infraNodeBlk",
            "infraFexP",
            "infraFexBndlGrp",
            "infraAccPortGrp",
            "infraAccBndlGrp",
            "infraAccBndlPolGrp",
            "l2IfPol",
            "fvnsRtVlanNs",
            "infraRsDomP",
            "infraRsAttEntP",
            "infraRsAccBaseGrp",
            "infraRsPathToAccBaseGrp",
            "infraRsHPathAtt",
            "infraRsAccPortP",
            "l2RtL2IfPol",
        ]
    )


def test_basic():
    data_str = tmpl.render(params)
    infra_mos = yaml.safe_load(data_str)
    a = script.AciAccessPolicyParser(infra_mos)
    assert sorted(a.nodes_per_ifp.items()) == sorted(
        [
            ("uni/infra/accportprof-L101", [101]),
            ("uni/infra/accportprof-L102", [102]),
            ("uni/infra/accportprof-L101-102", [101, 102]),
            ("uni/infra/accportprof-L103", [103]),
            ("uni/infra/accportprof-L104", [104]),
            ("uni/infra/accportprof-L103-104", [103, 104]),
        ]
    )

    assert sorted(a.vpool_per_dom.items()) == sorted(
        [
            (
                "uni/phys-PHYDOM1",
                {
                    "vlan_ids": [
                        2000,
                        2001,
                        2002,
                        2003,
                        2004,
                        2005,
                        2006,
                        2007,
                        2008,
                        2009,
                        2010,
                    ],
                    "dom_type": "phys",
                    "name": "VLANPool1",
                    "dom_name": "PHYDOM1",
                },
            ),
            (
                "uni/phys-PHYDOM2",
                {
                    "vlan_ids": [203, 204, 205, 206, 207],
                    "dom_type": "phys",
                    "name": "VLANPool2",
                    "dom_name": "PHYDOM2",
                },
            ),
            (
                "uni/phys-PHYDOM3",
                {
                    "vlan_ids": [
                        200,
                        201,
                        202,
                        203,
                        204,
                        205,
                        2000,
                        2001,
                        2002,
                        2003,
                        2004,
                        2005,
                        2006,
                        2007,
                        2008,
                        2009,
                        2010,
                    ],
                    "dom_type": "phys",
                    "name": "VLANPool3",
                    "dom_name": "PHYDOM3",
                },
            ),
            (
                "uni/l3dom-L3DOM1",
                {
                    "vlan_ids": [
                        200,
                        201,
                        202,
                        203,
                        204,
                        205,
                        2000,
                        2001,
                        2002,
                        2003,
                        2004,
                        2005,
                        2006,
                        2007,
                        2008,
                        2009,
                        2010,
                    ],
                    "dom_type": "l3dom",
                    "name": "VLANPool3",
                    "dom_name": "L3DOM1",
                },
            ),
            (
                "uni/phys-PHYDOM4",
                {
                    "vlan_ids": [410, 411, 412, 413, 414, 415],
                    "dom_type": "phys",
                    "name": "VLANPool4",
                    "dom_name": "PHYDOM4",
                },
            ),
            (
                "uni/vmmp-VMware/dom-VMMDOM1",
                {
                    "vlan_ids": [
                        2000,
                        2001,
                        2002,
                        2003,
                        2004,
                        2005,
                        2006,
                        2007,
                        2008,
                        2009,
                        2010,
                    ],
                    "dom_type": "vmm",
                    "name": "VLANPool1",
                    "dom_name": "VMMDOM1",
                },
            ),
            (
                "uni/vmmp-VMware/dom-VMMDOM4",
                {
                    "vlan_ids": [410, 411, 412, 413, 414, 415],
                    "dom_type": "vmm",
                    "name": "VLANPool4",
                    "dom_name": "VMMDOM4",
                },
            ),
        ]
    )

    assert sorted(a.port_data.items()) == sorted(
        [
            (
                "101/IFPG_PC1",
                {
                    "node": "101",
                    "pc_type": "pc",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG_PC1",
                    "vlan_scope": "global",
                    "port": "IFPG_PC1",
                    "fex": "0",
                },
            ),
            (
                "101/IFPG_VPC1",
                {
                    "node": "101",
                    "pc_type": "vpc",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG_VPC1",
                    "vlan_scope": "global",
                    "port": "IFPG_VPC1",
                    "fex": "0",
                },
            ),
            (
                "101/IFPG_VPC2",
                {
                    "node": "101",
                    "pc_type": "vpc",
                    "domain_dns": [
                        "uni/phys-PHYDOM2",
                        "uni/phys-PHYDOM3",
                    ],
                    "aep_name": "AEP2",
                    "ifpg_name": "IFPG_VPC2",
                    "vlan_scope": "portlocal",
                    "port": "IFPG_VPC2",
                    "fex": "0",
                },
            ),
            (
                "101/eth1/1",
                {
                    "node": "101",
                    "pc_type": "none",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG1",
                    "vlan_scope": "global",
                    "port": "eth1/1",
                    "fex": "0",
                },
            ),
            (
                "101/eth1/2",
                {
                    "node": "101",
                    "pc_type": "none",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG1",
                    "vlan_scope": "global",
                    "port": "eth1/2",
                    "fex": "0",
                },
            ),
            (
                "101/eth1/3",
                {
                    "node": "101",
                    "pc_type": "none",
                    "domain_dns": [
                        "uni/phys-PHYDOM2",
                        "uni/phys-PHYDOM3",
                    ],
                    "aep_name": "AEP2",
                    "ifpg_name": "IFPG2",
                    "vlan_scope": "portlocal",
                    "port": "eth1/3",
                    "fex": "0",
                },
            ),
            (
                "102/IFPG_PC1",
                {
                    "node": "102",
                    "pc_type": "pc",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG_PC1",
                    "vlan_scope": "global",
                    "port": "IFPG_PC1",
                    "fex": "0",
                },
            ),
            (
                "102/IFPG_PC2",
                {
                    "node": "102",
                    "pc_type": "pc",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG_PC2",
                    "override_ifpg_name": "IFPG_PC_Override",
                    "vlan_scope": "global",
                    "port": "IFPG_PC2",
                    "fex": "0",
                },
            ),
            (
                "102/IFPG_VPC1",
                {
                    "node": "102",
                    "pc_type": "vpc",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG_VPC1",
                    "vlan_scope": "global",
                    "port": "IFPG_VPC1",
                    "fex": "0",
                },
            ),
            (
                "102/IFPG_VPC2",
                {
                    "node": "102",
                    "pc_type": "vpc",
                    "domain_dns": [
                        "uni/phys-PHYDOM2",
                        "uni/phys-PHYDOM3",
                    ],
                    "aep_name": "AEP2",
                    "ifpg_name": "IFPG_VPC2",
                    "vlan_scope": "portlocal",
                    "port": "IFPG_VPC2",
                    "fex": "0",
                },
            ),
            (
                "102/eth1/1",
                {
                    "node": "102",
                    "pc_type": "none",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG1",
                    "vlan_scope": "global",
                    "port": "eth1/1",
                    "fex": "0",
                },
            ),
            (
                "102/eth1/2",
                {
                    "node": "102",
                    "pc_type": "none",
                    "domain_dns": [
                        "uni/phys-PHYDOM2",
                        "uni/phys-PHYDOM3",
                    ],
                    "aep_name": "AEP2",
                    "ifpg_name": "IFPG1",
                    "override_ifpg_name": "IFPG2",
                    "vlan_scope": "portlocal",
                    "port": "eth1/2",
                    "fex": "0",
                },
            ),
            (
                "102/eth1/3",
                {
                    "node": "102",
                    "pc_type": "none",
                    "domain_dns": [
                        "uni/phys-PHYDOM2",
                        "uni/phys-PHYDOM3",
                    ],
                    "aep_name": "AEP2",
                    "ifpg_name": "IFPG2",
                    "vlan_scope": "portlocal",
                    "port": "eth1/3",
                    "fex": "0",
                },
            ),
            (
                "103/IFPG_VPC3",
                {
                    "node": "103",
                    "pc_type": "vpc",
                    "domain_dns": [
                        "uni/phys-PHYDOM2",
                        "uni/phys-PHYDOM3",
                    ],
                    "aep_name": "AEP2",
                    "ifpg_name": "IFPG_VPC3",
                    "vlan_scope": "portlocal",
                    "port": "IFPG_VPC3",
                    "fex": "0",
                },
            ),
            (
                "103/eth1/5",
                {
                    "node": "103",
                    "pc_type": "none",
                    "domain_dns": [],
                    "aep_name": "",
                    "ifpg_name": "system-breakout-25g-4x",
                    "vlan_scope": "unknown",
                    "port": "eth1/5",
                    "fex": "0",
                },
            ),
            (
                "103/eth1/5/1",
                {
                    "node": "103",
                    "pc_type": "none",
                    "domain_dns": [
                        "uni/phys-PHYDOM2",
                        "uni/phys-PHYDOM3",
                    ],
                    "aep_name": "AEP2",
                    "ifpg_name": "IFPG2",
                    "vlan_scope": "portlocal",
                    "port": "eth1/5/1",
                    "fex": "0",
                },
            ),
            (
                "103/eth1/10",
                {
                    "node": "103",
                    "pc_type": "pc",
                    "domain_dns": [],
                    "aep_name": "",
                    "ifpg_name": "FEX110",
                    "vlan_scope": "unknown",
                    "port": "eth1/10",
                    "fex": "0",
                },
            ),
            (
                "103/110/eth1/20",
                {
                    "node": "103",
                    "pc_type": "none",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG1",
                    "vlan_scope": "global",
                    "port": "eth1/20",
                    "fex": "110",
                },
            ),
            (
                "104/IFPG_PC1",
                {
                    "node": "104",
                    "pc_type": "pc",
                    "domain_dns": [
                        "uni/phys-PHYDOM1",
                        "uni/phys-PHYDOM3",
                        "uni/l3dom-L3DOM1",
                        "uni/vmmp-VMware/dom-VMMDOM1",
                    ],
                    "aep_name": "AEP1",
                    "ifpg_name": "IFPG_PC1",
                    "vlan_scope": "global",
                    "port": "IFPG_PC1",
                    "fex": "0",
                },
            ),
            (
                "104/IFPG_VPC3",
                {
                    "node": "104",
                    "pc_type": "vpc",
                    "domain_dns": [
                        "uni/phys-PHYDOM2",
                        "uni/phys-PHYDOM3",
                    ],
                    "aep_name": "AEP2",
                    "ifpg_name": "IFPG_VPC3",
                    "vlan_scope": "portlocal",
                    "port": "IFPG_VPC3",
                    "fex": "0",
                },
            ),
        ]
    )
