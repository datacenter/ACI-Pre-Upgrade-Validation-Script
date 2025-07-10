import os
import pytest
import logging
import importlib
import json
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))
pcons_rs_subtree_dep_api = 'pconsRsSubtreeDep.json?query-target-filter=wcard(pconsRsSubtreeDep.tDn,"/instdn-")'
pcons_ra_api = 'registry/class-1809/instdn-[uni/phys-PHY-DOM]/ra-[uni/infra/attentp-PHY-DOM_AttEntityP]-6-0-0-0-SubtreeWithRels-mo.json'
policy_dn_api = 'uni/phys-PHY-DOM.json'

@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # pass when version tversion is older than 6.0(3d)
        (
            {
                pcons_rs_subtree_dep_api: read_data(dir, 'pconsRsSubtreeDep.json'),
                pcons_ra_api: read_data(dir, 'pconsRA.json'),
                policy_dn_api: read_data(dir, 'policyDn.json'),
            },
            "5.3(2a)",
            "6.0(3c)",
            script.PASS,
        ),
        # pass when version tversion is older than 6.0(3d) and policy_dn is found.
        (
            {
                pcons_rs_subtree_dep_api: read_data(dir, 'pconsRsSubtreeDep.json'),
                pcons_ra_api: read_data(dir, 'pconsRA.json'),
                policy_dn_api: read_data(dir, 'policyDn.json')
            },
            "5.3(2a)",
            "6.0(3d)",
            script.PASS,
        ),
        # fail when version tversion is older than 6.0(3d) and policy_dn is NOT found.
        (
            {
                pcons_rs_subtree_dep_api: read_data(dir, 'pconsRsSubtreeDep.json'),
                pcons_ra_api: read_data(dir, 'pconsRA.json'),
                policy_dn_api: read_data(dir, 'policyDn_empty.json'),
            },
            "5.3(2a)",
            "6.0(3d)",
            script.FAIL_O,
        ),


    ],
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    cver = script.AciVersion(cversion) if cversion else None
    tver = script.AciVersion(tversion) if tversion else None

    result = script.stale_pcons_ra_mo_check(1, 1, cver, tver,)
    assert result == expected_result