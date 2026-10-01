import importlib

import pytest


script = importlib.import_module('aci-preupgrade-validation-script')
test_function = 'atomic_counter_check'

TENANT_COUNT_API = (
    'dbgacTenantSpaceCmn.json?query-target-filter='
    'ne(dbgacTenantSpaceCmn.dn,"uni/tn-common/acIpToIp-default")'
    '&rsp-subtree-include=count'
)
ALL_PATH_COUNT_API = 'dbgAcPathA.json?rsp-subtree-include=count'
PATH_COUNT_API = 'dbgAcPath.json?rsp-subtree-include=count'
EP_TO_EP_COUNT_API = 'dbgacEpToEp.json?rsp-subtree-include=count'


def count_response(count):
    return [{'moCount': {'attributes': {'count': str(count)}}}]


@pytest.mark.parametrize(
    'tversion,tenant_count,all_path_count,path_count,ep_to_ep_count,expected_result,expected_concerns',
    [
        ('6.1(2a)', 1, 0, None, None, script.MANUAL, ['Deprecated tenant policies']),
        ('6.2(1a)', 0, 1, None, None, script.MANUAL, ['Deprecated TEP paths']),
        ('6.1(2a)', 0, 0, 0, 0, script.NA, []),
        ('6.1(1a)', None, None, 0, 0, script.NA, []),
        ('6.1(1a)', None, None, 1600, 0, script.PASS, []),
        ('6.1(1a)', None, None, 1601, 0, script.FAIL_UF, ['TEP-to-TEP scalability']),
        ('6.1(1a)', None, None, 0, 1, script.MANUAL, ['Configuration rollback review']),
        ('6.1(1a)', None, None, 1601, 1, script.FAIL_UF, ['TEP-to-TEP scalability', 'Configuration rollback review']),
        (None, None, None, 0, 0, script.MANUAL, []),
    ],
)
def test_atomic_counter_order_and_results(
    run_check, mock_icurl, icurl_outputs, tversion, tenant_count, all_path_count,
    path_count, ep_to_ep_count, expected_result, expected_concerns,
):
    counts = {
        TENANT_COUNT_API: tenant_count,
        ALL_PATH_COUNT_API: all_path_count,
        PATH_COUNT_API: path_count,
        EP_TO_EP_COUNT_API: ep_to_ep_count,
    }
    icurl_outputs.update({query: count_response(count) for query, count in counts.items() if count is not None})

    result = run_check(tversion=script.AciVersion(tversion) if tversion else None)

    assert result.result == expected_result
    assert [row[0] for row in result.data] == expected_concerns
    if expected_concerns and expected_concerns[0].startswith('Deprecated'):
        assert 'Cleanup is mandatory' in result.msg
    if tversion is None:
        assert 'deprecation could not be assessed' in result.msg
