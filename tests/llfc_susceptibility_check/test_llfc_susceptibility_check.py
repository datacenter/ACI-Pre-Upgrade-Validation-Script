import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
ethpmFcots = 'ethpmFcot.json?query-target-filter=and(eq(ethpmFcot.type,"sfp"),eq(ethpmFcot.state,"inserted"))'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, vpc_node_ids, expected_result",
    [
        (
            {ethpmFcots: read_data(dir, "ethpmFcot.json")},
            "4.2(1b)",
            "5.2(2a)",
            ["101", "103", "204", "206"],
            script.MANUAL,
        ),
        (
            {ethpmFcots: read_data(dir, "ethpmFcot.json")},
            "3.2(1a)",
            "4.2(4d)",
            ["101", "103", "204", "206"],
            script.MANUAL,
        ),
        (
            {ethpmFcots: read_data(dir, "ethpmFcot.json")},
            "3.2(1a)",
            "5.2(6a)",
            ["101", "103", "204", "206"],
            script.MANUAL,
        ),
        (
            {ethpmFcots: read_data(dir, "ethpmFcot.json")},
            "4.2(3a)",
            "4.2(7d)",
            ["101", "103", "204", "206"],
            script.MANUAL,
        ),
        (
            {ethpmFcots: read_data(dir, "ethpmFcot.json")},
            "2.2(3a)",
            "2.2(4r)",
            ["101", "103", "204", "206"],
            script.PASS,
        ),
        (
            {ethpmFcots: read_data(dir, "ethpmFcot.json")},
            "5.2(1a)",
            None,
            ["101", "103", "204", "206"],
            script.MANUAL,
        ),
        (
            {ethpmFcots: read_data(dir, "ethpmFcot.json")},
            "4.1(1a)",
            "5.2(7f)",
            ["101", "103", "204", "206"],
            script.MANUAL,
        ),
        (
            {ethpmFcots: read_data(dir, "ethpmFcot.json")},
            "4.1(1a)",
            "5.2(7f)",
            [],
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, cversion, tversion, vpc_node_ids, expected_result):
    result = script.llfc_susceptibility_check(
        1,
        1,
        script.AciVersion(cversion),
        script.AciVersion(tversion) if tversion else None,
        vpc_node_ids=vpc_node_ids,
    )
    assert result == expected_result
