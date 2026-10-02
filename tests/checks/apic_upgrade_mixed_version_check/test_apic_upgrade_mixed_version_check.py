import importlib

import pytest


script = importlib.import_module('aci-preupgrade-validation-script')
test_function = 'apic_upgrade_mixed_version_check'


def fabric_node(node_id, role, version, state='active', pod='1'):
    return {'fabricNode': {'attributes': {
        'dn': 'topology/pod-{}/node-{}'.format(pod, node_id),
        'id': str(node_id),
        'name': '{}{}'.format(role, node_id),
        'role': role,
        'version': version,
        'fabricSt': state,
    }}}


def run_mixed_check(run_check, nodes, current='6.1(4h)', target='6.2(1a)'):
    return run_check(
        cversion=script.AciVersion(current) if current else None,
        tversion=script.AciVersion(target) if target else None,
        fabric_nodes=nodes,
    )


def test_missing_target_and_current_version(run_check):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-16.1(4h)')]
    assert run_mixed_check(run_check, nodes, target=None).result == script.MANUAL
    assert run_mixed_check(run_check, nodes, current=None).result == script.MANUAL


@pytest.mark.parametrize('target', ['6.1(4h)', '6.1(3a)'])
def test_only_apic_upgrades_are_checked(run_check, target):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-15.2(8f)')]
    assert run_mixed_check(run_check, nodes, target=target).result == script.NA


def test_uniform_active_fabric_passes(run_check):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(2, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-16.1(4h)'),
             fabric_node(201, 'spine', 'n9000-16.1(4h)')]
    result = run_mixed_check(run_check, nodes)
    assert result.result == script.PASS
    assert result.data == []


@pytest.mark.parametrize('target, message', [
    ('6.1(5a)', 'unsupported'),
    ('6.2(1a)', 'third version'),
    ('6.2(2a)', 'third version'),
])
def test_mismatch_fails_at_every_target(run_check, target, message):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-15.2(8f)'),
             fabric_node(201, 'spine', 'n9000-16.1(4h)')]
    result = run_mixed_check(run_check, nodes, target=target)
    assert result.result == script.FAIL_UF
    assert result.msg == ""
    assert message in result.recommended_action
    assert result.data == [
        ['1', '101', 'leaf101', 'leaf', 'n9000-15.2(8f)', '6.1(4h)',
         'Switch differs from APIC']]
    assert len(result.headers) == len(result.data[0])


def test_every_mismatched_node_is_reported(run_check):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-15.2(8f)'),
             fabric_node(202, 'spine', 'n9000-16.0(5a)', pod='2'),
             fabric_node(102, 'leaf', 'n9000-16.2(1a)')]
    result = run_mixed_check(run_check, nodes)
    assert result.result == script.FAIL_UF
    assert [row[1] for row in result.data] == ['101', '102', '202']
    assert result.data[1][6] == 'Switch newer than APIC'
    assert result.msg == ''
    assert 'newer than the APIC' in result.recommended_action


def test_apic_versions_must_agree(run_check):
    nodes = [fabric_node(1, 'controller', '6.1(3a)'),
             fabric_node(2, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-16.1(4h)')]
    result = run_mixed_check(run_check, nodes)
    assert result.result == script.FAIL_UF
    assert result.msg == ''
    assert 'APIC cluster upgrade' in result.recommended_action
    assert result.data[0][1] == '1'


def test_inactive_switch_is_excluded(run_check):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-16.1(4h)'),
             fabric_node(102, 'leaf', '', state='inactive')]
    assert run_mixed_check(run_check, nodes).result == script.PASS


def test_unknown_active_version_requires_manual_check(run_check):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-16.1(4h)'),
             fabric_node(102, 'leaf', '')]
    result = run_mixed_check(run_check, nodes)
    assert result.result == script.MANUAL
    assert result.data[0][1] == '102'


def test_known_mismatch_takes_precedence_over_unknown_version(run_check):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', 'n9000-15.2(8f)'),
             fabric_node(102, 'leaf', '')]
    result = run_mixed_check(run_check, nodes)
    assert result.result == script.FAIL_UF
    assert [row[6] for row in result.data] == [
        'Switch differs from APIC', 'Switch version not found']


def test_no_active_switch_requires_manual_check(run_check):
    nodes = [fabric_node(1, 'controller', '6.1(4h)'),
             fabric_node(101, 'leaf', '', state='inactive')]
    assert run_mixed_check(run_check, nodes).result == script.MANUAL
