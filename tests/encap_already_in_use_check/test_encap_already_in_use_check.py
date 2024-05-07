import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
faultInsts = (
    'faultInst.json?query-target-filter=wcard(faultInst.descr,"encap-already-in-use")'
)
fvIfConns = "fvIfConn.json"


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {
                faultInsts: read_data(dir, "faultInst-new-version.json"),
                fvIfConns: read_data(dir, "fvIfConn.json"),
            },
            script.FAIL_O,
        ),
        (
            {
                faultInsts: read_data(dir, "faultInst-encap-pos.json"),
                fvIfConns: read_data(dir, "fvIfConn.json"),
            },
            script.FAIL_O,
        ),
        (
            {
                faultInsts: [],
                fvIfConns: read_data(dir, "fvIfConn.json"),
            },
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.encap_already_in_use_check(1, 1)
    assert result == expected_result
