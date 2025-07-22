import pytest
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")

# icurl queries
fabricNodePEps = "fabricNodePEp.json"

data = [
    {
        "fabricNodePEp": {
            "attributes": {
                "dn": "uni/fabric/protpol/expgep-101-103/nodepep-101",
                "id": "101"
            }
        }
    },
    {
        "fabricNodePEp": {
            "attributes": {
                "dn": "uni/fabric/protpol/expgep-204-206/nodepep-206",
                "id": "206"
            }
        }
    },
    {
        "fabricNodePEp": {
            "attributes": {
                "dn": "uni/fabric/protpol/expgep-101-103/nodepep-103",
                "id": "103"
            }
        }
    },
    {
        "fabricNodePEp": {
            "attributes": {
                "dn": "uni/fabric/protpol/expgep-204-206/nodepep-204",
                "id": "204"
            }
        }
    }
]

data2 = [
    {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-101-102/nodepep-101", "id": "101"}}},
    {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-101-102/nodepep-102", "id": "102"}}},
    {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-103-104/nodepep-103", "id": "103"}}},
    {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-103-104/nodepep-104", "id": "104"}}},
    {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-105-106/nodepep-105", "id": "105"}}},
    {"fabricNodePEp": {"attributes": {"dn": "uni/fabric/protpol/expgep-105-106/nodepep-106", "id": "106"}}},
]


@pytest.mark.parametrize(
    "icurl_outputs, expected_result, expected_stdout",
    [
        (
            {fabricNodePEps: []},
            [],
            "Collecting VPC Node IDs...\n\n",
        ),
        (
            {fabricNodePEps: data},
            ["101", "103", "204", "206"],
            "Collecting VPC Node IDs...101, 103, 204, 206\n\n",
        ),
        (
            {fabricNodePEps: data2},
            ["101", "102", "103", "104", "105", "106"],
            "Collecting VPC Node IDs...101, 102, 103, 104, ... (and 2 more)\n\n",
        )
    ]
)
def test_get_vpc_nodes(capsys, mock_icurl, expected_result, expected_stdout):
    vpc_nodes = script.get_vpc_nodes()
    assert vpc_nodes == expected_result

    captured = capsys.readouterr()
    print(captured.out)
    assert captured.out == expected_stdout
