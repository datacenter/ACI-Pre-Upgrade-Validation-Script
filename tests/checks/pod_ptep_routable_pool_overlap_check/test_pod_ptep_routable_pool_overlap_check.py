import importlib

import pytest


script = importlib.import_module('aci-preupgrade-validation-script')
test_function = 'pod_ptep_routable_pool_overlap_check'

POD_PROFILES = 'fvPodConnP.json?rsp-subtree=children'
ROUTABLE_POOLS = 'fabricExtRoutablePodSubnet.json'


def pod_profile(pod_id, addresses, other_child_address=None):
    dn = 'uni/tn-infra/fabricExtConnP-1/podConnP-{}'.format(pod_id)
    children = [
        {'fvIp': {'attributes': {'addr': address, 'dn': '{}/ip-[{}]'.format(dn, address)}}}
        for address in addresses
    ]
    if other_child_address:
        children.append({'fvExtRoutableUcastConnP': {'attributes': {'addr': other_child_address}}})
    return {'fvPodConnP': {'attributes': {'dn': dn, 'id': str(pod_id)}, 'children': children}}


def routable_pool(pod_id, subnet, reserved_count):
    return {'fabricExtRoutablePodSubnet': {'attributes': {
        'dn': 'uni/controller/setuppol/setupp-{}/extrtpodsubnet-[{}]'.format(pod_id, subnet),
        'pool': subnet,
        'reserveAddressCount': str(reserved_count),
        'state': 'active',
    }}}


@pytest.mark.parametrize('profiles,pools,expected_result,expected_addresses', [
    # The connected APIC has PTEPs in the reserved part of each pod's pool.
    (
        [pod_profile(1, ['172.16.11.1/32'], '172.16.11.20/32'),
         pod_profile(2, ['172.16.22.1/32'])],
        [routable_pool(1, '172.16.11.0/24', 6),
         routable_pool(2, '172.16.22.0/24', 7)],
        script.PASS,
        [],
    ),
    # CDETS verification: with three reserved addresses, .1-.3 pass and .4 fails.
    (
        [pod_profile(2, ['192.30.30.1/32', '192.30.30.2/32',
                         '192.30.30.3/32', '192.30.30.4/32'])],
        [routable_pool(2, '192.30.30.0/24', 3)],
        script.FAIL_O,
        ['192.30.30.4/32'],
    ),
    (
        [pod_profile(1, ['40.40.40.40/32'])],
        [routable_pool(1, '40.40.40.0/24', 0)],
        script.FAIL_O,
        ['40.40.40.40/32'],
    ),
    # The APIC fix compares each POD PTEP with all configured routable pools.
    (
        [pod_profile(1, ['50.50.50.4/32'])],
        [routable_pool(2, '50.50.50.0/24', 3)],
        script.FAIL_O,
        ['50.50.50.4/32'],
    ),
    (
        [pod_profile(1, ['50.50.50.50/32'])],
        [routable_pool(1, '40.40.40.0/24', 0)],
        script.PASS,
        [],
    ),
    ([pod_profile(1, ['50.50.50.50/32'])], [], script.PASS, []),
    ([], [routable_pool(1, '50.50.50.0/24', 0)], script.PASS, []),
])
def test_pod_ptep_routable_pool_overlap(run_check, mock_icurl, icurl_outputs,
                                        profiles, pools, expected_result, expected_addresses):
    icurl_outputs[POD_PROFILES] = profiles
    icurl_outputs[ROUTABLE_POOLS] = pools

    result = run_check()

    assert result.result == expected_result
    assert [row[1] for row in result.data] == expected_addresses
