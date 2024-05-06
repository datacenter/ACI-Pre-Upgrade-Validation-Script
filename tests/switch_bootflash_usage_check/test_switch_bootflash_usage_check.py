import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
partitions =  'eqptcapacityFSPartition.json' 
partitions += '?query-target-filter=eq(eqptcapacityFSPartition.path,"/bootflash")'

download_sts =  'maintUpgJob.json'
download_sts += '?query-target-filter=and(eq(maintUpgJob.dnldStatus,"downloaded")' 
download_sts += ',eq(maintUpgJob.desiredVersion,"n9000-16.0(2h)"))'

@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            {partitions: read_data(dir, "eqptcapacityFSPartition.json"),
            download_sts: read_data(dir, "maintUpgJob_not_downloaded.json")},
            "6.0(2h)",
            script.FAIL_UF,
        ),
        (
            {partitions: read_data(dir, "eqptcapacityFSPartition.json"),
            download_sts: read_data(dir, "maintUpgJob_pre_downloaded.json")},
            "6.0(2h)",
            script.PASS,
        ),
        (
            {partitions: read_data(dir, "eqptcapacityFSPartition.json"),
            download_sts: read_data(dir, "maintUpgJob_old_ver_no_prop.json")},
            "6.0(2h)",
            script.FAIL_UF,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.switch_bootflash_usage_check(1, 1, script.AciVersion(tversion))
    assert result == expected_result
