import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "aaa_snmpd_dns_provider_check"

# icurl queries
providers_api = 'uni.json?query-target=subtree&target-subtree-class=aaaTacacsPlusProvider,aaaRadiusProvider,aaaLdapProvider'
snmp_api = 'snmpPol.json?query-target-filter=and(eq(snmpPol.adminSt,"enabled"))'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result, expected_data_count",
    [
        # Test case 1: No target version provided - should return MANUAL
        (
            {
                providers_api: read_data(dir, "providers_with_dns.json"),
                snmp_api: read_data(dir, "snmp_disabled.json"),
            },
            None,
            script.MANUAL,
            0,
        ),
        # Test case 2: Target version 6.1(5e) or newer - should return PASS (not affected)
        (
            {
                providers_api: read_data(dir, "providers_with_dns.json"),
                snmp_api: read_data(dir, "snmp_enabled.json"),
            },
            "6.1(5e)",
            script.PASS,
            0,
        ),
        # Test case 3: Target version newer than 6.1(5e) - should return PASS (not affected)
        (
            {
                providers_api: read_data(dir, "providers_with_dns.json"),
                snmp_api: read_data(dir, "snmp_enabled.json"),
            },
            "6.2(1a)",
            script.PASS,
            0,
        ),
        # Test case 4: Target version older than 6.1(5e) with DNS names but no SNMP - should return PASS
        (
            {
                providers_api: read_data(dir, "providers_with_dns.json"),
                snmp_api: read_data(dir, "snmp_disabled.json"),
            },
            "6.1(4h)",
            script.PASS,
            2,
        ),
        # Test case 5: Target version older than 6.1(5e) with DNS names and SNMP enabled - should return MANUAL
        (
            {
                providers_api: read_data(dir, "providers_with_dns.json"),
                snmp_api: read_data(dir, "snmp_enabled.json"),
            },
            "6.1(4h)",
            script.MANUAL,
            3,
        ),
        # Test case 6: Target version older than 6.1(5e) with only IP addresses - should return PASS
        (
            {
                providers_api: read_data(dir, "providers_with_ips.json"),
                snmp_api: read_data(dir, "snmp_disabled.json"),
            },
            "6.1(3g)",
            script.PASS,
            0,
        ),
        # Test case 7: Target version older than 6.1(5e) with mixed (IP and DNS) and SNMP enabled - should return MANUAL
        (
            {
                providers_api: read_data(dir, "providers_mixed.json"),
                snmp_api: read_data(dir, "snmp_enabled.json"),
            },
            "6.0(9e)",
            script.MANUAL,
            3,
        ),
        # Test case 8: Target version older than 6.1(5e) with no providers but SNMP enabled - should return PASS
        (
            {
                providers_api: read_data(dir, "providers_empty.json"),
                snmp_api: read_data(dir, "snmp_enabled.json"),
            },
            "5.2(8i)",
            script.PASS,
            0,
        ),
        # Test case 9: Target version older than 6.1(5e) with no providers and no SNMP - should return PASS
        (
            {
                providers_api: read_data(dir, "providers_empty.json"),
                snmp_api: read_data(dir, "snmp_disabled.json"),
            },
            "5.2(8i)",
            script.PASS,
            0,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result, expected_data_count):
    result = run_check(tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result
    if expected_data_count > 0:
        assert len(result.data) == expected_data_count
