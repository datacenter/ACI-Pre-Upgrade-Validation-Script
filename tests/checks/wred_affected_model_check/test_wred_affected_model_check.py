import pytest
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "wred_affected_model_check"


def _node(node_id, name, role, model):
    return {
        "fabricNode": {
            "attributes": {
                "id": str(node_id),
                "name": name,
                "role": role,
                "model": model,
                "dn": "topology/pod-1/node-{}".format(node_id),
            }
        }
    }


@pytest.mark.parametrize(
    "tversion, fabric_nodes, icurl_outputs, expected_result, expected_data",
    [
        (
            None,
            [_node(101, "leaf101", "leaf", "N9K-C9236C")],
            {},
            script.MANUAL,
            [],
        ),
        (
            "6.2(2a)",
            [_node(101, "leaf101", "leaf", "N9K-C9236C")],
            {},
            script.PASS,
            [],
        ),
        (
            "6.1(5e)",
            [_node(101, "leaf101", "leaf", "N9K-C9236C")],
            {
                "qosCong.json": [
                    {"qosCong": {"attributes": {"algo": "wred"}}},
                ],
                "eqptLC.json": [],
                "eqptFC.json": [],
            },
            script.FAIL_O,
            [["101", "leaf101", "Leaf", "N9K-C9236C"]],
        ),
        (
            "6.2(1f)",
            [
                _node(1001, "spine1001", "spine", "N9K-C9504"),
            ],
            {
                "qosCong.json": [
                    {"qosCong": {"attributes": {"algo": "tail-drop"}}},
                    {"qosCong": {"attributes": {"algo": "wred"}}},
                ],
                "eqptLC.json": [
                    {
                        "eqptLC": {
                            "attributes": {
                                "dn": "topology/pod-1/node-1001/sys/ch/lcslot-1/lc",
                                "model": "N9K-C92304QC",
                            }
                        }
                    }
                ],
                "eqptFC.json": [
                    {
                        "eqptFC": {
                            "attributes": {
                                "dn": "topology/pod-1/node-1001/sys/ch/fcslot-1/fc",
                                "model": "N9K-C9508-FM-E",
                            }
                        }
                    }
                ],
            },
            script.FAIL_O,
            [
                ["1001", "spine1001", "FM", "N9K-C9508-FM-E"],
                ["1001", "spine1001", "LC", "N9K-C92304QC"],
            ],
        ),
        (
            "6.1(5e)",
            [_node(101, "leaf101", "leaf", "N9K-C9236C")],
            {
                "qosCong.json": [
                    {"qosCong": {"attributes": {"algo": "tail-drop"}}},
                ],
                "eqptLC.json": [],
                "eqptFC.json": [],
            },
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, fabric_nodes, expected_result, expected_data):
    kwargs = {
        "tversion": script.AciVersion(tversion) if tversion else None,
        "fabric_nodes": fabric_nodes,
    }

    result = run_check(**kwargs)
    assert result.result == expected_result
    assert result.data == expected_data
