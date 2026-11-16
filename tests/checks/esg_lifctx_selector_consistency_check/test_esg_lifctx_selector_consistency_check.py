import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "esg_lifctx_selector_consistency_check"

# icurl queries
fvLIfCtxSelector = "fvLIfCtxSelector.json"
vnsRsLIfCtxToBD = "vnsRsLIfCtxToBD.json"
vnsRsLIfCtxToLIf = "vnsRsLIfCtxToLIf.json"

# Test data
#
# Terms: a Service EPG is a vnsLIfCtx (connector) of a device selection policy (vnsLDevCtx).
# Each fixture holds only the relations the check reads: Service EPG -> BD (vnsRsLIfCtxToBD) and
# Service EPG -> device interface (vnsRsLIfCtxToLIf), and ESG -> Service EPG (fvLIfCtxSelector).
#
# Base topology (vnsRsLIfCtxToBD.json, vnsRsLIfCtxToLIf.json), tenant coke:
#   Device selection policy                 Service EPG  BD        Device interface
#   ldevCtx-c-webCtrct-g-WebGraph-n-FW      consumer     FWExtBD   lDevVip-FW/lIf-external
#                                           provider     FWIntBD   lDevVip-FW/lIf-internal
#   ldevCtx-c-webCtrct_e2-g-WebGraph-n-FW   same as webCtrct
#   ldevCtx-c-webCtrct_e3-g-WebGraph-n-FW   same as webCtrct
#   ldevCtx-c-lbCtrct-g-LBGraph-n-LB        consumer     FWExtBD   lDevVip-LB/lIf-external
#                                           provider     LBIntBD   lDevVip-LB/lIf-internal
#   Service EPGs sharing a device and BD (they must have the same ESG):
#     FW + FWExtBD: the three webCtrct* consumers
#     FW + FWIntBD: the three webCtrct* providers
#     LB + FWExtBD: lbCtrct consumer (same BD as the FW consumers, but a different device)
#     LB + LBIntBD: lbCtrct provider
#
# Topology variants (used instead of the base files where a test case says so):
#   vnsRsLIfCtxToLIf_ldevif.json       base, but every device interface is on an imported device
#                                      (uni/tn-coke/lDevIf-[uni/tn-prov/lDevVip-FW]/lDevIfLIf-*)
#   vnsRsLIfCtxToBD_mixed.json,        base + ldevCtx-c-l3Ctrct-g-L3Graph-n-FW with
#   vnsRsLIfCtxToLIf_mixed.json          consumer: no BD (like an L3Out connector), lDevVip-FW/lIf-external
#                                        provider: BD FWExtBD, lDevVip-FW/lIf-external
#                                      so the l3Ctrct provider joins the FW + FWExtBD group of the webCtrct* consumers
#   vnsRsLIfCtxToBD_shared.json,       tenant tnA only: ldevCtx-c-sharedCtrct1-g-WebGraph-n-FW and
#   vnsRsLIfCtxToLIf_shared.json       ldevCtx-c-sharedCtrct2-g-WebGraph-n-FW, both using the tn-common device
#                                      lDevVip-SharedFW with tn-common BDs SharedExtBD (consumer) and
#                                      SharedIntBD (provider)
#   vnsRsLIfCtxToBD_unexpected.json,   base + uni/tn-coke/ldevCtx-unexpected, a DN that is not in the
#   vnsRsLIfCtxToLIf_unexpected.json   ldevCtx-c-<contract>-g-<graph>-n-<node> format, with a consumer on
#                                      FW + FWExtBD and a provider on FW + FWIntBD
#
# ESG Service EPG selectors (fvLIfCtxSelector_*.json), which ESG selects which Service EPG.
# APIC rejects a second ESG selecting the same Service EPG, and an ESG selecting a Service EPG
# without a BD, so the test data has neither.
#   _one             svc  selects webCtrct consumer
#   _all_same        svc  selects webCtrct, webCtrct_e2 and webCtrct_e3 consumers
#   _different       svc  selects webCtrct and webCtrct_e2 consumers; svc2 selects webCtrct_e3 consumer
#   _lb_only         svc  selects lbCtrct consumer
#   _provider_only   svc  selects webCtrct provider
#   _mixed           svc  selects l3Ctrct provider (on FW + FWExtBD; l3Ctrct's consumer has no BD,
#                         from the _mixed variant)
#   _shared          svcA (tenant tnA) selects sharedCtrct1 consumer

def outputs(selectors, to_bd="vnsRsLIfCtxToBD.json", to_lif="vnsRsLIfCtxToLIf.json"):
    """Mocked responses for the three class queries; selectors=None means no ESG selector."""
    return {
        fvLIfCtxSelector: read_data(dir, selectors) if selectors else [],
        vnsRsLIfCtxToBD: read_data(dir, to_bd),
        vnsRsLIfCtxToLIf: read_data(dir, to_lif),
    }


def rows(esgs):
    """Expected rows for the webCtrct, webCtrct_e2 and webCtrct_e3 consumers, in that order.

    Each item in esgs is (ESG of that consumer, other ESGs on FW + FWExtBD); "-" means no ESG.
    """
    return [
        ["coke", contract, "WebGraph", "FW", "consumer", "FW", "coke:FWExtBD", esg, others]
        for contract, (esg, others) in zip(["webCtrct", "webCtrct_e2", "webCtrct_e3"], esgs)
    ]


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result, expected_data, expected_unformatted_data",
    [
        # No target version given -> MANUAL
        # Expected rows: none
        (
            outputs("fvLIfCtxSelector_one.json"),
            "6.1(2f)",
            None,
            script.MANUAL,
            [],
            [],
        ),
        # Current version 5.2(3g): the ESG Service EPG selector does not exist before 5.2(4) -> N/A
        # Expected rows: none
        (
            outputs("fvLIfCtxSelector_one.json"),
            "5.2(3g)",
            "6.3(1a)",
            script.NA,
            [],
            [],
        ),
        # Target version 6.2(3g): consumer-side Service EPGs are validated only from 6.3(1) (CSCwv51642),
        # so the target raises no new fault -> N/A
        # Expected rows: none
        (
            outputs("fvLIfCtxSelector_one.json"),
            "6.1(2f)",
            "6.2(3g)",
            script.NA,
            [],
            [],
        ),
        # Current version already 6.3(1), selectors as in _one: an affected graph stays applied until it is
        # re-rendered, and the upgrade can trigger the re-render -> still checked, FAIL_O
        # Expected rows (data):
        #   Tenant | Contract    | Service Graph | Node | Connector | Device | Bridge Domain | ESG | Other ESGs
        #   -------+-------------+---------------+------+-----------+--------+---------------+-----+-----------
        #   coke   | webCtrct    | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | svc | -
        #   coke   | webCtrct_e2 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        #   coke   | webCtrct_e3 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        (
            outputs("fvLIfCtxSelector_one.json"),
            "6.3(1a)",
            "6.3(2a)",
            script.FAIL_O,
            rows([("svc", "-"), ("-", "svc"), ("-", "svc")]),
            [],
        ),
        # No ESG selects any Service EPG -> PASS
        # Expected rows: none
        (
            outputs(None),
            "5.2(8h)",
            "6.3(1a)",
            script.PASS,
            [],
            [],
        ),
        # svc selects all three webCtrct* consumers on FW + FWExtBD: same ESG everywhere -> PASS
        # Expected rows: none
        (
            outputs("fvLIfCtxSelector_all_same.json"),
            "6.0(5h)",
            "6.3(1a)",
            script.PASS,
            [],
            [],
        ),
        # svc selects only the webCtrct consumer. On FW + FWExtBD, webCtrct has svc and the other two have no
        # ESG, so every webCtrct* consumer differs from another one -> FAIL_O, one row per graph
        # Expected rows (data):
        #   Tenant | Contract    | Service Graph | Node | Connector | Device | Bridge Domain | ESG | Other ESGs
        #   -------+-------------+---------------+------+-----------+--------+---------------+-----+-----------
        #   coke   | webCtrct    | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | svc | -
        #   coke   | webCtrct_e2 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        #   coke   | webCtrct_e3 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        (
            outputs("fvLIfCtxSelector_one.json"),
            "6.0(5h)",
            "6.3(1a)",
            script.FAIL_O,
            rows([("svc", "-"), ("-", "svc"), ("-", "svc")]),
            [],
        ),
        # The webCtrct* consumers on FW + FWExtBD have ESGs svc, svc and svc2 -> FAIL_O, one row per graph
        # Expected rows (data):
        #   Tenant | Contract    | Service Graph | Node | Connector | Device | Bridge Domain | ESG  | Other ESGs
        #   -------+-------------+---------------+------+-----------+--------+---------------+------+-----------
        #   coke   | webCtrct    | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | svc  | svc2
        #   coke   | webCtrct_e2 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | svc  | svc2
        #   coke   | webCtrct_e3 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | svc2 | svc
        (
            outputs("fvLIfCtxSelector_different.json"),
            "6.1(2f)",
            "6.3(1b)",
            script.FAIL_O,
            rows([("svc", "svc2"), ("svc", "svc2"), ("svc2", "svc")]),
            [],
        ),
        # svc selects the lbCtrct consumer, which is on FWExtBD like the webCtrct* consumers but uses device LB.
        # Service EPGs are compared only on the same device and BD, and lbCtrct's consumer is alone on
        # LB + FWExtBD -> PASS
        # Expected rows: none
        (
            outputs("fvLIfCtxSelector_lb_only.json"),
            "6.1(2f)",
            "6.3(1b)",
            script.PASS,
            [],
            [],
        ),
        # Same selector as _one, but every Service EPG uses an imported device (vnsLDevIf). APIC compares only
        # Service EPGs on a vnsLDevVip, so nothing is validated -> PASS
        # Expected rows: none
        (
            outputs("fvLIfCtxSelector_one.json", to_lif="vnsRsLIfCtxToLIf_ldevif.json"),
            "6.1(2f)",
            "6.3(1b)",
            script.PASS,
            [],
            [],
        ),
        # Two graphs in tenant tnA use the tn-common device SharedFW and BD SharedExtBD (one vnsREPpInfo).
        # svcA selects only the sharedCtrct1 consumer, so the two consumers differ -> FAIL_O, one row per graph
        # Expected rows (data):
        #   Tenant | Contract     | Service Graph | Node | Connector | Device   | Bridge Domain      | ESG  | Other ESGs
        #   -------+--------------+---------------+------+-----------+----------+--------------------+------+-----------
        #   tnA    | sharedCtrct1 | WebGraph      | FW   | consumer  | SharedFW | common:SharedExtBD | svcA | -
        #   tnA    | sharedCtrct2 | WebGraph      | FW   | consumer  | SharedFW | common:SharedExtBD | -    | svcA
        (
            outputs("fvLIfCtxSelector_shared.json", "vnsRsLIfCtxToBD_shared.json", "vnsRsLIfCtxToLIf_shared.json"),
            "6.1(2f)",
            "6.3(1b)",
            script.FAIL_O,
            [
                ["tnA", "sharedCtrct1", "WebGraph", "FW", "consumer", "SharedFW", "common:SharedExtBD", "svcA", "-"],
                ["tnA", "sharedCtrct2", "WebGraph", "FW", "consumer", "SharedFW", "common:SharedExtBD", "-", "svcA"],
            ],
            [],
        ),
        # svc selects only the webCtrct provider (FW + FWIntBD). Providers are validated before 6.3(1) too,
        # so this is not a new fault after the upgrade -> PASS
        # Expected rows: none
        (
            outputs("fvLIfCtxSelector_provider_only.json"),
            "6.1(2f)",
            "6.3(1b)",
            script.PASS,
            [],
            [],
        ),
        # svc selects the l3Ctrct provider, which is on FW + FWExtBD next to the three webCtrct* consumers
        # (no ESG). l3Ctrct itself is not validated because its consumer has no BD, but each webCtrct*
        # consumer now differs from the l3Ctrct provider -> FAIL_O for the three webCtrct* graphs only
        # Expected rows (data):
        #   Tenant | Contract    | Service Graph | Node | Connector | Device | Bridge Domain | ESG | Other ESGs
        #   -------+-------------+---------------+------+-----------+--------+---------------+-----+-----------
        #   coke   | webCtrct    | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        #   coke   | webCtrct_e2 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        #   coke   | webCtrct_e3 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        (
            outputs("fvLIfCtxSelector_mixed.json", "vnsRsLIfCtxToBD_mixed.json", "vnsRsLIfCtxToLIf_mixed.json"),
            "6.1(2f)",
            "6.3(1b)",
            script.FAIL_O,
            rows([("-", "svc"), ("-", "svc"), ("-", "svc")]),
            [],
        ),
        # Same selector as _one, plus ldevCtx-unexpected on FW + FWExtBD whose DN cannot be split into
        # contract/graph/node -> FAIL_O; the three webCtrct* graphs in data, the unexpected Service EPG DN in
        # unformatted_data
        # Expected rows (data):
        #   Tenant | Contract    | Service Graph | Node | Connector | Device | Bridge Domain | ESG | Other ESGs
        #   -------+-------------+---------------+------+-----------+--------+---------------+-----+-----------
        #   coke   | webCtrct    | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | svc | -
        #   coke   | webCtrct_e2 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        #   coke   | webCtrct_e3 | WebGraph      | FW   | consumer  | FW     | coke:FWExtBD  | -   | svc
        # Expected unparsed rows (unformatted_data):
        #   DN of vnsLIfCtx                                   | Device | Bridge Domain | ESG | Other ESGs
        #   uni/tn-coke/ldevCtx-unexpected/lIfCtx-c-consumer | FW     | coke:FWExtBD  | -   | svc
        (
            outputs("fvLIfCtxSelector_one.json", "vnsRsLIfCtxToBD_unexpected.json", "vnsRsLIfCtxToLIf_unexpected.json"),
            "6.1(2f)",
            "6.3(1b)",
            script.FAIL_O,
            rows([("svc", "-"), ("-", "svc"), ("-", "svc")]),
            [["uni/tn-coke/ldevCtx-unexpected/lIfCtx-c-consumer", "FW", "coke:FWExtBD", "-", "svc"]],
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result, expected_data, expected_unformatted_data):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,
    )
    assert result.result == expected_result
    assert result.data == expected_data
    assert result.unformatted_data == expected_unformatted_data
