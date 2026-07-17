import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")
Result = script.Result

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "certificate_expiration_check"


# Fault codes in the same order as `fault_min_versions` (dict insertion order),
# which is the order the check builds the OR filter.
MASTER_ORDER = ["F4501", "F4502", "F4503", "F4617", "F3081", "F3082", "F4752", "F4753"]


def fault_query(codes):
    ordered = [c for c in MASTER_ORDER if c in codes]
    return 'faultInst.json?query-target-filter=or({})'.format(
        ",".join('eq(faultInst.code,"{}")'.format(c) for c in ordered)
    )


# icurl queries per applicable version range
faultInst = fault_query(MASTER_ORDER)                                    # cversion >= 6.1(5e)
faultInst_pre_factory = fault_query(["F4501", "F4502", "F4503", "F4617", "F3081", "F3082"])  # 6.1(1e)–6.1(5e)
faultInst_keyring_saml = fault_query(["F4501", "F4502", "F3081", "F3082"])                    # 6.0(4c)–6.1(1e)
faultInst_saml = fault_query(["F3081", "F3082"])                                              # 3.1(2f)–6.0(4c)


# --- Factory certificate (F4752/F4753) SSH check test data ---
fabric_nodes_ssh = [
    {"fabricNode": {"attributes": {"id": "1", "name": "apic1", "role": "controller", "address": "10.0.0.1"}}},
]

fabric_nodes_multi = [
    {"fabricNode": {"attributes": {"id": "1", "name": "apic1", "role": "controller", "address": "10.0.0.1"}}},
    {"fabricNode": {"attributes": {"id": "2", "name": "apic2", "role": "controller", "address": "10.0.0.2"}}},
    {"fabricNode": {"attributes": {"id": "3", "name": "apic3", "role": "controller", "address": "10.0.0.3"}}},
]

DATE_OUTPUT = "Wed Jul 15 06:35:30 UTC 2026\nfab-apic#"

VERIFYAPIC_EXPIRED = """\
openssl_check: Manufacturing certificate details
issuer=CN=Cisco Manufacturing CA,O=Cisco Systems
notBefore=Jul  6 19:33:57 2019 GMT
notAfter=May 14 20:25:42 2024 GMT
openssl_check: passed
all_checks: passed
"""

VERIFYAPIC_EXPIRING = """\
openssl_check: Manufacturing certificate details
issuer=CN=Cisco Manufacturing CA,O=Cisco Systems
notBefore=Jul  6 19:33:57 2019 GMT
notAfter=Aug  1 06:57:40 2026 GMT
openssl_check: passed
all_checks: passed
"""

VERIFYAPIC_VALID = """\
openssl_check: Manufacturing certificate details
issuer=CN=Cisco Manufacturing CA,O=Cisco Systems
notBefore=Jul  6 19:33:57 2019 GMT
notAfter=May 14 20:25:42 2029 GMT
openssl_check: passed
all_checks: passed
"""


def ssh_cmds(outputs):
    if isinstance(outputs, str):
        outputs = {"10.0.0.1": outputs}
    return {
        addr: [
            {"cmd": "date", "output": DATE_OUTPUT, "exception": None},
            {"cmd": "acidiag verifyapic", "output": out, "exception": None},
        ]
        for addr, out in outputs.items()
    }

@pytest.mark.parametrize(
    "icurl_outputs, conn_failure, conn_cmds, cversion, fabric_nodes, expected_result, expected_data",
    [
        
        # ==== cversion >= 6.1(5e): all 8 fault codes, SSH skipped ====

        # PASS - no certificate faults
        (
            {
                faultInst: []
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.PASS,
            [],
        ),
        # MANUAL - only expiring certificate (F4501 - KeyRing)
        (
            {
                faultInst: read_data(dir, "faultInst_F4501.json")
            },
            False, 
            {}, 
            "6.1(5e)",
            [],
            script.MANUAL,
            [
                ["F4501", "major", "KeyRing Certificate THD_KEYRING expiring"],
            ],
        ),
        # MANUAL - only expiring certificate (F3081 - SAML)
        (
            {
                faultInst: read_data(dir, "faultInst_F3081.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.MANUAL,
            [
                ["F3081", "major", "SAML Signing Certificate expiring in one month"],
            ],
        ),
        # MANUAL - only expiring certificate (F4617 - TP)
        (
            {
                faultInst: read_data(dir, "faultInst_F4617.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.MANUAL,
            [
                ["F4617", "major", "TP Certificate expiring"],
            ],
        ),
        # MANUAL - only expiring factory certificate (F4752 - Factory)
        (
            {
                faultInst: read_data(dir, "faultInst_F4752.json")
            },
            False,
            {},
            "6.1(5e)",
            [],
            script.MANUAL,
            [
                ["F4752", "major", "Factory certificate expiring"],
            ],
        ),
        # MANUAL - multiple expiring certificates
        (
            {
                faultInst: read_data(dir, "faultInst_multiple_expiring.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.MANUAL,
            [
                ["F4501", "major", "KeyRing Certificate THD_KEYRING expiring"],
                ["F3081", "major", "SAML Signing Certificate expiring in one month"],
                ["F4617", "major", "TP Certificate expiring"],
            ],
        ),
        # FAIL_O - only expired certificate (F4502 - KeyRing)
        (
            {
                faultInst: read_data(dir, "faultInst_F4502.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.FAIL_O,
            [
                ["F4502", "critical", "KeyRing Certificate THD_KEYRING expired"],
            ],
        ),
        # FAIL_O - only expired certificate (F4503 - TP)
        (
            {
                faultInst: read_data(dir, "faultInst_F4503.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.FAIL_O,
            [
                ["F4503", "critical", "TP Certificate THD_CA expired"],
            ],
        ),
        # FAIL_O - only expired certificate (F3082 - SAML)
        (
            {
                faultInst: read_data(dir, "faultInst_F3082.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.FAIL_O,
            [
                ["F3082", "critical", "SAML Encryption Certificate has expired"],
            ],
        ),
        # FAIL_O - only expired factory certificate (F4753 - Factory)
        (
            {
                faultInst: read_data(dir, "faultInst_F4753.json")
            },
            False,
            {},
            "6.1(5e)",
            [],
            script.FAIL_O,
            [
                ["F4753", "critical", "Factory certificate expired"],
            ],
        ),
        # FAIL_O - multiple expired certificates
        (
            {
                faultInst: read_data(dir, "faultInst_multiple_expired.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.FAIL_O,
            [
                ["F4502", "critical", "KeyRing Certificate THD_KEYRING expired"],
                ["F4503", "critical", "TP Certificate THD_CA expired"],
                ["F3082", "critical", "SAML Encryption Certificate has expired"],
            ],
        ),
        # FAIL_O - mixed: both expiring and expired certificates (expired takes priority)
        (
            {
                faultInst: read_data(dir, "faultInst_mixed.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.FAIL_O,
            [
                ["F4501", "major", "KeyRing Certificate KEYRING1 expiring"],
                ["F4502", "critical", "KeyRing Certificate THD_KEYRING expired"],
                ["F3081", "major", "SAML Signing Certificate expiring in one month"],
                ["F3082", "critical", "SAML Encryption Certificate has expired"],
            ],
        ),
        # PASS - faults exist but not in raised/soaking state (cleared/retaining)
        (
            {
                faultInst: read_data(dir, "faultInst_cleared.json")
            },
            False, 
            {}, 
            "6.1(5e)", 
            [],
            script.PASS,
            [],
        ),

        # ==== Version gating: only applicable fault codes are queried ====

        # 6.1(1e) <= cversion < 6.1(5e): 6 codes (no factory). TP expired.
        (
            {
                faultInst_pre_factory: read_data(dir, "faultInst_F4503.json")
            },
            False, 
            {}, 
            "6.1(1e)", 
            [],
            script.FAIL_O,
            [
                ["F4503", "critical", "TP Certificate THD_CA expired"],
            ],
        ),
        # 6.0(4c) <= cversion < 6.1(1e): KeyRing + SAML only. KeyRing expired.
        (
            {
                faultInst_keyring_saml: read_data(dir, "faultInst_F4502.json")
            },
            False, 
            {}, 
            "6.0(4c)", 
            [],
            script.FAIL_O,
            [
                ["F4502", "critical", "KeyRing Certificate THD_KEYRING expired"],
            ],
        ),
        # 3.1(2f) <= cversion < 6.0(4c): SAML only. Expired.
        (
            {
                faultInst_saml: read_data(dir, "faultInst_F3082.json")
            },
            False, 
            {}, 
            "5.2(7g)", 
            [],
            script.FAIL_O,
            [
                ["F3082", "critical", "SAML Encryption Certificate has expired"],
            ],
        ),
        # 3.1(2f) <= cversion < 6.0(4c): SAML only, none raised.
        (
            {faultInst_saml: []},
            False, 
            {}, 
            "5.2(7g)", 
            [],
            script.PASS,
            [],
        ),
        # cversion < 3.1(2f): no applicable fault codes, no fault query issued.
        (
            {}, 
            False, 
            {}, 
            "2.3(1a)", 
            [],
            script.PASS,
            [],
        ),

        # ==== Factory certificate SSH check (cversion < 6.1(5e)) ====

        # PASS - manufacturing certificate valid (far future)
        (
            {
                faultInst_pre_factory: []
            },
            False, 
            ssh_cmds(VERIFYAPIC_VALID), 
            "6.1(4a)", 
            fabric_nodes_ssh,
            script.PASS,
            [],
        ),
        # FAIL_O - manufacturing certificate expired
        (
            {
                faultInst_pre_factory: []
            },
            False, 
            ssh_cmds(VERIFYAPIC_EXPIRED), 
            "6.1(4a)", 
            fabric_nodes_ssh,
            script.FAIL_O,
            [
                ["N/A", "critical",
                 "APIC 1 (apic1): manufacturing certificate expired on 2024-05-14 20:25:42 UTC"],
            ],
        ),
        # MANUAL - manufacturing certificate expiring within threshold (30 days)
        (
            {faultInst_pre_factory: []},
            False, 
            ssh_cmds(VERIFYAPIC_EXPIRING), 
            "6.1(4a)", 
            fabric_nodes_ssh,
            script.MANUAL,
            [
                ["N/A", "major",
                 "APIC 1 (apic1): manufacturing certificate expiring on 2026-08-01 06:57:40 UTC"],
            ],
        ),
        # ERROR - SSH connection failure while verifying manufacturing certificate
        (
            {
                faultInst_pre_factory: []
            },
            True, 
            {}, 
            "6.1(4a)", 
            fabric_nodes_ssh,
            script.ERROR,
            [
                ["N/A", "error",
                 "APIC 1 (apic1): unable to verify manufacturing certificate - Simulated exception at connect()"],
            ],
        ),
        # FAIL_O - combined: a raised fault AND an expired manufacturing cert (both reported)
        (
            {faultInst_pre_factory: read_data(dir, "faultInst_F4502.json")},
            False, 
            ssh_cmds(VERIFYAPIC_EXPIRED), 
            "6.1(4a)", 
            fabric_nodes_ssh,
            script.FAIL_O,
            [
                ["F4502", "critical", "KeyRing Certificate THD_KEYRING expired"],
                ["N/A", "critical",
                 "APIC 1 (apic1): manufacturing certificate expired on 2024-05-14 20:25:42 UTC"],
            ],
        ),
        # FAIL_O - 3 APICs, only apic2 has an expired manufacturing cert
        (
            {faultInst_pre_factory: []},
            False,
            ssh_cmds({
                "10.0.0.1": VERIFYAPIC_VALID,
                "10.0.0.2": VERIFYAPIC_EXPIRED,
                "10.0.0.3": VERIFYAPIC_VALID,
            }),
            "6.1(4a)",
            fabric_nodes_multi,
            script.FAIL_O,
            [
                ["N/A", "critical",
                 "APIC 2 (apic2): manufacturing certificate expired on 2024-05-14 20:25:42 UTC"],
            ],
        ),
    ],
)
def test_logic(run_check, mock_icurl, mock_conn, cversion, fabric_nodes, expected_result, expected_data):
    result = run_check(
        cversion=script.AciVersion(cversion) if cversion else None,
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert result.data == expected_data