# Getting Started

The script (`aci-preupgrade-validation-script.py`) needs to be run on one of your Cisco APICs via SSH session.

Cisco APIC is an linux appliance. You can download the script and copy it over to an APIC just as you do for a regular linux machine.

In case you are wondering how to do this, here are some examples.

!!! Note
    `/data/techsupport` is an ideal location to place the script on your APIC


## 1. Download the script (`aci-preupgrade-validation-script.py`)

### Option1: `git clone`
```sh title="On your local machine"
git clone git@github.com:datacenter/ACI-Pre-Upgrade-Validation-Script.git
```

### Option2: via browser
Download the script from here: [`aci-preupgrade-validation-script.py`][1]

[1]: https://raw.githubusercontent.com/datacenter/ACI-Pre-Upgrade-Validation-Script/master/aci-preupgrade-validation-script.py


## 2. Copy the script to an APIC

### Option1: SCP, SFTP, etc.
```sh title="On your local machine"
scp aci-preupgrade-validation-script.py admin@<apic IP>:/data/techsupport
```

### Option2: SSH and copy/paste via `cat`
```sh title="On your APIC via SSH"
admin@f2-apic1:~> cd /data/techsupport
admin@f2-apic1:techsupport> cat > aci-preupgrade-validation-script.py (Enter)
<.. paste the contents of aci-preupgrade-validation-script.py ..>
(Ctrl+D)
```

### Option3: SSH and copy/paste via `vi`
```sh title="On your APIC via SSH"
admin@f2-apic1:~> cd /data/techsupport
admin@f2-apic1:techsupport> vi aci-preupgrade-validation-script.py
    1. press `i` for insert mode
    2. paste the contents of aci-preupgrade-validation-script.py
    3. `:wq` to save and quit vi
```
