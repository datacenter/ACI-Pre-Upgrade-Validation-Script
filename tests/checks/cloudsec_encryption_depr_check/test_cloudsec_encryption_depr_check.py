# -*- coding: utf-8 -*-
import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "cloudsec_encryption_depr_check"

# icurl queries
cloudsecPreSharedKey = 'cloudsecPreSharedKey.json'


@pytest.mark.parametrize(
    "icurl_outputs, tversion, expected_result",
    [
        (
            ## TARGET VERSION IS OLDER THAN 6.0(6), Single KEY PRESENT, VALIDATION RESULT : N/A
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_err.json")},
            "4.2(1a)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS OLDER THAN 6.0(6), Single KEY PRESENT, VALIDATION RESULT : N/A
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_pos.json")},
            "5.2(6a)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS OLDER THAN 6.0(6), NO KEYS PRESENT, VALIDATION RESULT : N/A
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_neg.json")},
            "5.2(6b)",
            script.NA,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.0(6), NO KEYS PRESENT, VALIDATION RESULT : PASS
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_neg.json")},
            "6.0(6b)",
            script.PASS,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.0(6), Single KEY PRESENT, VALIDATION RESULT : FAIL_O            
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_pos.json")},
            "6.0(6b)",
            script.MANUAL,
        ),
        (
            ## TARGET VERSION IS NEWER THAN 6.0(6), MULTIPLE KEYs PRESENT, VALIDATION RESULT : FAIL_O            
            {cloudsecPreSharedKey: read_data(dir, "cloudsecPreSharedKey_pos2.json")},
            "6.0(6b)",
            script.MANUAL,
        ),
    ],
)
def test_logic(run_check, mock_icurl, tversion, expected_result):
    result = run_check(tversion=script.AciVersion(tversion))
    assert result.result == expected_result
