import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "service_bd_forceful_routing_check"

# icurl queries
fvRtEPpInfoToBD = "fvRtEPpInfoToBD.json"


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # tversion missing
        (
            {fvRtEPpInfoToBD: read_data(dir, "fvRtEPpInfoToBD.json")},
            "5.2(8h)",
            None,
            script.MANUAL
        ),
        # Version not affected (both new)
        (
            {fvRtEPpInfoToBD: read_data(dir, "fvRtEPpInfoToBD.json")},
            "6.0(2h)",
            "6.1(3b)",
            script.NA,
        ),
        # Version not affected (both old)
        (
            {fvRtEPpInfoToBD: read_data(dir, "fvRtEPpInfoToBD.json")},
            "4.2(7s)",
            "6.0(1h)",
            script.NA,
        ),
        # Version affected with L4L7 service graph BD
        (
            {fvRtEPpInfoToBD: read_data(dir, "fvRtEPpInfoToBD.json")},
            "5.2(8h)",
            "6.0(2h)",
            script.MANUAL
        ),
        # Version affected without L4L7 service graph BD
        (
            {fvRtEPpInfoToBD: []},
            "5.2(8h)",
            "6.0(2h)",
            script.PASS,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
