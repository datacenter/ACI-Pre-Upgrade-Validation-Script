# -*- coding: utf-8 -*-
import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))


# icurl queries
cloudsecPreSharedKey = 'cloudsecPreSharedKey.json'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            ## TARGET VERSION IS OLDER THAN 6.0(6), CLOUDSEC IS PRESENT, VALIDATION RESULT : N/A
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_pos.json")},
            "5.2(6a)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS OLDER THAN 6.0(6), NO CLOUDSEC PRESENT, VALIDATION RESULT : N/A
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_neg.json")},
            "5.2(6b)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.0(6), NO CLOUDSEC PRESENT, VALIDATION RESULT : PASS
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_neg.json")},
            "6.0(6b)",
            script.PASS,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.0(6), CLOUDSEC PRESENT, VALIDATION RESULT : FAIL_O            
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_pos.json")},
            "6.0(6b)",
            script.FAIL_O,
        ),
    ],
)
def test_logic(mock_icurl, tversion, expected_result):
    result = script.cloudsec_encryption_check(1, 1, script.AciVersion(tversion))
    assert result == expected_result
