import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
vnsAdjacencyDefCont_api = 'vnsAdjacencyDefCont.json'
vnsSvcRedirEcmpBucketCons_api = 'vnsSvcRedirEcmpBucketCons.json'
fvAdjDefCons_api = 'fvAdjDefCons.json'
count_filter = '?rsp-subtree-include=count'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        # HIGH PBR scale and targeting affected version
        (
            {
                vnsAdjacencyDefCont_api+count_filter: read_data(dir, "vnsAdjacencyDefCont_HIGH.json"),
                vnsSvcRedirEcmpBucketCons_api+count_filter: read_data(dir, "vnsSvcRedirEcmpBucketCons_HIGH.json"),
                fvAdjDefCons_api+count_filter: read_data(dir, "fvAdjDefCons_HIGH.json"),
            },
            "5.2(8h)",
            script.FAIL_O,
        ),
        # High PBR scale and targeting fixed version
        (
            {
                vnsAdjacencyDefCont_api+count_filter: read_data(dir, "vnsAdjacencyDefCont_HIGH.json"),
                vnsSvcRedirEcmpBucketCons_api+count_filter: read_data(dir, "vnsSvcRedirEcmpBucketCons_HIGH.json"),
                fvAdjDefCons_api+count_filter: read_data(dir, "fvAdjDefCons_HIGH.json"),
            },
            "5.3(2c)",
            script.PASS,
        ),
        # Low fabric scale and targeting affected version
        (
            {
                vnsAdjacencyDefCont_api+count_filter: read_data(dir, "vnsAdjacencyDefCont_LOW.json"),
                vnsSvcRedirEcmpBucketCons_api+count_filter: read_data(dir, "vnsSvcRedirEcmpBucketCons_LOW.json"),
                fvAdjDefCons_api+count_filter: read_data(dir, "fvAdjDefCons_LOW.json"),
            },
            "5.2(8h)",
            script.PASS,
        ),
        # low fabric scale and targeting fixed version
        (
            {
                vnsAdjacencyDefCont_api+count_filter: read_data(dir, "vnsAdjacencyDefCont_LOW.json"),
                vnsSvcRedirEcmpBucketCons_api+count_filter: read_data(dir, "vnsSvcRedirEcmpBucketCons_LOW.json"),
                fvAdjDefCons_api+count_filter: read_data(dir, "fvAdjDefCons_LOW.json"),
            },
            "5.3(2c)",
            script.PASS,
        ),
        # tversion not given
        (
            {
                vnsAdjacencyDefCont_api+count_filter: read_data(dir, "vnsAdjacencyDefCont_LOW.json"),
                vnsSvcRedirEcmpBucketCons_api+count_filter: read_data(dir, "vnsSvcRedirEcmpBucketCons_LOW.json"),
                fvAdjDefCons_api+count_filter: read_data(dir, "fvAdjDefCons_LOW.json"),
            },
            None,
            script.MANUAL,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.pbr_high_scale_check(
        1,
        1,
        script.AciVersion(tversion) if tversion else None,
    )
    assert result == expected_result
