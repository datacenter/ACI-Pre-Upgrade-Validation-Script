import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "access_untagged_check"

# icurl queries
faultInsts = 'faultInst.json?&query-target-filter=wcard(faultInst.changeSet,"native-or-untagged-encap-failure")'


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {faultInsts: read_data(dir, "faultInst_POS.json")},
            script.FAIL_O,
        ),
        (
            {faultInsts: read_data(dir, "faultInst_NEG.json")},
            script.PASS,
        )
    ],
)
def test_logic(run_check, mock_icurl, expected_result):
    result = run_check()
    assert result.result == expected_result


def test_standard_and_fex_path_details(run_check, mock_icurl, icurl_outputs):
    icurl_outputs[faultInsts] = read_data(dir, "faultInst_PATH_VARIANTS.json")
    recommended_action = (
        "Resolve the conflict by removing this config or other configs using this port "
        "in Access(untagged) or native mode."
    )

    result = run_check()

    assert result.result == script.FAIL_O
    assert result.data == [
        ["F0467", "1", "101", "eth1/10", "TENANT-A", "APP-A", "EPG-A", recommended_action],
        ["F0467", "2", "102", "eth1/20 on FEX 110", "TENANT-B", "APP-B", "EPG-B", recommended_action],
    ]
    assert result.unformatted_data == []


def test_unrecognized_dn_uses_unformatted_details(run_check, mock_icurl, icurl_outputs):
    icurl_outputs[faultInsts] = read_data(dir, "faultInst_UNFORMATTED.json")
    description = (
        "Configuration failed for a synthetic attachment due to Only One Native or "
        "Untagged Encap Allowed on Interface, debug message: "
    )
    recommended_action = (
        "Resolve the conflict by removing this config or other configs using this port "
        "in Access(untagged) or native mode."
    )

    result = run_check()

    assert result.result == script.FAIL_O
    assert result.data == []
    assert result.unformatted_data == [["F0467", description, recommended_action]]
