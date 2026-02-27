import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
# shared contracts
shrd_contracts_api = 'vzBrCP.json'
shrd_contracts_api += '?query-target-filter=and(eq(vzBrCP.scope,"global"))'

# global epgs  ( 16 <= pgtag <= 16385) with Preferred group enabled with provided contracts

glbl_epgs_api = 'fvAEPg.json'
glbl_epgs_api += '?query-target-filter=and(le(fvAEPg.pcTag,"16385"),ge(fvAEPg.pcTag,"16"),eq(fvAEPg.prefGrMemb,"include"))'
glbl_epgs_api += '&rsp-subtree=children&rsp-subtree-class=fvRsProv'

# global external Epgs  ( 16 <= pgtag <= 16385) with Preferred group enabled with provided contracts

glbl_ext_epgs_api = 'l3extInstP.json'
glbl_ext_epgs_api += '?query-target-filter=and(le(l3extInstP.pcTag,"16385"),ge(l3extInstP.pcTag,"16"),eq(l3extInstP.prefGrMemb,"include"))'
glbl_ext_epgs_api += '&rsp-subtree=children&rsp-subtree-class=fvRsProv'


@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [

        # MANUAL cases
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(4a)", None,
            script.MANUAL,
        ),
        # NA cases
        # Target version is lower than 4.2(6d), Result = NA
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "4.2(6c)",
            script.NA,
        ),
        # Target version is lower than 5.1(1h), Result = NA
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "5.1(1g)",
            script.NA,
        ),
        # There are no global contracts, Result = NA
        (
            {
                shrd_contracts_api: [],
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "6.1(1g)",
            script.NA,
        ),
        # FAIL_O Cases
        # Target version is older than 6.0(1g), Result = FAIL_O
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "6.0(1f)",
            script.FAIL_O,
        ),
        # Target version is newer than 6.0(1g), both global_pg EPGs and extEPGs , Result = FAIL_O
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "6.0(1g)",
            script.FAIL_O,
        ),
        # Target version is newer than 6.0(1g), no EPGS, only global_pg extEPGs , Result = FAIL_O
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [],
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "6.0(1g)",
            script.FAIL_O,
        ),
        # PASS Cases
        # Target version is older than 6.0(1g), no global_pg EPGs or extEPGs , Result = PASS
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [],
                glbl_ext_epgs_api: []
            },
            "4.2(1a)", "6.0(1f)",
            script.PASS,
        ),
        # Target version is newer than 6.0(1g), no global_pg EPGs or extEPGs , Result = PASS
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: [],
                glbl_ext_epgs_api: []
            },
            "4.2(1a)", "6.0(1h)",
            script.PASS,
        ),
        # Target version is newer than 6.0(1g), only global_pg EPGs , no global_pg extEPGs , Result = PASS
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: []
            },
            "4.2(1a)", "6.0(1h)",
            script.PASS,
        ),
    ]
)
def test_logic(mock_icurl, cversion, tversion, expected_result):
    result = script.pg_and_shared_svc_contract_check(
        1,
        1,
        script.AciVersion(cversion),
        script.AciVersion(tversion) if tversion else None
    )
    assert result == expected_result
