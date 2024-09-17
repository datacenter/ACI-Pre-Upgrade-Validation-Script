import os
import pytest
import logging
import importlib
import json
from jinja2 import Environment, FileSystemLoader
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

j2_env = Environment(loader=FileSystemLoader("/".join([dir, "templates"])))
tmpl = {
    "infra": j2_env.get_template("access_policy.j2"),
    "epg": j2_env.get_template("fvAEPg.j2"),
    "ifconn": j2_env.get_template("fvIfConn.j2"),
}

base_params = {
    "nodes": [
        {"name": "L101", "ifp_name": "L101", "from": "101", "to": "101"},
        {"name": "L102", "ifp_name": "L102", "from": "102", "to": "102"},
        {"name": "L103", "ifp_name": "L103", "from": "103", "to": "103"},
        {"name": "L104", "ifp_name": "L104", "from": "104", "to": "104"},
        {"name": "L101-102", "ifp_name": "L101-102", "from": "101", "to": "102"},
        {"name": "L103-104", "ifp_name": "L103-104", "from": "103", "to": "104"},
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
            "name": "IFPG1_local",
            "aep": "AEP1",
            "l2if": "VLAN_SCOPE_LOCAL",
        },
        {
            "class": "infraAccPortGrp",
            "name": "IFPG2",
            "aep": "AEP2",
            "l2if": "default",
        },
        {
            "class": "infraAccPortGrp",
            "name": "IFPG2_local",
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
            "name": "IFPG_PC1_local",
            "aep": "AEP1",
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
            "name": "IFPG_VPC1_local",
            "aep": "AEP1",
            "lagT": "node",
            "l2if": "VLAN_SCOPE_LOCAL",
        },
        {
            "class": "infraAccBndlGrp",
            "name": "IFPG_VPC2",
            "aep": "AEP2",
            "lagT": "node",
            "l2if": "default",
        },
        {
            "class": "infraBrkoutPortGrp",
            "name": "system-breakout-25g-4x",
        },
        {
            "class": "infraFexBndlGrp",
            "name": "FEX101",
            "lagT": "link",
        },
    ],
    "aeps": ["AEP1", "AEP2"],
}
params = [
    {
        "id": "one_port_multiple_pools",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/24",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "one_port_multiple_pools_local",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/24",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1_local",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "one_port_multiple_pools_fex",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "fex": "101",
                        "port": "eth1/24",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "10",
                "ifpg_class": "infraFexBndlGrp",
                "ifpg_name": "FEX101",
                "fex": "101",
            },
            {
                "fexp": "FEX101",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "one_port_multiple_pools_breakout",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/24/1",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraBrkoutPortGrp",
                "ifpg_name": "system-breakout-25g-4x",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "24",
                "subport": "1",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "one_port_multiple_pools_pc",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "IFPG_PC1",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_PC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "25",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_PC1",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "one_port_multiple_pools_vpc",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "one_port_one_pool_two_domains_vpc",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "one_port_two_pools_three_domains_vpc",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}, {"name": "PHYDOM3"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
            {"name": "PHYDOM3", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "1000", "to": "1050"}],
                "domains": [{"name": "PHYDOM3"}],
            },
        ],
    },
    {
        "id": "one_port_two_pools_three_domains_vpc2",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}, {"name": "PHYDOM3"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
            {"name": "PHYDOM3", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM3"}],
            },
        ],
    },
    {
        "id": "one_port_multiple_pools_vpc_local",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1_local",
                        "vlan": "2011",
                    }
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "24",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1_local",
            }
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_for_each",
        "result": script.MANUAL,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
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
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_for_each_one_local",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_for_each_both_local",
        "result": script.MANUAL,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2_local",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_for_each_vpc",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_for_each_vpc_one_local",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2_local",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_for_each_vpc_both_local",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1_local",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2_local",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools",
        "result": script.MANUAL,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
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
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_one_local",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_both_local",
        "result": script.MANUAL,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2_local",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_pc",
        "result": script.MANUAL,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "IFPG_PC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_PC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_pc_one_local",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "IFPG_PC1_local",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_PC1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_pc_one_local2",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "IFPG_PC1_local",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_PC1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1", "AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_pc_both_local",
        "result": script.MANUAL,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101",
                        "port": "IFPG_PC1_local",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_PC1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2_local",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_vpc",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_two_domains_vpc",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_vpc_one_local",
        "result": script.MANUAL,
        "num_bad_ports": 1,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1_local",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_vpc_one_local2",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1_local",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1", "AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_vpc_both_local",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1_local",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1_local",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2_local",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_vpc_dy",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "VMMDOM1", "class": "vmmDomP"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "dynamic",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "VMMDOM1", "aeps": ["AEP1", "AEP2"], "class": "vmmDomP"},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "dynamic",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "VMMDOM1", "class": "vmmDomP"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_two_domains_vpc_dy",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "VMMDOM1", "class": "vmmDomP"}, {"name": "VMMDOM2", "class": "vmmDomP"}],
                "bindings": [
                    {
                        "type": "dynamic",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "dynamic",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "VMMDOM1", "aeps": ["AEP1", "AEP2"], "class": "vmmDomP"},
            {"name": "VMMDOM2", "aeps": ["AEP1", "AEP2"], "class": "vmmDomP"},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "dynamic",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "VMMDOM1", "class": "vmmDomP"}, {"name": "VMMDOM2", "class": "vmmDomP"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_two_domains_vpc_dy2",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "VMMDOM1", "class": "vmmDomP"}, {"name": "VMMDOM2", "class": "vmmDomP"}],
                "bindings": [
                    {
                        "type": "dynamic",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "dynamic",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2012",
                    },
                    {
                        "type": "dynamic",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "VMMDOM1", "aeps": ["AEP1", "AEP2"], "class": "vmmDomP"},
            {"name": "VMMDOM2", "aeps": ["AEP1", "AEP2"], "class": "vmmDomP"},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "dynamic",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "VMMDOM1", "class": "vmmDomP"}, {"name": "VMMDOM2", "class": "vmmDomP"}],
            },
        ],
    },
    {
        "id": "two_ports_multiple_pools_vpc_aep",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "aep",
                        "aep": "AEP1",
                        "node": "101-102",
                        "vlan": "2011",
                    },
                    {
                        "type": "aep",
                        "aep": "AEP2",
                        "node": "101",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_one_pool_two_domains_vpc_aep",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "aep",
                        "aep": "AEP1",
                        "node": "101-102",
                        "vlan": "2011",
                    },
                    {
                        "type": "aep",
                        "aep": "AEP2",
                        "node": "101",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP1", "AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
            },
        ],
    },
    {
        "id": "two_ports_two_pools_three_domains_vpc_aep",
        "result": script.PASS,
        "num_bad_ports": 0,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}, {"name": "PHYDOM3"}],
                "bindings": [
                    {
                        "type": "aep",
                        "aep": "AEP1",
                        "node": "101-102",
                        "vlan": "2011",
                    },
                    {
                        "type": "aep",
                        "aep": "AEP2",
                        "node": "103",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
            {"name": "PHYDOM3", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM3"}],
            },
        ],
    },
    {
        "id": "two_ports_two_pools_three_domains_vpc_aep2",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}, {"name": "PHYDOM3"}],
                "bindings": [
                    {
                        "type": "aep",
                        "aep": "AEP1",
                        "node": "101-102",
                        "vlan": "2011",
                    },
                    {
                        "type": "aep",
                        "aep": "AEP2",
                        "node": "101",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
            {"name": "PHYDOM3", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM3"}],
            },
        ],
    },
    {
        "id": "two_ports_three_pools_three_domains_vpc_aep3",
        "result": script.FAIL_O,
        "num_bad_ports": 2,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}, {"name": "PHYDOM3"}],
                "bindings": [
                    {
                        "type": "aep",
                        "aep": "AEP1",
                        "node": "101-102",
                        "vlan": "2011",
                    },
                    {
                        "type": "aep",
                        "aep": "AEP2",
                        "node": "101",
                        "vlan": "2011",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1"]},
            {"name": "PHYDOM2", "aeps": ["AEP1"]},
            {"name": "PHYDOM3", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "1000", "to": "1020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
            {
                "name": "VLANPool3",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM3"}],
            },
        ],
    },
    {
        "id": "multiple_nodes_epgs",
        "result": script.FAIL_O,
        "num_bad_ports": 8,
        "epgs": [
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG1",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "101",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "102",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "103",
                        "port": "eth1/1",
                        "vlan": "2011",
                    },
                    {
                        "type": "static",
                        "node": "103",
                        "port": "eth1/2",
                        "vlan": "2011",
                    },
                ],
            },
            {
                "tenant": "TN1",
                "ap": "AP1",
                "epg": "EPG2",
                "domains": [{"name": "PHYDOM1"}, {"name": "PHYDOM2"}],
                "bindings": [
                    {
                        "type": "static",
                        "node": "101-102",
                        "port": "IFPG_VPC1",
                        "vlan": "2012",
                    },
                    {
                        "type": "static",
                        "node": "102",
                        "port": "eth1/2",
                        "vlan": "2012",
                    },
                    {
                        "type": "static",
                        "node": "103",
                        "port": "eth1/1",
                        "vlan": "2012",
                    },
                    {
                        "type": "static",
                        "node": "103",
                        "port": "eth1/2",
                        "vlan": "2012",
                    },
                    {
                        "type": "static",
                        "node": "103-104",
                        "port": "IFPG_VPC2",
                        "vlan": "2012",
                    },
                ],
            }
        ],
        "ports": [
            {
                "ifp": "L101-102",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC1",
            },
            {
                "ifp": "L101",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
            {
                "ifp": "L102",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1",
            },
            {
                "ifp": "L103",
                "card": "1",
                "port": "1",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG1",
            },
            {
                "ifp": "L103",
                "card": "1",
                "port": "2",
                "ifpg_class": "infraAccPortGrp",
                "ifpg_name": "IFPG2",
            },
            {
                "ifp": "L103-104",
                "card": "1",
                "port": "3",
                "ifpg_class": "infraAccBndlGrp",
                "ifpg_name": "IFPG_VPC2",
            },
        ],
        "domains": [
            {"name": "PHYDOM1", "aeps": ["AEP1", "AEP2"]},
            {"name": "PHYDOM2", "aeps": ["AEP2"]},
        ],
        "vpools": [
            {
                "name": "VLANPool1",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2050"}],
                "domains": [{"name": "PHYDOM1"}],
            },
            {
                "name": "VLANPool2",
                "mode": "static",
                "vlan_ranges": [{"from": "2000", "to": "2020"}],
                "domains": [{"name": "PHYDOM2"}],
            },
        ],
    },
]


def input(param):
    param.update(base_params)
    data = {}
    for key in tmpl:
        data_str = tmpl[key].render(param)
        data[key] = json.loads(data_str)
    return (
        {
            infraSetPol: read_data(dir, "infraSetPol_no.json"),
            infra: data["infra"],
            epgs: data["epg"],
            ifconns: data["ifconn"],
        },
        param["result"],
        param["num_bad_ports"],
    )


# icurl queries
infraSetPol = "uni/infra/settings.json"
infra = "infraInfra.json"
infra += "?query-target=subtree&target-subtree-class="
infra += ",".join(script.AciAccessPolicyParser.get_classes())
ifconns = "fvIfConn.json"
epgs = "fvAEPg.json"
epgs += (
    "?rsp-subtree-include=required&rsp-subtree=children&rsp-subtree-class=fvRsDomAtt"
)


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_num_bad_ports",
    [
        # Validation yes
        (
            {
                infraSetPol: read_data(dir, "infraSetPol_yes.json"),
                infra: read_data(dir, "access_policy.json"),
                ifconns: read_data(dir, "fvIfConn.json"),
                epgs: read_data(dir, "fvAEPg.json"),
            },
            script.PASS,
            0,
        ),
        # Validation no
        (
            {
                infraSetPol: read_data(dir, "infraSetPol_no.json"),
                infra: read_data(dir, "access_policy.json"),
                ifconns: read_data(dir, "fvIfConn.json"),
                epgs: read_data(dir, "fvAEPg.json"),
            },
            script.MANUAL,
            6,
        ),
    ]
    + [input(param) for param in params],
    ids=["validation_yes", "validation_no"] + [param["id"] for param in params],
)
def test_logic(capsys, mock_icurl, expected_result, expected_num_bad_ports):
    result = script.overlapping_vlan_pools_check(1, 1)
    assert result == expected_result

    captured = capsys.readouterr()
    log.debug(captured.out)
    lines = [
        x
        for x in captured.out.split("\n")
        if x.endswith("Outage") or x.endswith("Flood Scope")
    ]
    assert len(lines) == expected_num_bad_ports
