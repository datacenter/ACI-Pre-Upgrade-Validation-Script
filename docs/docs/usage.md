# Usage

Run the script on your APIC via `python aci-preupgrade-validation-script.py`.

The script will prompt for user credentials.

The script will then present a list of firmware from the APIC firmware repository and ask which one is the target version for the next planned upgrade. Ensure you have the desired ACI Firmware uploaded to the APIC Firmware Repository before running this script.

!!! info "Target Firmware Image"
    If the APIC Firmware Repository is empty, the script will proceed but will mark checks that required the target version as `MANUAL CHECK REQUIRED`

!!! info "Required User Proviledges"
    `admin` level privileges with `read` permission are recommended. User permissions are important as most of these checks rely on API query responses.
    This script only performs read operations and will not modify any config or filesystem properties.
    Non-admin remote user credentials can result in RBAC causing queries to return empty responses. This can result in inconsistent script results.


## Example Output
```
admin@f2-apic1:~> cd /data/techsupport
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
--- omit ---

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

## Results

Each check has a unique result which will help determine how to proceed. The results are explained as follows:

- **PASS** - The check has completed, and the ACI Fabric is not affected by the issue.
- **FAIL - OUTAGE WARNING** - The check has completed, and the ACI Fabric is currently affected by an issue which may cause an outage.
- **FAIL - UPGRADE FAILURE** - The check has completed, and the ACI Fabric is currently affected by an issue which may cause the upgrade to fail.
- **MANUAL CHECK REQUIRED** - The check has completed, and the specific check needs to be investigated manually using the steps outlines in the "ACI Upgrade Guide".
- **N/A** - The check completed successfully, and the ACI fabric is not susceptible because the needed configuration is not deployed.
- **ERROR** - The check did not complete successfully, and needs further investigation.

## Logs

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

The `preupgrade_validator_*.txt` file contains a dump of the resulting output which can be referenced for check results post-run.

If there are any issues with the script or run results which require TAC assistance, open a proactive TAC case for the
upgrade and upload the result bundle for analysis.
