import os
import pytest
import logging
import importlib
from helpers.utils import read_data
script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
infraWiNode = "infraWiNode.json"
apContainerPol = "pluginPolContr/ContainerPol.json"


@pytest.mark.parametrize(
    "icurl_outputs, expected_result",
    [
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_10_0_0_0__16.json"),
                apContainerPol: [],
            },
            script.PASS,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_10_0_0_0__16.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_17_0_1__16.json"),
            },
            script.PASS,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_10_0_0_0__16.json"),
                apContainerPol: read_data(dir, "apContainerPol_10_0_0_1__16.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_10_0_x_0__24_remote_apic.json"),
                apContainerPol: [],
            },
            script.PASS,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_10_0_x_0__24_remote_apic.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_17_0_1__16.json"),
            },
            script.PASS,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_10_0_x_0__24_remote_apic.json"),
                apContainerPol: read_data(dir, "apContainerPol_10_0_0_1__16.json"),
            },
            script.FAIL_UF,
        ),
        # This scenario is the most likely one where, prior to the upgrade,
        # apContainerPol does not exist by default and docker falls back to
        # 172.18.0.1/16. Then apContainerPol is created after the upgrade
        # with the default value 172.17.0.0/16 which overlaps the TEP.
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_0_0__16.json"),
                apContainerPol: [],
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_0_0__16.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_17_0_1__16.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_0_0__16.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_17_0_10__16.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_0_0__16.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_17_0_1__17.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_0_0__16.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_16_0_1__15.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_0_0__16.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_18_0_1__16.json"),
            },
            script.PASS,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_x_0__24_remote_apic.json"),
                apContainerPol: [],
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_x_0__24_remote_apic.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_17_0_1__16.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_x_0__24_remote_apic.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_17_0_10__16.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_x_0__24_remote_apic.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_17_0_1__17.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_x_0__24_remote_apic.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_16_0_1__15.json"),
            },
            script.FAIL_UF,
        ),
        (
            {
                infraWiNode: read_data(dir, "infraWiNode_172_17_x_0__24_remote_apic.json"),
                apContainerPol: read_data(dir, "apContainerPol_172_18_0_1__16.json"),
            },
            script.PASS,
        ),
    ],
)
def test_logic(mock_icurl, expected_result):
    result = script.docker0_subnet_overlap_check(1, 1)
    assert result == expected_result
