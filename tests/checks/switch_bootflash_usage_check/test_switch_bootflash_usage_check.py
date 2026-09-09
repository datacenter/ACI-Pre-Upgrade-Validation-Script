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

# No pre-downloaded nodes unless a test overrides this key.
no_predownload = []

# Older versions don't have `dnldStatus`/`dnldPercent` props on `maintUpgJob`.
old_ver_no_prop = read_data(dir, "maintUpgJob_old_ver_no_prop.json")

# Firmware images for target 6.0(2h): both current/target are >= 6.0(2a) so both
# 32/64-bit isos are considered. The 64-bit image is the larger of the two.
# Of all nodes in eqptcapacityFSPartition.json, only node-101 (avail 5347648 KB)
# falls below the resulting required space (~5859375 KB) and thus fails.
firmware_dual_602 = read_data(dir, "firmwareFirmware_dual_602.json")

# node-101 has fully downloaded/extracted the target image already.
maintUpgJob_node_101_downloaded = [
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-101/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
]

# node-999 (not present in eqptcapacityFSPartition.json) has pre-downloaded the image.
maintUpgJob_node_999_downloaded = [
    {"maintUpgJob": {"attributes": {"dn": "topology/pod-1/node-999/sys/maintupgjob", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
]

# Every node in eqptcapacityFSPartition.json has fully pre-downloaded the target image.
maintUpgJob_all_downloaded = read_data(dir, "maintUpgJob_all_downloaded.json")

# `dn` doesn't match `node_regex` (unparseable): skipped gracefully, not added to the map.
maintUpgJob_malformed_dn = [
    {"maintUpgJob": {"attributes": {"dn": "uni/some/unexpected/format", "dnldStatus": "downloaded", "dnldPercent": "100"}}},
]

# Only node-101 (one of several failing nodes with the insufficient-space fixture) is pre-downloaded.
maintUpgJob_partial_of_failing = maintUpgJob_node_101_downloaded

# All 8 nodes that fail with the insufficient-space fixture are pre-downloaded; the
# remaining 3 nodes (2002, 2003, 2010) already have enough free space on their own.
maintUpgJob_all_of_failing = read_data(dir, "maintUpgJob_all_of_failing.json")

# Mixed real-world response: node-102 and node-103 are present and downloaded, the
# other failing nodes (205, 206, 1002, 1001, 2001, 101) are simply missing from the
# response, and one entry has an empty-string `dn` (unparseable, skipped gracefully).
maintUpgJob_partial_missing_empty = read_data(dir, "maintUpgJob_partial_missing_empty.json")


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
        # A `maintUpgJob` entry with an unparseable `dn` is skipped gracefully (no crash,
        # no false skip): node-101 is not excluded and the check still fails.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: maintUpgJob_malformed_dn,
                firmware: firmware_dual_602,
            },
            "6.0(3a)",
            "6.0(2h)",
            script.FAIL_UF,
        ),
        # Multiple nodes fail with the insufficient-space fixture; pre-downloading only
        # one of them still leaves the rest failing.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: maintUpgJob_partial_of_failing,
                firmware: read_data(dir, "firmwareFirmware_dual_image_insufficient.json"),
            },
            "5.2(8h)",
            "6.1(5e)",
            script.FAIL_UF,
        ),
        # Pre-downloading every node that would otherwise fail with the insufficient-space
        # fixture leaves only the already-sufficient nodes, so the result is PASS.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: maintUpgJob_all_of_failing,
                firmware: read_data(dir, "firmwareFirmware_dual_image_insufficient.json"),
            },
            "5.2(8h)",
            "6.1(5e)",
            script.PASS,
        ),
        # Mixed response: only node-102/node-103 are covered, the rest of the failing
        # nodes are missing from `maintUpgJob`, and an empty-`dn` entry is ignored.
        # The uncovered failing nodes (205, 206, 1002, 1001, 2001, 101) still fail.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts: maintUpgJob_partial_missing_empty,
                firmware: read_data(dir, "firmwareFirmware_dual_image_insufficient.json"),
            },
            "5.2(8h)",
            "6.1(5e)",
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
