# Test Cases for aaa_snmpd_dns_provider_check

## Overview
This directory contains test cases for the `aaa_snmpd_dns_provider_check` function, which validates AAA provider configurations to prevent snmpd memory exhaustion issues (CSCwq57598).

## Test Function
**Function Name:** `aaa_snmpd_dns_provider_check`  
**Bug Reference:** CSCwq57598 - hundreds of snmpd process exhaust memory and lead kernel panic with oom

## Test Scenarios

### Test Case 1: No Target Version Provided
- **Input:** No target version (None)
- **JSON File:** `providers_with_dns.json`
- **Expected Result:** `MANUAL CHECK REQUIRED`
- **Expected Data Count:** 0
- **Description:** When target version is not provided, the check should return MANUAL and indicate that target version is missing.

### Test Case 2: Target Version 6.1(5e) - Not Affected
- **Input:** Target version `6.1(5e)`
- **JSON File:** `providers_with_dns.json`
- **Expected Result:** `PASS`
- **Expected Data Count:** 0
- **Description:** Version 6.1(5e) includes the fix, so the check should pass with "Version not affected" message.

### Test Case 3: Target Version Newer Than 6.1(5e) - Not Affected
- **Input:** Target version `6.2(1a)`
- **JSON File:** `providers_with_dns.json`
- **Expected Result:** `PASS`
- **Expected Data Count:** 0
- **Description:** Versions newer than 6.1(5e) are not affected, so the check should pass.

### Test Case 4: Target Version Older Than 6.1(5e) with DNS Names - FAIL
- **Input:** Target version `6.1(4a)`
- **JSON File:** `providers_with_dns.json`
- **Expected Result:** `FAIL_O` (FAIL - OUTAGE WARNING!!)
- **Expected Data Count:** 2
- **Description:** When target version is older than 6.1(5e) and DNS names are found in AAA providers, the check should fail.
- **Flagged Providers:**
  - RADIUS provider: `rad.cisco.com`
  - LDAP provider: `aaa.domain.com`

### Test Case 5: Target Version Older Than 6.1(5e) with Only IP Addresses - PASS
- **Input:** Target version `6.1(3a)`
- **JSON File:** `providers_with_ips.json`
- **Expected Result:** `PASS`
- **Expected Data Count:** 0
- **Description:** When only IP addresses are configured, the check should pass even on affected versions.
- **Providers (all IPs):**
  - TACACS+ provider: `10.0.0.1`
  - RADIUS provider: `192.168.1.100`
  - LDAP provider: `10.10.10.50`

### Test Case 6: Target Version Older Than 6.1(5e) with Mixed (IP and DNS) - FAIL
- **Input:** Target version `6.0(5a)`
- **JSON File:** `providers_mixed.json`
- **Expected Result:** `FAIL_O` (FAIL - OUTAGE WARNING!!)
- **Expected Data Count:** 2
- **Description:** When a mix of IP and DNS names is configured, only DNS entries should be flagged.
- **Flagged Providers:**
  - RADIUS provider: `radius.example.com`
  - LDAP provider: `ldap-server.local`
- **Not Flagged:**
  - TACACS+ provider: `10.0.0.1` (IP address)

### Test Case 7: Target Version Older Than 6.1(5e) with No Providers - PASS
- **Input:** Target version `5.2(8a)`
- **JSON File:** `providers_empty.json`
- **Expected Result:** `PASS`
- **Expected Data Count:** 0
- **Description:** When no AAA providers are configured, the check should pass.

## JSON Test Data Files

### providers_with_dns.json
Contains AAA providers with DNS names:
- RADIUS provider: `rad.cisco.com`
- LDAP provider: `aaa.domain.com`

### providers_with_ips.json
Contains AAA providers with only IP addresses:
- TACACS+ provider: `10.0.0.1`
- RADIUS provider: `192.168.1.100`
- LDAP provider: `10.10.10.50`

### providers_mixed.json
Contains a mix of IP and DNS configurations:
- TACACS+ provider: `10.0.0.1` (IP)
- RADIUS provider: `radius.example.com` (DNS)
- LDAP provider: `ldap-server.local` (DNS)

### providers_empty.json
Empty array - no AAA providers configured.

## Running the Tests

```bash
# Run all tests
cd /data/ssd/dhaselva/repo/ACI-Escalation/ACI-Pre-Upgrade-Validation-Script
python3 -m pytest tests/checks/aaa_snmpd_dns_provider_check/test_aaa_snmpd_dns_provider_check.py -v

# Run with detailed output
python3 -m pytest tests/checks/aaa_snmpd_dns_provider_check/test_aaa_snmpd_dns_provider_check.py -v -s
```

## Test Results
All 7 test cases pass successfully, validating:
1. Version checking logic (missing version, affected versions, not affected versions)
2. DNS name detection (alphabetic characters in provider names)
3. Proper handling of IP addresses (should not be flagged)
4. Mixed configurations (only DNS names should be flagged)
5. Empty configurations (no providers)

## Expected Output Format
When DNS names are detected in affected versions:
- **Headers:** ["Provider Type", "Provider Name", "Provider DN"]
- **Data:** List of providers with DNS names
- **Recommended Action:** "Replace DNS names with IP addresses in AAA provider configurations to prevent snmpd memory exhaustion"
