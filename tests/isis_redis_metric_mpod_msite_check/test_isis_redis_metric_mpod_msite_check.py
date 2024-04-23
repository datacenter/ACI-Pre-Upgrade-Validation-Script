import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
isisDomPs = "uni/fabric/isisDomP-default.json"
fvFabricExtConnPs = "fvFabricExtConnP.json?query-target=children"


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {
                isisDomPs: read_data(dir, "isisDomP-default_pos.json"),
                fvFabricExtConnPs: read_data(dir, "fvFabricExtConnP_pos1.json"),
            },
            script.FAIL_O,
        ),
        (
            {
                isisDomPs: read_data(dir, "isisDomP-default_pos.json"),
                fvFabricExtConnPs: read_data(dir, "fvFabricExtConnP_pos2.json"),
            },
            script.FAIL_O,
        ),
        (
            {
                isisDomPs: read_data(dir, "isisDomP-default_pos.json"),
                fvFabricExtConnPs: read_data(dir, "fvFabricExtConnP_pos3.json"),
            },
            script.FAIL_O,
        ),
        (
            {
                isisDomPs: read_data(dir, "isisDomP-default_neg.json"),
                fvFabricExtConnPs: read_data(dir, "fvFabricExtConnP_pos1.json"),
            },
            script.PASS,
        ),
        (
            {
                isisDomPs: read_data(dir, "isisDomP-default_missing.json"),
                fvFabricExtConnPs: read_data(dir, "fvFabricExtConnP_pos1.json"),
            },
            script.FAIL_O,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.isis_redis_metric_mpod_msite_check(1, 1)
    assert result == expected_result
