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

download_sts = 'maintUpgJob.json'
download_sts += '?query-target-filter=and(eq(maintUpgJob.dnldStatus,"downloaded"),eq(maintUpgJob.dnldPercent,"100"))'
download_sts += '&rsp-subtree=full'

# No pre-downloaded nodes unless a test overrides this key.
no_predownload = []

# Older versions don't have `dnldStatus`/`dnldPercent` props on `maintUpgJob`.
old_ver_no_prop = [{"error": {"attributes": {"code": "400", "text": "Prop 'dnldStatus' not found in class 'maintUpgJob' property table"}}}]

# Firmware images for target 6.0(2h): both current/target are >= 6.0(2a) so both
# 32/64-bit isos are considered. The 64-bit image is the larger of the two.
# Of all nodes in eqptcapacityFSPartition.json, only node-101 (avail 5347648 KB)
# falls below the resulting required space (~5859375 KB) and thus fails.
firmware_dual_602 = [
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.0.2h.bin", "size": "2000000000"}}},
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.0.2h-cs_64.bin", "size": "3000000000"}}},
]

# node-101 has fully downloaded/extracted the target image already.
maintUpgJob_node_101_downloaded = [
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-101/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
]

# node-999 (not present in eqptcapacityFSPartition.json) has pre-downloaded the image.
maintUpgJob_node_999_downloaded = [
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-999/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
]

# Every node in eqptcapacityFSPartition.json has fully pre-downloaded the target image.
maintUpgJob_all_downloaded = [
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-102/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-103/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-2/node-205/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-2/node-206/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-1002/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-1001/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-2/node-2002/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-2/node-2003/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-2/node-2001/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-2/node-2010/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-101/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
]


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # No tversion provided.
        (
            {},
            None,
            None,
            script.MANUAL,
        ),
        # /bootflash partition objects not found at all. Returns before maintUpgJob is queried.
        (
            {
                partitions: [],
            },
            "6.0(3a)",
            "6.0(2h)",
            script.MANUAL,
        ),
        # Baseline failure: node-101 lacks sufficient space and is not pre-downloaded.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: no_predownload,
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
                download_sts: no_predownload,
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
                download_sts: no_predownload,
                firmware: read_data(dir, "firmwareFirmware_dual_image_insufficient.json"),
            },
            "5.2(8h)",
            "6.1(5e)",
            script.FAIL_UF,
        ),
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: no_predownload,
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
                download_sts: no_predownload,
                firmware: [],
            },
            "6.0(3a)",
            "6.0(2h)",
            script.MANUAL,
        ),
        # node-101 (the only node that would otherwise fail) already fully downloaded
        # the target image, so it's excluded from the check and the result is PASS.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: maintUpgJob_node_101_downloaded,
                firmware: firmware_dual_602,
            },
            "6.0(3a)",
            "6.0(2h)",
            script.PASS,
        ),
        # A pre-downloaded node unrelated to the failing node doesn't change the outcome.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: maintUpgJob_node_999_downloaded,
                firmware: firmware_dual_602,
            },
            "6.0(3a)",
            "6.0(2h)",
            script.FAIL_UF,
        ),
        # Every node has pre-downloaded the image, so all are skipped and the result is PASS.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: maintUpgJob_all_downloaded,
                firmware: firmware_dual_602,
            },
            "6.0(3a)",
            "6.0(2h)",
            script.PASS,
        ),
        # Older versions don't have `dnldStatus`/`dnldPercent` on `maintUpgJob`: `OldVerPropNotFound`
        # is caught and treated as no pre-downloaded nodes found (node-101 still fails).
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: old_ver_no_prop,
                firmware: firmware_dual_602,
            },
            "6.0(3a)",
            "6.0(2h)",
            script.FAIL_UF,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion) if cversion else None,
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
