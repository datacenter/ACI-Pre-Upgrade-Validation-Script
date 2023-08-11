# Introduction

Run the script on your APIC and get prepared for your ACI upgrade.

## Quick Start

1. Copy [`aci-preupgrade-validation-script.py`](https://raw.githubusercontent.com/datacenter/ACI-Pre-Upgrade-Validation-Script/master/aci-preupgrade-validation-script.py) to your APIC (suggested path: `/data/techsupport`)
2. On your APIC, run `cd /data/techsupport` then `python aci-preupgrade-validation-script.py`
3. Provide a user name and password (admin level privileges are recommended) 
4. Select the target version (the version needs to be on APIC)
5. Follow recommendations for all checks that have been flagged as `FAIL` or `MANUAL CHECK REQUIRED`

### Example

```sh
# On your local machine
your_machine> git clone git@github.com:datacenter/ACI-Pre-Upgrade-Validation-Script.git
your_machine> cd ACI-Pre-Upgrade-Validation-Script
your_machine> scp aci-preupgrade-validation-script.py admin@<apic IP>:/data/techsupport

# On your APIC CLI
admin@f2-apic1:~> cd /data/techsupport
admin@f2-apic1:techsupport> python aci-preupgrade-validation-script.py
    ==== 2023-08-10T16-54-29+0000, Script Version v1.6.0  ====

!!!! Check https://github.com/datacenter/ACI-Pre-Upgrade-Validation-Script for Latest Release !!!!

To use a non-default Login Domain, enter apic#DOMAIN\\USERNAME
Enter username for APIC login          : admin
Enter password for corresponding User  :

Checking current APIC version (switch nodes are assumed to be on the same version)...5.0(1g)

Gathering APIC Versions from Firmware Repository...

[1]: aci-apic-dk9.5.2.1d.bin
[2]: aci-apic-dk9.5.2.1g.bin

What is the Target Version?     : 1

You have chosen version "aci-apic-dk9.5.2.1d.bin"

[Check  1/47] APIC Target version image and MD5 hash...
              Checking f2-apic1......                                                                                                 DONE
                                                                                                                                      PASS
[Check  2/47] Target version compatibility...                                                                                         PASS
--- omit ---

=== Summary Result ===

PASS                     : 36
FAIL - OUTAGE WARNING!!  :  5       <--- Watch for these !!!
FAIL - UPGRADE FAILURE!! :  0       <--- Watch for these !!!
MANUAL CHECK REQUIRED    :  3       <--- Watch for these !!!
N/A                      :  3
ERROR !!                 :  0
TOTAL                    : 47

--- omit ---
```


## Example full output

```
admin@f2-apic1:techsupport> python aci-preupgrade-validation-script.py
    ==== 2023-08-10T16-54-29+0000, Script Version v1.6.0  ====

!!!! Check https://github.com/datacenter/ACI-Pre-Upgrade-Validation-Script for Latest Release !!!!

To use a non-default Login Domain, enter apic#DOMAIN\\USERNAME
Enter username for APIC login          : admin
Enter password for corresponding User  :

Checking current APIC version (switch nodes are assumed to be on the same version)...5.0(1g)

Gathering APIC Versions from Firmware Repository...

[1]: aci-apic-dk9.5.2.1d.bin
[2]: aci-apic-dk9.5.2.1g.bin

What is the Target Version?     : 1

You have chosen version "aci-apic-dk9.5.2.1d.bin"

[Check  1/47] APIC Target version image and MD5 hash...
              Checking f2-apic1......                                                                                                 DONE
                                                                                                                                      PASS
[Check  2/47] Target version compatibility...                                                                                         PASS
[Check  3/47] Gen 1 switch compatibility...                                                                                           PASS
[Check  4/47] Remote Leaf Compatibility... No Remote Leaf Found                                                                        N/A
[Check  5/47] APIC CIMC Compatibility...                                                                                              PASS
[Check  6/47] APIC Cluster is Fully-Fit...                                                                                            PASS
[Check  7/47] Switches are all in Active state...                                                                                     PASS
[Check  8/47] NTP Status...                                                                                                           PASS
[Check  9/47] Firmware/Maintenance Groups when crossing 4.0 Release... Versions not applicable                                         N/A
[Check 10/47] Features that need to be Disabled prior to Upgrade...                                                FAIL - OUTAGE WARNING!!
  Feature      Name            Status  Recommended Action
  -------      ----            ------  ------------------
  App Center   ELAM Assistant  active  Disable the app
  App Center   Policy Viewer   active  Disable the app
  Config Zone  test            Locked  Change the status to "Open" or remove the zone



[Check 11/47] Switch Upgrade Group Guidelines... No upgrade groups found!                                            MANUAL CHECK REQUIRED
[Check 12/47] APIC Disk Space Usage (F1527, F1528, F1529 equipment-full)...                                                           PASS
[Check 13/47] Switch Node /bootflash usage... all below 50%                                                                           PASS
[Check 14/47] Standby APIC Disk Space Usage... No standby APIC found                                                                   N/A
[Check 15/47] APIC SSD Health...                                                                                                      PASS
[Check 16/47] Switch SSD Health (F3073, F3074 equipment-flash-warning)...                                                             PASS
[Check 17/47] Config On APIC Connected Port (F0467 port-configured-for-apic)...                                                       PASS
[Check 18/47] L3 Port Config (F0467 port-configured-as-l2)...                                                                         PASS
[Check 19/47] L2 Port Config (F0467 port-configured-as-l3)...                                                                         PASS
[Check 20/47] L3Out Subnets (F0467 prefix-entry-already-in-use)...                                                                    PASS
[Check 21/47] Encap Already In Use (F0467 encap-already-in-use)...                                                                    PASS
[Check 22/47] BD Subnets (F1425 subnet-overlap)...                                                                                    PASS
[Check 23/47] BD Subnets (F0469 duplicate-subnets-within-ctx)...                                                                      PASS
[Check 24/47] VMM Domain Controller Status...                                                                                         PASS
[Check 25/47] VMM Domain LLDP/CDP Adjacency Status... No LLDP/CDP Adjacency Failed Faults Found                                       PASS
[Check 26/47] Different infra VLAN via LLDP (F0454 infra-vlan-mismatch)...                                         FAIL - OUTAGE WARNING!!
  Fault  Pod  Node  Port     Recommended Action
  -----  ---  ----  ----     ------------------
  F0454  1    103   eth1/48  Disable LLDP on this port if it is expected to receive LLDP with a mismatched infra VLAN
  F0454  1    104   eth1/48  Disable LLDP on this port if it is expected to receive LLDP with a mismatched infra VLAN



[Check 27/47] HW Programming Failure (F3544 L3Out Prefixes, F3545 Contracts, actrl-resource-unavailable)...                           PASS
[Check 28/47] Scalability (faults related to Capacity Dashboard)...                                                                   PASS
[Check 29/47] VPC-paired Leaf switches...                                                                            MANUAL CHECK REQUIRED
  Node ID  Node Name  Recommended Action
  -------  ---------  ------------------
  101      f2-leaf1   Determine if dataplane redundancy is available if this node goes down
  102      f2-leaf2   Determine if dataplane redundancy is available if this node goes down

  Reference Document: "All switch nodes in vPC" from Pre-Upgrade Check Lists


[Check 30/47] Overlapping VLAN Pools...                                                                            FAIL - OUTAGE WARNING!!
  Tenant          AP   EPG     VLAN Pool (Domain) 1                         VLAN Pool (Domain) 2                       Recommended Action
  ------          --   ---     --------------------                         --------------------                       ------------------
  VLAN_POOL_TEST  AP1  EPG1-1  VLAN_TEST__EPG (VLAN_TEST__EPG)              VLAN_TEST__EPG_PORT (VLAN_TEST__EPG_PORT)  Resolve overlapping VLANs between these two VLAN pools
  VLAN_POOL_TEST  AP1  EPG1-1  VLAN_TEST__EPG_PORT2 (VLAN_TEST__EPG_PORT2)  VLAN_TEST__EPG (VLAN_TEST__EPG)            Resolve overlapping VLANs between these two VLAN pools
  VLAN_POOL_TEST  AP1  EPG1-1  VLAN_TEST__EPG_PORT2 (VLAN_TEST__EPG_PORT2)  VLAN_TEST__EPG_PORT (VLAN_TEST__EPG_PORT)  Resolve overlapping VLANs between these two VLAN pools

  Reference Document: "Overlapping VLAN Pool" from from Pre-Upgrade Check Lists


[Check 31/47] VNID Mismatch...                                                                                                        PASS
[Check 32/47] L3Out MTU... Verify that these MTUs match with connected devices                                       MANUAL CHECK REQUIRED
  Tenant  L3Out     Node Profile          Logical Interface Profile  Pod  Node     Interface       Type           IP Address    MTU
  ------  -----     ------------          -------------------------  ---  ----     ---------       ----           ----------    ---
  mgmt    INB_OSPF  INB_OSPF_nodeProfile  INB_OSPF_interfaceProfile  1    101      eth1/13         sub-interface  20.0.0.1/30   inherit (9000)



[Check 33/47] BGP Peer Profile at node level without Loopback...                                                                      PASS
[Check 34/47] L3Out Route Map import/export direction...                                                           FAIL - OUTAGE WARNING!!
  Tenant  L3Out  External EPG  Subnet      Subnet Scope                   Route Map         Direction  Recommended Action
  ------  -----  ------------  ------      ------------                   ---------         ---------  ------------------
  MT      OSPF   EPG1          10.0.0.0/8  export-rtctrl,import-security  CSCvm75395_test   import     The subnet scope must have import-rtctrl
  MT      OSPF   EPG1          10.0.0.0/8  export-rtctrl,import-security  CSCvm75395_test2  import     The subnet scope must have import-rtctrl
  MT      OSPF   EPG1          20.0.0.0/8  import-rtctrl                  CSCvm75395_test   export     The subnet scope must have export-rtctrl



[Check 35/47] Intersight Device Connector upgrade status...                                                                           PASS
[Check 36/47] ISIS Redistribution metric for MPod/MSite...                                                         FAIL - OUTAGE WARNING!!
  ISIS Redistribution Metric  MPod Deployment  MSite Deployment  Recommendation
  --------------------------  ---------------  ----------------  --------------
  63                          True             False             Change ISIS Redistribution Metric to less than 63

  Reference Document: "ISIS Redistribution Metric" from ACI Best Practices Quick Summary - http://cs.co/9001zNNr7


[Check 37/47] BGP route target type for GOLF over L2EVPN...                                                                           PASS
[Check 38/47] APIC Container Bridge IP Overlap with APIC TEP...                                                                       PASS
[Check 39/47] EP Announce Compatibility...                                                                                            PASS
[Check 40/47] Eventmgr DB size defect susceptibility...                                                                               PASS
[Check 41/47] Contract Port 22 Defect...                                                                                              PASS
[Check 42/47] telemetryStatsServerP Object...                                                                                         PASS
[Check 43/47] Link Level Flow Control...                                                                                              PASS
[Check 44/47] Internal VLAN Pool...                                                                                                   PASS
[Check 45/47] APIC CA Cert Validation...                                                                                              PASS
[Check 46/47] FabricDomain Name...                                                                                                    PASS
[Check 47/47] Spine SUP HW Revision...                                                                                                PASS


=== Summary Result ===

PASS                     : 36
FAIL - OUTAGE WARNING!!  :  5
FAIL - UPGRADE FAILURE!! :  0
MANUAL CHECK REQUIRED    :  3
N/A                      :  3
ERROR !!                 :  0
TOTAL                    : 47

    Pre-Upgrade Check Complete.
    Next Steps: Address all checks flagged as FAIL, ERROR or MANUAL CHECK REQUIRED

    Result output and debug info saved to below bundle for later reference.
    Attach this bundle to Cisco TAC SRs opened to address the flagged checks.

      Result Bundle: /data/techsupport/preupgrade_validator_2023-08-11T13-35-18-0700.tgz
```
