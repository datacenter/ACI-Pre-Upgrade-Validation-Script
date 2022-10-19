Table of Contents
=================

* [Table of Contents](#table-of-contents)
* [Quick Start](#quick-start)
* [Introduction](#introduction)
* [Preparation](#preparation)
   * [ssh copy/paste and vi](#ssh-copypaste-and-vi)
   * [local file transfer client](#local-file-transfer-client)
* [Usage](#usage)
* [Details](#details)
   * [Results](#results)
   * [General Checks](#general-checks)
   * [Fault Checks](#fault-checks)
   * [Configuration Checks](#configuration-checks)
   * [Defect Condition Checks](#defect-condition-checks)
   * [Log Files](#log-files)
* [Example run output](#example-run-output)

   
# Quick Start

1. copy `aci-preupgrade-validation-script.py` ([link](https://raw.githubusercontent.com/datacenter/ACI-Pre-Upgrade-Validation-Script/master/aci-preupgrade-validation-script.py?token=AJD5RRLZ5LVFDIW6Z6ZDIMTBBW5X6)) on your APIC (`/data/techsupport`)
2. `cd /data/techsupport`
3. `python aci-preupgrade-validation-script.py` 
4. follow recommendations for all checks that have been flagged as `FAIL` or `MANUAL CHECK REQUIRED`


# Introduction

The Goal of this script is to provide you with an automated list of proactive checks before performing an ACI fabric upgrade.  Each check is documented in the "Cisco ACI Upgrade guide - Pre-upgrade CheckLists" with a detailed explanation of the importance to resolve each issue before upgrading.

[ACI Upgrade Documentation](https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/all/apic-installation-upgrade-downgrade/Cisco-APIC-Installation-Upgrade-Downgrade-Guide.html)

Failure to address an affected issue before an upgrade is known to cause challenges during or post upgrade.

For every check that has been flagged as `FAIL`, a general recommended action has been provided to guide next steps.  There is also a summary with the number of checks that matched a given status.


# Preparation

Download the script from here: [aci-preupgrade-validation-script.py](https://raw.githubusercontent.com/datacenter/ACI-Pre-Upgrade-Validation-Script/master/aci-preupgrade-validation-script.py?token=AJD5RRLZ5LVFDIW6Z6ZDIMTBBW5X6)

## ssh copy/paste and vi

1. SSH to an APIC in a fabric that is to be upgraded
2. `cd /data/techsupport`
3. `vi aci-preupgrade-validation-script.py`
4. press `i` for insert mode
5. paste the contents of aci-preupgrade-validation-script.py
6. `:wq` to save and quit vi
7. `chmod 755 aci-preupgrade-validation-script.py`

## local file transfer client

1. Download aci-preupgrade-validation-script.py locally
2. Transfer aci-preupgrade-validation-script.py onto an APIC using your sftp client of choice
   - `/data/techsupport` is an ideal location to place the script
3. SSH to the APIC which received the aci-preupgrade-validation-script.py script
4. `cd /data/techsupport`
5. `chmod 755 aci-preupgrade-validation-script.py`

# Usage

When run, the script will prompt for user credentials.

The script will then present a list of firmware from the APIC firmware repository and ask which one is the target 
version for the next 
planned upgrade. Ensure you have the desired ACI Firmware uploaded to the APIC Firmware Repository before 
running this script.

Notes:
1. If the APIC FIrmware Repository is empty, the script will proceed but will mark checks that required the target version as 
`MANUAL CHECK REQUIRED`

2. `admin` level privileges are recommended. User permissions are important as most of these checks rely on API query responses. 
Non-admin remote user credentials can result in RBAC causing queries to return empty responses.
This can result in inconsistent script results.

3. This script only performs read operations and will not modify any config or filesystem properties. 

```
admin@f2-apic1:techsupport> python aci-preupgrade-validation-script.py 
    ==== 2021-07-30T13-28-25-0700 ====

Enter username for APIC login          : admin
Enter password for corresponding User  : 

Checking current APIC version (switch nodes are assumed to be on the same version)...5.0(1g)

Gathering APIC Versions from Firmware Repository...

[1]: aci-apic-dk9.5.2.1d.bin
[2]: aci-apic-dk9.5.2.1g.bin

What is the Target Version?     : 1

You have chosen version "aci-apic-dk9.5.2.1d.bin"

[Check  1/36] APIC Target version image and MD5 hash... 
              Checking f2-apic1......                                                                                                 DONE
                                                                                                                                      PASS
[Check  2/36] Target version compatibility...                                                                                         PASS
```

# Details

## Results

Each check has a unique result which will help determine how to proceed.  The results are explained as follows:

- **PASS** - The check has completed, and the ACI Fabric is not affected by the issue.
- **FAIL - OUTAGE WARNING** - The check has completed, and the ACI Fabric is currently affected by an issue which may cause an outage.
- **FAIL - UPGRADE FAILURE** - The check has completed, and the ACI Fabric is currently affected by an issue which may cause the upgrade to fail.
- **MANUAL CHECK REQUIRED** - The check has completed, and the specific check needs to be investigated manually using the steps outlines in the "ACI Upgrade Guide".
- **N/A** - The check completed successfully, and the ACI fabric is not susceptible because the needed configuration is not deployed.
- **ERROR** - The check did not complete successfully, and needs further investigation.

## General Checks

aci-preupgrade-validation-script.py currently performs the following checks:

Key:
- **CREDS** = credentials; uname/pw supplied on script run
- **CVER** = current version; Version on APIC during run
- **TVER** = Target Version; selected on run if found

| Check Name                                            | What is this check doing                                                                       | Pre-upgrade Checklist Mapping |
|-------------------------------------------------------|------------------------------------------------------------------------------------------------|-------------------------------|
| APIC Target version image and MD5 hash                | Requires CREDS and TVER.<br> Logs into each APIC and checks image md5 file |  MD5Sum Check for APIC and Switch Firmware + APIC Firmware Synchronization Across APICs |
| Target version compatibility                          | Requires TVER. Checks catalogue objects for TVER compatibility given CVER | Compatibility (Target ACI Version) |
| Gen 1 switch compatibility                            | Checks for gen1 hardware and flags incompatibility if TVER >= 5.0 | Compatibility (Switch Hardware) |
| Remote Leaf Compatibility                             | Checks for "Direct Traffic Forwarding" requirement | Compatibility (Remote Leaf Switch) |
| APIC CIMC Compatibility                               | Checks running CIMC against minimum recommended CIMC from CApability catalogue given TVER | Compatibility (CIMC Version) |
| APIC Cluster is Fully-Fit                             | -- | All Your APICs Are In a Fully Fit State |
| Switches are all in Active state                      | -- | All Your Switches Are In an Active State |
| NTP Status                                            | Checks that NTP is running on the fabric, and that all nodes synchronized to configured NTP server | NTP (Clocks are synchronized Across the Fabric) |
| Firmware/Maintenance Groups when crossing 4.0 Release | Checks for existing FW/maint groups | Implementation Change for Firmware Update Groups on APICs from Release 4.0(1) |
| Features that need to be Disabled prior to Upgrade    | See Pre-Upgrade Checklist  | Configurations That Must Be Disabled Prior To Upgrades |
| Switch Upgrade Group Guidelines                       | See Pre-Upgrade Checklist | Grouping Rules 1, 2 and 3 + Switch Graceful Upgrade Guidelines |

## Fault Checks

| Check Name                                                                                 | What is this check doing                  | Pre-upgrade Checklist Mapping |
|--------------------------------------------------------------------------------------------|-------------------------------------------|-------------------------------|
| APIC Disk Space Usage (F1527, F1528, F1529 equipment-full)                                 | -- | APIC DIsk Space Usage (F1527, F1528, F1529) |
| Switch Node /bootflash usage                                                               | Checks /bootflash usage object, flags if over 50% | ACI Switch bootflash Usage  |
| Standby APIC Disk Space Usage                                                              | Login to Standby APICs and checks `df -h` | Filesystem on Standby APICs |
| APIC SSD Health                                                                            | Check F2731, if not found, for version earlier than 4.2(7f) and 5.2(1g), get SSD lifetime from AE log  | SSD health status on APICs |
| Switch SSD Health (F3073, F3074 equipment-flash-warning)                                   | -- | SSD health status on ACI switches |
| Config On APIC Connected Port (F0467 port-configured-for-apic)                             | --| EPG config on ports connected to APICs |
| L3 Port Config (F0467 port-configured-as-l2)                                               | -- | Conflicting interface L2/L3 mode|
| L2 Port Config (F0467 port-configured-as-l3)                                               | -- | Conflicting interface L2/L3 mode |
| L3Out Subnets (F0467 prefix-entry-already-in-use)                                          | -- | Conflicting L3Out subnets for contracts |
| BD Subnets (F1425 subnet-overlap)                                                          |  -- | Overlapping BD subnets in the same VRF |
| BD Subnets (F0469 duplicate-subnets-within-ctx)                                            | -- | Overlapping BD subnets in the same VRF|
| VMM Domain Controller Status                                                               | -- | VMM Controller Connectivity |
| VMM Domain LLDP/CDP Adjacency Status                                                       | -- | Missing LLDP/CDP adjacency between leaf nodes and VMM hypervisors |
| Different infra VLAN via LLDP (F0454 infra-vlan-mismatch)                                  | -- | Different infra VLAN being injected via LLDP |
| HW Programming Failure (F3544 L3Out Prefixes, F3545 Contracts, actrl-resource-unavailable) | -- | Policy CAM + L3Out Subnets programming for contracts |
| Scalability (faults related to Capacity Dashboard)                                         | -- | General Scalability Limits |

## Configuration Checks

| Check Name                                      | What is this check doing                                         | Pre-upgrade Checklist Mapping |
|-------------------------------------------------|------------------------------------------------------------------|-------------------------------|
| VPC-paired Leaf switches                        | Flags any Leaf switches not in a VPC| All Switch Nodes In vPC |
| Overlapping VLAN Pools                          | Checks for multiple domains attached to EPGs, then looks up the corresponding VLAN pools for VLAN overlap | Overlapping VLAN Pool |
| VNID Mismatch                                   | For a given VLAN, flags the VLAN if found to have different VNIDS across different leaves  | Overlapping VLAN Pool |
| L3Out MTU                                       | Grabs all MTU defined on L3outs for manual peer MTU verification | L3Out MTU mismatch |
| BGP Peer Profile at node level without Loopback | See Pre-Upgrade Checklist| L3Out BGP Peer Connectivity Profile under a node profile without a loopback |
| L3Out Route Map import/export direction         | See Pre-Upgrade Checklist | L3Out incorrect route map direction |
| Intersight Device Connector upgrade status      | Flags if APIC Intersight Connector is upgrading| Intersight Device Connector is upgrading |
| ISIS Redistribution Metric for MPOD/Msite       | For multi-pod/multi-site deployment, whether isis redistribute metric is less than 63 |Switch Graceful Upgrade Guidelines|

## Defect Condition Checks

| Check Name                             | What is this check doing                                  | Pre-upgrade Checklist Mapping |
|----------------------------------------|-----------------------------------------------------------|-------------------------------|
| EP Announce Compatibility              | Checks if TVER and CVER are affected by CSCvi76161   | EP Announce version mismatch |
| Eventmgr DB size defect susceptibility | Check if CVER is affected by CSCvn20175 | None, Contact TAC for verification |
| Contract Port 22 defect susceptibility | Check if TVER is affected by CSCvz65560 | None  |
| Link Level Flow Control susceptibility | Check if CVER and TVER are affected by CSCvo27498 | None  |

## Log Files

A single log bundle will be generated with each run of the script

```
Result Bundle: /data/techsupport/preupgrade_validator_2021-07-27T17-13-12+0000.tgz
```
This bundle contains 3 inner files; debug.log, .json and .txt.
```
admin@APIC-1:techsupport> tar -xvf preupgrade_validator_2021-07-27T17-13-12+0000.tgz
preupgrade_validator_logs/
preupgrade_validator_logs/preupgrade_validator_debug.log
preupgrade_validator_logs/preupgrade_validator_2021-07-27T17-13-12+0000.json
preupgrade_validator_logs/preupgrade_validator_2021-07-27T17-13-12+0000.txt
```

the `preupgrade_validator_*.txt` file contains a dump of the resulting output which can be referenced for check results post-run.

If there are any issues with the script or run results which require TAC assistance, open a proactive TAC case for the 
upgrade and upload the result bundle for analysis.

# Example run output

```
admin@f2-apic1:techsupport> python aci-preupgrade-validation-script.py 
    ==== 2021-07-30T13-28-25-0700 ====

Enter username for APIC login          : admin
Enter password for corresponding User  : 

Checking current APIC version (switch nodes are assumed to be on the same version)...5.0(1g)

Gathering APIC Versions from Firmware Repository...

[1]: aci-apic-dk9.5.2.1d.bin
[2]: aci-apic-dk9.5.2.1g.bin

What is the Target Version?     : 1

You have chosen version "aci-apic-dk9.5.2.1d.bin"

[Check  1/36] APIC Target version image and MD5 hash... 
              Checking f2-apic1......                                                                                                 DONE
                                                                                                                                      PASS
[Check  2/36] Target version compatibility...                                                                                         PASS
[Check  3/36] Gen 1 switch compatibility...                                                                                           PASS
[Check  4/36] Remote Leaf Compatibility... No Remote Leaf Found                                                                        N/A
[Check  5/36] APIC CIMC Compatibility...                                                                                              PASS
[Check  6/36] APIC Cluster is Fully-Fit...                                                                                            PASS
[Check  7/36] Switches are all in Active state...                                                                                     PASS
[Check  8/36] NTP Status...                                                                                                           PASS
[Check  9/36] Firmware/Maintenance Groups when crossing 4.0 Release... Versions not applicable                                         N/A
[Check 10/36] Features that need to be Disabled prior to Upgrade...                                                FAIL - OUTAGE WARNING!!
  Feature      Name           Status  Recommended Action
  -------      ----           ------  ------------------
  App Center   Policy Viewer  active  Disable the app
  Config Zone  test           Locked  Change the status to "Open" or remove the zone



[Check 11/36] Switch Upgrade Group Guidelines... No upgrade groups found!                                            MANUAL CHECK REQUIRED
[Check 12/36] APIC Disk Space Usage (F1527, F1528, F1529 equipment-full)...                                                           PASS
[Check 13/36] Switch Node /bootflash usage... all below 50%                                                                           PASS
[Check 14/36] Standby APIC Disk Space Usage... No standby APIC found                                                                   N/A
[Check 15/36] APIC SSD Health (F2731 equipment-wearout)...                                                                            PASS
[Check 16/36] Switch SSD Health (F3073, F3074 equipment-flash-warning)...                                                             PASS
[Check 17/36] Config On APIC Connected Port (F0467 port-configured-for-apic)...                                                       PASS
[Check 18/36] L3 Port Config (F0467 port-configured-as-l2)...                                                                         PASS
[Check 19/36] L2 Port Config (F0467 port-configured-as-l3)...                                                                         PASS
[Check 20/36] L3Out Subnets (F0467 prefix-entry-already-in-use)...                                                                    PASS
[Check 21/36] BD Subnets (F1425 subnet-overlap)...                                                                                    PASS
[Check 22/36] BD Subnets (F0469 duplicate-subnets-within-ctx)...                                                                      PASS
[Check 23/36] VMM Domain Controller Status...                                                                                         PASS
[Check 24/36] VMM Domain LLDP/CDP Adjacency Status... No LLDP/CDP Adjacency Failed Faults Found                                       PASS
[Check 25/36] Different infra VLAN via LLDP (F0454 infra-vlan-mismatch)...                                         FAIL - OUTAGE WARNING!!
  Fault  Pod  Node  Port     Recommended Action
  -----  ---  ----  ----     ------------------
  F0454  1    103   eth1/48  Disable LLDP on this port if it is expected to receive LLDP with a mismatched infra VLAN
  F0454  1    104   eth1/48  Disable LLDP on this port if it is expected to receive LLDP with a mismatched infra VLAN



[Check 26/36] HW Programming Failure (F3544 L3Out Prefixes, F3545 Contracts, actrl-resource-unavailable)...                           PASS
[Check 27/36] Scalability (faults related to Capacity Dashboard)...                                                                   PASS
[Check 28/36] VPC-paired Leaf switches...                                                                            MANUAL CHECK REQUIRED
  Node ID  Node Name  Recommended Action
  -------  ---------  ------------------
  101      f2-leaf1   Determine if dataplane redundancy is available if this node goes down
  102      f2-leaf2   Determine if dataplane redundancy is available if this node goes down

  Reference Document: "All switch nodes in vPC" from Pre-Upgrade Check Lists


[Check 29/36] Overlapping VLAN Pools...                                                                            FAIL - OUTAGE WARNING!!
  Tenant          AP   EPG     VLAN Pool (Domain) 1                         VLAN Pool (Domain) 2                       Recommended Action
  ------          --   ---     --------------------                         --------------------                       ------------------
  VLAN_POOL_TEST  AP1  EPG1-1  VLAN_TEST__EPG (VLAN_TEST__EPG)              VLAN_TEST__EPG_PORT (VLAN_TEST__EPG_PORT)  Resolve overlapping VLANs between these two VLAN pools
  VLAN_POOL_TEST  AP1  EPG1-1  VLAN_TEST__EPG_PORT2 (VLAN_TEST__EPG_PORT2)  VLAN_TEST__EPG (VLAN_TEST__EPG)            Resolve overlapping VLANs between these two VLAN pools
  VLAN_POOL_TEST  AP1  EPG1-1  VLAN_TEST__EPG_PORT2 (VLAN_TEST__EPG_PORT2)  VLAN_TEST__EPG_PORT (VLAN_TEST__EPG_PORT)  Resolve overlapping VLANs between these two VLAN pools

  Reference Document: "Overlapping VLAN Pool" from from Pre-Upgrade Check Lists


[Check 30/36] VNID Mismatch...                                                                                                        PASS
[Check 31/36] L3Out MTU... Verify that these MTUs match with connected devices                                       MANUAL CHECK REQUIRED
  Tenant  L3Out     Node Profile          Logical Interface Profile  Pod  Node     Interface       Type           IP Address    MTU
  ------  -----     ------------          -------------------------  ---  ----     ---------       ----           ----------    ---
  mgmt    INB_OSPF  INB_OSPF_nodeProfile  INB_OSPF_interfaceProfile  1    101      eth1/13         sub-interface  20.0.0.1/30   inherit (9000)



[Check 32/36] BGP Peer Profile at node level without Loopback...                                                                      PASS
[Check 33/36] L3Out Route Map import/export direction...                                                           FAIL - OUTAGE WARNING!!
  Tenant  L3Out  External EPG  Subnet      Subnet Scope                   Route Map         Direction  Recommended Action
  ------  -----  ------------  ------      ------------                   ---------         ---------  ------------------
  MT      OSPF   EPG1          10.0.0.0/8  export-rtctrl,import-security  CSCvm75395_test   import     The subnet scope must have import-rtctrl
  MT      OSPF   EPG1          10.0.0.0/8  export-rtctrl,import-security  CSCvm75395_test2  import     The subnet scope must have import-rtctrl
  MT      OSPF   EPG1          20.0.0.0/8  import-rtctrl                  CSCvm75395_test   export     The subnet scope must have export-rtctrl



[Check 34/36] Intersight Device Connector upgrade status...                                                                           PASS
[Check 35/36] EP Announce Compatibility...                                                                                            PASS
[Check 36/36] Eventmgr DB size defect susceptibility...                                                                               PASS

=== Summary Result ===

PASS                     : 26
FAIL - OUTAGE WARNING!!  :  4
FAIL - UPGRADE FAILURE!! :  0
MANUAL CHECK REQUIRED    :  3
N/A                      :  3
ERROR !!                 :  0
TOTAL                    : 36

    Pre-Upgrade Check Complete.
    Next Steps: Address all checks flagged as FAIL, ERROR or MANUAL CHECK REQUIRED

    Result output and debug info saved to below bundle for later reference.
    Attach this bundle to Cisco TAC SRs opened to address the flagged checks.

      Result Bundle: /data/techsupport/preupgrade_validator_2021-07-30T13-28-25-0700.tgz
```

