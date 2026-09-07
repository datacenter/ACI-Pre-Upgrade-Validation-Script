import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "switch_bootflash_usage_check"

# icurl queries
partitions = "eqptcapacityFSPartition.json"
partitions += '?query-target-filter=eq(eqptcapacityFSPartition.path,"/bootflash")'

firmware = 'firmwareFirmware.json?query-target-filter=eq(firmwareFirmware.type,"switch")'

# Firmware images for target 6.0(2h): both current/target are >= 6.0(2a) so both
# 32/64-bit isos are considered. The 64-bit image is the larger of the two.
firmware_dual_602 = [
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.0.2h.bin", "size": "2000000000"}}},
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.0.2h-cs_64.bin", "size": "3000000000"}}},
]


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        (
            {
                partitions: [],
            },
            "6.0(3a)",
            "6.0(2h)",
            script.MANUAL,
        ),
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                firmware: firmware_dual_602,
            },
            "6.0(3a)",
            "6.0(2h)",
            script.FAIL_UF,
        ),
        # Both current and target are pre-6.0(2a): only the single 32-bit iso matters.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                firmware: [
                    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.15.2.8h.bin", "size": "1000000000"}}},
                ],
            },
            "5.2(8h)",
            "5.2(8h)",
            script.PASS,
        ),
        # Crossing 6.0(2a): current 32-bit image size is deducted from the two target isos.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                firmware: read_data(dir, "firmwareFirmware_dual_image_insufficient.json"),
            },
            "5.2(8h)",
            "6.1(5e)",
            script.FAIL_UF,
        ),
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                firmware: read_data(dir, "firmwareFirmware_dual_image_sufficient.json"),
            },
            "5.2(8h)",
            "6.1(5e)",
            script.PASS,
        ),
        # Target image not yet uploaded to the Firmware Repository.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                firmware: [],
            },
            "6.0(3a)",
            "6.0(2h)",
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion),
    )
    assert result.result == expected_result
