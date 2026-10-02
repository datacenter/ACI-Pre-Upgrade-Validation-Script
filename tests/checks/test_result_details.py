"""Check result data and recommended actions in console and JSON output."""
import importlib
import json
import os

import pytest


script = importlib.import_module('aci-preupgrade-validation-script')


def run_check(name, **kwargs):
    return getattr(script, name)(finalize_check=lambda *_: None, **kwargs)


def assert_outputs(monkeypatch, name, result, detail):
    titles = []
    getattr(script, name)(initialize_check=lambda _, title: titles.append(title))
    output = []
    monkeypatch.setattr(script, 'prints', output.append)
    script.print_result(117, 117, titles[0], **result.as_dict())
    status_line, table_and_action = output[0].split('\n', 1)
    assert status_line.endswith(' ' + result.result)
    assert detail not in status_line
    assert detail in table_and_action
    assert result.recommended_action in table_and_action

    payload = json.loads(json.dumps(script.AciResult(name, titles[0], result).as_dict()))
    assert payload['recommended_action'] == result.recommended_action
    assert payload['failureDetails']['header'] == result.headers
    assert payload['failureDetails']['data'] == [dict(zip(result.headers, row)) for row in result.data]


@pytest.mark.parametrize('failing_class', ['svccoreCtrlr', 'svccoreNode'])
def test_svccore_collection_error_uses_existing_table(monkeypatch, failing_class):
    detail = 'APIC query timed out while collecting core counts'

    def icurl(_, query):
        if query.startswith(failing_class + '.'):
            raise RuntimeError(detail)
        return [{'moCount': {'attributes': {'count': '0'}}}]

    monkeypatch.setattr(script, 'icurl', icurl)
    name = 'svccore_excessive_data_check'
    result = run_check(name)
    assert result.result == script.ERROR
    assert result.msg == ''
    assert result.headers == ['Class Name', 'Count']
    assert result.data == [['svccoreCtrlr/svccoreNode', 'ERR']]
    assert detail in result.recommended_action
    assert_outputs(monkeypatch, name, result, detail)


@pytest.mark.parametrize('failing_class', ['vnsGraphInst', 'fvCtx', 'vnsEPgDef'])
def test_service_graph_query_errors_keep_details_in_action(monkeypatch, failing_class):
    fixture_dir = os.path.join(os.path.dirname(__file__), 'vzany_svcgraph_stretched_vrf_check')
    fixtures = {
        'vnsGraphInst': 'vnsGraphInst_with_consumer.json',
        'fvCtx': 'fvCtx_stretched_vrf.json',
        'vzRsAnyToCons': 'vzRsAnyToCons_consumer.json',
    }
    detail = 'API collection failed: ' + 'long diagnostic text ' * 12

    def icurl(_, query):
        mo_class = query.split('.')[0]
        if mo_class == failing_class:
            raise RuntimeError(detail)
        if mo_class == 'vzRsAnyToProv':
            return []
        with open(os.path.join(fixture_dir, fixtures[mo_class])) as fixture_file:
            return json.load(fixture_file)

    monkeypatch.setattr(script, 'icurl', icurl)
    name = 'vzany_svcgraph_stretched_vrf_check'
    result = run_check(name, cversion=script.AciVersion('6.0(1a)'), tversion=script.AciVersion('6.1(4a)'))
    assert result.result == script.ERROR
    assert result.msg == ''
    assert result.headers == ['Tenant', 'VRF', 'Contract', 'Graph', 'Issue']
    assert result.data == [['-', '-', '-', '-', 'ERR']]
    assert detail in result.recommended_action
    assert_outputs(monkeypatch, name, result, detail)


def test_openssl_failure_uses_certificate_response_column(monkeypatch, tmpdir):
    monkeypatch.chdir(tmpdir)
    monkeypatch.setattr(script, 'icurl', lambda *_: [
        {'pkiFabricSelfCAEp': {'attributes': {'currCertReqPassphrase': 'test-passphrase'}}}
    ])
    class FailedProcess(object):
        returncode = 7

        def communicate(self):
            return b'error', None

    monkeypatch.setattr(script.subprocess, 'Popen', lambda *args, **kwargs: FailedProcess())
    name = 'apic_ca_cert_validation'
    result = run_check(name)
    assert result.result == script.ERROR
    assert result.msg == ''
    assert result.headers == ['Certreq Response']
    assert result.data == [['ERR']]
    assert str(FailedProcess.returncode) in result.recommended_action
    assert_outputs(monkeypatch, name, result, 'OpenSSL command failed (exit code 7).')


IMAGE_32 = 'aci-n9000-dk9.16.0.2h.bin'
IMAGE_64 = 'aci-n9000-dk9.16.0.2h-cs_64.bin'
OLD_IMAGE = 'aci-n9000-dk9.15.2.8h.bin'


@pytest.mark.parametrize('current, target, available, missing', [
    ('6.0(3a)', '5.2(8h)', [], [['Target', '32-bit', OLD_IMAGE, 'Missing']]),
    ('6.0(3a)', '6.0(2h)', [], [
        ['Target', '32-bit', IMAGE_32, 'Missing'], ['Target', '64-bit', IMAGE_64, 'Missing']]),
    ('6.0(3a)', '6.0(2h)', [IMAGE_32], [['Target', '64-bit', IMAGE_64, 'Missing']]),
    ('6.0(3a)', '6.0(2h)', [IMAGE_64], [['Target', '32-bit', IMAGE_32, 'Missing']]),
    ('5.2(8h)', '6.0(2h)', [IMAGE_32, IMAGE_64], [['Current', '32-bit', OLD_IMAGE, 'Missing']]),
])
def test_missing_images_are_results_with_repository_action(monkeypatch, current, target, available, missing):
    def icurl(_, query):
        if query.startswith('eqptcapacityFSPartition.'):
            return [{'eqptcapacityFSPartition': {'attributes': {
                'dn': 'topology/pod-1/node-101/sys/eqptcapacity/fspartition-bootflash', 'avail': '1'}}}]
        if query.startswith('maintUpgJob.'):
            return []
        assert query.startswith('firmwareFirmware.')
        return [{'firmwareFirmware': {'attributes': {'isoname': name, 'size': '2000000000'}}}
                for name in available]

    monkeypatch.setattr(script, 'icurl', icurl)
    name = 'switch_bootflash_usage_check'
    result = run_check(name, sw_cversion=script.AciVersion(current), tversion=script.AciVersion(target))
    assert result.result == script.MANUAL
    assert result.msg == ''
    assert result.headers == ['Image Role', 'Architecture', 'Filename', 'Status']
    assert result.data == missing
    assert result.recommended_action
    assert_outputs(monkeypatch, name, result, missing[0][2])
