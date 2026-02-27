import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "fc_ex_model_check"

# icurl queries
fcEntity_api = "fcEntity.json"


@pytest.mark.parametrize(
    "icurl_outputs, tversion, fabric_nodes, expected_result, expected_data",
    [
        # TVERSION MISSING
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102_103.json")},
            None,
            read_data(dir, "fabricNode_POS.json"),
            script.MANUAL,
            [],
        ),
        # TVERSION NOT AFFECTED
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102_103.json")},
            "6.0(1f)",
            read_data(dir, "fabricNode_POS.json"),
            script.PASS,
            [],
        ),
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102_103.json")},
            "6.0(9f)",
            read_data(dir, "fabricNode_POS.json"),
            script.PASS,
            [],
        ),
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102_103.json")},
            "6.1(4h)",
            read_data(dir, "fabricNode_POS.json"),
            script.PASS,
            [],
        ),
        # FABRIC HAS EX NODES and ALL OF THEM HAVE FC/FCOE CONFIG
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102_103.json")},
            "6.1(1f)",
            read_data(dir, "fabricNode_POS.json"),
            script.FAIL_O,
            [
                ["topology/pod-1/node-101", "N9K-C93180YC-EX"],
                ["topology/pod-1/node-102", "N9K-C93108TC-EX"],
                ["topology/pod-1/node-103", "N9K-C93108LC-EX"],
            ],
        ),
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102_103.json")},
            "6.0(7e)",
            read_data(dir, "fabricNode_POS.json"),
            script.FAIL_O,
            [
                ["topology/pod-1/node-101", "N9K-C93180YC-EX"],
                ["topology/pod-1/node-102", "N9K-C93108TC-EX"],
                ["topology/pod-1/node-103", "N9K-C93108LC-EX"],
            ],
        ),
        # FABRIC HAS EX NODES and SOME OF THEM HAVE FC/FCOE CONFIG
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102.json")},
            "6.1(1f)",
            read_data(dir, "fabricNode_POS.json"),
            script.FAIL_O,
            [
                ["topology/pod-1/node-101", "N9K-C93180YC-EX"],
                ["topology/pod-1/node-102", "N9K-C93108TC-EX"],
            ],
        ),
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102.json")},
            "6.0(7e)",
            read_data(dir, "fabricNode_POS.json"),
            script.FAIL_O,
            [
                ["topology/pod-1/node-101", "N9K-C93180YC-EX"],
                ["topology/pod-1/node-102", "N9K-C93108TC-EX"],
            ],
        ),
        # FABRIC HAS EX NODES and NONE OF THEM HAVE FC/FCOE CONFIG
        (
            {fcEntity_api: []},
            "6.0(7e)",
            read_data(dir, "fabricNode_POS.json"),
            script.PASS,
            [],
        ),
        (
            {fcEntity_api: read_data(dir, "fcEntity_104.json")},
            "6.0(7e)",
            read_data(dir, "fabricNode_POS.json"),
            script.PASS,
            [],
        ),
        # FABRIC DOES NOT HAVE EX NODES
        (
            {fcEntity_api: []},
            "6.0(7e)",
            read_data(dir, "fabricNode_NEG.json"),
            script.PASS,
            [],
        ),
        (
            {fcEntity_api: read_data(dir, "fcEntity_101_102_103.json")},
            "6.0(7e)",
            read_data(dir, "fabricNode_NEG.json"),
            script.PASS,
            [],
        ),
        (
            {fcEntity_api: read_data(dir, "fcEntity_104.json")},
            "6.0(7e)",
            read_data(dir, "fabricNode_NEG.json"),
            script.PASS,
            [],
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, fabric_nodes, expected_result, expected_data):
    result = run_check(
        tversion=script.AciVersion(tversion) if tversion else None,
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data
