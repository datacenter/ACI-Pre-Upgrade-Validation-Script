import importlib

import pytest

script = importlib.import_module("aci-preupgrade-validation-script")

test_function = "cimc_cscwe61589_check"
eqptCh_api = 'eqptCh.json?query-target-filter=wcard(eqptCh.descr,"APIC")'
CMD = "acidiag show cimc"


def fabric_node(node_id, ip):
    return {"fabricNode": {"attributes": {
        "id": node_id, "name": "apic" + node_id, "address": ip, "role": "controller",
        "dn": "topology/pod-1/node-" + node_id,
    }}}


def eqpt_ch(node_id, model="L3", cimc="4.3(2.250016)", serial="WZP00000001"):
    return {"eqptCh": {"attributes": {
        "descr": "APIC-SERVER-" + model, "cimcVersion": cimc, "ser": serial,
        "dn": "topology/pod-1/node-{}/sys/ch".format(node_id),
    }}}


def acidiag_output(pid="APIC-SERVER-L3", serial="WZP00000001", product=None):
    return "\n".join([
        CMD,
        "==================== CIMC DETAILS ====================",
        "PID : " + pid,
        "Serial Number : " + serial,
        "Product Name : " + (product if product is not None else pid),
        "BIOS Version : C220M5.4.2.2b.0.0613220203",
        "CIMC Version : 4.3(2.250016)",
        "==================== END of CIMC DETAILS!! ====================",
        "apic1#",
    ])


# Real output of `acidiag show cimc` on APIC 6.0(3d), where the command does not exist (choices shortened).
UNSUPPORTED_OUTPUT = "\n".join([
    CMD,
    "usage: acidiag [-h] [-v]",
    "               {avread,fnvread,version,platform,hwcheck,verifyapic,reboot,dmecore} ...",
    "acidiag: error: argument : invalid choice: 'show' (choose from 'avread', 'fnvread', "
    "'version', 'platform', 'hwcheck', 'verifyapic', 'reboot', 'dmecore')",
    "apic1#",
])


BAD_IDENTITY_OUTPUT = acidiag_output(serial="UCSC-C220-M5", product="UCSC-C220-M5")


def conn_output(ip, output=None, exception=None):
    return {ip: [{"cmd": CMD, "output": output, "exception": exception}]}


@pytest.mark.parametrize("version, expected", [
    ("3.0(4d)", False),
    ("4.0(2g)", True),
    ("4.1(3m)", True),
    ("4.2(2a)", True),
    ("4.2(3b)", True),
    ("4.2(3e)", True),
    ("4.2(3g)", False),
    ("4.2(3h)", False),
    ("4.3(1.220001)", True),
    ("4.3(2.220001)", True),
    ("4.3(2.230206)", True),
    ("4.3(2.230207)", False),
    ("4.3(2.250016)", False),
    ("4.3(4.241063)", False),
    ("6.0(1.250126)", True),
    ("6.0(1.250127)", False),
    ("6.0(2.260044)", False),
    ("", None),
    (None, None),
    ("garbage", None),
])
def test_is_affected(version, expected):
    assert script.cimc_cscwe61589_is_affected(version) is expected


@pytest.mark.parametrize("kwargs, definitive_count, review_count", [
    ({}, 0, 0),
    ({"product": "UCSC-C220-M5", "serial": "UCSC-C220-M5"}, 3, 0),
    ({"serial": "123456789"}, 1, 0),
    ({"product": "UCSC-C220-M5"}, 2, 0),
    ({"pid": "APIC-SERVER-L3", "product": "APIC-SERVER-M3"}, 1, 0),
])
def test_identity_findings(kwargs, definitive_count, review_count):
    fields = script.parse_acidiag_show_cimc(acidiag_output(**kwargs))
    definitive, review = script.cimc_cscwe61589_identity_findings(fields, "WZP00000001")
    assert (len(definitive), len(review)) == (definitive_count, review_count)


def test_identity_findings_empty_and_serial_mismatch():
    definitive, review = script.cimc_cscwe61589_identity_findings({}, None)
    assert len(definitive) == 3
    fields = script.parse_acidiag_show_cimc(acidiag_output(serial="WZP00000002"))
    definitive, review = script.cimc_cscwe61589_identity_findings(fields, "WZP00000001")
    assert definitive == []
    assert len(review) == 1


IP1 = "10.0.0.1"
NODES = [fabric_node("1", IP1)]


@pytest.mark.parametrize(
    "icurl_outputs, conn_failure, conn_cmds, fabric_nodes, expected_result, expected_nodes",
    [
        # Fixed CIMC, healthy identity
        (
            {eqptCh_api: [eqpt_ch("1")]}, False, conn_output(IP1, acidiag_output()), NODES,
            script.PASS, [],
        ),
        # Affected CIMC on APIC M3/L3, healthy identity -> MANUAL
        (
            {eqptCh_api: [eqpt_ch("1", cimc="4.2(3b)")]}, False, conn_output(IP1, acidiag_output()), NODES,
            script.MANUAL, ["1"],
        ),
        # APIC M4/L4 (UCS C225 M6) can be affected too
        (
            {eqptCh_api: [eqpt_ch("1", model="M4", cimc="4.2(3b)")]}, False,
            conn_output(IP1, acidiag_output(pid="APIC-SERVER-M4")), NODES,
            script.MANUAL, ["1"],
        ),
        # Affected CIMC and `acidiag show cimc` not supported -> MANUAL (CIMC version only)
        (
            {eqptCh_api: [eqpt_ch("1", cimc="4.2(3b)")]}, False, conn_output(IP1, UNSUPPORTED_OUTPUT), NODES,
            script.MANUAL, ["1"],
        ),
        # Fixed CIMC on APIC M4/L4
        (
            {eqptCh_api: [eqpt_ch("1", model="L4", cimc="4.3(4.241063)")]}, False,
            conn_output(IP1, acidiag_output(pid="APIC-SERVER-L4")), NODES,
            script.PASS, [],
        ),
        # Old CIMC on APIC M2/L2 (UCS M4) is out of scope for the version check
        (
            {eqptCh_api: [eqpt_ch("1", model="M2", cimc="4.1(2m)")]}, False,
            conn_output(IP1, acidiag_output(pid="APIC-SERVER-M2")), NODES,
            script.PASS, [],
        ),
        # CIMC version unparseable on M3/L3
        (
            {eqptCh_api: [eqpt_ch("1", cimc="")]}, False, conn_output(IP1, acidiag_output()), NODES,
            script.MANUAL, ["1"],
        ),
        # Bad identity and affected CIMC -> FAIL_UF (the CSCwe61589 condition)
        (
            {eqptCh_api: [eqpt_ch("1", cimc="4.2(3b)")]}, False, conn_output(IP1, BAD_IDENTITY_OUTPUT), NODES,
            script.FAIL_UF, ["1"],
        ),
        # Bad identity with a CIMC that is not affected -> MANUAL (not attributed to CSCwe61589)
        (
            {eqptCh_api: [eqpt_ch("1")]}, False, conn_output(IP1, BAD_IDENTITY_OUTPUT), NODES,
            script.MANUAL, ["1"],
        ),
        # Bad identity on APIC M2/L2 where the CIMC version is not evaluated -> MANUAL
        (
            {eqptCh_api: [eqpt_ch("1", model="M2", cimc="4.1(2m)")]}, False,
            conn_output(IP1, BAD_IDENTITY_OUTPUT), NODES,
            script.MANUAL, ["1"],
        ),
        # Valid-looking serial that differs from inventory -> MANUAL only
        (
            {eqptCh_api: [eqpt_ch("1")]}, False, conn_output(IP1, acidiag_output(serial="WZP00000002")), NODES,
            script.MANUAL, ["1"],
        ),
        # `acidiag show cimc` not supported (older release) -> PASS with message
        (
            {eqptCh_api: [eqpt_ch("1")]}, False,
            conn_output(IP1, UNSUPPORTED_OUTPUT), NODES,
            script.PASS, [],
        ),
        # `acidiag show cimc` output unexpected -> cannot verify
        (
            {eqptCh_api: [eqpt_ch("1")]}, False, conn_output(IP1, CMD + "\nCIMC query failed\napic1#"), NODES,
            script.MANUAL, ["1"],
        ),
        # Command raised an exception
        (
            {eqptCh_api: [eqpt_ch("1")]}, False, conn_output(IP1, "", Exception("Simulated exception")), NODES,
            script.MANUAL, ["1"],
        ),
        # Connection failure
        (
            {eqptCh_api: [eqpt_ch("1")]}, True, {}, NODES,
            script.MANUAL, ["1"],
        ),
    ],
)
def test_logic(run_check, mock_icurl, mock_conn, fabric_nodes, expected_result, expected_nodes):
    result = run_check(
        cversion=script.AciVersion("6.1(6g)"),
        username="fake_username",
        password="fake_password",
        fabric_nodes=fabric_nodes,
    )
    assert result.result == expected_result
    assert [row[0] for row in result.data] == expected_nodes


@pytest.mark.parametrize("icurl_outputs, conn_failure, conn_cmds", [({eqptCh_api: []}, False, {})])
def test_no_apic(run_check, mock_icurl, mock_conn):
    result = run_check(
        cversion=script.AciVersion("6.1(6g)"), username="u", password="p", fabric_nodes=[],
    )
    assert result.result == script.ERROR


@pytest.mark.parametrize("icurl_outputs, conn_failure, conn_cmds", [
    ({eqptCh_api: [eqpt_ch("1", cimc="4.2(3b)")]}, False, conn_output(IP1, acidiag_output())),
])
def test_serialized_result(run_check, mock_icurl, mock_conn):
    result = run_check(
        cversion=script.AciVersion("6.1(6g)"), username="u", password="p", fabric_nodes=NODES,
    )
    aci_result = script.AciResult(test_function, "CIMC IPMI Stall and APIC Identity (CSCwe61589)", result)
    assert aci_result.ruleStatus == script.AciResult.FAIL
    assert aci_result.failureDetails["failType"] == script.MANUAL
    assert aci_result.failureDetails["data"][0]["Node ID"] == "1"
