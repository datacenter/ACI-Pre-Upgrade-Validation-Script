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


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {fabricNodePEps: data},
            ["101", "103", "204", "206"]
        )
    ]
)
def test_get_vpc_nodes(mock_icurl, expected_result):
    assert set(script.get_vpc_nodes()) == set(expected_result)
