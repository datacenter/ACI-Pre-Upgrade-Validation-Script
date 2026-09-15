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

download_sts_602 = 'maintUpgJob.json'
download_sts_602 += '?query-target-filter=and(eq(maintUpgJob.dnldStatus,"downloaded")'
download_sts_602 += ',eq(maintUpgJob.desiredVersion,"n9000-16.0(2h)"))'

download_sts_528 = 'maintUpgJob.json'
download_sts_528 += '?query-target-filter=and(eq(maintUpgJob.dnldStatus,"downloaded")'
download_sts_528 += ',eq(maintUpgJob.desiredVersion,"n9000-15.2(8h)"))'

download_sts_615 = 'maintUpgJob.json'
download_sts_615 += '?query-target-filter=and(eq(maintUpgJob.dnldStatus,"downloaded")'
download_sts_615 += ',eq(maintUpgJob.desiredVersion,"n9000-16.1(5e)"))'

# No pre-downloaded nodes unless a test overrides this key.
no_predownload = []

# Older versions don't have `dnldStatus`/`dnldPercent` props on `maintUpgJob`.
old_ver_no_prop = read_data(dir, "maintUpgJob_old_ver_no_prop.json")

# Firmware images for target 6.0(2h): both current/target are >= 6.0(2a) so both
# 32/64-bit isos are considered. The 64-bit image is the larger of the two.
# Of all nodes in eqptcapacityFSPartition.json, only node-101 (avail 5347648 KB)
# falls below the resulting required space (~5859375 KB) and thus fails.
firmware_dual_602 = read_data(dir, "firmwareFirmware_dual_602.json")

# Only the 64-bit target image (6.0(2h)) is missing from the Firmware Repository.
firmware_602_missing_64 = [
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.0.2h.bin", "size": "2000000000"}}},
]

# Only the 32-bit target image (6.0(2h)) is missing from the Firmware Repository.
firmware_602_missing_32 = [
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.0.2h-cs_64.bin", "size": "3000000000"}}},
]

# Crossing 6.0(2a): current (5.2(8h)) image plus only the 32-bit target (6.1(5e)); the
# 64-bit target image is missing from the Firmware Repository.
firmware_crossing_missing_64 = [
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.15.2.8h.bin", "size": "2000000000"}}},
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.1.5e.bin", "size": "3000000000"}}},
]

# Crossing 6.0(2a): current (5.2(8h)) image plus only the 64-bit target (6.1(5e)); the
# 32-bit target image is missing from the Firmware Repository.
firmware_crossing_missing_32 = [
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.15.2.8h.bin", "size": "2000000000"}}},
    {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.1.5e-cs_64.bin", "size": "3000000000"}}},
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

# APIC (cversion) reaches 6.0(2a)+ before the switches per the documented upgrade
# sequence, so sw_cversion (5.2(8h), pre-boundary) must still drive the crossing decision
# even though the APIC cluster (cversion 6.0(3a)) is already post-boundary. cversion is
# passed here (as it would be via query_common_data() in production) solely to prove the
# check ignores it: switch_bootflash_usage_check() only declares sw_cversion/tversion, so
# cversion lands in **kwargs and has no effect on the result. Sizes are chosen so
# target_size_32 (3 GiB) exceeds current_size (2 GiB), forcing the full crossing formula:
# 2 * (3 GiB + 3 GiB - 2 GiB) = 8 GiB required.
apic_post_boundary_switch_pre_boundary_case = [
    {
        partitions: read_data(dir, "eqptcapacityFSPartition.json"),
        download_sts_615: no_predownload,
        firmware: [
            {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.15.2.8h.bin", "size": str(2 * 1024 ** 3)}}},
            {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.1.5e.bin", "size": str(3 * 1024 ** 3)}}},
            {"firmwareFirmware": {"attributes": {"isoname": "aci-n9000-dk9.16.1.5e-cs_64.bin", "size": str(3 * 1024 ** 3)}}},
        ],
    },
]


@pytest.mark.parametrize("icurl_outputs", apic_post_boundary_switch_pre_boundary_case)
def test_apic_post_boundary_switch_pre_boundary_uses_crossing_formula(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("6.0(3a)"),
        sw_cversion=script.AciVersion("5.2(8h)"),
        tversion=script.AciVersion("6.1(5e)"),
    )
    assert result.result == script.FAIL_UF
    assert result.data
    required_mb = str(8 * 1024.0)  # "8192.0" MB == 8 GiB
    assert all(row[3] == required_mb for row in result.data)


#`dnldStatus == "downloaded"` only proves the image was delivered, not
# that extraction (which still consumes bootflash) succeeded, so node-101 having
# pre-downloaded the exact target must still fail when its remaining space (1 KB) can't
# fit the extraction-only requirement (max(target_size_32, target_size_64) == 3 GB).
exact_target_downloaded_insufficient_case = [
    {
        partitions: [
            {"eqptcapacityFSPartition": {"attributes": {"dn": "topology/pod-1/node-101/sys/eqptcapacity/fspartition-bootflash", "avail": "1", "used": "999999999"}}},
        ],
        download_sts_602: maintUpgJob_node_101_downloaded,
        firmware: firmware_dual_602,
    },
]


@pytest.mark.parametrize("icurl_outputs", exact_target_downloaded_insufficient_case)
def test_exact_target_downloaded_still_fails_on_insufficient_extraction_space(run_check, mock_icurl):
    result = run_check(
        sw_cversion=script.AciVersion("6.0(3a)"),
        tversion=script.AciVersion("6.0(2h)"),
    )
    assert result.result == script.FAIL_UF
    assert result.data == [["1", "101", "0.0", "2861.02"]]


def test_missing_target_version_takes_precedence(run_check):
    result = run_check(sw_cversion=None, tversion=None)

    assert result.result == script.MANUAL
    assert result.msg == script.TVER_MISSING


@pytest.mark.parametrize(
    "icurl_outputs, sw_cversion, tversion, expected_result",
    [
        # No tversion provided.
        (
            {},
            "6.0(3a)",
            None,
            script.MANUAL,
        ),
        # No sw_cversion (lowest switch version) found.
        (
            {},
            None,
            "6.0(2h)",
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
                download_sts_602: no_predownload,
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
                download_sts_528: no_predownload,
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
                download_sts_615: no_predownload,
                firmware: read_data(dir, "firmwareFirmware_dual_image_insufficient.json"),
            },
            "5.2(8h)",
            "6.1(5e)",
            script.FAIL_UF,
        ),
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts_615: no_predownload,
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
                download_sts_602: no_predownload,
                firmware: [],
            },
            "6.0(3a)",
            "6.0(2h)",
            script.MANUAL,
        ),
        # Post-6.0(2a): only the 64-bit target image is missing from the Firmware Repository.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts_602: no_predownload,
                firmware: firmware_602_missing_64,
            },
            "6.0(3a)",
            "6.0(2h)",
            script.MANUAL,
        ),
        # Post-6.0(2a): only the 32-bit target image is missing from the Firmware Repository.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts_602: no_predownload,
                firmware: firmware_602_missing_32,
            },
            "6.0(3a)",
            "6.0(2h)",
            script.MANUAL,
        ),
        # Crossing 6.0(2a): only the 64-bit target image is missing from the Firmware Repository.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts_615: no_predownload,
                firmware: firmware_crossing_missing_64,
            },
            "5.2(8h)",
            "6.1(5e)",
            script.MANUAL,
        ),
        # Crossing 6.0(2a): only the 32-bit target image is missing from the Firmware Repository.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts_615: no_predownload,
                firmware: firmware_crossing_missing_32,
            },
            "5.2(8h)",
            "6.1(5e)",
            script.MANUAL,
        ),
        # node-101 (the only node that would otherwise fail) already fully downloaded
        # the target image, so it's excluded from the check and the result is PASS.
        (
            {
                partitions: read_data(dir, "eqptcapacityFSPartition.json"),
                download_sts_602: maintUpgJob_node_101_downloaded,
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
                download_sts_602: maintUpgJob_node_999_downloaded,
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
                download_sts_602: maintUpgJob_all_downloaded,
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
                download_sts_602: old_ver_no_prop,
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
                download_sts_602: maintUpgJob_malformed_dn,
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
                download_sts_615: maintUpgJob_partial_of_failing,
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
                download_sts_615: maintUpgJob_all_of_failing,
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
                download_sts_615: maintUpgJob_partial_missing_empty,
                firmware: read_data(dir, "firmwareFirmware_dual_image_insufficient.json"),
            },
            "5.2(8h)",
            "6.1(5e)",
            script.FAIL_UF,
        ),
    ],
)
def test_logic(run_check, mock_icurl, sw_cversion, tversion, expected_result):
    result = run_check(
        sw_cversion=script.AciVersion(sw_cversion) if sw_cversion else None,
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
