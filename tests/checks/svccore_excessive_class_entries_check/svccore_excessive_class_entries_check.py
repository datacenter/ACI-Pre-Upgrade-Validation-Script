import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "svccore_excessive_data_check"
svccoreClassEntry = 'svccoreCtrlr.json?&rsp-subtree-include=count'
svccoreNodeEntry = 'svccoreNode.json?&rsp-subtree-include=count'

@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        # No excessive class entries
        (
            {svccoreClassEntry: read_data(dir, "svccore_positive.json"),svccoreNodeEntry: read_data(dir, "svccoreNode_positive.json")},
            script.PASS,
        ),
        # Excessive class entries found
        (
            {svccoreClassEntry: read_data(dir, "svccore_negative.json"),svccoreNodeEntry: read_data(dir, "svccoreNode_positive.json")},
            script.MANUAL,
        ),
        (
            {svccoreClassEntry: read_data(dir, "svccoreNode_negative.json"),svccoreNodeEntry: read_data(dir, "svccoreNode_negative.json")},
            script.MANUAL,
        ),
        (
            {svccoreClassEntry: read_data(dir, "svccore_positive.json"),svccoreNodeEntry: read_data(dir, "svccoreNode_negative.json")},
            script.MANUAL,
        )
    ],
)

def test_logic(run_check,mock_icurl,expected_result):
    result = run_check()
    assert result.result == expected_result