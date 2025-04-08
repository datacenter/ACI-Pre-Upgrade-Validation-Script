# Validation Reference

Tables in this page list the validations supported by the script and compare them with other pre-upgrade validation tools for Cisco ACI.

* **This Script**: The python script provided in [GitHub][0]
* **APIC built-in**: A validator embedded in the Cisco APIC Upgrade Workflow. This is automatically performed when performing an upgrade or downgrade for the Cisco APIC or switches.
* **Pre-Upgrade Validator (App)**: A validator that can be installed on the Cisco APICs as an app that can be downloaded through dcappcenter.cisco.com.

!!! info
    The tables in this page assume the **latest version** of the script.

    If you copied the script to your APIC in the past, make sure that is still the latest version.


## Summary List

### General Checks

Items                                                        | This Script        | APIC built-in             | Pre-Upgrade Validator (App)
-------------------------------------------------------------|--------------------|---------------------------|---------------------------
[Compatibility (Target ACI Version)][g1]                     | :white_check_mark: | :white_check_mark: 4.2(4) | :white_check_mark:
[Compatibility (CIMC Version)][g2]                           | :white_check_mark: | :white_check_mark: 4.2(4) | :white_check_mark:
[Compatibility (Switch Hardware)][g3]                        | :no_entry_sign:    | :white_check_mark:        | :no_entry_sign:
[Compatibility (Switch Hardware Gen1)][g4]                   | :white_check_mark: | :white_check_mark: 4.2(4) | :white_check_mark:
[Compatibility (Remote Leaf Switch)][g5]                     | :white_check_mark: | :grey_exclamation: Except CSCvs16767 | :white_check_mark:
[APIC Target version image and MD5 hash][g6]                 | :white_check_mark: | :white_check_mark: 5.2(3e)| :no_entry_sign:
[APIC Cluster is Fully-Fit][g7]                              | :white_check_mark: | :white_check_mark: 4.2(6) | :white_check_mark:
[Switches are all in Active state][g8]                       | :white_check_mark: | :no_entry_sign:           | :white_check_mark:
[NTP Status][g9]                                             | :white_check_mark: | :white_check_mark: 4.2(5) | :white_check_mark:
[Firmware/Maintenance Groups when crossing 4.0 Release][g10] | :white_check_mark: | :no_entry_sign:           | :white_check_mark:
[Features that need to be disabled prior to Upgrade][g11]    | :white_check_mark: | :grey_exclamation: 5.2(c)<br>Only AppCenter Apps | :white_check_mark:
[Switch Upgrade Group Guidelines][g12]                       | :white_check_mark: | :grey_exclamation: 4.2(4)<br>Only RR spines (IPN connectivity not checked) | :white_check_mark:
[Intersight Device Connector upgrade status][g13]            | :white_check_mark: | :white_check_mark: 4.2(5) | :white_check_mark:
[Mini ACI Upgrade to 6.0(2)+][g14]                           | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[Post Upgrade CallBack Integrity][g15]                       | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[6.0(2)+ requires 32 and 64 bit switch images][g16]          | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[Leaf to Spine Redundancy Validation][g17]                   | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:

[g1]: #compatibility-target-aci-version
[g2]: #compatibility-cimc-version
[g3]: #compatibility-switch-hardware
[g4]: #compatibility-switch-hardware-gen1
[g5]: #compatibility-remote-leaf-switch
[g6]: #apic-target-version-image-and-md5-hash
[g7]: #apic-cluster-is-fully-fit
[g8]: #switches-are-all-in-active-state
[g9]: #ntp-status
[g10]: #firmwaremaintenance-groups-when-crossing-40-release
[g11]: #features-that-need-to-be-disabled-prior-to-upgrade
[g12]: #switch-upgrade-group-guidelines
[g13]: #intersight-device-connector-upgrade-status
[g14]: #mini-aci-upgrade-to-602-or-later
[g15]: #post-upgrade-callback-integrity
[g16]: #602-requires-32-and-64-bit-switch-images
[g17]: #leaf-to-spine-redundancy-validation

### Fault Checks
Items                                         | Faults         | This Script       | APIC built-in                 | Pre-Upgrade Validator (App)
----------------------------------------------|----------------|-------------------|-------------------------------|--------------------------------
[APIC Disk Space Usage][f1]                   | F1527: 80% - 85%<br>F1528: 85% - 90%<br>F1529: 90% or more | :white_check_mark: | :white_check_mark: 4.2(1) | :white_check_mark:
[Standby APIC Disk Space Usage][f2]           |                | :white_check_mark: | :white_check_mark: 5.2(3) | :no_entry_sign:
[Switch Node `/bootflash` usage][f3]          | F1821: 90% or more | :white_check_mark: | :white_check_mark: 4.2(4) | :white_check_mark:
[APIC SSD Health][f4]                         | F2730: less than 10% remaining<br>F2731: less than 5% remaining<br>F2732: less than 1% remaining | :white_check_mark: | :white_check_mark: 4.2(1) | :white_check_mark:
[Switch SSD Health][f5]                       | F3074: reached 80% lifetime<br>F3073: reached 90% lifetime<br> | :white_check_mark: | :white_check_mark: 4.2(1) | :white_check_mark:
[Config On APIC Connected Port][f6]           | F0467: port-configured-for-apic | :white_check_mark: | :white_check_mark: 6.0(1g) | :white_check_mark:
[L3 Port Config][f7]                          | F0467: port-configured-as-l2 | :white_check_mark: | :white_check_mark: 5.2(4d) | :white_check_mark:
[L2 Port Config][f8]                          | F0467: port-configured-as-l3 | :white_check_mark: | :white_check_mark: 5.2(4d) | :white_check_mark:
[Access (Untagged) Port Config][f9]           | F0467: native-or-untagged-encap-failure | :white_check_mark: | :no_entry_sign: | :no_entry_sign:
[Encap Already in Use][f10]                   | F0467: encap-already-in-use | :white_check_mark: | :no_entry_sign: | :no_entry_sign:
[L3Out Subnets][f11]                          | F0467: prefix-entry-already-in-use | :white_check_mark: | :white_check_mark: 6.0(1g) | :white_check_mark:
[BD Subnets][f12]                             | F0469: duplicate-subnets-within-ctx | :white_check_mark: | :white_check_mark: 5.2(4d) | :white_check_mark:
[BD Subnets][f13]                             | F1425: subnet-overlap | :white_check_mark: | :white_check_mark: 5.2(4d) | :white_check_mark:
[VMM Domain Controller Status][f14]           | F0130         | :white_check_mark: | :white_check_mark: 4.2(1) | :white_check_mark:
[VMM Domain LLDP/CDP Adjacency Status][f15]   | F606391       | :white_check_mark: | :white_check_mark: 4.2(1) | :white_check_mark:
[Different infra VLAN via LLDP][f16]          | F0454: infra-vlan-mismatch | :white_check_mark: | :white_check_mark: 4.2(4) | :white_check_mark:
[HW Programming Failure][f17]                 | F3544: L3Out Prefixes<br>F3545: Contracts | :white_check_mark: | :white_check_mark: 5.1(1) | :white_check_mark:
[Scalability (faults related to Capacity Dashboard)][f18] | TCA faults for eqptcapacityEntity | :white_check_mark: | :no_entry_sign: | :white_check_mark:
[Fabric Port is Down][f19]                    | F1394: ethpm-if-port-down-fabric | :white_check_mark: | :no_entry_sign: | :no_entry_sign:
[Equipment Disk Limits Exceeded][f20]         | F1820: 80% -minor<br>F1821: -major<br>F1822: -critical | :white_check_mark: | :no_entry_sign: | :no_entry_sign:



[f1]: #apic-disk-space-usage
[f2]: #standby-apic-disk-space-usage
[f3]: #switch-node-bootflash-usage
[f4]: #apic-ssd-health
[f5]: #switch-ssd-health
[f6]: #config-on-apic-connected-port
[f7]: #l2l3-port-config
[f8]: #l2l3-port-config
[f9]: #access-untagged-port-config
[f10]: #encap-already-in-use
[f11]: #l3out-subnets
[f12]: #bd-subnets
[f13]: #bd-subnets
[f14]: #vmm-domain-controller-status
[f15]: #vmm-domain-lldpcdp-adjacency-status
[f16]: #different-infra-vlan-via-lldp
[f17]: #hw-programming-failure
[f18]: #scalability-faults-related-to-capacity-dashboard
[f19]: #fabric-port-is-down
[f20]: #equipment-disk-limits-exceeded


### Configuration Checks

 Items                                                | This Script        | APIC built-in             | Pre-Upgrade Validator (App)
------------------------------------------------------|--------------------|---------------------------|-------------------------------
[VPC-paired Leaf switches][c1]                        | :white_check_mark: | :white_check_mark: 4.2(4) | :white_check_mark:
[Overlapping VLAN Pool][c2]                           | :white_check_mark: | :no_entry_sign:           | :white_check_mark:
[VNID Mismatch][c3] (deprecated)                      | :warning:          | :no_entry_sign:           | :no_entry_sign:
[L3Out MTU][c4]                                       | :white_check_mark: | :no_entry_sign:           | :white_check_mark:
[BGP Peer Profile at node level without Loopback][c5] | :white_check_mark: | :no_entry_sign:           | :white_check_mark:
[L3Out Route Map import/export direction][c6]         | :white_check_mark: | :no_entry_sign:           | :white_check_mark:
[L3Out Route Map Match Rule with missing-target][c7]  | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[L3Out Loopback IP Overlap with L3Out Interfaces][c8] | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[ISIS Redistribution Metric for MPod/Msite][c9]       | :white_check_mark: | :no_entry_sign:           | :white_check_mark:
[BGP Route-target Type for GOLF over L2EVPN][c10]     | :white_check_mark: | :no_entry_sign:           | :white_check_mark:
[APIC Container Bridge IP Overlap with APIC TEP][c11] | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[Per-Leaf Fabric Uplink Scale Validation][c12]        | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[OoB Mgmt Security][c13]                              | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[EECDH SSL Cipher Disabled][c14]                      | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[BD and EPG Subnet must have matching scopes][c15]    | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[Unsupported FEC Configuration for N9K-C93180YC-EX][c16]    | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[CloudSec Encryption Check][c17]                      | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[Out-of-Service Ports check][c18]                     | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:  
[TEP-to-TEP atomic counters Scalability Check][c19]   | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[HTTPS Request Throttle Rate][c20]                    | :white_check_mark: | :no_entry_sign:           | :no_entry_sign:
[Global AES Encryption][c21]                          | :white_check_mark: | :white_check_mark: 6.1(2) | :no_entry_sign:

[c1]: #vpc-paired-leaf-switches
[c2]: #overlapping-vlan-pool
[c3]: #vnid-mismatch
[c4]: #l3out-mtu
[c5]: #bgp-peer-profile-at-node-level-without-loopback
[c6]: #l3out-route-map-importexport-direction
[c7]: #l3out-route-map-match-rule-with-missing-target
[c8]: #l3out-loopback-ip-overlap-with-l3out-interfaces
[c9]: #isis-redistribution-metric-for-mpodmsite
[c10]: #bgp-route-target-type-for-golf-over-l2evpn
[c11]: #apic-container-bridge-ip-overlap-with-apic-tep
[c12]: #fabric-uplink-scale-cannot-exceed-56-uplinks-per-leaf
[c13]: #oob-mgmt-security
[c14]: #eecdh-ssl-cipher
[c15]: #bd-and-epg-subnet-must-have-matching-scopes
[c16]: #unsupported-fec-configuration-for-n9k-c93180yc-ex
[c17]: #cloudsec-encryption-check
[c18]: #out-of-service-ports-check
[c19]: #tep-to-tep-atomic-counters-scalability-check
[c20]: #https-request-throttle-rate
[c21]: #global-aes-encryption

### Defect Condition Checks

Items                                           | Defect       | This Script        |  APIC built-in            | Pre-Upgrade Validator (App)
------------------------------------------------|--------------|--------------------|---------------------------|---------------------------
[EP Announce Compatibility][d1]                 | CSCvi76161   | :white_check_mark: | :no_entry_sign:           |:white_check_mark:
[Eventmgr DB size defect susceptibility][d2]    | CSCvn20175   | :white_check_mark: | :no_entry_sign:           |:white_check_mark:
[Contract Port 22 Defect][d3]             | CSCvz65560   | :white_check_mark: | :no_entry_sign:           |:white_check_mark:
[telemetryStatsServerP Object Check][d4]        | CSCvt47850   | :white_check_mark: | :no_entry_sign:           |:white_check_mark:
[Link Level Flow Control Check][d5]             | CSCvo27498   | :white_check_mark: | :no_entry_sign:           |:white_check_mark:
[Internal VLAN Pool Check][d6]                  | CSCvw33061   | :white_check_mark: | :no_entry_sign:           |:white_check_mark:
[APIC CA Cert Validation][d7]                   | CSCvy35257   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[FabricDomain Name][d8]                   | CSCwf80352   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[Spine SUP HW Revision][d9]                     | CSCwb86706   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[SUP-A/A+ High Memory Usage][d10]               | CSCwh39489   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[VMM Uplink Container with empty Actives][d11]  | CSCvr96408   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[CoS 3 with Dynamic Packet Prioritization][d12] | CSCwf05073   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[N9K-C93108TC-FX3P/FX3H Interface Down][d13]    | CSCwh81430   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[Invalid fabricPathEp Targets][d14]   | CSCwh68103   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[LLDP Custom Interface Description][d15]        | CSCwf00416   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[Route-map Community Match][d16]                | CSCwb08081   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[L3out /32 overlap with BD Subnet][d17]         | CSCwb91766   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[vzAny-to-vzAny Service Graph when crossing 5.0 release][d18] | CSCwh75475   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[FC/FCOE support for EX switches][d19]         | CSCwm92166   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[Nexus 950X FM or LC Might Fail to boot after reload][d20] | CSCvg26013   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[Stale Decommissioned Spine Check][d21]               | CSCwf58763   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[GX2A Platform Model Check][d22]               | CSCwk77800   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[PBR High Scale Check][d23]               | CSCwi66348   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:
[Standby Sup Image Sync Check][d24]               | CSCwi66348   | :white_check_mark: | :no_entry_sign:           |:no_entry_sign:


[d1]: #ep-announce-compatibility
[d2]: #eventmgr-db-size-defect-susceptibility
[d3]: #contract-port-22-defect
[d4]: #telemetrystatsserverp-object
[d5]: #link-level-flow-control
[d6]: #internal-vlan-pool
[d7]: #apic-ca-cert-validation
[d8]: #fabricdomain-name
[d9]: #spine-sup-hw-revision
[d10]: #sup-aa-high-memory-usage
[d11]: #vmm-uplink-container-with-empty-actives
[d12]: #cos-3-with-dynamic-packet-prioritization
[d13]: #n9k-c93108tc-fx3pfx3h-interface-down
[d14]: #invalid-fabricpathep-targets
[d15]: #lldp-custom-interface-description
[d16]: #route-map-community-match
[d17]: #l3out-32-overlap-with-bd-subnet
[d18]: #vzany-to-vzany-service-graph-when-crossing-50-release
[d19]: #fcfcoe-support-for-ex-switches
[d20]: #nexus-950x-fm-or-lc-might-fail-to-boot-after-reload
[d21]: #stale-decommissioned-spine-check
[d22]: #gx2a-platform-model-check
[d23]: #pbr-high-scale-check
[d24]: #standby-sup-image-sync-check

## General Check Details

### Compatibility (Target ACI Version)

The [APIC Upgrade/Downgrade Support Matrix][1] should be checked for the supported upgrade paths from your current version.

The script performs the equivalent check by querying objects `compatRsUpgRel`.


### Compatibility (CIMC Version)

The script checks the minimum recommended CIMC version for the given APIC model on the target version by querying `compatRsSuppHw` objects.

As the `compatRsSuppHw` object recommendation is strictly tied to the target software image, it is possible that the [Release Note Documentation][4] for your model/target version has a different recommendation than what the software recommends. Always check the release note of your Target version and APIC model to ensure you are getting the latest recommendations.

!!! note
    Older versions of CIMC may required multi-step CIMC upgrades to get to the identified target version. Refer to the [Cisco UCS Rack Server Upgrade Matrix][22] for the latest documentation on which steps are required and support given your current and target CIMC versions.

### Compatibility (Switch Hardware)

The [Release Notes of ACI switches][2] should be checked for the target version to make sure your hardware is supported.

This is mainly for downgrades because all switches operating in one ACI version will be supported in newer ACI versions, except for [generation one switches][g4].

### Compatibility (Switch Hardware - gen1)

The script checks the presence of generation one switches when the upgrade is crossing 5.0(1)/15.0(1).

Or you can check the [Release Note 15.0(1) of ACI switches][3] to see the list of generation one switches, typically the one without any suffix such as N9K-C9372PX, that are no longer supported from 15.0(1) release.


### Compatibility (Remote Leaf Switch)

The script checks the requirement to use remote leaf switches on the target version.

It is critical to enable **Direct Traffic Forwarding** for remote leaf switches prior to upgrading to Cisco APIC release 5.0(1) as the option becomes mandatory starting from this release.

**Direct Traffic Forwarding** can be enabled starting from the Cisco APIC release 4.1(2). Note that additional configuration for TEP IP addresses such as Routable Subnets or External TEP might be required for this option to be enabled. This means that if you are running a version prior to 4.1(2) and you have a remote leaf switch configured, you cannot directly upgrade to release 5.0. In this case, we recommend that you upgrade to a 4.2 release, enable **Direct Traffic Forwarding**, and then upgrade to the desired 5.0 version.

See "Upgrade the Remote Leaf Switches and Enable Direct Traffic Forwarding" in the [Cisco APIC Layer 3 Networking Configuration Guide][4] for more information.

A related issue (CSCvs16767) is also addressed in this validation. If you are upgrading to the release 14.2(2) release while **Direct Traffic Forwarding** is enabled for the remote leaf switches, you may hit a defect (CSCvs16767) that could cause remote leaf switches to crash due to the Multicast FIB Distribution Manager (MFDM) process. This issue happens only when spine switches are upgraded to release 14.2(2) first while remote leaf switches with **Direct Traffic Forwarding** are still on release 14.1(2). Note that **Direct Traffic Forwarding** was introduced in release 14.1(2).

To avoid this issue, it is critical that you upgrade to release 14.2(3) or a later release instead of release 14.2(2) when **Direct Traffic Forwarding** is enabled.

If you must upgrade to release 14.2(2) for any reason, you must upgrade the remote leaf nodes first to avoid this issue.


### APIC Target version image and MD5 hash

When performing an upgrade in an ACI fabric, there are multiple image transfers that must occur to prepare all nodes for upgrades. Most of these transfers perform a first level image validation. However, in the event of a failure, there is value in double-checking the image on each respective node.

Upgrade Image transfer touchpoints:

1. Transfer the image onto your desktop/file server from cisco.com.

    Manually run MD5 against this image. You can validate the expected MD5 of the image from cisco.com.

2. Upload the image from your desktop or FTP server onto one of the Cisco APICs.

    See the *Downloading APIC and Switch Images on APICs* section in the ACI Upgrade Guide for instructions on performing this operation on the Cisco APICs:

       * Upgrading or Downgrading with APIC Releases Prior to 4.x Using the GUI
       * Upgrading or Downgrading with APIC Releases 4.x or 5.0 Using the GUI
       * Upgrading or Downgrading with APIC Release 5.1 or Later Using the GUI

    The Cisco APIC will automatically perform an image validation and raise a fault F0058 if the image looks corrupt or incomplete once the transfer has completed.

3. Once the image is added into the firmware repository, the initially uploaded Cisco APIC will copy that image to the remaining Cisco APICs in the cluster.
   
    You can manually check MD5 on each Cisco APIC's copy of the upgrade image by running the md5sum command against each Cisco APIC's copy of the image.

    !!! example
        ```
        APIC1# md5sum /firmware/fwrepos/fwrepo/aci-apic-dk9.5.2.1g.bin
        f4c79ac1bb3070b4555e507c3d310826 /firmware/fwrepos/fwrepo/aci-apic-dk9.5.2.1g.bin
        ```

4. The switches will eventually each get a copy of the switch .bin image when they are preparing for upgrade.
    
    You can run MD5 on the individual switch image within /bootflash.

    !!! example
        ```
        leaf1# md5sum /bootflash/aci-n9000-dk9.15.2.1g.bin
        02e3b3fb45a51e36db28e7ff917a0c96 /bootflash/aci-n9000-dk9.15.2.1g.bin
        ```


### APIC Cluster is Fully-Fit

The script checks whether or not the APIC cluster is in the **Fully Fit** state.

Or you can check the status in `System > Dashboard > Controller` to ensure that the cluster status on all your Cisco Application Policy Infrastructure Controllers (APICs) is in the **Fully Fit** state. If one or more of the APICs are in other state, such as **Data Layer Partially Diverged**, you must resolve the status of your APIC cluster first.

If your APICs are currently on release 4.2(1) or later, the command `acidiag cluster` on each APIC CLI will check the basic items related to APIC clustering for you. If not, follow Initial Fabric Setup in [ACI Troubleshooting Guide 2nd Edition][5]



### Switches are all in Active state

The script checks whether or not all ACI switches are in an **Active** state.

Check `Fabric > Inventory > Fabric Membership` in the APIC GUI to ensure that all your ACI switches are in an **Active** state. If one or more of the ACI switches are in other state, such as **Inactive**, **Maintenance**, etc., you must resolve those issues first.

**Inactive**: This means that the switch has fabric discovery issues, such as IP reachability from APICs through the ACI infra network. If your switches are currently on release 14.2(1) or later, the command `show discoveryissues` on the switch CLI will check the basic items related to switch fabric discovery for you.

**Maintenance**: This means that the switch is in **Maintenance Mode** through the GIR (Graceful Insertion and Removal) operation. This implies that the switch is isolated from the fabric and does not process most of the APIC communications, including the upgrade-related communications. You must bring the switch back to the **Active** state before you can perform an upgrade. If you want to gracefully upgrade the switch by isolating the switches from the network first, consider **Graceful Upgrade** instead. See the [Graceful Upgrade or Downgrade of ACI Switches][6] section in the ACI Upgrade Guide for details.


### NTP Status

The script checks all ACI nodes (APICs and switches) are synchronized to NTP.

Ensure that NTP is configured on both the APICs and the ACI switches along with the necessary IP reachability to the NTP servers through Out-of-band (OOB) or In-band (INB) from each individual node.

Check the following sections in [ACI Troubleshooting Guide 2nd Edition][5]

* In-band and out-of-band management
* Pod Policies — BGP RR / Date&Time / SNMP


### Firmware/Maintenance Groups when crossing 4.0 Release

Beginning with Cisco APIC release 4.0(1), there is only one type of switch update group instead of the two that were used in previous releases (the firmware groups and maintenance groups). By consolidating two groups into one, the upgrade configurations are simplified. However, when upgrading Cisco APICs from a pre-4.0 release to release 4.0(1) or later, you must remove all firmware group and maintenance group policies prior to the upgrade.

* To remove a firmware group policy, navigate to `Admin > Firmware > Fabric Node Firmware > Firmware Groups`, then right-click on the name of firmware group and choose `Delete the Firmware Group`.

* To remove a maintenance group policy, navigate to `Admin > Firmware > Fabric Node Firmware > Maintenance Groups`, then right-click on the name of maintenance group and choose `Delete the Maintenance Group`.

Once the Cisco APICs are upgraded to 4.0(1) or later, you can create new switch update groups and perform the switch upgrade from pre-14.0 release to 14.0(1) or later.

This is applicable only when you are upgrading your Cisco APICs from pre-4.0 to 4.0(1) or later. Once your Cisco APICs are on 4.0(1) or later, you do not have to worry about this for any further upgrades.

!!! note
    Internally, Cisco APICs running the 4.0(1) or later release handle the switch update groups with the same objects as the old maintenance group policies (such as **maintMaintP**), but with additional attributes. If you are using an API to configure upgrade policies, you should only use maintenance group policies starting from Cisco APIC release 4.0(1) or later without manually creating any firmware group policies, unlike the old pre-4.0 releases.


### Features that need to be disabled prior to Upgrade

The following features must be disabled prior to upgrades or downgrades:

* App Center apps
* Maintenance Mode through Fabric > Inventory > Fabric Membership > Maintenance (GIR)
* Config Zone
* Rogue Endpoint (only when the running version is 14.1(x) or when upgrading to 14.1(x))


### Switch Upgrade Group Guidelines

The script checks if these [guidelines from the ACI Upgrade Guide][7] are followed.

* Rule 1 – Divide your leaf and spine switches into at least two groups
* Rule 2 – Determine how spine switches should be grouped
* Rule 3 – Determine how leaf switches should be grouped


### Intersight Device Connector upgrade status

If you start an Cisco APIC upgrade while an intersight Device Connector (DC) upgrade is in progress, the DC upgrade may fail.

You can check the status of intersight DC from `System > System Settings > intersight`. If the upgrade of the DC is in progress, wait for a minute and retry the Cisco APIC upgrade. The upgrade of the Intersight Device Connector typically takes less than a minute.

### Mini ACI Upgrade to 6.0(2) or later

Starting with APIC Release 6.0(2), controllers use a new linux operating system which requires any virtual APIC to be redeployed on the target version.

When upgrading from ACI release 6.0(1) or earlier to release 6.0(2) or later, any virtual APICs must be removed from the APIC cluster prior to upgrade. You must follow the documented steps under the [Mini ACI Upgrade Guide][18] for this specific upgrade path. A regular policy upgrade will fail and result in a diverged cluster.

!!! tip
    You can check whether any APICs are virtual by querying `topSystem` and looking at the `nodeType` attribute. `unspecified` is used for any physical APIC appliance while `virtual` is used for any virtual APIC.
    ```
    # top.System
    address                  : 10.1.0.2
    --- omit ---
    dn                       : topology/pod-1/node-2/sys
    lastRebootTime           : 2024-04-21T11:35:24.844-04:00
    lastResetReason          : unknown
    lcOwn                    : local
    modTs                    : 2024-04-21T11:56:04.032-04:00
    mode                     : unspecified
    monPolDn                 : uni/fabric/monfab-default
    name                     : vapic2
    nameAlias                :
    nodeType                 : virtual
    --- omit ---
    ```

### Post Upgrade CallBack Integrity

Post APIC cluster upgrade, APICs may invoke the post-upgrade callback against an existing object class, which will introduce an object of the new class corresponding to the existing class to extend/enhance/optimize an existing feature. This is also called data conversion.

Once successfully completed, the number of objects for the existing and newly created classes should be the same.

If the post-upgrade callback has failed or hasn't been able to fully complete for some reason, the data conversion will be incomplete.The impact of incomplete data conversion varies depending on the class that is missing as a result.

The post-upgrade callback may fail due to a software defect, or due to an inappropriate human intervention during APIC upgrades such as decommissioning an APIC, rebooting an APIC etc.

This validation checks whether the number of objects for the existing and newly created classes are the same.

!!! tip
    This validation **must** be performed after an APIC upgrade but before a switch upgrade.
    
    Regardless of this validation, it is a best practice to run this script twice, before an APIC upgrade AND before a switch upgrade, especially when the upgrade of the entire fabric cannot be completed within the same maintenance window. If you have been doing it, please keep doing it. If not, make sure to do that because this specific validation must be run after an APIC upgrade.
    Because of this reason, this validation warns users to run the script again if the current APIC version and the target version are different when the script is run because it implies the script was run before an APIC upgrade.


!!! example
    If the old/new class result is `infraRsToEncapInstDef`/`infraAssocEncapInstDef` or `infraRsToInterfacePolProfile`/`infraRsToInterfacePolProfileOpt`, the impact of incomplete post-upgrade callback (i.e. incomplete data conversion) is that VLANs will not be deployed on leaf switches after the upgrade of the switch.

    You can check the number of objects for each of these classes via moquery and the query option `rsp-subtree-include=count`:
    ```
    apic1# moquery -c infraRsToEncapInstDef -x rsp-subtree-include=count
    Total Objects shown: 1

    # mo.Count
    childAction  :
    count        : 11
    dn           : cnt
    lcOwn        : local
    modTs        : never
    rn           : cnt
    status       :


    apic1# moquery -c infraAssocEncapInstDef -x rsp-subtree-include=count
    Total Objects shown: 1

    # mo.Count
    childAction  :
    count        : 11
    dn           : cnt
    lcOwn        : local
    modTs        : never
    rn           : cnt
    status       :
    ```

    If the Mo count for both old/new classes are the same, it means that new class was created successfully after the APIC upgrade by the old class's post-upgrade callback.


### 6.0(2)+ requires 32 and 64 bit switch images

When targeting any version that is 6.0(2) or greater, download both the 32-bit and 64-bit Cisco ACI-mode switch images to the Cisco APIC. Downloading only one of the images may result in errors during the upgrade process.

For additional information, see the [Guidelines and Limitations for Upgrading or Downgrading][28] section of the Cisco APIC Installation and ACI Upgrade and Downgrade Guide.


### Leaf to Spine Redundancy Validation

When upgrading the Switches, traffic traversing any Leaf Switch that is connected to only a single spine will exhibit a Data Path Outage during the spine upgrade as there will be no alternate dataplane paths available.

To prevent this scenario, ensure that every leaf is connected to at least two Spine Switches. This check will alert if any Leaf Switches are found to only be connected to a single Spine Switch.


## Fault Check Details

### APIC Disk Space Usage

If a Cisco APIC is running low on disk space for any reason, the Cisco APIC upgrade can fail. The Cisco APIC will raise three different faults depending on the amount of disk space remaining. If any of these faults are raised on the system, the issue should be resolved prior to performing the upgrade.

* **F1527**: A warning level fault for Cisco APIC disk space usage. This is raised when the utilization is between 80% and 85%.

* **F1528**: A major level fault for Cisco APIC disk space usage. This is raised when the utilization is between 85% and 90%.

* **F1529**: A critical level fault for Cisco APIC disk space usage. This is raised when the utilization is between 90% and above.

You can run the following `moquery` on the CLI of any Cisco APIC to check if these faults exist on the system. The faults are visible within the GUI as well. In the example below, with the faults against `/firmware`, you can simply remove unnecessary firmware images under `Admin > Firmware` in the Cisco APIC GUI. You should not perform the Linux command rm to remove an image directly from `/firmware`, as the firmware images are synchronized across Cisco APICs. If the fault is raised against a disk space that you are not aware of, contact Cisco TAC to resolve the issue prior to the upgrade.

!!! example "Fault Example (F1528: Major Fault for APIC disk space usage)"
    The following shows an example situation where the disk space in `/firmware` is running low on APIC 1 (node 1).
    ```
    admin@apic1:~> moquery -c faultInst -f 'fault.Inst.code=="F1528"'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F1528
    ack              : no
    annotation       :
    cause            : equipment-full
    changeSet        : available (Old: 5646352, New: 6036744), capUtilized (Old: 86, New: 85), used (Old: 33393968, New: 33003576)
    childAction      :
    created          : 2021-05-27T11:58:19.061-04:00
    delegated        : no
    descr            : Storage unit /firmware on Node 1 with hostname apic1 mounted at /firmware is 85% full
    dn               : topology/pod-1/node-1/sys/ch/p-[/firmware]-f-[/dev/mapper/vg_ifc0-firmware]/fault-F1528
    domain           : infra
    extMngdBy        : undefined
    highestSeverity  : major
    lastTransition   : 2021-05-27T12:01:37.128-04:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : major
    prevSeverity     : major
    rn               : fault-F1528
    rule             : eqpt-storage-full-major
    severity         : major
    status           :
    subject          : equipment-full
    type             : operational
    uid              :
    ```

!!! note
    All three faults look the same except for the utilization percentage and the fault’s severity.


### Standby APIC Disk Space Usage

Because a standby Cisco APIC is a cold standby and is not part of the cluster, it is not actively monitored for fault conditions. As filesystem full checks falls under this category, this means that any standby Cisco APICs exhibiting these conditions will not flag a fault and instead must be manually verified.

The script performs SSH into each standby Cisco APIC as `rescue-user`, then run `df -h` to verify the filesystem usage. If any filesystem is found to be at 75% or above, the script will alert users to contact TAC to identify and clear out the condition.

!!! note
    This check is not using faults but positioned in Fault Check just to be viewed with other disk space usage checks using faults.


### Switch Node `/bootflash` usage

ACI switches mainly have two different faults about the filesystem usage of each partition:

* **F1820**: A minor level fault for switch partition usage. This is raised when the utilization of the partition exceeds the minor threshold.

* **F1821**: A major level fault for switch partition usage. This is raised when the utilization of the partition exceeds the major threshold.

!!! note
    The threshold for minor and major depends on partitions. The critical one for upgrades is `/bootflash`. The threshold of bootflash is 80% for minor and 90% for major threshold.

On top of this, there is a built-in behavior added to every switch node where it will take action to ensure that the `/bootflash` directory maintains 50% capacity. This is specifically to ensure that switch upgrades are able to successfully transfer and extract the switch image over during an upgrade.

To do this, there is an internal script that is monitoring `/bootflash` usage and, if over 50% usage, it will start removing files to free up the filesystem. Given its aggressiveness, there are some corner case scenarios where this cleanup script could potentially trigger against the switch image it is intending to use, which can result in a switch upgrade booting a switch into the loader prompt given that the boot image was removed from `/bootflash`.

To prevent this, check the `/bootflash` prior to an upgrade and take the necessary steps to understand what is written there and why. Once understood, take the necessary steps to clear up unnecessary `/bootflash` files to ensure there is enough space to prevent the auto-cleanup corner case scenario.

The pre-upgrade validation built into Cisco APIC upgrade workflow monitors the fault F1821, which can capture the high utilization of any partition. When this fault is present, we recommend that you resolve it prior to the upgrade even if the fault is not for bootflash.

The ACI Pre-Upgrade Validation script (this script) focuses on the utilization of bootflash on each switch specifically to see if there are any issues with bootflash where the usage is more than 50%, which might trigger the internal cleanup script.

!!! example "Example of a query used by this script"
    The script is calculating the bootflash usage using `avail` and `used` in the object `eqptcapacityFSPartition` for each switch.
    ```
    f2-apic1# moquery -c eqptcapacityFSPartition -f 'eqptcapacity.FSPartition.path=="/bootflash"'
    Total Objects shown: 6

    # eqptcapacity.FSPartition
    name            : bootflash
    avail           : 7214920
    childAction     :
    dn              : topology/pod-1/node-101/sys/eqptcapacity/fspartition-bootflash
    memAlert        : normal
    modTs           : never
    monPolDn        : uni/fabric/monfab-default
    path            : /bootflash
    rn              : fspartition-bootflash
    status          :
    used            : 4320184
    --- omit ---
    ```

!!! tip
    Alternatively you can log into a leaf switch CLI, and check `/bootflash` usage `df -h`
    ```
    leaf1# df -h
    Filesystem             Size    Used   Avail   Use%   Mounted on
    rootfs                 2.5G    935M   1.6G    38%    /bin
    /dev/sda4               12G    5.7G   4.9G    54%    /bootflash
    /dev/sda2              4.7G    9.6M   4.4G     1%    /recovery
    /dev/mapper/map-sda9    11G    5.7G   4.2G    58%    /isan/lib
    none                   3.0G    602M   2.5G    20%    /dev/shm
    none                    50M    3.4M    47M     7%    /etc
    /dev/sda6               56M    1.3M    50M     3%    /mnt/cfg/1
    /dev/sda5               56M    1.3M    50M     3%    /mnt/cfg/0
    /dev/sda8               15G    140M    15G     1%    /mnt/ifc/log
    /dev/sda3              115M     52M    54M    50%    /mnt/pss
    none                   1.5G    2.3M   1.5G     1%    /tmp
    none                    50M    240K    50M     1%    /var/log
    /dev/sda7               12G    1.4G   9.3G    13%    /logflash
    none                   350M     54M   297M    16%    /var/log/dme/log/dme_logs
    none                   512M     24M   489M     5%    /var/sysmgr/mem_logs
    none                    40M    4.0K    40M     1%    /var/sysmgr/startup-cfg
    none                   500M     0     500M     0%    /volatile
    ```

!!! note
    If you suspect that the auto cleanup removed some files within `/bootflash`, you can review a log to validate this:

    ```
    leaf1# egrep "higher|removed" /mnt/pss/core_control.log
    [2020-07-22 16:52:08.928318] Bootflash Usage is higher than 50%!!
    [2020-07-22 16:52:08.931990] File: MemoryLog.65%_usage removed !!
    [2020-07-22 16:52:08.943914] File: mem_log.txt.old.gz removed !!
    [2020-07-22 16:52:08.955376] File: libmon.logs removed !!
    [2020-07-22 16:52:08.966686] File: urib_api_log.txt removed !!
    [2020-07-22 16:52:08.977832] File: disk_log.txt removed !!
    [2020-07-22 16:52:08.989102] File: mem_log.txt removed !!
    [2020-07-22 16:52:09.414572] File: aci-n9000-dk9.13.2.1m.bin removed !!
    ```


### APIC SSD Health

Starting from Cisco APIC release 2.3(1), faults occur when the SSD media wearout indicator (life remaining) is less than a certain percentage on Cisco APIC nodes. An SSD with little lifetime may cause any operations that require updates for the internal database, such as upgrade or downgrade operations, to fail. The Cisco APIC will raise three different faults, depending on the amount of SSD life remaining. If the most critical fault (F2732) is raised on the system, you must replace the SSD by contacting Cisco TAC prior to performing the upgrade.

* **F2730**: A warning level fault for Cisco APIC SSD life remaining. This is raised when the life remaining is less than 10%.

* **F2731**: A major level fault for Cisco APIC SSD life remaining. This is raised when the life remaining is less than 5%.

* **F2732**: A critical level fault for Cisco APIC SSD life remaining. This is raised when the life remaining is less than 1%.

Also, in very rare occasions, the SSD might have other operational issues than its lifetime. In such a case, look for the fault F0101.

However, if your Cisco APICs are still running on a release older than the 4.2(7f) or 5.2(1g), these fault may not report a correct value due to CSCvx28453. In such a case, look for `SSD Wearout Indicator is XX` in `/var/log/dme/log/svc_ifc_ae.bin.log` on your APICs, where XX is a number.

See the [APIC SSD Replacement technote][8] for more details.

!!! example "Fault Example (F2731: Major Fault for APIC SSD life remaining)"
    The following shows an example of APIC 3 (node 3) with an SSD life remaining of 1% (the major fault F2731). In this case, although the critical fault F2732 for the life remaining less than 1% is not raised, it is close enough to F2732’s threshold and it is recommended to replace the SSD.
    ```
    APIC1# moquery -c faultInfo -f 'fault.Inst.code=="F2731"'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F2731
    ack              : no
    annotation       :
    cause            : equipment-wearout
    changeSet        : mediaWearout (Old: 2, New: 1)
    childAction      :
    created          : 2019-10-22T11:47:40.791+01:00
    delegated        : no
    descr            : Storage unit /dev/sdb on Node 3 mounted at /dev/sdb has 1% life remaining
    dn               : topology/pod-2/node-3/sys/ch/p-[/dev/sdb]-f-[/dev/sdb]/fault-F2731
    domain           : infra
    extMngdBy        : undefined
    highestSeverity  : major
    lastTransition   : 2019-10-22T11:49:48.788+01:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : major
    prevSeverity     : major
    rn               : fault-F2731
    rule             : eqpt-storage-wearout-major
    severity         : major
    status           :
    subject          : equipment-wearout
    type             : operational
    uid              :
    ```


### Switch SSD Health

Starting from release 2.1(4), 2.2(4), 2.3(1o), and 3.1(2m), faults occur if the flash SSD lifetime usage has reached a certain endurance limit on the leaf or spine switches. A flash SSD with little lifetime may cause any operations that require updates for the internal database, such as Cisco APIC communication, to fail, or the switch may fail to boot up. The ACI switch will raise two different faults depending on the amount of SSD life it’s consumed. If the most critical fault (F3073) is raised on the system, you must replace the SSD by contacting Cisco TAC prior to performing the upgrade.

* **F3074**: A warning level fault for switch SSD lifetime. This is raised when the lifetime reached 80% of its limit.

* **F3073**: A major level fault for switch SSD lifetime. This is raised when the lifetime reached 90% of its limit.

You can run the moquery below on the CLI of any Cisco APIC to check if these faults exist on the system. The faults are visible within the GUI as well.

If your Cisco APICs are still running an older release, contact Cisco TAC to check the SSD life status.

See the [ACI Switch Node SSD Lifetime Explained technote][9] for more details.

!!! example "Fault Example (F3074: Warning Fault for switch SSD lifetime)"
    The following shows an example of node 101 that has reached 85% of its SSD lifetime.
    ```
    APIC1# moquery -c faultInst -f 'fault.Inst.code=="F3074"'

    Total Objects shown: 4
     
    # fault.Inst
    code             : F3074
    ack              : no
    annotation       : 
    cause            : equipment-flash-warning
    changeSet        : acc:read-write, cap:61057, deltape:23, descr:flash, gbb:0, id:1, lba:0, lifetime:85, majorAlarm:no, mfgTm:2020-09-22T02:21:45.675+00:00, minorAlarm:yes, model:Micron_M600_MTFDDAT064MBF, operSt:ok, peCycles:4290, readErr:0, rev:MC04, ser:MSA20400892, tbw:21.279228, type:flash, vendor:Micron, warning:yes, wlc:0
    childAction      : 
    created          : 2020-09-21T21:21:45.721-05:00
    delegated        : no
    descr            : SSD has reached 80% lifetime and is nearing its endurance limit. Please plan for Switch/Supervisor replacement soon
    dn               : topology/pod-1/node-101/sys/ch/supslot-1/sup/flash/fault-F3074
    domain           : infra
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2020-09-21T21:24:03.132-05:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F3074
    rule             : eqpt-flash-flash-minor-alarm
    severity         : minor
    status           : 
    subject          : flash-minor-alarm
    type             : operational
    --- omit ---
    ```


### Config On APIC Connected Port

In a healthy ACI deployment, there should be no EPG or policy deployment pushed to any interfaces where a Cisco APIC is connected. When a Cisco APIC is connected to a leaf switch, LLDP validation occurs between the Cisco APIC and the leaf switch to allow it into the fabric without any configuration by the user. When a policy is pushed to a leaf switch interface that is connected to a Cisco APIC, that configuration will be denied and a fault will be raised. However, if the link to the Cisco APIC flaps for any reason, primarily during an upgrade when the Cisco APIC reboots, the policy can then be deployed to that leaf switch interface. This results in the Cisco APIC being blocked from re-joining the fabric after it has reloaded.

It is critical that you resolve these issues before the upgrade to prevent any issues. You can run the moquery below on the CLI of any Cisco APIC to check if these faults exist on the system. The faults are visible within the GUI as well.

!!! example "Fault Example (F0467: port-configured-for-apic)"
    The following fault shows an example of node 101 eth1/1 that is connected to a Cisco APIC that has some EPG configurations on it.
    ```
    admin@apic1:~> moquery -c faultInst -x 'query-target-filter=wcard(faultInst.descr,"port-configured-for-apic")'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F0467
    ack              : no
    annotation       : 
    cause            : configuration-failed
    changeSet        : configQual:port-configured-for-apic, configSt:failed-to-apply, debugMessage:port-configured-for-apic: Port is connected to the APIC;, temporaryError:no
    childAction      :
    created          : 2021-06-03T07:51:42.263-04:00
    delegated        : yes
    descr            : Configuration failed for uni/tn-jr/ap-ap1/epg-epg1 node 101 eth1/1 due to Port Connected to Controller, debug message: port-configured-for-apic: Port is connected to the APIC;
    dn               : topology/pod-1/node-101/local/svc-policyelem-id-0/uni/epp/fv-[uni/tn-jr/ap-ap1/epg-epg1]/node-101/stpathatt-[eth1/1]/nwissues/fault-F0467
    domain           : tenant
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2021-06-03T07:53:52.021-04:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F0467
    rule             : fv-nw-issues-config-failed
    severity         : minor
    status           :
    subject          : management
    type             : config
    uid              :
    ```


### L2/L3 Port Config

This is another type of the F0467 fault code family that you should check before an upgrade. This fault alerts that an interface configured under a Layer3 Out (L3Out) has failed because the port that the policy is deployed for is operating in the opposite mode. For example, you might have configured a routed sub-interface under an L3Out, making the port an L3 port. However, there is already L2 policy on that port. A port in ACI can either be L2 or L3, but not both, just like a port on any layer 3 switches that can be either **switchport** (L2) or **no switchport** (L3), so this policy fails in this situation. The same rule applies if a port is already an L3 port, but you deploy L2 config onto it. After an upgrade, it’s possible that the previously working configuration will break if this faulty policy is deployed first after the switch reloads.

It is critical that you resolve these issues before the upgrade to prevent any issues. The interface that the fault is raised on should either be corrected or deleted in order to clear the fault. You can run the moquery below on the CLI of any Cisco APIC to check if these faults exist on the system. The faults are visible within the GUI as well.

!!! example "Fault Example (F0467: port-configured-as-l2)"
    The following fault shows an example of the configuration from L3Out `OSPF` under tenant `jr` has failed on node 101 eth1/7 because the same port is already configured as L2 by other components, such as EPGs or other L3Outs using the same port as SVI. It implies that, in this case, L3Out OSPF is trying to use node 101 eth1/7 as a routed port or routed sub-interface (L3) as opposed to SVI (L2).
    ```
    admin@apic1:~> moquery -c faultDelegate -x 'query-target-filter=wcard(faultInst.changeSet,"port-configured-as-l2")'
    Total Objects shown: 1
     
    # fault.Delegate
    affected         : resPolCont/rtdOutCont/rtdOutDef-[uni/tn-jr/out-OSPF]/node-101/stpathatt-[eth1/7]/nwissues
    code             : F0467
    ack              : no
    cause            : configuration-failed
    changeSet        : configQual:port-configured-as-l2, configSt:failed-to-apply, temporaryError:no
    childAction      :
    created          : 2021-06-23T12:17:54.775-04:00
    descr            : Fault delegate: Configuration failed for uni/tn-jr/out-OSPF node 101 eth1/7 due to Interface Configured as L2, debug message:
    dn               : uni/tn-jr/out-OSPF/fd-[resPolCont/rtdOutCont/rtdOutDef-[uni/tn-jr/out-OSPF]/node-101/stpathatt-[eth1/7]/nwissues]-fault-F0467
    domain           : tenant
    highestSeverity  : minor
    lastTransition   :2021-06-23T12:20:09.780-04:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fd-[resPolCont/rtdOutCont/rtdOutDef-[uni/tn-jr/out-OSPF]/node-101/stpathatt-[eth1/7]/nwissues]-fault-F0467
    rule             : fv-nw-issues-config-failed
    severity         : minor
    status           :
    subject          : management
    type             : config
    ```

!!! example "Fault Example (F0467: port-configured-as-l3)"
    The following fault shows an example of the opposite of above situation. In this example, L3Out IPV6 tries to use node 101 eth1/7 as an L2 port and it failed because other L3Outs are already using the same port as an L3 port.
    ```
    admin@apic1:~> moquery -c faultDelegate -x 'query-target-filter=wcard(faultInst.changeSet,"port-configured-as-l3")'
    Total Objects shown: 1

    # fault.Delegate
    affected         : resPolCont/rtdOutCont/rtdOutDef-[uni/tn-jr/out-IPV6]/node-101/stpathatt-[eth1/7]/nwissues
    code             : F0467
    ack              : no
    cause            : configuration-failed
    changeSet        : configQual:port-configured-as-l3, configSt:failed-to-apply, debugMessage:port-configured-as-l3: Port has one or more layer3 sub-interfaces;, temporaryError:no
    childAction      :
    created          : 2021-06-23T12:31:41.949-04:00
    descr            : Fault delegate: Configuration failed for uni/tn-jr/out-IPV6 node 101 eth1/7 due to Interface Configured as L3, debug message: port-configured-as-l3: Port has one or more layer3 sub-interfaces;
    dn               : uni/tn-jr/out-IPV6/fd-[resPolCont/rtdOutCont/rtdOutDef-[uni/tn-jr/out-IPV6]/node-101/stpathatt-[eth1/7]/nwissues]-fault-F0467
    domain           : tenant
    highestSeverity  : minor
    lastTransition   : 2021-06-23T12:31:41.949-04:00
    lc               : soaking
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fd-[resPolCont/rtdOutCont/rtdOutDef-[uni/tn-jr/out-IPV6]/node-101/stpathatt-[eth1/7]/nwissues]-fault-F0467
    rule             : fv-nw-issues-config-failed
    severity         : minor
    status           :
    subject          : management
    type             : config
    ```


### Access (Untagged) Port Config
The APIC GUI or REST previously accepted two different access encapsulations on the same port, despite raising a fault with code F0467 and "native-or-untagged-encap-failure" in the changeSet. This configuration, likely resulting from user error, presents a significant risk of outage during switch upgrades or stateless reloads.

The script verifies these faults to ensure that a port is not configured as part of two access VLANs. You need to resolve the conflict causing this fault before any upgrades to prevent potential outages. Failure to do so may result in the deployment of a new VLAN/EPG on the port after the upgrade, leading to downtime in the environment.

!!! example "Fault Example (F0467: native-or-untagged-encap-failure)"
    ```
    apic1# moquery -c faultInst  -x 'query-target-filter=wcard(faultInst.changeSet,"native-or-untagged-encap-failure")'
    Total Objects shown: 1

    # fault.Inst
    code             : F0467
    ack              : no
    alert            : no
    annotation       : 
    cause            : configuration-failed
    changeSet        : configQual:native-or-untagged-encap-failure, configSt:failed-to-apply, temporaryError:no
    childAction      : 
    created          : 2024-04-20T10:03:48.493+02:00
    delegated        : yes
    descr            : Configuration failed for uni/tn-EEA-1/ap-APP1/epg-EPG-2 node 101 eth1/28 due to Only One Native or Untagged Encap Allowed on Interface, debug message: 
    dn               : topology/pod-1/node-101/local/svc-policyelem-id-0/uni/epp/fv-[uni/tn-EEA-1/ap-APP1/epg-EPG-2]/node-101/stpathatt-[eth1/28]/nwissues/fault-F0467
    domain           : tenant
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2024-04-20T10:03:53.045+02:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F0467
    rule             : fv-nw-issues-config-failed
    severity         : minor
    status           : 
    subject          : management
    title            : 
    type             : config
    uid              : 
    userdom          : all
    apic1# 
    ```
Please note that this behavior has recently changed. With the new behavior, rejected through policy distributor validation, two different access encapsulations are no longer allowed on the same port by the APIC. This change has been documented in CSCwj69435.


### Encap Already in Use

This is another type of the F0467 fault code family that you should check before an upgrade. This fault alerts that an interface configuration under an EPG or an SVI configuration for an L3Out has failed because the VLAN encapsulation for the interface is already used by another interface on the same switch for a different purpose. After an upgrade, it’s possible that the previous working configuration will break if this faulty policy is deployed first after the switch reloads.

It is critical that you resolve these issues before the upgrade to prevent any unexpected outages when the switch(es) upgrade. The VLAN encapsulation on the interface that the fault is raised on should either be corrected or deleted in order to clear the fault. You can run the moquery in the example below on the CLI of any Cisco APIC to check if these faults exist on the system. The faults are visible within the GUI as well.

!!! example "Fault Example (F0467: encap-already-in-use)"
    The following shows three examples.

    The first fault is for the interface configuration under the EPG `EPG1-2` in application profile `AP1` in tenant `TK` on node `101` interface `eth1/4` with VLAN `2011`. The fault description indicates that VLAN `2011` is already used by EPG `EPG1-1` in application profile `AP1` in tenant `TK`.

    The second fault is for the SVI configuration under L3Out `BGP` in tenant `TK` on `node-103` interface `eth1/11` with VLAN `2013`. The fault description indicates that VLAN `2013` is already used by `EPG1-3` in application profile `AP1` in tenant `TK`.

    The third fault is for the interface configuration under the EPG `EPG3-1` in application profile `AP1` in tenant `TK` on node `103` interface `eth1/1` with VLAN `2051`. The fault description indicates that VLAN `2051` is already used by L3Out `BGP` in tenant `TK`.

    Note that the fault description may not include `(vlan-2011)` in `Encap (vlan-2011)` on older versions.
    ```
    admin@apic1:~> moquery -c faultInst -x 'query-target-filter=wcard(faultInst.descr,"encap-already-in-use")'
    Total Objects shown: 3

    # fault.Inst
    code             : F0467
    ack              : no
    alert            : no
    annotation       :
    cause            : configuration-failed
    changeSet        : configQual:encap-already-in-use, configSt:failed-to-apply, debugMessage:encap-already-in-use: Encap (vlan-2011) is already in use by TK:AP1:EPG1-1;, temporaryError:no
    childAction      :
    created          : 2024-04-19T21:02:20.878-07:00
    delegated        : yes
    descr            : Configuration failed for uni/tn-TK/ap-AP1/epg-EPG1-2 node 101 eth1/4 due to Encap Already Used in Another EPG, debug message: encap-already-in-use: Encap (vlan-2011) is already in use by TK:AP1:EPG1-1;
    dn               : topology/pod-1/node-101/local/svc-policyelem-id-0/uni/epp/fv-[uni/tn-TK/ap-AP1/epg-EPG1-2]/node-101/stpathatt-[eth1/4]/nwissues/fault-F0467
    domain           : tenant
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2024-04-19T21:04:25.300-07:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F0467
    rule             : fv-nw-issues-config-failed
    severity         : minor
    status           :
    subject          : management
    title            :
    type             : config
    uid              :
    userdom          : all

    # fault.Inst
    code             : F0467
    ack              : no
    alert            : no
    annotation       :
    cause            : configuration-failed
    changeSet        : configQual:encap-already-in-use, configSt:failed-to-apply, debugMessage:encap-already-in-use: Encap (vlan-2013) is already in use by TK:AP1:EPG1-3;, temporaryError:no
    childAction      :
    created          : 2024-04-19T21:59:31.948-07:00
    delegated        : yes
    descr            : Configuration failed for uni/tn-TK/out-BGP node 103 eth1/11 due to Encap Already Used in Another EPG, debug message: encap-already-in-use: Encap (vlan-2013) is already in use by TK:AP1:EPG1-3;
    dn               : topology/pod-2/node-103/local/svc-policyelem-id-0/resPolCont/rtdOutCont/rtdOutDef-[uni/tn-TK/out-BGP]/node-103/stpathatt-[eth1/11]/nwissues/fault-F0467
    domain           : tenant
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2024-04-19T21:59:31.948-07:00
    lc               : soaking
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F0467
    rule             : fv-nw-issues-config-failed
    severity         : minor
    status           :
    subject          : management
    title            :
    type             : config
    uid              :
    userdom          : all

    # fault.Inst
    code             : F0467
    ack              : no
    alert            : no
    annotation       :
    cause            : configuration-failed
    changeSet        : configQual:encap-already-in-use, configSt:failed-to-apply, debugMessage:encap-already-in-use: Encap (vlan-2051) is already in use by TK:VRFA:l3out-BGP:vlan-2051;, temporaryError:no
    childAction      :
    created          : 2024-04-19T21:58:02.758-07:00
    delegated        : yes
    descr            : Configuration failed for uni/tn-TK/ap-AP1/epg-EPG3-1 node 103 eth1/1 due to Encap Already Used in Another EPG, debug message: encap-already-in-use: Encap (vlan-2051) is already in use by TK:VRFA:l3out-BGP:vlan-2051;
    dn               : topology/pod-2/node-103/local/svc-policyelem-id-0/uni/epp/fv-[uni/tn-TK/ap-AP1/epg-EPG3-1]/node-103/stpathatt-[eth1/1]/nwissues/fault-F0467
    domain           : tenant
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2024-04-19T21:58:02.758-07:00
    lc               : soaking
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F0467
    rule             : fv-nw-issues-config-failed
    severity         : minor
    status           :
    subject          : management
    title            :
    type             : config
    uid              :
    userdom          : all
    ```


### L3Out Subnets

There is another type of the F0467 fault code family that you should check before an upgrade. This fault alerts that an external EPG defined under a Layer3 Out (L3Out) has a subnet with the **External Subnet for the External EPG** scope configured that overlaps with another L3Out external EPG in the same VRF. After an upgrade, it’s possible that the previous working configuration will break if this faulty policy is deployed first after the switch reloads.

It is critical that you resolve these issues before the upgrade to prevent any unexpected outages when the switch(es) upgrade. The subnet that the fault is raised on should either be corrected or deleted in order to clear the fault. You can run the moquery below on the CLI of any Cisco APIC to check if these faults exist on the system. The faults are visible within the GUI as well.

!!! example "Fault Example (F0467: prefix-entry-already-in-use)"
    The following shows an example of L3Out `OSPF` with an external EPG called `all`. In this external EPG, an L3Out subnet 112.112.112.112/32 is configured with **External Subnet for the External EPG** in the attempt to classify the source or destination IP address of packets to this external EPG for contracts application. However, it failed because the same subnet is already in use by another external EPG in the same VRF.
    ```
    admin@apic1:~> moquery -c faultInst -x'query-target-filter=wcard(faultInst.descr,"prefix-entry-already-in-use")'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F0467
    ack              : no
    annotation       :
    cause            : configuration-failed
    changeSet        : configQual:prefix-entry-already-in-use, configSt:failed-to-apply, debugMessage:prefix-entry-already-in-use: Prefix entry sys/ctx-[vxlan-2621440]/pfx-[112.112.112.112/32] is in use;, temporaryError:no
    childAction      :
    created          : 2021-06-22T09:02:36.630-04:00
    delegated        : yes
    descr            : Configuration failed for uni/tn-jr/out-OSPF/instP-all due to Prefix Entry Already Used in Another EPG, debug message: prefix-entry-already-in-use: Prefix entry sys/ctx-[vxlan-2621440]/pfx-[112.112.112.112/32] is in use;
    dn               : topology/pod-1/node-101/local/svc-policyelem-id-0/uni/epp/rtd-[uni/tn-jr/out-OSPF/instP-all]/nwissues/fault-F0467
    domain           : tenant
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2021-06-22T09:04:51.985-04:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F0467
    rule             : fv-nw-issues-config-failed
    severity         : minor
    status           :
    subject          : management
    type             : config
    uid              :
    ```


### BD Subnets

If at any point in time an overlapping IP address or subnet is deployed within a VRF, that policy will fail and a fault will be raised at the node level. However, on upgrade, it’s possible that this previously failing configuration will get pushed to the leaf switch before the previously working configuration. This results in a situation where the known working state before the upgrade is broken after the upgrade and can cause connectivity issues for the previously working subnet.

There are two faults for this situation:

* **F0469** (duplicate-subnets-within-ctx) is raised when multiple BD subnets are configured with the exact same subnet in the same VRF

* **F1425** (subnet-overlap) is raised when BD subnets are not the same but overlapping

It is critical that you resolve these issues before the upgrade to prevent any issues. The subnet that the fault is raised on should either be corrected or deleted in order to clear the fault. You can run the moquery below on the CLI of any Cisco APIC to check if these faults exist on the system. The faults are visible within the GUI as well.

!!! example "Fault Example (F0469: duplicate-subnets-within-ctx)"
    ```
    admin@f1-apic1:~> moquery -c faultInst -f 'fault.Inst.code=="F0469"'
    Total Objects shown: 4
     
    # fault.Inst
    code             : F0469
    ack              : no
    annotation       :
    cause            : configuration-failed
    changeSet        : configQual (New: duplicate-subnets-within-ctx), configSt (New: failed-to-apply), debugMessage (New: uni/tn-TK/BD-BD2,uni/tn-TK/BD-BD1)
    childAction      :
    created          : 2021-07-08T17:40:37.630-07:00
    delegated        : yes
    descr            : BD Configuration failed for uni/tn-TK/BD-BD2  due to duplicate-subnets-within-ctx: uni/tn-TK/BD-BD2 ,uni/tn-TK/BD-BD1
    dn               : topology/pod-1/node-101/local/svc-policyelem-id-0/uni/bd-[uni/tn-TK/BD-BD2]-isSvc-no/bdcfgissues/fault-F0469
    domain           : tenant
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2021-07-08T17:40:37.630-07:00
    lc               : soaking
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F0469
    rule             : fv-bdconfig-issues-config-failed
    severity         : minor
    status           :
    subject          : management
    type             : config
    uid              :
    --- omit ---
    ```

!!! example "Fault Example (F1425: subnet-overlap)"
    ```
    admin@apic1:~> moquery -c faultInst -f 'fault.Inst.code=="F1425"'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F1425
    ack              : no
    annotation       : 
    cause            : ip-provisioning-failed
    changeSet        : ipv4CfgFailedBmp (New: ipv4:Addraddr_failed_flag,ipv4:Addrctrl_failed_flag,ipv4:AddrlcOwn_failed_flag, ipv4:AddrmodTs_failed_flag,ipv4:AddrmonPolDn_failed_flag,ipv4:Addrpref_failed_flag,ipv4:Addrtag_failed_flag, ipv4:Addrtype_failed_flag,ipv4:AddrvpcPeer_failed_flag), ipv4CfgState (New: 1), operStQual (New: subnet-overlap)
    childAction      : 
    created          : 2020-02-27T01:50:45.656+01:00
    delegated        : no
    descr            : IPv4 address(10.10.10.1/24) is operationally down, reason:Subnet overlap on node 101 fabric hostname leaf-101
    dn               : topology/pod-1/node-101/sys/ipv4/inst/dom-jr:v1/if-[vlan10]/addr-[10.10.10.1/24]/fault-F1425
    domain           : access
    extMngdBy        : undefined
    highestSeverity  : major
    lastTransition   : 2020-02-27T01:52:49.812+01:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : major
    prevSeverity     : major
    rn               : fault-F1425
    rule             : ipv4-addr-oper-st-down
    severity         : major
    status           : 
    subject          : oper-state-err
    type             : operational
    uid              : 
    ```


### VMM Domain Controller Status

If there is an issue in communication between the Cisco APIC and the VMM controller, the VMM controller status is marked as offline and the fault F0130 is raised. Ensure that the connectivity between them is restored prior to upgrades so that any resources that are currently deployed on switches based on the communication with the VMM controller will not be changed or lost due to the Cisco APICs not being able to retrieve necessary information after an upgrade.

!!! example "Fault Example (F0130: VMM Controller connection failure)"
    The following is an example of the Cisco APIC failing to communicate with the VMM controller `MyVMMControler` with the IP 192.168.100.100 in VMM domain `LAB_VMM`.
    ```
    apic1# moquery -c faultInst -f 'fault.Inst.code=="F0130"'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F0130
    ack              : no
    cause            : connect-failed
    changeSet        : operSt (Old: unknown, New: offline)
    childAction      :
    created          : 2016-05-23T16:07:50.205-05:00
    delegated        : yes
    descr            : Connection to VMM controller: 192.168.100.100 with name MyVMMController in datacenter LAB1 in domain: LAB_VMM is failing repeatedly with error: [Failed to retrieve ServiceContent from the vCenter server 192.168.100.100]. Please verify network connectivity of VMM controller 192.168.100.100 and check VMM controller user credentials are valid.
    dn               : comp/prov-VMware/ctrlr-[LAB_VMM]-MyVMMController/fault-F0130
    domain           : external
    highestSeverity  : major
    lastTransition   : 2016-05-23T16:10:04.219-05:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : major
    prevSeverity     : major
    rn               : fault-F0130
    rule             : comp-ctrlr-connect-failed
    severity         : major
    status           :
    subject          : controller
    type             : communications
    uid              :
    ```


### VMM Domain LLDP/CDP Adjacency Status

With **On Demand** or **Immediate** resolution immediacy as opposed to **pre-provision** in the VMM domain when attaching it to an EPG, for some VMM integrations such as VMware DVS integration, the Cisco APIC checks LLDP or CDP information from leaf switches connected to the hypervisors and also from the VMM controller managing the hypervisors. This information is required from both leaf switches and hypervisors to dynamically detect the leaf interface connecting to the hypervisor, even when there is an intermediate switch in between such as Cisco UCS Fabric Interconnect. Once the interface is detected, the Cisco APIC dynamically deploys VLANs only on the necessary interface(s) of the leaf switch that the hypervisor is connected to.

Prior to Cisco APIC release 3.0(1), VLANs used to be removed from the leaf interfaces if the Cisco APIC loses the connectivity to the VMM controller because the Cisco APIC can no longer compare the LLDP or CDP information from the hypervisor’s point of view. Starting from Cisco APIC release 3.0(1), VLANs will not be removed from the leaf interfaces even if the Cisco APIC loses the connectivity to the VMM controller to prevent transient management plane issues from impacting the data plane traffic. However, it may cause some churns in the Cisco APIC process by repeatedly trying to obtain the LLDP/CDP information. When the LLDP/CDP information is missing, the fault F606391 is raised.

Due to these reasons, regardless of the Cisco APIC release, it is important to resolve this fault prior to the upgrade. If the faults are raised on a VMM domain configured for the Cisco Application Virtual Edge (AVE), LLDP and CDP can be disabled entirely because the control plane built to program the switches is based on the opflex protocol and not LLDP/CDP. When LLDP and CDP are disabled, the faults should clear. The configuration to change the LLDP/CDP state for a VMM domain is configured under the vSwitch Policy for the VMM Domain.

!!! example "Fault Example (F606391: LLDP/CDP adjacency missing for hypervisors)"
    ```
    apic1# moquery -c faultInst -f 'fault.Inst.code=="F606391"'
    Total Objects shown: 5
     
    # fault.Inst
    code                      : F606391
    ack                       : no
    annotation                : 
    cause                     : fsm-failed
    changeSet                 : 
    childAction               : 
    created                   : 2019-07-18T01:17:39.435+08:00
    delegated                 : yes
    descr                     : [FSM:FAILED]: Get LLDP/CDP adjacency information for the physical adapters on the host: hypervisor1.cisco.com(TASK:ifc:vmmmgr:CompHvGetHpNicAdj)
    dn                        : comp/prov-VMware/ctrlr-[LAB_VMM]-MyVMMController/hv-host-29039/fault-F606391
    domain                    : infra
    extMngdBy                 : undefined
    highestSeverity           : major
    lastTransition            : 2019-07-18T01:17:39.435+08:00
    lc                        : raised
    modTs                     : never
    occur                     : 1
    origSeverity              : major
    prevSeverity              : major
    rn                        : fault-F606391
    rule                      : fsm-get-hp-nic-adj-fsm-fail
    severity                  : major
    status                    : 
    subject                   : task-ifc-vmmmgr-comp-hv-get-hp-nic-adj
    type                      : config
    uid                       :
    ```


### Different infra VLAN via LLDP

If you have interfaces connected back-to-back between two different ACI fabrics, you must disable LLDP on those interfaces prior to upgrades. This is because when the switch comes back up after the upgrade, it may receive and process LLDP packets from the other fabric that may be using a different infra VLAN. If that happens, the switch incorrectly tries to be discovered through the infra VLAN of the other fabric and will not be discoverable in the correct fabric.

There is a fault to detect if an ACI switch is currently is receiving an LLDP packet with infra VLAN mismatch from other fabrics.

!!! example "Fault Example (F0454: LLDP with mismatched parameters)"
    ```
    apic1# moquery -c faultInst -f 'fault.Inst.code=="F0454"'
    Total Objects shown: 2
     
    # fault.Inst
    code             : F0454
    ack              : no
    alert            : no
    annotation       :
    cause            : wiring-check-failed
    changeSet        : wiringIssues (New: ctrlr-uuid-mismatch,fabric-domain-mismatch,infra-ip-mismatch,infra-vlan-mismatch)
    childAction      :
    created          : 2021-06-30T10:44:25.576-07:00
    delegated        : no
    descr            : Port eth1/48 is out of service due to Controller UUID mismatch,Fabric domain name mismatch,Infra subnet mismatch,Infra vlan mismatch
    dn               : topology/pod-1/node-104/sys/lldp/inst/if-[eth1/48]/fault-F0454
    --- omit ---
    ```


### HW Programming Failure

The fault F3544 occurs when the switch fails to activate an entry to map a prefix to pcTag due to either a hardware or software programming failure. These entries are configured for L3Out subnets with the **External Subnets for the External EPG** scope under an external EPG in an L3Out, and used to map L3Out subnets to L3Out EPGs. If you see this because of the LPM or host routes capacity on the switch, such a switch may activate different sets of entries after a reboot or upgrade. This may lead to services that used to work before an upgrade begins to fail after an upgrade. When this fault is present, check the `Operations > Capacity Dashboard > Leaf Capacity` in the Cisco APIC GUI for LPM and /32 or /128 routes usage.

The fault F3545 occurs when the switch fails to activate a contract rule (zoning-rule) due to either a hardware or software programming failure. If you see this, it's because the policy CAM is full and no more contracts can be deployed on the switch, and a different sets of contracts may deploy after a reboot or upgrade. This may lead to services that used to work before an upgrade begins to fail after an upgrade. Note that the same fault could occur for other reasons, such as an unsupported type of filter in the contract(s) instead of policy CAM usage. For instance, first generation ACI switches support EtherType IP but not IPv4 or IPv6 in contract filters. When this fault is present, check the `Operations > Capacity Dashboard > Leaf Capacity` in the Cisco APIC GUI for policy CAM usage.

!!! example "Fault Example (F3544: L3Out Subnet Programming Failure)"
    The following shows an example of node 101 with programming failure for 80 L3Out subnets with **External Subnets for the External EPG** (`pfxRuleFailed`). Although it also shows the programming failure of contracts themselves (`zoneRuleFailed`) in the `changeSet`, a separate fault F3545 is raised for that.
    ```
    apic1# moquery -c faultInst -f 'fault.Inst.code=="F3544"'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F3544
    ack              : no
    annotation       : 
    cause            : actrl-resource-unavailable
    changeSet        : pfxRuleFailed (New: 80), zoneRuleFailed (New: 266)
    childAction      : 
    created          : 2020-02-26T01:01:49.246-05:00
    delegated        : no
    descr            : 80 number of Prefix failed on leaf1
    dn               : topology/pod-1/node-101/sys/actrl/dbgStatsReport/fault-F3544
    domain           : infra
    extMngdBy        : undefined
    highestSeverity  : major
    lastTransition   : 2020-02-26T01:03:59.849-05:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : major
    prevSeverity     : major
    rn               : fault-F3544
    rule             : actrl-stats-report-pre-fix-prog-failed
    severity         : major
    status           : 
    subject          : hwprog-failed
    type             : operational
    uid              :
    ```

!!! example "Fault Example (F3545: Zoning Rule Programming Failure)"
    The following shows an example of node 101 with programming failure for 266 contract rules (`zoneRuleFailed`). Although it also shows the programming failure of L3Out subnets (`pfxRuleFailed`) in the `changeSet`, a separate fault F3544 is raised for that.
    ```
    apic1# moquery -c faultInst -f 'fault.Inst.code=="F3545"'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F3545
    ack              : no
    annotation       : 
    cause            : actrl-resource-unavailable
    changeSet        : pfxRuleFailed (New: 80), zoneRuleFailed (New: 266)
    childAction      : 
    created          : 2020-02-26T01:01:49.256-05:00
    delegated        : no
    descr            : 266 number of Rules failed on leaf1
    dn               : topology/pod-1/node-101/sys/actrl/dbgStatsReport/fault-F3545
    domain           : infra
    extMngdBy        : undefined
    highestSeverity  : major
    lastTransition   : 2020-02-26T01:03:59.849-05:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : major
    prevSeverity     : major
    rn               : fault-F3545
    rule             : actrl-stats-report-zone-rule-prog-failed
    severity         : major
    status           : 
    subject          : hwprog-failed
    type             : operational
    uid              :
    ```


### Scalability (faults related to Capacity Dashboard)

The script checks faults raised under `eqptcapacityEntity`, which are TCA (Threshold Crossed Alert) faults for various objects monitored in the **Capacity Dashboard** from `Operations > Capacity Dashboard > Leaf Capacity` on the Cisco APIC GUI.

It is important to ensure that any capacity does not exceed its limit. When it's exceeding the limit, it may cause inconsistency on resources that are deployed before and after an upgrade just like it was warned for [Policy CAM Programming for Contracts (F3545) and L3Out Subnets Programming for Contracts (F3544)][f15].

Examples of what's monitored via `Operations > Capacity Dashboard > Leaf Capacity` are the number of endpoints such as MAC (Learned), IPv4 (Learned), Policy CAM, LPM, host routes, VLANs and so on.

!!! example "Fault Example (F193568: TCA VLAN Usage)"
    ```
    apic1# moquery -c eqptcapacityEntity -x 'rsp-subtree-include=faults,no-scoped'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F193568
    ack              : no
    annotation       : 
    cause            : threshold-crossed
    changeSet        : totalCum:4018
    childAction      : 
    created          : 2022-12-09T10:53:01.103-08:00
    delegated        : no
    descr            : TCA: Total vlan entries cumulative(eqptcapacityVlanUsage5min:totalCum) value 4018 raised above threshold 90
    dn               : topology/pod-1/node-101/sys/eqptcapacity/fault-F193568
    domain           : infra
    extMngdBy        : undefined
    highestSeverity  : critica
    lastTransition   : 2022-12-09T10:53:01.103-08:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : critical 
    prevSeverity     : critical
    rn               : fault-F193568
    rule             : tca-eqptcapacity-vlan-usage5min-total-cum
    severity         : critical
    status           : 
    subject          : counter
    type             : operational
    uid              :
    ```


### Fabric Port is Down

The script checks for fault code `F1394` with rule `ethpm-if-port-down-fabric`, which indicate that ACI has flagged configured Fabric ports for being in a down state.

It is important to understand whether or not these downed fabric prots are preventing your leaf nodes from having redundant paths. If unexpected, address these issues before performing the ACI Upgrade.

Failure to do so may lead to outages during switch upgrades due to leaf nodes not having redundant spine paths.

!!! example "Fault Example (F0469: duplicate-subnets-within-ctx)"
    ```
    admin@f1-apic1:~> moquery -c faultInst -f 'fault.Inst.code=="F1394"'
    Total Objects shown: 4
     
    # fault.Inst
    code             : F1394
    ack              : no
    alert            : no
    annotation       : 
    cause            : interface-physical-down
    changeSet        : lastLinkStChg (New: 2023-10-24T03:24:57.051+00:00), operBitset (New: 4-5,11,35)
    childAction      : 
    created          : 2023-09-09T08:53:35.125+00:00
    delegated        : no
    descr            : Port is down, reason:err-disabled-link-flaps(err-disabled), used by:Fabric
    dn               : topology/pod-1/node-101/sys/phys-[eth1/53]/phys/fault-F1394
    domain           : access
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2023-10-24T03:24:57.101+00:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F1394
    rule             : ethpm-if-port-down-fabric
    severity         : minor
    status           : 
    subject          : port-down
    title            : 
    type             : communications
    uid              : 
    userdom          : all
    --- omit ---
    ```


## Equipment Disk Limits Exceeded

This fault occurs when the disk usage of a partiton increases beyond its threshold.

This fault also occurs when the MTS buffer memory usage increases beyond its threshold. /proc/isan/sw/mts/mem/stats is checked when this scenario occurs.

Recommended Action:

1. Check `df -h` output on affected node to see the usage of the partition.
    - If the fault is about MTS, check `cat /proc/isan/sw/mts/mem/stats` output on affected node to see the usage of the MTS memory. 
    - Focus on "mem_in_use" and "mem_free" in /proc/isan/sw/mts/mem/stats. 
    - The usage is calculated by "mem_in_use / (mem_in_use + mem_free)". 
    - The same output as /proc/isan/sw/mts/mem/stats can be obtained by `show system internal mts memory` command on affected switch node.
2. Check `ls -l` output of folders under affected partition to see which file is consuming the space.
    - If the fault is about MTS, check `show system internal mts buffers details` to see what is consuming the MTS buffer space.

To recover from this fault, try the following action

1. Free up space from affected disk partition or MTS buffer.
2. TAC may be required to analyze and cleanup certain directories due to filesystem permissions. Cleanup of `/` is one such example.

!!! example "Fault Example (F1820: High Disk usage)"
    ```
    apic1# moquery -c eqptcapacityEntity -x 'rsp-subtree-include=faults,no-scoped'
    Total Objects shown: 1
     
    # fault.Inst
    code             : F1820
    ack              : no
    alert            : no
    annotation       : 
    cause            : equipment-disk-limits-exceeded
    changeSet        : avail (New: 1971936), path (New: /mnt/ifc/cfg), used (New: 8194392)
    childAction      : 
    created          : 2025-02-17T13:55:20.263-06:00
    delegated        : no
    descr            : Disk usage for /mnt/ifc/cfg is above normal
    dn               : topology/pod-1/node-102/sys/eqptcapacity/fspartition-ifc:cfg/fault-F1820
    domain           : access
    extMngdBy        : undefined
    highestSeverity  : minor
    lastTransition   : 2025-02-17T13:57:25.020-06:00
    lc               : raised
    modTs            : never
    occur            : 1
    origSeverity     : minor
    prevSeverity     : minor
    rn               : fault-F1820
    rule             : eqptcapacity-fspartition-fs-partition-limits-exceeded-minor
    severity         : minor
    status           : 
    subject          : high-disk-usage
    title            : 
    type             : operational
    uid              : 
    userdom          : all
    ```

## Configuration Check Details

### VPC-paired Leaf switches                       

High availability (HA) is always the key in network design. There are multiple ways to achieve this, such as with server configurations like NIC teaming, virtualization technology like VMware vMotion, or network device technology like link aggregation across different chassis. ACI provides high availability using virtual Port Channel (vPC) as the link aggregation across chassis.

It is important to keep the traffic flowing even during upgrades by upgrading one switch in the same HA pair at a time. In ACI, that will be a vPC pair unless you have other HA technologies on the server or virtualization side.

The script checks if all leaf switch nodes are in a vPC pair. The APIC built-in pre-upgrade validation performs this check when you upgrade Cisco APICs instead of switches because in ACI, Cisco APICs are upgraded first prior to switches, and configuring a new vPC pair potentially requires a network design change and that should be done prior to any upgrades. If you have other HA technologies in place, you can ignore this validation. vPC is not a requirement for the upgrade to complete, but the built-in tools to prevent leaf switches in a vPC domain from upgrading at the same time will not work if they are not in a vPC. If you are not using vPC, you must ensure the switches being upgraded will not cause an outage if done at the same time.


### Overlapping VLAN Pool                          

Overlapping VLAN blocks across different VLAN pools may result in some forwarding issues, such as:

* Packet loss due to issues in endpoint learning with vPC
* STP BPDUs, or any BUM traffic when using Flood-in-Encap, are not flooded to all ports within the same VLAN ID.

**These issues may suddenly appear after upgrading your switches** because switches fetch the policies from scratch after an upgrade and may apply the same VLAN ID from a different pool than what was used prior to the upgrade. As a result, the VLAN ID is mapped to a different VXLAN VNID than other switch nodes. This causes the two problems mentioned above.


!!! Tip "VLAN Pools and VXLAN VNID on switches"
    In ACI, multiple VLANs and EPGs can be mapped to the same bridge domain, which serves as the Layer 2 domain. As a result, most Layer 2 forwarding, such as bridging or flooding a packet, uses the VXLAN VNID of the bridge domain. However, each VLAN within the bridge domain is also mapped to a unique VXLAN VNID, distict from that of the bridge domain. This is known as Forwarding Domain (FD) VNID or VLAN VNID, and it's used for special purposes such as:

    * Endpoint synchronization between vPC peer switches.
    * Flooding STP BPDUs across switches.
    * Flooding BUM (Broadcast, Unknown Unicast, Multicast) traffic across switches when `Flood-in-Encap` is configured on the bridge domain or EPG.

    To prevent the impact for these mechanism, VLAN VNID mapping must be consistent across switches as needed.


!!! Tip "How VLAN Pools are tied to the VLAN on switches"
    Each switch port can be associated to multiple VLAN pools that may or may not have VLAN ID ranges overlapping with each other.

    ``` mermaid
    graph LR
      A[Port] --> B[Interface Policy Group] --> C[AEP];
      C[AEP] --> D(Phy Domain A):::dom --> E[VLAN Pool 1];
      C[AEP] --> F(Phy Domain B):::dom --> G[VLAN Pool 2];
      C[AEP] --> H(VMM Domain C):::dom --> G[VLAN Pool 2];
      classDef dom fill:#fff
    ```

    When configuring a switch port (node-101 eth1/1) with VLAN 10 as EPG A, two things are checked:

    1. Whether node-101 eth1/1 is associated to VLAN 10 via `AEP -> Domain -> VLAN Pool`
    2. Whether EPG A is associated with the same domain

    If the port is associated with multiple domains/VLAN pools as shown above, and EPG A is associated only with `Phy Domain A`, then only `VLAN Pool 1` is available for the port in the context of EPG A, avoiding any overlapping VLAN pool issues. However, if VLAN 10 is not included in `VLAN Pool 1`, it cannot be deployed on the port via EPG A. The same principle applies when deploying a VLAN through AEP binding, as it serves as a shortcut to specify all ports within the AEP.

    This concept of domains is crucial in multi-domain tenancy to ensure the tenant/EPG has the appropriate set of ports and VLANs.

    However, if EPG A is associated with both `Phy Domain A` and `Phy Domain B`, the port can use either `VLAN Pool 1` or `VLAN Pool 2` to pull a VLAN. If VLAN 10 is configured in both pools, EPG A and its VLAN 10 are susceptible to an overlapping VLAN pool issue.


!!! example "Bad Example 1"
    ``` mermaid
    graph LR
      port["`node-101
      eth1/1`"];
      vpool1["`VLAN Pool 1
      (VLAN 1-20)`"];
      vpool2["`VLAN Pool 2
      (VLAN 10-20)`"];
      X["`EPG A
      node-101 eth1/1
      VLAN 10`"]

      subgraph one [Access Policies]
      port --> B[AEP];
      B[AEP] --> C(Domain A):::dom --> vpool1;
      B[AEP] --> E(Domain B):::dom --> vpool2;
      end
      X --> C(Domain A):::dom;
      X --> E(Domain B):::dom;
      classDef dom fill:#fff
    ```
    In this scenario, VLAN 10 can be pulled from either `VLAN Pool 1` or `VLAN Pool2` because the port (`node-101 eth 1/1`) and the EPG are associated to both pools. And VLAN ID 10 is also configured on both pools.

    As a result, VNID mapping for VLAN 10 on node-101 may become inconsistent after an upgrade or when the switch initializes and downloads configurations from the APICs.

    This can be resolved by associating EPG A to only one of the domains, associating the AEP to only one of the domains, or associating the domains to the same VLAN Pool as shown below.

    **Resolution 1:**
    ``` mermaid
    graph LR
      port["`node-101
      eth1/1`"];
      vpool1["`VLAN Pool 1
      (VLAN 1-20)`"];
      vpool2["`VLAN Pool 2
      (VLAN 10-20)`"];
      X["`EPG A
      node-101 eth1/1
      VLAN 10`"]

      subgraph one [Access Policies]
      port --> B[AEP];
      B[AEP] --> C(Domain A):::dom --> vpool1;
      B[AEP] --> E(Domain B):::dom --> vpool2;
      end
      X --> E(Domain B):::dom;
      classDef dom fill:#fff
    ```

    **Resolution 2:**
    ``` mermaid
    graph LR
      port["`node-101
      eth1/1`"];
      vpool1["`VLAN Pool 1
      (VLAN 1-20)`"];
      vpool2["`VLAN Pool 2
      (VLAN 10-20)`"];
      X["`EPG A
      node-101 eth1/1
      VLAN 10`"]

      subgraph one [Access Policies]
      port --> B[AEP];
      B[AEP] --> C(Domain A):::dom --> vpool1;
      E(Domain B):::dom --> vpool2;
      end
      X --> C(Domain A):::dom;
      X --> E(Domain B):::dom;
      classDef dom fill:#fff
    ```

    **Resolution 3:**
    ``` mermaid
    graph LR
      port["`node-101
      eth1/1`"];
      vpool1["`VLAN Pool 1
      (VLAN 1-20)`"];
      X["`EPG A
      node-101 eth1/1
      VLAN 10`"]

      subgraph one [Access Policies]
      port --> B[AEP];
      B[AEP] --> C(Domain A):::dom --> vpool1;
      B[AEP] --> E(Domain B):::dom --> vpool1;
      end
      X --> C(Domain A):::dom;
      X --> E(Domain B):::dom;
      classDef dom fill:#fff
    ```

!!! example "Bad Example 2"
    ``` mermaid
    graph LR
      port1["`node-101
      eth1/1`"];
      port2["`node-101
      eth1/2`"];
      vpool1["`VLAN Pool 1
      (VLAN 1-20)`"];
      vpool2["`VLAN Pool 2
      (VLAN 10-20)`"];
      X["`EPG A
      node-101 eth1/1-2
      VLAN 10`"]

      subgraph one [Access Policies]
      port1 --> aep2[AEP 2] --> C(Domain A):::dom --> vpool1;
      port2 --> aep1[AEP 1] --> E(Domain B):::dom --> vpool2;
      end
      X --> C(Domain A):::dom;
      X --> E(Domain B):::dom;
      classDef dom fill:#fff
    ```
    In this scenario, VLAN 10 can be pulled from either `VLAN Pool 1` or `VLAN Pool2` from the EPG's perspective. However, each port is associated to only one VLAN pool respectively.

    This is a problem because both ports are on the same switch. Essentially, this VLAN Pool design attempts to map a different VNID for VLAN 10 on eth1/1 and eth1/2 on the same switch, which isn't allowed - there can be only one VLAN 10 per switch except for when using VLAN scope `local`.

    As a result, VNID mapping for VLAN 10 on node-101 may become inconsistent after an upgrade or when the switch initializes and downloads configurations from the APICs.

    This can be resolved by associating AEPs to the same domain or associating the domains to the same VLAN Pool as shown below.

    **Resolution 1**
    ``` mermaid
    graph LR
      port1["`node-101
      eth1/1`"];
      port2["`node-101
      eth1/2`"];
      vpool1["`VLAN Pool 1
      (VLAN 1-20)`"];
      vpool2["`VLAN Pool 2
      (VLAN 10-20)`"];
      X["`EPG A
      node-101 eth1/1-2
      VLAN 10`"]

      subgraph one [Access Policies]
      port1 --> aep2[AEP 2] --> C(Domain A):::dom --> vpool1;
      port2 --> aep1[AEP 1] --> C(Domain A):::dom
      E(Domain B):::dom --> vpool2;
      end
      X --> C(Domain A):::dom;
      X --> E(Domain B):::dom;
      classDef dom fill:#fff
    ```

    **Resolution 2**
    ``` mermaid
    graph LR
      port1["`node-101
      eth1/1`"];
      port2["`node-101
      eth1/2`"];
      vpool1["`VLAN Pool 1
      (VLAN 1-20)`"];
      X["`EPG A
      node-101 eth1/1-2
      VLAN 10`"]

      subgraph one [Access Policies]
      port1 --> aep2[AEP 2] --> C(Domain A):::dom --> vpool1;
      port2 --> aep1[AEP 1] --> E(Domain B):::dom --> vpool1;
      end
      X --> C(Domain A):::dom;
      X --> E(Domain B):::dom;
      classDef dom fill:#fff
    ```

!!! example "Example: good only for a specific use case"
    ``` mermaid
    graph LR
      port1["`node-101
      eth1/1`"];
      port2["`node-102
      eth1/1`"]:::red;
      vpool1["`VLAN Pool 1
      (VLAN 1-20)`"];
      vpool2["`VLAN Pool 2
      (VLAN 10-20)`"];
      X["`EPG A
      node-101 eth1/1
      node-102 eth1/1
      VLAN 10`"]

      subgraph one [Access Policies]
      port1 --> aep2[AEP 2] --> C(Domain A):::dom --> vpool1;
      port2 --> aep1[AEP 1] --> E(Domain B):::dom --> vpool2;
      end
      X --> C(Domain A):::dom;
      X --> E(Domain B):::dom;
      classDef dom fill:#fff
      classDef red stroke:#f00
    ```
    In this scenario, each port is tied to a different VLAN pool for VLAN 10, but each port is on a different node. This ensures that the VLAN VNID mapping remains consistent within each node even after an upgrade, with no ambiguity about which VLAN pool is used. However, VLAN 10 on each node will map to a different VLAN VNID, which may or may not be your intent.

    Without the Flood-in-Encap feature, VLAN VNIDs act as flooding domains for spanning tree BPDUs. Even if VLAN 10 on node 101 and 102 map to different VLAN VNIDs, regular traffic is forwarded without issues via bridge domain VNID or VRF VNID.

    This VLAN pool design is ideal for keeping the spanning tree domains small, such as in a multi-pod fabric with one STP domain per pod where each pod is physically separate with no L2 connecitivity between them except for the IPN. It helps contain spanning tree issues within a single pod. For instance, if Pod 1 continuously receives STP TCNs due to a malfuncationing device in the external network in Pod 1, the impact of flushing endpoints and causing connectivity issues due to TCNs is contained within that pod, keeping other pods unaffected.

    However, this design is not suitable if you prefer a simpler configuration, if the nodes belong to the same vPC switch pair, or if the VLAN uses the Flood-in-Encap feature.


It is critical to ensure that there are no overlapping VLAN pools in your fabric unless it is on purpose with the appropriate understanding of VLAN ID and VXLAN ID mapping behind the scene. If you are not sure, consider **Enforce EPG VLAN Validation** under `System > System Settings > Fabric Wide Setting` in the Cisco APIC GUI [available starting with release 3.2(6)], which prevents the most common problematic configuration (two domains containing overlapping VLAN pools being associated to the same EPG).

Refer to the following documents to understand how overlapping VLAN pools become an issue and when this scenario might occur:

* [Overlap VLAN pool Lead Intermittent Packet Drop to VPC Endpoints and Spanning-tree Loop][10]
* [ACI: Common migration issue / Overlapping VLAN pools][11]
* [Validating Overlapping VLANs in the Cisco APIC Layer 2 Networking Configuration Guide, Release 4.2(x)][12]
* [VLAN Pool - ACI Best Practice Quick Summary][13]


### <del>VNID Mismatch</del>

!!! warning "Deprecated"
    This check was deprecated and removed as it had not only become redundant after the updates in the [Overlapping VLAN Pool][c2] check but also contained a risk of rainsing a false alarm. See [PR #182](https://github.com/datacenter/ACI-Pre-Upgrade-Validation-Script/pull/182) for details.

<span style="color:lightgray">
A VNID mismatch can arise due to an [Overlapping VLAN Pool][c2] situation. This verification is closely tied to the [Overlapping VLAN Pool][c2] scenario, which often leads to problems post-upgrade. Nonetheless, if your fabric is currently experiencing any VNID mismatches, you might encounter the challenges outlined in [Overlapping VLAN Pool][c2] even without undergoing an upgrade. This situation also implies the presence of an overlapping VLAN pool configuration, potentially resulting in a VNID mismatch at a distinct EPG following an upgrade, causing different impact to your traffic. 
</span>


### L3Out MTU                                      

It is critical to ensure that MTU values on ACI L3Out interfaces and the routers that connect to them match. Otherwise, when the ACI switch boots up after an upgrade, it may cause problem during the routing protocol neighborship establishment or exchanging the route information between peers.

See below for example details on each protocol.

* **BGP** is a protocol which would establish session without MTU consideration. BGP "Open and Establish" messages are small, but the messages to exchange routes can be huge.

* **OSPF** will fail to form neighborship if the MTU from both end of the link does not match. However, although it is strongly not recommended, if the side with larger MTU is configured to ignore MTU to bring up OSPF neighborship, then OSPF neighborship will be formed.

For both protocols, during a border leaf switch upgrade, routing sessions can be teared off due to a mismatched MTU. When a border leaf switch comes online with a new version, it will bring up routing peers. After this, when it starts to exchange information about routing prefixes, frames may need to carry a huge payload containing lots of prefixes. Based on the size of the table, the update may need a larger frame size which might not reach the other side. The size of this payload will depend upon local MTU. If the MTU on the other side does not match (if it's smaller than the local MTU size), then these exchanges will fail, resulting in routing issues.

You can check and configure the MTU on L3Out interfaces through `Tenant > Networking > L3Out > Logical Node Profile > Logical Interface Profile > Select interface type`.

!!! tip
    You can run the `moquery` below on the CLI of any Cisco APIC to check the configured MTU of all L3Out interfaces. Use `grep` for concise output if necessary, such as this example: `egrep "dn|encap|mtu"`

    In this example, an L3Out interface with VLAN 2054 is configured with MTU 9000 in tenant `TK`, L3Out `OSPF`, Logical Node Profile `OSPF_nodeProfile`, and Logical Interface Profile `OSPF_interfaceProfile`.
    ```
    apic1# moquery -c l3extRsPathL3OutAtt
    Total Objects shown: 1

    # l3ext.RsPathL3OutAtt
    addr      : 20.54.0.1/24
    --- omit ---
    dn        : uni/tn-TK/out-OSPF/lnodep-OSPF_nodeProfile/lifp-OSPF_interfaceProfile/
    rspathL3OutAtt-[topology/pod-1/paths-101/pathep-[eth1/12]]
    encap     : vlan-2054
    --- omit ---
    mtu       : 9000
    --- omit ---
    ```

    Alternatively, you can run `fabric <node_id> show interface` with your border leaf switch's node ID as well.

    If the MTU shows `inherit`, the value is inherited from `Fabric > Fabric Policies > Policies > Global > Fabric L2 MTU > default`.

!!! warning
    The script checks the MTU of all L3Out interfaces for you. However, you have to run the script on Cisco APIC, and the Cisco APIC does not have visibility on the MTU value configured on the connected devices. Therefore, you should manually check the MTU on the connected devices.


### BGP Peer Profile at node level without Loopback

Prior to upgrading to release 4.1(2) or later, you must ensure that one of the following two requirements are met:

* A node profile with a **BGP Peer Connectivity Profile** has a loopback configured for all switches in the profile, or
* **BGP Peer Connectivity Profiles** are configured per interface.

You can configure the **BGP Peer Connectivity Profile** per node profile or per interface. The former is to source the BGP session from a loopback while the latter is to source the BGP session from each interface.

Prior to release 4.1(2), when a **BGP Peer Connectivity Profile** is configured at a node profile without configuring a loopback, Cisco APIC uses another available IP address on the same border leaf switch in the same VRF as the BGP source, such as a loopback IP address from another L3Out or an IP address configured for each interface. This has a risk of the BGP source IP address being changed unintentionally across reboots or upgrades. This behavior has been changed based on CSCvm28482 and ACI no longer establishes a BGP session through a **BGP Peer Connectivity Profile** at a node profile when a loopback is not configured in the node profile. Instead, a fault F3488 is raised in these situations. This fault cannot be used as a pre-upgrade check because it is raised only after an upgrade.

Due to this change, when upgrading from an older version to release 4.1(2) or later, a BGP session is no longer established if the session was generated via a **BGP Peer Connectivity Profile** under a node profile and a loopback is not configured in the node profile.

!!! tip
    When multiple interfaces in the same node profile need to establish a BGP peer with the same peer IP, you might attempt to configure a **BGP Peer Connectivity Profile** at a node profile without a loopback so that the same BGP Peer configuration is applied, as a fallback due to the missing loopback, to each interface in the same node profile. This is because a **BGP Peer Connectivity Profile** with the same peer IP address could not be configured at multiple interface profiles within the same node profile. This limitation was loosened based on CSCvw88636 on 4.2(7f). Until then, for this specific requirement, you need to configure a node interface per interface profile and configure the **BGP Peer Connectivity Profile** at each interface profile in a different node profile.


### L3Out Route Map import/export direction

Prior to upgrading to release 4.1(1) or later, you must ensure that the route map (route profile) configuration is correct.

Due to the defect CSCvm75395, the following configuration might have worked prior to release 4.1(1) despite the wrong configuration (a mismatch in the direction):

* A route map with `export` direction attached to an L3Out subnet with **Import Route Control Subnet**
* A route map with `import` direction attached to an L3Out subnet with **Export Route Control Subnet**

Where the L3Out subnet means the subnet configured under an External EPG in an L3Out.

However, these wrong configurations will no longer work, which is the expected behavior, after you upgrade the fabric to release 4.1(1) or later.

Although this method is not the most common or recommended one among many ways to control the routes being advertised or learned by ACI L3Outs, the correct configuration with this method should be as follows:

* A route map with `export` direction attached to an L3Out subnet with **Export Route Control Subnet**
* A route map with `import` direction attached to an L3Out subnet with **Import Route Control Subnet**

!!! tip
    Or alternatively, you can follow the recommended configurations below to control the route exchange in L3Outs instead:

    * `default-export` route map with IP prefix-lists
    * `default-import` route map with IP prefix-lists

    With this configuration, you don’t need **Export Route Control Subnet** or **Import Route Control Subnet** in the external EPGs, and you can have external EPGs that are dedicated for contracts or route leaking while you have the full control of routing protocol through route maps just like a normal router.

    Also note that any import direction route maps only take effect when **Route Control Enforcement** is enabled for import under `Tenant > Networking > L3Out > Main profile`. Otherwise, everything is imported (learned) by default.


### L3Out Route Map Match Rule with missing-target

Prior to upgrading to release 5.2(8), 6.0(2) or later, you must ensure that the route map (route profile) with type **Match Prefix AND Routing Policy** (type `combinable` in the object `rtctrlProfile`) does not contain a match rule with the `missing-target` state.

Each context in an L3Out route-map with type **Match Prefix AND Routing Policy** creates a route-map sequence by combining multiple match conditions shown below:

* Match rules referenced by the route-map context
* L3Out subnets to which the route-map is associated directly or through an L3Out EPG.
* BD subnets in a BD to which the route-map is associated

!!! note
    Match rule references in a route-map context is located at the following path in the APIC GUI:

    * `Tenants > Networking > L3Outs > (your L3Out) > Route map for import and export route control > Contexts > Match Rules`

    Whereas the match rule itself is located at the following path in the APIC GUI:

    * `Tanants > Policies > Protocol > Match Rules`

However, prior to the fix of CSCwc11570, when the state of the match rule reference in the route map was `missing-target`, that is when the target match rule didn't exist due to a mis-configuration, no route-map sequence was created even when there were other match conditions such as L3Out subnets or BD subnets.

After the fix of CSCwc11570, a route-map sequence is created correctly based on other available match conditions (i.e. L3Out/BD subnets) even when the state of the match rule reference is `missing-target`.

Because of this, if users have route maps with type **Match Prefix AND Routing Policy** and a match rule reference that resulted in `missing-target` prior to an upgrade, route-map sequences that weren't deployed prior to the upgrade may be deployed after the upgrade. This may change how the routes are exported(advertised) or imported(learned) through an L3Out after the upgrade.

To avoid an unexpected behavior change after an upgrade, if the route map context has a match rule reference with `missing-target`, you should either remove the match rule reference or update it such that it points to an existing match rule.

!!! Tip
    When a match rule reference with `missing-target` is present for a route map with type **Match Prefix AND Routing Policy** prior to the upgrade and prior to the fix of CSCwx11570, the corresponding route-map context is not functioning. However, the fact that it has not been functioning without any operational impact indicates that the route map context may not be needed in the first place. If you remove the match rule reference with `missing-target`, a new route-map sequence will be deployed based on other match conditions which may or may not be needed. Thus, it is important for you to check the original intent of the route-map context and decide how to resolve it. If the route-map context is not needed in the first place, you would need to remove the entire route-map context instead of just removing the match rule reference with `missing-target`.


### L3Out Loopback IP Overlap with L3Out Interfaces

When a loopback IP address in an L3Out is overlapping with a subnet of L3Out interfaces on the same leaf in the same VRF, only one of them (loopback or L3Out interface) is deployed even though the configuration is allowed without any faults. As a result, after an upgrade, what's deployed out of the two may change, and traffic may suddenly stop working after an upgrade because the interface that used to be deployed prior to the upgrade may be replaced with the other one.

In an L3Out, there are two ways to configure a loopback IP:

1. Use Router ID as Loopback IP Address.
2. Configure an explicit loopback iP address that may be different from the router ID.

Both options are configured under `Tenant > L3Out > Logical Node Profile > (node ID)` in the APIC GUI.

This script checks both options to see if any of them is overlapping with the subnet configured as the L3Out interfaces under `Tenant > L3Out > Logical Node Profile > Logical Interface Profile` in the APIC GUI.

Note that the overlap may happen across different L3Outs. For example, the loopback IP address is configured on `L3Out 1` on `node-101` in `VRF A` while the L3Out interface with the overlapping subnet is configrued on `L3Out 2` on the same node and the same VRF.

!!! tip
    There are other overlapping configurations like overlaps between an L3Out loopback IP address and a BD subnet. Those are, however, covered by a fault (F1425), which is validated by another check - [BD Subnets (F1425 subnet-overlap)][f13].

!!! tip
    The enhancement (CSCwa48038) was made on APIC to prevent users from doing this conflicting configuration in the first place. However, if the user already had this conflicting configuration, and proceeded with an upgrade from an older version to the version with the enhancement, the conflicting configuration remains there with the remaining risk of uncertainty where we don't know which interface will be deployed after the next upgrade.

!!! example
    Alternative to the APIC GUI, you can also check these objects for the loopback IP addresses or L3Out Interface subnets via API.

    **Use Router ID as Loopback Address** in the APIC GUI corresponds to the object `l3extRsNodeL3OutAtt` with `rtrIdLoopBack` set to `yes`.
    In this example, `node-103` is configured with a loopback IP `10.0.0.3` via L3Out `BGP` in tenant `TK`.

    ```
    admin@f1-apic1:~> moquery -c l3extRsNodeL3OutAtt | egrep 'dn|rtr'
    dn             : uni/tn-TK/out-OSPF/lnodep-IPv4/rsnodeL3OutAtt-[topology/pod-1/node-103]
    rtrId          : 10.0.0.3
    rtrIdLoopBack  : no
    dn             : uni/tn-TK/out-BGP/lnodep-IPv4/rsnodeL3OutAtt-[topology/pod-1/node-103]
    rtrId          : 10.0.0.3
    rtrIdLoopBack  : yes
    ```

    Configuring an explicit loopback IP address is done via the object `l3extLoopBackIfP` which is optionally configured under `l3extRsNodeL3OutAtt` when `l3extRsNodeL3OutAtt.rtrIdLoopBack` is set to `no`.

    ```
    admin@f1-apic1:~> moquery -c l3extLoopBackIfP | egrep 'dn|addr'
    addr         : 10.0.0.103
    dn           : uni/tn-TK/out-BGP2/lnodep-IPv4/rsnodeL3OutAtt-[topology/pod-1/node-103]/lbp-[10.0.0.103]
    ```

    Note that you need to get the corresponding VRF from the parent L3Out to see which VRF these loopbacks are deployed.



### ISIS Redistribution Metric for MPod/Msite      

ISIS Redistribution Metric is used when a spine redistributes routes from another pod or site into local underlay network (ISIS). If this metric is not set to less than 63, traffic disruption may occur with an upgrade of spine swithces.

See the [ACI Best Practice Quick Summary][14] for details.

This script checks the ISIS Redistribution Metric via `redistribMetric` of an object `isisDomPol` (DN: `uni/fabric/isisDomP-default`).

!!! example
    ```
    admin@f2-apic1:~> moquery -d uni/fabric/isisDomP-default | grep redistribMetric
    redistribMetric  : 32
    ```


### BGP Route-target Type for GOLF over L2EVPN     

Prior to upgrading to release 4.2 or later, if you are using the ACI GOLF feature with **Explicit Route Targets**, you must ensure that all **Explicit Route Targets** point to a route-target policy explicitly configured with a `route-target` community type instead of `extended` (CSCvm23100).

You can verify this configuration under `Tenant > VRF > BGP Route Target Profile X > Route Targets`.

Prior to release 4.2 there was an unexpected behavior where a **BGP Route Target Profile** containing an `extended` community type is treated as a `route-target` community type. This results in the unexpected configuration and deployment of EVPN route targets for GOLF VRFs:

``` title="Used to work unexpectedly prior to 4.2"
extended:as4-nn2:1234:1300
extended:as4-nns:1.2.3.4:20
```

After release 4.2, with the addition of the Stretched L3out feature, `route-target` community type enforcement was corrected.
Due to this change, when upgrading from an older version to release 4.2 or later, EVPN Route Target configuration pushed due to an `extended` community type will no longer occur, which can lead to an unexpected outage.
If found, BGP Route Target Configuration must be corrected during a window to the `route-target` type prior to upgrade:

``` title="Correct configuration after 4.2"
route-target:as4-nn2:1234:1300
route-target:as4-nns:1.2.3.4:20
```


### APIC Container Bridge IP Overlap with APIC TEP 

By default, the APIC Container Bridge IP (docker0 interface) for AppCenter uses 172.17.0.1/16. If this overlaps with the APIC TEP IP range, APICs may not be able to communicate with each other. Depending on the version, the bridge IP may fallback to 172.18.0.1/16 to avoid the conflict. However, after an upgrade, the bridge IP may start using 172.17.0.1/16 again, which can result in an upgrade failure with an unhealthy APIC cluster.

To avoid this, the APIC Container Bridge IP must be expliplicitly configured to be a different range than the APIC TEP IP range. The APIC Container Bridge IP can be changed from `Apps > Settings` in the APIC GUI.

The script checks if the APIC Container Bridge IP is overlapping withe the APIC TEP IP range via `containerBip` of an object `apContainerPol` (DN: `pluginPolContr/ContainerPol`).

!!! example
    ```
    admin@f2-apic1:~> moquery -d pluginPolContr/ContainerPol | grep containerBip
    containerBip : 172.17.0.1/16
    ```


### Fabric Uplink Scale cannot exceed 56 uplinks per leaf

Prior to release 6.0, the per-leaf fabric uplink count was not enforced. However, surpassing 56 could lead to programming issues on the leaf.

After release 6.0, per-leaf fabric uplink count is enforced via enhancement CSCwb80058. If a leaf switch has surpassed 56 uplinks and is upgraded, 56 uplinks will come up and the rest will not.

To avoid this, explicitly modify the port profile uplink scale to be 56 or less per leaf.

The script counts the amount of port-profile provisioned uplinks per leaf, and fails if any leaf is found to surpass 56.


### OoB Mgmt Security

In the configuration of APIC Out-of-Band Management EPG, users can limit the protocols and source IP addresses that can access APIC nodes.

To prevent accidental blocking of necessary access to APIC, essential access (ICMP, SSH, HTTP, and HTTPS) to APICs from the same subnet as the APIC OoB IP address is always permitted, regardless of the contracts and subnets configuration of the OoB Management EPG.

Starting from releases 4.2(7) and 5.2(1), this safeguard implementation was extended to allow ICMP, SSH, and HTTPS from any source. However, CSCvz96117 reverted this change in release 5.2(3) due to use cases where ICMP, SSH, and HTTPS should only be allowed from a known secure source — the same subnet as the APIC OoB IP address and other user-configured IP addresses.

This implies that for users running releases 4.2(7), 5.2(1), or 5.2(2), and when the OoB Management EPG is configured with contracts to restrict ICMP, SSH and HTTPS access to a specific subnet, OoB security is not honored, and those can still be allowed from any subnet. After upgrading to release 5.2(3) or a newer version, OoB Management access to APICs will only be permitted from the configured subnet or ICMP, SSH, HTTP and HTTPS from the same subnet as the APIC OoB IP addresses as it were before 4.2(7). This change might catch users by surprise if they were previously accessing APICs via ICMP, SSH, or HTTPS from a subnet other than the configured one.

The script checks whether you should be aware of this change in behavior prior to your ACI upgrade so that appropriate subnets can be added to the configuration or you can prepare a workstation that is within the configured subnet, which will continue to be accessible to APICs even after the upgrade.


### EECDH SSL Cipher

Under `Fabric > Fabric Policies > Policies > Pod > Management Access > default`, there are multiple SSL ciphers which can be enabled or disabled by the user. Cipher states should only be modified if a configured cipher is declared insecure or weak by the IETF. When modifying any cipher it is important to validate that the configuration is valid otherwise NGINX may fail to validate and the GUI will become unusable due to no cipher match. For more information reference the [APIC Security Configuration Guide][19].

EECDH is a key algorithm that many cipher suites use for HTTPS communication. If the key algorithm is disabled any cipher suite using this key algorithm will also be implicitly disabled. Cisco does not recommend disabling EECDH.

When disabled, the nginx.conf configuration file may fail to validate and NGINX will continue to use the last known good configuration. On upgrade, nginx.conf will also fail to validate but there is no known good configuration so the APIC GUI will be down until EECDH is re-enabled.

!!! tip
    If the GUI is inaccessible due to the EECDH cipher being disabled, it can be re-enabled from the CLI using icurl.
    ```
    apic1# bash
    admin@apic1:~> icurl -X POST 'http://localhost:7777/api/mo/uni/fabric/comm-default/https/cph-EECDH.json' -d '{"commCipher":{"attributes":{"state":"enabled"}}}'
    {"totalCount":"0","imdata":[]}
    admin@apic1:~>
    ```


### BD and EPG Subnet must have matching scopes

Bridge Domains and EPGs can both have subnets defined. Depending on the features in use, there are 3 scope options that can be applied on these BD and EPG subnets to enable specific functionality:

- **Private** — The subnet applies only within its tenant. This is the default scope option.
- **Public**  — The subnet can be exported to a routed connection. This scope option is used with matching L3Out definitions to export the subnet outside of the ACI Fabric.
- **Shared**  — The subnet can be shared with and exported to multiple VRFs in the same tenant or across
tenants as part of a "Shared Service" configuration within the ACI Fabric. An example of a shared service is a routed connection from one VRF having access to an EPG in a different VRF. The 'shared' scope option is required to enable traffic to pass in both directions across VRFs.

Before the fix implemented in [CSCvv30303][21], it was possible for a BD and an associated EPG to have the same subnet defined, but with mismatching scopes. The non-deterministic nature of ACI meant that policy re-programmings, such as via Upgrade or Clean Reloads, could change which subnet scope option definition would take affect first, the BD or the EPG, and could result in a loss of expected traffic flows.

[CSCvv30303][21] introduced policy validations to prevent this configuration and enforce that matching subnets defined in both the BD and related EPG have the same scope. It is imperative that identified mismatching subnet scopes are corrected within an ACI fabric to prevent unexpected traffic pattern issues in the future.

### Unsupported FEC Configuration for N9K-C93180YC-EX

Nexus C93180YC-EX switches [do not support CONS16-RS-FEC or IEEE-RS-FEC][26] mode. In older versions a FEC mode misconfiguration does not cause the interface to be down. However after upgrading to 5.0(1) or later the port will become hardware disabled until the misconfiguration is removed. 

It is important to remove any unsupported configuration prior to ugprade to avoid any unexpected downtime.

!!! example
    On each N9K-C93180YC-EX switch, you can check the FEC mode for each interface with the following query:
    ```
    leaf101# moquery -c l1PhysIf -x query-target-filter=or\(eq\(l1PhysIf.fecMode,\"ieee-rs-fec\"\),eq\(l1PhysIf.fecMode,\"cons16-rs-fec\"\)\)
    Total Objects shown: 1

    # l1.PhysIf
    id                             : eth1/1
    adminSt                        : up
    autoNeg                        : on
    breakT                         : nonbroken
    bw                             : 0
    childAction                    :
    delay                          : 1
    descr                          :
    dfeDelayMs                     : 0
    dn                             : sys/phys-[eth1/1]
    dot1qEtherType                 : 0x8100
    emiRetrain                     : disable
    enablePoap                     : no
    ethpmCfgFailedBmp              : 
    ethpmCfgFailedTs               : 00:00:00:00.000
    ethpmCfgState                  : 2
    fcotChannelNumber              : Channel32
    fecMode                        : ieee-rs-fec   <<<
    ```


### CloudSec Encryption Check

Starting in Cisco ACI 6.0(6) the CloudSec Encryption feature is deprecated. This is documented within the [Cisco Application Policy Infrastructure Controller Release Notes, Release 6.0(6)][33]

This check will look for configured Pre-shared keys (PSK) within your APIC cluster. Note the following behaviors on these objects:

1. Due to [CSCwe67926][34], if even a single PSK was configured for CloudSec Encryption at any point, even if never used, the object will remain and this check will alert you to this finding.
2. The only way to truly validate whether or not CloudSec Encryption is in use on your ACI fabric is to validate if CloudSec Encryption is enabled from within the [Nexus Dashboard Orchstrator Configuration][35]


### Out-of-Service Ports Check

Any Port that has been disabled via policy creates a `fabricRsOosPath` object and marks the ports usage as `blacklist`, or `blacklist,epg` if policy was applied to it. `fabricRsOosPath` objects can be found within the UI at the "Fabric" > "Disabled Interfaces and Decommissioned Switches" view.

While generally not recommended, there are policy bypass methods to bring up ports which are out-of-service via policy. The problem arises from the ports active state deviating from ports configured policy, and this fact generally remains undetected as policy was bypassed. If an event occurs which causes Switch Nodes to receive and reprogram policy from the APICs, the configured out-of-service policy will bring the out-of-service ports down, as expected.

A Switch upgrade is one such event which results in Switch Nodes receiving policy from APICs. This will push the `fabricRsOosPath` policy to the switch again, resulting in all affected ports being rought down until the matching out-of-service policy is properly removed.


### TEP-to-TEP atomic counters Scalability Check

As documented in the [Verified Scalability Guide for Cisco APIC][38], ACI supports a maximum of 1600 instances of TEP-to-TEP Atomic counter policy `dbgAcPath`.
Exceeding any scalability number documented in this guide can cause unexpected issues. In this specific scenario, exceeding the atomic counter limit has been seen to create issues with collecting techsupports and configuration exports.

The script validates the count of `dbgAcPath` is less than the documented supported number. 


### HTTPS Request Throttle Rate

ACI supports **HTTPS Request Throttle** via NGINX rate limit to prevent external API clients from consuming too much resources on APICs. This feature, which is disabled by default, is located at `Fabric > Fabric Policies > Pod > Management Access > default (or name you configured)` in the APIC GUI.

Starting from ACI version 6.1(2), the supported maximum rate for this feature was reduced to 40 requests per second (r/s) or 2400 requests per minute (r/m) from 10,000 r/m. Configuration with a value larger than these gets rejected starting from 6.1(2).
This change is to ensure that users using this feature configure a meaningful rate. If the rate is larger than the new maximum, APIC may not be able to keep up with incoming requests despite the throttling in place, and the APIC GUI can get sluggish or unresponsive which defeats the purpose of the feature.

This script checks the configuration in all Management Access Policies to alert users when the following conditions are met because APIC upgrade will fail in such a case.

* The upgrade is from a version older than 6.1(2a) to a version newer than 6.1(2a). (ex. 5.2(8g) to 6.1(2h))
* HTTPS Request Throttling is enabled and its rate is larger than 40 r/s or 2400 r/m

!!! tip
    Regardless of the APIC version, the best practice is to enable **HTTPS Request Throttle** with 30 requests per second. See [ACI Best Practices Quick Summary][47] for reference and details about the feature.

    Also note that **HTTPS Request Throttle** in this check is referring to the global throttling as opposed to the new feature **Custom Throttle Group** that was introduced in 6.1(2).


### Global AES Encryption

**Global AES Encryption** enables Cisco APICs to encrypt passwords and include them in the configuration export (backup). See [ACI Best Practices Quick Summary][49] for details about the feature itself.

In terms of upgrade, taking a configuration backup with **Global AES Encryption** enabled before your upgrade is highly recommended so that you or Cisco TAC can restore your fabric even if something unexpected may occur during your upgrade.

Although enabling **Global AES Encryption** has been a best practice, it has become mandatory to upgrade to ACI version 6.1(2) or later. If you proceed with your APIC upgrade to 6.1(2) or newer version while **Global AES Encryption** is disabled, the upgrade will immediately fail.

When **Global AES Encryption** is not enabled, this script alerts users in two different ways depending on the target version.

* When it is not enabled and the target version is 6.1(2) or later, this check is flagged as `UPGRADE FAILURE`.
* When it is not enabled and the target version is older than 6.1(2), this check is flagged as `MANUAL CHECK REQUIRED` to encourage users to follow the best practice to enable it (and take a configuration back again before the upgrade).


## Defect Check Details

### EP Announce Compatibility

If your current ACI switch version is pre-12.2(4p) or 12.3(1) and you are upgrading to release 13.2(2) or later, you are susceptible to a defect CSCvi76161, where a version mismatch between Cisco ACI leaf switches may cause an unexpected EP announce message to be received by the EPM process on the leaf switch, resulting in an EPM crash and the reload of the switch.

To avoid this issue, it is critical that you upgrade to a fixed version of CSCvi76161 prior to upgrading to release 13.2(2) or later.

* For fabrics running a pre-12.2(4p) ACI switch release, upgrade to release 12.2(4r) first, then upgrade to the desired destination release.
* For fabrics running a 12.3(1) ACI switch release, upgrade to release 13.1(2v) first, then upgrade to the desired destination release.


### Eventmgr DB size defect susceptibility

Due to defects CSCvn20175 or CSCvt07565, the upgrade of APICs may get stuck or take an unusually long time to complete. Either eventmanager defect results in a database shard with a replica 0 that grew exceptionally large. This, in turn, increases the time it takes for dataconvergence to complete.

Root access is required to check the current size of APIC database shards. A Cisco TAC SR is required for root access.

This script checks if the current version is susceptible to either CSCvn20175 or CSCvt07565.


### Contract Port 22 Defect

Due to the defect CSCvz65560, a contract using TCP port 22 is either disabled or programmed with a wrong value during while upgrading the fabric to 5.0 or a newer version. The issue was fixed and not observed when upgrading to 5.2(2g) or newer.

The script checks whether the your upgrade is susceptible to the defect from the version point of view.


### `telemetryStatsServerP` Object

Beginning with the Cisco APIC 5.2(3) release, the `telemetryStatsServerP` managed object with `collectorLocation` of type `apic` is no longer supported and removed post Cisco APIC upgrade.

Due to the defect CSCvt47850, if the switches are still on an older version than the 4.2(4) release the managed object is deleted before the switches are upgraded and this may cause the switches to become inactive or crash.

To avoid this issue, change the `collectorLocation` type to `none` through the API to prevent the object from being automatically deleted post upgrade.

1. If `telemetryStatsServerP` exists with `collectorLocation="apic"`, use the API to change the `collectorLocation` type to `none`.

    !!! example
        `collectorLocation` is set to `apic` so this fabric is susceptible to CSCvt47850. Use icurl to change `collectorLocation` to `none`.
        ```
        apic# moquery -c telemetryStatsServerP
        # telemetry.StatsServerP
        collectorLocation  : apic <<<
        apic# bash
        apic:~> icurl -kX POST "http://localhost:7777/api/mo/uni/fabric/servers/stserverp-default.xml" -d '<telemetryStatsServerP status="modified" collectorLocation="none"/>'
        apic:~> exit
        apic# moquery -c telemetryStatsServerP
        # telemetry.StatsServerP
        collectorLocation  : none <<<
        ```
2. Upgrade both Cisco APICs and switches to the target version.

3. After validating that all switches have been upgraded successfully, delete the `telemetryStatsSeverP` managed object.

    !!! example
        Object can safely be removed from the fabric.
        ```
        apic# bash
        apic:~> icurl -kX POST "http://localhost:7777/api/mo/uni/fabric/servers/stserverp-default.xml" -d '<telemetryStatsServerP status="deleted"/>'
        ```


### Link Level Flow Control

Due to the defect CSCvo27498, after upgrade of first ACI leaf switch in a VPC pair to newer 15.x version from older 13.x version, downstream VPC might be down due to `vpc port channel mis-config due to vpc links in the 2 switches connected to different partners` even though they are connected to same device. 

By default Link level Flow control is off in ACI but in older code, the ACI software was incorrectly signalling far end device to enable transmit flow control. if far end device transmit(send) flow control  in auto or desirable mode, it will enable transmit flow control.

After the first switch in VPC pair is upgraded to newer 15.x code, the  incorrect flow control signalling is fixed. But due to mismatched software versions in ACI during upgrade, the far end device port-channel member interfaces will end up with mismatched send flow control. When this happens. they could send a different LACP operational key causing the ACI leaf to interpret that it is connected to different partners. 

The script checks if the version is susceptible to the default along with the specific 1G SFPs that are affected by the defect.


### Internal VLAN Pool

Prior to upgrading to Cisco APIC release 4.2(6) or later, you must ensure that any VLAN encap blocks that are explicitly used for front-panel ports are set to type **external (on the wire)**. The encap block type **internal** is reserved only for AVE deployment. Due to the defect CSCvw33061, this configuration might have worked prior to release 4.2(6) despite being misconfigured. If you fail to correct the misconfiguration before you upgrade Cisco APIC, it will result in the affected VLANs being removed from the front-panel port that can result in a data plane outage.


### APIC CA Cert Validation

Due to the defect CSCvy35257, APIC may have a corrupted CA certificate after importing a backup config without AES encryption. If an upgrade is performed while the CA certificate is corrupted, spine switches will repeatedly reboot (CSCwc74242).

The script checks if the APIC CA certificate is corrupted or not.


### FabricDomain Name

Due to the defect CSCwf80352, ACI switches cannot join the fabric after an upgrade to 6.0(2) release when the name of the ACI fabric (`fabricDomain` in an object `topSystem`) containis "#" or ";".

The script checks if the target version is 6.0(2) and if the fabric name contains "#" or ";".


### Spine SUP HW Revision

Field Notice [FN74050][43] outlines 2 issue scenarios that can be hit for a subset of Spine Sup-A+ and SUP-B+ Part Numbers.

There is a VRM Issue outlined by [CSCwd65255][44] which can occur for affected SUP parts after performing an EPLD upgrade, forcing the user to perofrm an additional power cyclel beforeo they will boot up. If 'VRM Concern' is flagged, review the FN details which includes a link to a script which can be run by TAC to proactively address this specific issue.

There is also an FPGA Downgrade Issue which is due to a combination of [CSCwb86706][29] and [CSCwf44222][30]. This specific scenario is more severe in that ACI modular spine switches will not be able to boot after an upgrade if hit and a replacement is required. However, the FPGA Downgrade Issue can be avoided entirely by targeting a fixed version of [CSCwf44222][30].

The script checks if the version and the SUP Part Numbers are susceptible to either FN issue scenario.


### CoS 3 with Dynamic Packet Prioritization

Due to the defect CSCwf05073, ACI unexpectedly assigning a COS3 value to traffic egressing front ports. 

In certain cases, such as when frames goes through FCoE supported devices, these get classified into the no drop FCoE class. In FCoE devices, this can cause drop of packets when the packet length is higher than the allowed 2184 bytes.

For example, on the UCS Fabric Interconnect COS3 value is hardcoded for fiber channel (FC) or fiber channel over ethernet (FCoE) traffic. FC/FCoE traffic is highly sensitive and is treated as non-droppable, and cannot exceed MTU of 2184 bytes long.

This script checks if the target version is susceptible to CSCwf05073 and dynamic packet prioritization feature is set to "on".
### SUP-A/A+ High Memory Usage

Due to the increased memory utilization from 6.0(3), N9K-SUP-A or N9K-SUP-A+ will likely experience constant high memory utilization.

It is highly recommended not to upgrade your ACI fabric to 6.0(3), 6.0(4) or 6.0(5) if your fabric contains N9K-SUP-A and/or N9K-SUP-A+. Instead, wait for the memory optimization in a near-future Cisco ACI 6.0 maintenance release that will allow the N9K-SUP-A and N9K-SUP-A+ supervisors to operate in a normal memory condition.

!!! note
    This is also called out in release notes of each version - [6.0(3)][15], [6.0(4)][16], [6.0(5)][17]:


### VMM Uplink Container with empty Actives

Due to the defect CSCvr96408, affected versions with VMM domains having VMM parameters changed via the UI could have resulted in `fvUplinkOrderCont` objects created with the parameter `"active": ""` ('active' set to blank). This `active` parameter defines which uplinks should be set to active on the Vmware created EPG portgroup, and if blank, results in no active uplinks. In most cases, traffic issues due to this config were worked-around by manually modifying the active uplink configuration directly within VMware vCenter.

The issue arises when an upgrade or VMM parameter change occurs. Either change causes a re-validation of the `fvUplinkOrderCont` VMM policy as defined in ACI. The result is that any `fvUplinkOrderCont` still having `active: ""` will push a config change into VMware vCenter to map back to APIC policy, resulting in the removal of active uplinks and a corresponding outage.

This script checks for `fvUplinkOrderCont` with `active: ""` and alerts the user to their existence. The `active` parameter must match your current active configuration to avoid an outage on subsequent upgrade of VMM Parameter change.

The example shows a correctly defined `fvUplinkOrderCont`, with uplinks under the `active` field.

!!! example
    ```
    apic1# moquery -c fvUplinkOrderCont
    Total Objects shown: 1

    # fv.UplinkOrderCont
    active       : 1,2,3,4,5,6,7,8
    annotation   : 
    childAction  : 
    descr        : 
    dn           : uni/tn-test1/ap-ap3/epg-epg3/rsdomAtt-[uni/vmmp-VMware/dom-test-dvs]/uplinkorder
    extMngdBy    : 
    lcOwn        : local
    modTs        : 2024-04-30T16:15:06.815+00:00
    name         : 
    nameAlias    : 
    ownerKey     : 
    ownerTag     : 
    rn           : uplinkorder
    standby      : 
    status       : 
    uid          : 15374
    userdom      : :all:common:
    ```


### N9K-C93108TC-FX3P/FX3H Interface Down

Due to the defect CSCwh81430, some RJ45 interfaces on Cisco Nexus N9K-C93108TC-FX3P and N9K-C93108TC-FX3H Switches might not come up, even when connected.

This issue can be triggered by a switch reload that occurs for any reason, including a software upgrade, software reset, system crash, or the power being turned up or down.

The problem is related only to the front-panel interfaces Ethernet 1/1- 1/48. Optical ports Ethernet 1/49 - 54 and MGMT0 port are not affected.

Because of this, the target version of your upgrade must be a version with a fix of CSCwh81430 when your fabric includes those switches mentioned above. See the Field Notice [FN74085][20] for details.


### Invalid fabricPathEp Targets

Prior to [CSCwh68103][23], `fabricPathEp` objects could be created using DN formats that do not match a valid schema and are technically invalid. The issue arises after upgrading to a version with validations included; any fixed version of [CSCwh68103][23]. While on a fixed version, if changes are made to objects that target `fabricPathEp` objects with invalid DNs, such as `infraRsHPathAtt` or `fabricRsOosPath`, an error resembling `Failed to decode IfIndex, id: 0x.......` will be seen and the desired configuration change will be prevented until the invalid DN syntax objects are cleaned up.

The details documented within [CSCwh68103][23] describe the various validations that were added to `fabricPathEp` DNs. 

If invalid DNs are found, and depending on the scale of invalid DNs, work with TAC to plan a deletion of identified objects. 

This check queries `infraRsHPathAtt` and `fabricRsOosPath` objects and then scans all the `tDn` parameters for known invalid `fabricPathEp` references.


### LLDP Custom Interface Description

Due to the defect [CSCwf00416][24], custom interface descriptions may override the port topology DN. In ACI LLDP should always advertise the topology DN as the port description irrespective of whether an interface description is configured or not.

In cases where there is a custom interface description and a VMM-integrated deployment with deploy immediacy set to on-demand, connectivity may break on upgrade. If both of these features are enabled it is not recommended to upgrade to 6.0(1) or 6.0(2).

!!! note
    To check for any custom interface descriptions, you can use the following moquery command.
    ```
    apic1# moquery -c infraPortBlk -x query-target-filter=ne\(infraPortBlk.descr,""\)
    Total Objects shown: 11

    # infra.PortBlk
    name         : portblock1
    annotation   :
    childAction  :
    descr        : port 30 on Leaf 101 and 103 to FI-B      <<< Description is set
    dn           : uni/infra/accportprof-system-port-profile-node-103/hports-system-port-selector-accbundle-VPC_FIB-typ-range/portblk-portblock1
    --- omit ---
    ```

    To check for any VMM Domains using on-demand deploy immediacy, you can use the following moquery command.
    ```
    apic1# moquery -c fvRsDomAtt -x query-target-filter=and\(eq\(fvRsDomAtt.tCl,\"vmmDomP\"\),eq\(fvRsDomAtt.instrImedcy,\"lazy\"\)\)
    Total Objects shown: 90

    # fv.RsDomAtt
    tDn                  : uni/vmmp-VMware/dom-shared-dvs
    dn                   : uni/tn-prod/ap-inet/epg-epg1/rsdomAtt-[uni/vmmp-VMware/dom-shared-dvs]
    instrImedcy          : lazy                            <<< deploy immediacy is on-demand
    tCl                  : vmmDomP
    --- omit ---
    ```

### Route-map Community Match

Due to the defect [CSCwb08081][25], if you have a route-map with a community match statement but there is no prefix list match the set clause may not be applied.

It is recommended if you are upgrading to an affected release to add a prefix list match statement prior to upgrade.

!!! example
    In this example, the Route-map match rule `rtctrlSubjP` has a community match `rtctrlMatchCommFactor` but no prefix list match `rtctrlMatchRtDest`. This match rule would be affected by the defect.
    ```
    apic1# moquery -c rtctrlSubjP -x rsp-subtree=full -x rsp-subtree-class=rtctrlMatchCommFactor,rtctrlMatchRtDest | egrep "^#|dn "
    # rtctrl.SubjP
    dn           : uni/tn-Cisco/subj-match-comm
    # rtctrl.MatchCommTerm
    dn           : uni/tn-Cisco/subj-match-comm/commtrm-test
    # rtctrl.MatchCommFactor
        dn           : uni/tn-Cisco/subj-match-comm/commtrm-test/commfct-regular:as2-nn2:4:15
    ```
    In order to fix this, navigate to `Tenants > "Cisco" > Policies > Protocol > Match Rules > "match-comm"` and add a prefix-list.
    ```
    apic1# moquery -c rtctrlSubjP -x rsp-subtree=full -x rsp-subtree-class=rtctrlMatchCommFactor,rtctrlMatchRtDest | egrep "^#|dn "
    # rtctrl.SubjP
    dn           : uni/tn-Cisco/subj-match-comm
    # rtctrl.MatchCommTerm
    dn           : uni/tn-Cisco/subj-match-comm/commtrm-test
    # rtctrl.MatchCommFactor
        dn           : uni/tn-Cisco/subj-match-comm/commtrm-test/commfct-regular:as2-nn2:4:15
    # rtctrl.MatchRtDest
    dn           : uni/tn-Cisco/subj-match-comm/dest-[0.0.0.0/0]
    ```


### L3out /32 overlap with BD Subnet

Due to defect [CSCwb91766][27], L3out /32 Static Routes that overlap with BD Subnets within the same VRF will be programmed into RIB but not FIB of the relevant switches in the forwarding path. This will cause traffic loss as packets will not be able to take the /32 route, resulting in unexpecteded forwarding issues.

If found, the target version of your upgrade should be a version with a fix for CSCwb91766. Otherwise, the other option is to change the routing design of the affected fabric.


### vzAny-to-vzAny Service Graph when crossing 5.0 release

When your APIC upgrade is crossing 5.0 release, for instance upgrading from 4.2(7w) to 5.2(8i), traffic hitting a vzAny-to-vzAny contract with Service Graph may experience disruption for a short amount of time.

!!! note
    A vzAny-to-vzAny contract refers to a contract that is provided and consumed by the same VRF (vzAny) so that the contract is applied to all traffic in the said VRF.

    The potential transient traffic disruption occurs during an APIC upgrade instead of a switch upgrade.

The script checks the two points:

1. The combination of your source and target version is susceptible
2. You have any vzAny-to-vzAny contract with Service Graph

When both conditions are met, the script results in `FAIL - OUTAGE WARNING!!` to inform you of potential disruption to your traffic going through such Service Graph. In such a case, make sure to upgrade your APICs during a maintenance window that can tolerate some traffic impact.

This transient disruption is because the pcTag of the service EPG for a vzAny-vzAny Service Graph is updated from APIC and re-programmed on switches due to an internal architecture update in [APIC Release 5.0][31] (See also [CSCwh75475][32]).
Depending on the timing and how fast the re-programming finishes, you may not see any traffic disruption. Unfortunately, it is difficult to estimate the amount of time the re-programming takes but it generally depends on the number of VRFs, service graphs, contract rules etc.

!!! tip
    With L4-L7 Service Graph, ACI deploys an internal/hidden EPG representing the service node to be inserted via the Service Graph. Such a hidden EPG is called Service EPG. When a Service Graph is applied to a contract, internally a service EPG is inserted between the provider and consumer EPGs so that the traffic flow will be consumer EPG to service EPG (i.e. service node such as firewall), coming back from the service node, then service EPG to provider EPG. Because of this, if the pcTag of service EPG is updated, such traffic flow gets impacted while it's being re-programmed in the switch hardware.

    Due to the update in [APIC Release 5.0][31], the pcTag of the service EPG for a vzAny-vzAny Service Graph will be updated to a Global pcTag from a Local pcTag. Global pcTags are in the range of 1 - 16384 while local pcTags are 16385 - 65535. You can check the pcTag of your service EPG from `Tenant > Services > L4-L7 > Deployed Graph Instances > Function Node > Policy > Function Connectors > Class ID` in the APIC GUI.


### FC/FCOE support for -EX switches

Due to defect [CSCwm92166][36], ACI switches with models ending in '-EX' will not support FC/FCOE configurations if upgraded to an affected release. If upgraded, the FC/FCOE interface will remain down and fault F4511 will be raised.

Refer to the [Cisco APIC Layer 2 Networking Configuration Guide, Release 6.1(x)][37] for a complete list of for FC/FCOE supported hardware.

The script checks if your upgrade is susceptible to this defect from both version and configuration perspectives.


### Nexus 950X FM or LC Might Fail to boot after reload

A clock signal component manufactured by one supplier, and included in some Cisco products, has been seen to degrade over time in some units.
Although the Cisco products with these components are currently performing normally, we expect product failures to increase over the years, beginning after the unit has been in operation for approximately 18 months. Additional details are document in [FN64251][39]

The matching defect is [CSCvg26013][40].

This check alerts you to potentially affected modules:

Fabric Modules

 - N9K-C9504-FM-E
 - N9K-C9508-FM-E

Line Card

 - N9K-X9732C-EX

If alerted, check if identified Serial Numbers are affected using the [Serial Number Validation Tool][41].


### Stale Decommissioned Spine Check

Due to defect [CSCwf58763][42], upgrading to non-fixed versions with `fabricRsDecommissionNode` objects pointing to Spine Node IDs, regardless of pod location defined in the `fabricRsDecommissionNode` object, will result in those Spine Nodes being removed from Leaf Node COOP Adjacency lists. This results in Leaf Nodes no longer publishing endpoint updates to affected Spine Nodes, resulting in packet drops for any spine proxy traffic hashed to an affected Spine Node.

### GX2A Platform Model Check

[CSCwk77800][45] fixed a behavior where `N9K-C9400-SW-GX2A` are expected to report their chassis as `N9K-C9408`.

When an identified node is upgraded to a fixed 6.1(3)+ version, the old model's entry will show up as inactive and must be decomissioned and the new model's entry must be registered. The result is that the node will not completely join the fabric post-upgrade until these additional steps are performed on each identified GX2A node.

### PBR High Scale Check

Due to [CSCwi66348][46], Leaf Switches with high scale PBR config (classes `vnsAdjacencyDefCont`, `vnsSvcRedirEcmpBucketCons` and `fvAdjDefCons` specifically) can take an unexpectedly long time to complete bootstrap after an upgrade.

This check will count the number of relevant PBR policies across the entire ACI fabric from an APIC perspective (classes `vnsAdjacencyDefCont`, `vnsSvcRedirEcmpBucketCons`) and alert if targeting an affected version with relevant PBR config objects greater than 100k. If alerted, the recommended action is to target a version that has the fix for [CSCwi66348][46].


### Standby Sup Image Sync Check

Due to [CSCwa44220][48], the Standy Supervisor Modules within Modular Chassis will be unable to successfully install switch images greater than 2 Gigs.

If this alert is flagged then plan for an interim upgrade hop to a fixed version that is less than 2 Gigs, for example to 5.2(8i).


[0]: https://github.com/datacenter/ACI-Pre-Upgrade-Validation-Script
[1]: https://www.cisco.com/c/dam/en/us/td/docs/Website/datacenter/apicmatrix/index.html
[2]: https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-release-notes-list.html
[3]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/5x/release-notes/cisco-aci-nx-os-release-notes-1501.html#_Toc140580685
[4]: https://www.cisco.com/c/en/us/support/cloud-systems-management/application-policy-infrastructure-controller-apic/tsd-products-support-series-home.html
[5]: http://cs.co/9003ybZ1d
[6]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/all/apic-installation-aci-upgrade-downgrade/Cisco-APIC-Installation-ACI-Upgrade-Downgrade-Guide/m-aci-firmware-upgrade-overview.html#Cisco_Concept.dita_78b8949b-2c61-4186-bca1-23954c7b3971__section_pyw_dss_gqb
[7]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/all/apic-installation-aci-upgrade-downgrade/Cisco-APIC-Installation-ACI-Upgrade-Downgrade-Guide/m-aci-firmware-upgrade-overview.html#Cisco_Concept.dita_78b8949b-2c61-4186-bca1-23954c7b3971
[8]: https://www.cisco.com/c/en/us/support/docs/cloud-systems-management/application-policy-infrastructure-controller-apic/215166-apic-ssd-replacement.html
[9]: https://www.cisco.com/c/en/us/support/docs/software/aci-data-center/215167-aci-switch-node-ssd-lifetime-explained.html
[10]: https://community.cisco.com/t5/data-center-documents/overlap-vlan-pool-lead-intermittent-packet-drop-to-vpc-endpoints/ta-p/3211107
[11]: https://community.cisco.com/t5/data-center-documents/aci-common-migration-issue-overlapping-vlan-pools/ta-p/3362376
[12]: https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/4-x/L2-configuration/Cisco-APIC-Layer2-Configuration-Guide-42x/Cisco-APIC-Layer2-Configuration-Guide-421_chapter_0110.html#id_109428
[13]: https://www.cisco.com/c/en/us/td/docs/dcn/whitepapers/cisco-aci-best-practices-quick-summary.html#_Toc114493697
[14]: https://www.cisco.com/c/en/us/td/docs/dcn/whitepapers/cisco-aci-best-practices-quick-summary.html#_Toc114493698
[15]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/6x/release-notes/cisco-apic-release-notes-603.html
[16]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/6x/release-notes/cisco-apic-release-notes-604.html
[17]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/6x/release-notes/cisco-apic-release-notes-605.html
[18]: https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/kb/cisco-mini-aci-fabric.html#Cisco_Task_in_List_GUI.dita_2d9ca023-714c-4341-9112-d96a7a598ee6
[19]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/5x/security-configuration/cisco-apic-security-configuration-guide-release-52x/https-access-52x.html
[20]: https://www.cisco.com/c/en/us/support/docs/field-notices/740/fn74085.html
[21]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvv30303
[22]: https://www.cisco.com/c/dam/en/us/td/docs/unified_computing/ucs/c/sw/CIMC-Upgrade-Downgrade-Matrix/index.html
[23]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwh68103
[24]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwf00416
[25]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwb08081
[26]: https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/kb/b_Cisco_ACI_and_Forward_Error_Correction.html#Cisco_Reference.dita_5cef69b3-b7fa-4bde-ba60-38129c9e7d82
[27]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwb91766
[28]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/all/apic-installation-aci-upgrade-downgrade/Cisco-APIC-Installation-ACI-Upgrade-Downgrade-Guide/m-aci-upgrade-downgrade-architecture.html#Cisco_Reference.dita_22480abb-4138-416b-8dd5-ecde23f707b4
[29]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwb86706
[30]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwf44222
[31]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/all/cisco-aci-releases-changes-in-behavior.html#ACIrelease501
[32]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwh75475
[33]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/6x/release-notes/cisco-apic-release-notes-606.html
[34]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwe67926
[35]: https://www.cisco.com/c/en/us/td/docs/dcn/ndo/3x/configuration/cisco-nexus-dashboard-orchestrator-configuration-guide-aci-371/ndo-configuration-aci-infra-cloudsec-37x.html#id_76319
[36]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwm92166
[37]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/6x/l2-configuration/cisco-apic-layer-2-networking-configuration-guide-61x/fcoe-connections-61x.html
[38]: https://www.cisco.com/c/en/us/td/docs/dcn/aci/apic/6x/verified-scalability/cisco-aci-verified-scalability-guide-612.html
[39]: https://www.cisco.com/c/en/us/support/docs/field-notices/642/fn64251.html
[40]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCvg26013
[41]: https://snvui.cisco.com/snv/FN64251
[42]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwf58763
[43]: https://www.cisco.com/c/en/us/support/docs/field-notices/740/fn74050.html
[44]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwd65255
[45]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwk77800
[46]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwi66348
[47]: https://www.cisco.com/c/en/us/td/docs/dcn/whitepapers/cisco-aci-best-practices-quick-summary.html#HTTPSRequestThrottle
[48]: https://bst.cloudapps.cisco.com/bugsearch/bug/CSCwa44220
[49]: https://www.cisco.com/c/en/us/td/docs/dcn/whitepapers/cisco-aci-best-practices-quick-summary.html#GlobalAESEncryption
