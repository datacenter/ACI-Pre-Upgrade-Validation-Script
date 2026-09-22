import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

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
faultInst = fault_query(MASTER_ORDER)
faultInst_pre_factory = fault_query(["F4501", "F4502", "F4503", "F4617", "F3081", "F3082"])
faultInst_keyring_saml = fault_query(["F4501", "F4502", "F3081", "F3082"])
faultInst_saml = fault_query(["F3081", "F3082"])

# --- Factory certificate (F4752/F4753) SSH check test data ---
fabric_nodes_ssh = [
    {"fabricNode": {"attributes": {"id": "1", "name": "apic1", "role": "controller", "address": "10.0.0.1"}}},
]

fabric_nodes_multi = [
    {"fabricNode": {"attributes": {"id": "1", "name": "apic1", "role": "controller", "address": "10.0.0.1"}}},
    {"fabricNode": {"attributes": {"id": "2", "name": "apic2", "role": "controller", "address": "10.0.0.2"}}},
    {"fabricNode": {"attributes": {"id": "3", "name": "apic3", "role": "controller", "address": "10.0.0.3"}}},
]

DATE_OUTPUT = "1784097330\nfab-apic#"

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

VERIFYAPIC_EXACTLY_30_DAYS = """\
openssl_check: Manufacturing certificate details
issuer=CN=Cisco Manufacturing CA,O=Cisco Systems
notBefore=Jul  6 19:33:57 2019 GMT
notAfter=Aug 14 06:35:30 2026 GMT
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
            {
                "cmd": "date -u +%s; acidiag verifyapic",
                "output": "{}\n{}".format(DATE_OUTPUT, out),
                "exception": None
            },
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
        # FAIL_O - raised expiring certificate (F4501 - KeyRing)
        (
            {
                faultInst: read_data(dir, "faultInst_F4501.json")
            },
            False,
            {},
            "6.1(5e)",
            [],
            script.FAIL_O,
            [
                ["F4501", "KeyRing Certificate THD_KEYRING expiring"],
            ],
        ),
        # FAIL_O - raised expiring certificate (F3081 - SAML)
        (
            {
                faultInst: read_data(dir, "faultInst_F3081.json")
            },
            False,
            {},
            "6.1(5e)",
            [],
            script.FAIL_O,
            [
                ["F3081", "SAML Signing Certificate expiring in one month"],
            ],
        ),
        # FAIL_O - raised expiring certificate (F4617 - TP)
        (
            {
                faultInst: read_data(dir, "faultInst_F4617.json")
            },
            False,
            {},
            "6.1(5e)",
            [],
            script.FAIL_O,
            [
                ["F4617", "TP Certificate expiring"],
            ],
        ),
        # FAIL_O - raised expiring factory certificate (F4752 - Factory)
        (
            {
                faultInst: read_data(dir, "faultInst_F4752.json")
            },
            False,
            {},
            "6.1(5e)",
            [],
            script.FAIL_O,
            [
                ["F4752", "Factory certificate expiring"],
            ],
        ),
        # FAIL_O - multiple raised expiring certificates
        (
            {
                faultInst: read_data(dir, "faultInst_multiple_expiring.json")
            },
            False,
            {},
            "6.1(5e)",
            [],
            script.FAIL_O,
            [
                ["F4501", "KeyRing Certificate THD_KEYRING expiring"],
                ["F3081", "SAML Signing Certificate expiring in one month"],
                ["F4617", "TP Certificate expiring"],
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
                ["F4502", "KeyRing Certificate THD_KEYRING expired"],
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
                ["F4503", "TP Certificate THD_CA expired"],
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
                ["F3082", "SAML Encryption Certificate has expired"],
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
                ["F4753", "Factory certificate expired"],
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
                ["F4502", "KeyRing Certificate THD_KEYRING expired"],
                ["F4503", "TP Certificate THD_CA expired"],
                ["F3082", "SAML Encryption Certificate has expired"],
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
                ["F4501", "KeyRing Certificate KEYRING1 expiring"],
                ["F4502", "KeyRing Certificate THD_KEYRING expired"],
                ["F3081", "SAML Signing Certificate expiring in one month"],
                ["F3082", "SAML Encryption Certificate has expired"],
            ],
        ),
        # PASS - faults exist but are not in the raised state (cleared/retaining)
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
            ssh_cmds(VERIFYAPIC_VALID),
            "6.1(1e)",
            fabric_nodes_ssh,
            script.FAIL_O,
            [
                ["F4503", "TP Certificate THD_CA expired"],
            ],
        ),
        # 6.0(4c) <= cversion < 6.1(1e): KeyRing + SAML only. KeyRing expired.
        (
            {
                faultInst_keyring_saml: read_data(dir, "faultInst_F4502.json")
            },
            False,
            ssh_cmds(VERIFYAPIC_VALID),
            "6.0(4c)",
            fabric_nodes_ssh,
            script.FAIL_O,
            [
                ["F4502", "KeyRing Certificate THD_KEYRING expired"],
            ],
        ),
        # 3.1(2f) <= cversion < 6.0(4c): SAML only. Expired.
        (
            {
                faultInst_saml: read_data(dir, "faultInst_F3082.json")
            },
            False,
            ssh_cmds(VERIFYAPIC_VALID),
            "5.2(7g)",
            fabric_nodes_ssh,
            script.FAIL_O,
            [
                ["F3082", "SAML Encryption Certificate has expired"],
            ],
        ),
        # 3.1(2f) <= cversion < 6.0(4c): SAML only, none raised.
        (
            {faultInst_saml: []},
            False,
            ssh_cmds(VERIFYAPIC_VALID),
            "5.2(7g)",
            fabric_nodes_ssh,
            script.PASS,
            [],
        ),
        # ERROR - no applicable fault query and no controller inventory for the factory certificate check.
        (
            {},
            False,
            {},
            "2.3(1a)",
            [],
            script.ERROR,
            [[
                "N/A",
                "No APIC controllers were found; factory certificate expiry could not be verified.",
            ]],
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
                ["N/A",
                 "APIC 1 (apic1): factory certificate expired on 2024-05-14 20:25:42 UTC"],
            ],
        ),
        # FAIL_O - manufacturing certificate expiring within threshold (30 days)
        (
            {faultInst_pre_factory: []},
            False,
            ssh_cmds(VERIFYAPIC_EXPIRING),
            "6.1(4a)",
            fabric_nodes_ssh,
            script.FAIL_O,
            [
                ["N/A",
                 "APIC 1 (apic1): factory certificate expiring on 2026-08-01 06:57:40 UTC"],
            ],
        ),
        # FAIL_O - manufacturing certificate expiring exactly at the 30-day threshold
        (
            {faultInst_pre_factory: []},
            False,
            ssh_cmds(VERIFYAPIC_EXACTLY_30_DAYS),
            "6.1(4a)",
            fabric_nodes_ssh,
            script.FAIL_O,
            [
                ["N/A",
                 "APIC 1 (apic1): factory certificate expiring on 2026-08-14 06:35:30 UTC"],
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
                ["N/A",
                 "APIC 1 (apic1): unable to verify factory certificate - Simulated exception at connect()"],
            ],
        ),
        # ERROR - APIC output has no parseable current date
        (
            {
                faultInst_pre_factory: []
            },
            False,
            {
                "10.0.0.1": [
                    {
                        "cmd": "date -u +%s; acidiag verifyapic",
                        "output": "BADDATE\nnotAfter=May 14 20:25:42 2024 GMT\n",
                        "exception": None
                    },
                ]
            },
            "6.1(4a)",
            fabric_nodes_ssh,
            script.ERROR,
            [
                ["N/A",
                "APIC 1 (apic1): unable to determine current date"],
            ],
        ),

        # ERROR - APIC output missing parseable notAfter
        (
            {
                faultInst_pre_factory: []
            },
            False,
            {
                "10.0.0.1": [
                    {
                        "cmd": "date -u +%s; acidiag verifyapic",
                        "output": "{}\nopenssl_check: Manufacturing certificate details\n".format(DATE_OUTPUT),
                        "exception": None
                    },
                ]
            },
            "6.1(4a)",
            fabric_nodes_ssh,
            script.ERROR,
            [
                ["N/A",
                "APIC 1 (apic1): unable to determine factory certificate expiry date"],
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
                ["F4502", "KeyRing Certificate THD_KEYRING expired"],
                ["N/A",
                 "APIC 1 (apic1): factory certificate expired on 2024-05-14 20:25:42 UTC"],
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
                ["N/A",
                 "APIC 2 (apic2): factory certificate expired on 2024-05-14 20:25:42 UTC"],
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


@pytest.mark.parametrize(
    "icurl_outputs, expected_data",
    [
        (
            {
                faultInst: [{
                    "faultInst": {
                        "attributes": {
                            "code": "F4501",
                            "severity": "critical",
                            "descr": "KeyRing certificate approaching expiry",
                            "lc": "raised",
                        }
                    }
                }]
            },
            [["F4501", "KeyRing certificate approaching expiry"]],
        ),
        (
            {
                faultInst: [{
                    "faultInst": {
                        "attributes": {
                            "code": "F4502",
                            "severity": "major",
                            "descr": "KeyRing certificate expired",
                            "lc": "raised",
                        }
                    }
                }]
            },
            [["F4502", "KeyRing certificate expired"]],
        ),
        (
            {
                faultInst: [{
                    "faultInst": {
                        "attributes": {
                            "code": "F4502",
                            "descr": "KeyRing certificate expired without a severity field",
                            "lc": "raised",
                        }
                    }
                }]
            },
            [["F4502", "KeyRing certificate expired without a severity field"]],
        ),
    ],
)
def test_raised_fault_blocks_regardless_of_reported_severity(
    run_check, mock_icurl, expected_data
):
    result = run_check(
        cversion=script.AciVersion("6.1(5e)"),
        username=None,
        password=None,
        fabric_nodes=[],
    )

    assert result.result == script.FAIL_O
    assert result.headers == ["Fault Code", "Description"]
    assert result.data == expected_data
    assert "Resolve all certificate conditions" in result.recommended_action


@pytest.mark.parametrize(
    "icurl_outputs",
    [{
        faultInst: [{
            "faultInst": {
                "attributes": {
                    "code": "F4502",
                    "severity": "critical",
                    "descr": "KeyRing certificate expired",
                    "lc": "soaking",
                }
            }
        }]
    }],
)
def test_soaking_fault_is_not_upgrade_blocking(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("6.1(5e)"),
        username=None,
        password=None,
        fabric_nodes=[],
    )

    assert result.result == script.PASS
    assert result.data == []


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            faultInst: [{
                "faultInst": {
                    "attributes": {
                        "code": "F4502",
                        "severity": "critical",
                        "descr": "KeyRing certificate expired",
                        "lc": lifecycle,
                    }
                }
            }]
        }
        for lifecycle in ("raised,soaking", "soaking, raised")
    ],
)
def test_compound_raised_fault_is_upgrade_blocking(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("6.1(5e)"),
        username=None,
        password=None,
        fabric_nodes=[],
    )

    assert result.result == script.FAIL_O
    assert result.data == [["F4502", "KeyRing certificate expired"]]


@pytest.mark.parametrize("icurl_outputs", [{faultInst_pre_factory: []}])
def test_api_only_requires_manual_factory_certificate_verification(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("6.1(4a)"),
        username=None,
        password=None,
        fabric_nodes=[],
    )

    assert result.result == script.MANUAL
    assert result.data == [[
        "N/A",
        "Factory certificate expiry was not checked because SSH credentials are unavailable.",
    ]]
    assert result.doc_url in result.recommended_action
    assert "manual factory certificate verification procedure" in result.recommended_action


@pytest.mark.parametrize("icurl_outputs", [{faultInst_pre_factory: []}])
@pytest.mark.parametrize(
    "fabric_nodes",
    [
        [],
        [{"fabricNode": {"attributes": {"id": "101", "name": "leaf101", "role": "leaf"}}}],
    ],
)
def test_missing_controller_inventory_is_error(run_check, mock_icurl, fabric_nodes):
    result = run_check(
        cversion=script.AciVersion("6.1(4a)"),
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )

    assert result.result == script.ERROR
    assert result.data == [[
        "N/A",
        "No APIC controllers were found; factory certificate expiry could not be verified.",
    ]]
    assert "Verify APIC cluster and node inventory health" in result.recommended_action
    assert result.doc_url in result.recommended_action


@pytest.mark.parametrize(
    "icurl_outputs",
    [{faultInst_pre_factory: read_data(dir, "faultInst_F4502.json")}],
)
@pytest.mark.parametrize("conn_failure", [True])
def test_raised_api_fault_takes_precedence_over_ssh_error(run_check, mock_icurl, mock_conn):
    result = run_check(
        cversion=script.AciVersion("6.1(4a)"),
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes_ssh,
    )

    assert result.result == script.FAIL_O
    assert result.data == [
        ["F4502", "KeyRing Certificate THD_KEYRING expired"],
        [
            "N/A",
            "APIC 1 (apic1): unable to verify factory certificate - Simulated exception at connect()",
        ],
    ]
    assert "Resolve all certificate conditions" in result.recommended_action
    assert "could not be verified on all APICs" in result.recommended_action
    assert result.doc_url in result.recommended_action


@pytest.mark.parametrize("icurl_outputs", [{faultInst_pre_factory: []}])
@pytest.mark.parametrize(
    "conn_cmds",
    [{
        "10.0.0.1": [{
            "cmd": "date -u +%s; acidiag verifyapic",
            "output": "{}\n{}".format(DATE_OUTPUT, VERIFYAPIC_EXPIRED),
            "exception": None,
        }],
        "10.0.0.2": [{
            "cmd": "date -u +%s; acidiag verifyapic",
            "output": "",
            "exception": RuntimeError("Simulated command failure"),
        }],
    }],
)
def test_expired_factory_certificate_takes_precedence_over_other_apic_error(
    run_check, mock_icurl, mock_conn
):
    result = run_check(
        cversion=script.AciVersion("6.1(4a)"),
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes_multi[:2],
    )

    assert result.result == script.FAIL_O
    assert result.data == [
        [
            "N/A",
            "APIC 1 (apic1): factory certificate expired on 2024-05-14 20:25:42 UTC",
        ],
        [
            "N/A",
            "APIC 2 (apic2): unable to verify factory certificate - Simulated command failure",
        ],
    ]
    assert "Resolve all certificate conditions" in result.recommended_action
    assert "could not be verified on all APICs" in result.recommended_action
    assert result.doc_url in result.recommended_action


@pytest.mark.parametrize(
    "icurl_outputs",
    [{faultInst_pre_factory: read_data(dir, "faultInst_F4502.json")}],
)
def test_raised_fault_takes_precedence_over_missing_controller_inventory(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("6.1(4a)"),
        username="fake_username",
        password="fake_password",
        fabric_nodes=[],
    )

    assert result.result == script.FAIL_O
    assert result.data == [
        ["F4502", "KeyRing Certificate THD_KEYRING expired"],
        [
            "N/A",
            "No APIC controllers were found; factory certificate expiry could not be verified.",
        ],
    ]
    assert "Resolve all certificate conditions" in result.recommended_action
    assert "Verify APIC cluster and node inventory health" in result.recommended_action
    assert result.doc_url in result.recommended_action


@pytest.mark.parametrize(
    "icurl_outputs",
    [{faultInst_pre_factory: read_data(dir, "faultInst_F4501.json")}],
)
@pytest.mark.parametrize("conn_failure", [True])
def test_raised_expiring_fault_takes_precedence_over_ssh_error(run_check, mock_icurl, mock_conn):
    result = run_check(
        cversion=script.AciVersion("6.1(4a)"),
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes_ssh,
    )

    assert result.result == script.FAIL_O
    assert result.data == [
        ["F4501", "KeyRing Certificate THD_KEYRING expiring"],
        [
            "N/A",
            "APIC 1 (apic1): unable to verify factory certificate - Simulated exception at connect()",
        ],
    ]


@pytest.mark.parametrize(
    "icurl_outputs",
    [{faultInst_pre_factory: read_data(dir, "faultInst_F4502.json")}],
)
def test_api_only_preserves_expired_certificate_failure(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("6.1(4a)"),
        username=None,
        password=None,
        fabric_nodes=fabric_nodes_ssh,
    )

    assert result.result == script.FAIL_O
    assert result.data == [
        ["F4502", "KeyRing Certificate THD_KEYRING expired"],
        [
            "N/A",
            "Factory certificate expiry was not checked because SSH credentials are unavailable.",
        ],
    ]
    assert result.doc_url in result.recommended_action


@pytest.mark.parametrize("icurl_outputs", [{faultInst: []}])
def test_api_only_does_not_require_ssh_on_newer_releases(run_check, mock_icurl):
    result = run_check(
        cversion=script.AciVersion("6.1(5e)"),
        username=None,
        password=None,
        fabric_nodes=[],
    )

    assert result.result == script.PASS
    assert result.data == []
    assert result.recommended_action == ""
