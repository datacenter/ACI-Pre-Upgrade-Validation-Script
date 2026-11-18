import importlib
import os
from helpers.utils import read_data
import pytest

script = importlib.import_module("aci-preupgrade-validation-script")
dir = os.path.dirname(os.path.abspath(__file__))
test_function = "span_destination_epg_conflict_check"

src_grp_api = 'spanSrcGrp.json?query-target-filter=eq(spanSrcGrp.adminSt,"enabled")'
label_api = 'spanSpanLbl.json'
dest_api = 'spanRsDestPathEp.json'
phys_api = 'topology/pod-1/node-101/sys/phys-[eth1/10].json'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result, expected_count",
    [
        (
            read_data(dir, "baseline.json"),
            None,
            script.MANUAL,
            0,
        ),
        (
            read_data(dir, "baseline.json"),
            "5.2(8i)",
            script.NA,
            0,
        ),
        (
            read_data(dir, "baseline.json"),
            "6.0(9e)",
            script.NA,
            0,
        ),
        (
            read_data(dir, "baseline.json"),
            "6.1(2g)",
            script.NA,
            0,
        ),
        (
            read_data(dir, "baseline.json"),
            "6.1(3a)",
            script.FAIL_O,
            1,
        ),
        (
            read_data(dir, "baseline.json"),
            "6.1(3f)",
            script.FAIL_O,
            1,
        ),
        (
            read_data(dir, "baseline.json"),
            "6.1(5e)",
            script.FAIL_O,
            1,
        ),
        (
            read_data(dir, "baseline.json"),
            "6.2(3g)",
            script.FAIL_O,
            1,
        ),
        (
            read_data(dir, "baseline.json"),
            "16.1(2g)",
            script.NA,
            0,
        ),
        (
            read_data(dir, "baseline.json"),
            "16.1(3f)",
            script.FAIL_O,
            1,
        ),
    ],
)
def test_version_gate(run_check, mock_icurl, tversion, expected_result, expected_count):
    result = run_check(tversion=script.AciVersion(tversion) if tversion else None)
    assert result.result == expected_result
    assert len(result.data) == expected_count


@pytest.mark.parametrize(
    "icurl_outputs, usage, span_mode, expected_result, expected_data",
    [
        (
            read_data(dir, "baseline.json"),
            "epg,span",
            "span-dest",
            script.FAIL_O,
            [["1", "101", "eth1/10", "Destination1", "span-dest", "epg,span"]],
        ),
        (
            read_data(dir, "baseline.json"),
            "epg",
            "not-a-span-dest",
            script.FAIL_O,
            [["1", "101", "eth1/10", "Destination1", "not-a-span-dest", "epg"]],
        ),
        (
            read_data(dir, "baseline.json"),
            "controller,epg,infra",
            "not-a-span-dest",
            script.FAIL_O,
            [["1", "101", "eth1/10", "Destination1", "not-a-span-dest", "controller,epg,infra"]],
        ),
        (
            read_data(dir, "baseline.json"),
            "span, epg ",
            "span-dest",
            script.FAIL_O,
            [["1", "101", "eth1/10", "Destination1", "span-dest", "span, epg "]],
        ),
        (
            read_data(dir, "baseline.json"),
            "span",
            "span-dest",
            script.PASS,
            [],
        ),
        (
            read_data(dir, "baseline.json"),
            "",
            "not-a-span-dest",
            script.PASS,
            [],
        ),
        (
            read_data(dir, "baseline.json"),
            "epgOther,span",
            "span-dest",
            script.PASS,
            [],
        ),
        (
            read_data(dir, "baseline.json"),
            "infra",
            "not-a-span-dest",
            script.PASS,
            [],
        ),
    ],
)
def test_usage(run_check, mock_icurl, icurl_outputs, usage, span_mode, expected_result, expected_data):
    icurl_outputs[phys_api][0]['l1PhysIf']['attributes'] = {'usage': usage, 'spanMode': span_mode}
    result = run_check(tversion=script.AciVersion("6.1(3f)"))
    assert result.result == expected_result
    assert result.data == expected_data


@pytest.mark.parametrize(
    "icurl_outputs, query",
    [
        (
            read_data(dir, "baseline.json"),
            src_grp_api,
        ),
        (
            read_data(dir, "baseline.json"),
            label_api,
        ),
        (
            read_data(dir, "baseline.json"),
            dest_api,
        ),
        (
            read_data(dir, "baseline.json"),
            phys_api,
        ),
    ],
)
def test_missing_objects(run_check, mock_icurl, icurl_outputs, query):
    icurl_outputs[query] = []
    result = run_check(tversion=script.AciVersion("6.1(3f)"))
    assert result.result == script.PASS
    assert result.data == []


@pytest.mark.parametrize(
    "icurl_outputs, source_dn, label_dn, label_name, dest_dn",
    [
        (
            read_data(dir, "baseline.json"),
            "uni/infra/srcgrp-Unmatched1",
            "uni/infra/srcgrp-Source1/spanlbl-Destination1",
            "Destination1",
            "uni/infra/destgrp-Destination1/dest-Destination1/rsdestPathEp",
        ),
        (
            read_data(dir, "baseline.json"),
            "uni/fabric/srcgrp-Source1",
            "uni/fabric/srcgrp-Source1/spanlbl-Destination1",
            "Destination1",
            "uni/infra/destgrp-Destination1/dest-Destination1/rsdestPathEp",
        ),
        (
            read_data(dir, "baseline.json"),
            "uni/infra/srcgrp-Source1",
            "uni/infra/srcgrp-Source1/spanlbl-Other",
            "Other",
            "uni/infra/destgrp-Destination1/dest-Destination1/rsdestPathEp",
        ),
        (
            read_data(dir, "baseline.json"),
            "uni/infra/srcgrp-Source1",
            "uni/infra/srcgrp-Source1/spanlbl-Destination1",
            "Destination1",
            "uni/fabric/destgrp-Destination1/dest-Destination1/rsdestPathEp",
        ),
        (
            read_data(dir, "baseline.json"),
            "uni/infra/srcgrp-Source1",
            "uni/infra/srcgrp-Source10/spanlbl-Destination1",
            "Destination1",
            "uni/infra/destgrp-Destination1/dest-Destination1/rsdestPathEp",
        ),
        (
            read_data(dir, "baseline.json"),
            "uni/tn-Tenant1/srcgrp-Source1",
            "uni/tn-Tenant1/srcgrp-Source1/spanlbl-Destination1",
            "Destination1",
            "uni/infra/destgrp-Destination1/dest-Destination1/rsdestPathEp",
        ),
        (
            read_data(dir, "baseline.json"),
            "uni/infra/srcgrp-Source1",
            "uni/infra/srcgrp-Source1/spanlbl-Destination1",
            "Destination1",
            "uni/tn-Tenant1/destgrp-Destination1/dest-Destination1/rsdestPathEp",
        ),
    ],
)
def test_access_session_scope(run_check, mock_icurl, icurl_outputs, source_dn, label_dn, label_name, dest_dn):
    icurl_outputs[src_grp_api][0]['spanSrcGrp']['attributes']['dn'] = source_dn
    icurl_outputs[label_api][0]['spanSpanLbl']['attributes'] = {'dn': label_dn, 'name': label_name}
    icurl_outputs[dest_api][0]['spanRsDestPathEp']['attributes']['dn'] = dest_dn
    result = run_check(tversion=script.AciVersion("6.1(3f)"))
    assert result.result == script.PASS
    assert result.data == []


@pytest.mark.parametrize(
    "icurl_outputs, path, expected_result, expected_ports",
    [
        (
            read_data(dir, "baseline.json"),
            "topology/pod-1/paths-101/pathep-[eth1/10]",
            script.FAIL_O,
            [["1", "101", "eth1/10"]],
        ),
        (
            read_data(dir, "baseline.json"),
            "topology/pod-2/paths-201/pathep-[eth1/10/2]",
            script.FAIL_O,
            [["2", "201", "eth1/10/2"]],
        ),
        (
            read_data(dir, "baseline.json"),
            "topology/pod-1/paths-101/pathep-[PortChannel1]",
            script.PASS,
            [],
        ),
        (
            read_data(dir, "baseline.json"),
            "topology/pod-1/protpaths-101-102/pathep-[Vpc1]",
            script.PASS,
            [],
        ),
        (
            read_data(dir, "baseline.json"),
            "topology/pod-1/paths-101/extpaths-112/pathep-[eth1/10]",
            script.PASS,
            [],
        ),
        (
            read_data(dir, "baseline.json"),
            "topology/pod-1/paths-101/pathep-[sup-eth0]",
            script.PASS,
            [],
        ),
        (
            read_data(dir, "baseline.json"),
            "",
            script.PASS,
            [],
        ),
        (
            read_data(dir, "baseline.json"),
            "topology/pod-1/paths-101/pathep-[eth1/10]/extra",
            script.PASS,
            [],
        ),
    ],
)
def test_destination_paths(run_check, mock_icurl, icurl_outputs, path, expected_result, expected_ports):
    icurl_outputs[dest_api][0]['spanRsDestPathEp']['attributes']['tDn'] = path
    icurl_outputs['topology/pod-2/node-201/sys/phys-[eth1/10/2].json'] = icurl_outputs[phys_api]
    result = run_check(tversion=script.AciVersion("6.1(3f)"))
    assert result.result == expected_result
    assert [row[:3] for row in result.data] == expected_ports


@pytest.mark.parametrize(
    "icurl_outputs",
    [read_data(dir, "shared.json")],
)
def test_shared_destination_and_multiple_ports(run_check, mock_icurl, icurl_outputs):
    result = run_check(tversion=script.AciVersion("6.1(3f)"))
    assert result.result == script.FAIL_O
    assert [row[:4] for row in result.data] == [
        ['1', '101', 'eth1/10', 'Destination1, Destination2'],
        ['2', '201', 'eth1/10', 'Destination2'],
    ]


@pytest.mark.parametrize(
    "icurl_outputs",
    [read_data(dir, "baseline.json")],
)
def test_api_error(run_check, mock_icurl, icurl_outputs):
    icurl_outputs[phys_api] = {
        'totalCount': '1',
        'imdata': [
            {
                'error': {
                    'attributes': {
                        'code': '503',
                        'text': 'Unable to deliver the message, Resolve timeout',
                    },
                },
            },
        ],
    }
    result = run_check(tversion=script.AciVersion("6.1(3f)"))
    assert result.result == script.ERROR


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {src_grp_api: []},
        {
            src_grp_api: read_data(dir, "baseline.json")[src_grp_api],
            label_api: [],
        },
    ],
)
def test_no_session_skips_downstream_queries(run_check, mock_icurl):
    result = run_check(tversion=script.AciVersion("6.1(3f)"))
    assert result.result == script.PASS
    assert result.data == []
