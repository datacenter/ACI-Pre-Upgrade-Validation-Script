import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "pg_and_shared_svc_contract_check"

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
        # Target version is lower than 4.2, Result = NA
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "4.1(2a)",
            script.NA,
        ),
        # Target version predates Preferred Group-specific F0467 enforcement,
        # but the forwarding risk is still present.
        (
            {
                shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
                glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
                glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
            },
            "4.2(1a)", "5.1(1g)",
            script.FAIL_O,
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
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None
    )
    assert result.result == expected_result


@pytest.mark.parametrize(
    "icurl_outputs",
    [
        {
            shrd_contracts_api: read_data(dir, "global_vzBrCP_pos.json"),
            glbl_epgs_api: read_data(dir, "global_pg_fvAEPg.json"),
            glbl_ext_epgs_api: read_data(dir, "global_pg_l3extInstP.json")
        }
    ]
)
@pytest.mark.parametrize(
    "tversion",
    [
        "4.2(5n)",
        "4.2(6d)",
        "5.1(1h)",
        "5.1(3e)",
        "5.2(1g)",
        "5.2(8i)",
        "6.0(1g)",
    ]
)
def test_all_4_2_and_newer_targets_are_checked(run_check, mock_icurl, tversion):
    result = run_check(
        cversion=script.AciVersion("4.2(1a)"),
        tversion=script.AciVersion(tversion)
    )
    assert result.result not in (script.NA, script.ERROR)
