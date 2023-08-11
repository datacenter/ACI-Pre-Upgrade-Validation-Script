# Quick Start

1. Copy [`aci-preupgrade-validation-script.py`](https://raw.githubusercontent.com/datacenter/ACI-Pre-Upgrade-Validation-Script/master/aci-preupgrade-validation-script.py) to your APIC (suggested path: `/data/techsupport`)
2. On your APIC, run `cd /data/techsupport` then `python aci-preupgrade-validation-script.py`
3. Provide a user name and password (admin level privileges are recommended) 
4. Select the target version (the version needs to be on APIC)
5. Follow recommendations for all checks that have been flagged as `FAIL` or `MANUAL CHECK REQUIRED`

# Introduction

The Goal of this script is to provide you with an automated list of proactive checks before performing an ACI fabric upgrade. Each check is documented in [this page][1] with a detailed explanation of the importance to resolve each issue before upgrading.

Check out [ACI Pre-Upgrade Validation Script Document][1] for details of the script.

Check out [ACI Upgrade Guide][2] for details of ACI upgrades in general.

Failure to address an affected issue before an upgrade is known to cause challenges during or post upgrade.

For every check that has been flagged as `FAIL`, a general recommended action has been provided to guide next steps. There is also a summary with the number of checks that matched a given status.


[1]: https://datacenter.github.io/ACI-Pre-Upgrade-Validation-Script/
[2]: https://www.cisco.com/c/en/us/td/docs/switches/datacenter/aci/apic/sw/all/apic-installation-upgrade-downgrade/Cisco-APIC-Installation-Upgrade-Downgrade-Guide.html
