import os
import pytest
import logging
import importlib
from helpers.utils import read_data

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)
dir = os.path.dirname(os.path.abspath(__file__))

test_function = "rogue_exception_mac_check"

# icurl queries
fvRogueExceptionMac = 'fvRogueExceptionMac.json'
presListener = 'presListener.json'
presListener += '?query-target-filter=and(wcard(presListener.dn,"exceptcont"))'



@pytest.mark.parametrize(
    "icurl_outputs, cversion, tversion, expected_result",
    [
        # MANUAL, Tversion is not provided
        (
            {
                fvRogueExceptionMac: read_data(
                    dir, "fvRogueExceptionMac.json"
                ),
                presListener: read_data(dir, "presListener-neg.json"),
            },
            "4.2(3b)",
            None,
            script.MANUAL,
        ),
        # NA Cversion is not affected (older than 5.2-3)
        (
            {
                fvRogueExceptionMac: read_data(
                    dir, "fvRogueExceptionMac.json"
                ),
                presListener: read_data(dir, "presListener-pos.json"),
            },
            "4.2(3b)",
            "6.0(4p)",
            script.NA,
        ),
        # NA Cversion is not affected (newer than 6.0-3)
        (
            {
                fvRogueExceptionMac: read_data(
                    dir, "fvRogueExceptionMac.json"
                ),
                presListener: read_data(dir, "presListener-pos.json"),
            },
            "6.0(4a)",
            "6.1(4p)",
            script.NA,
        ),
        # NA Cversion is affected, Tversion is not affected (> 6.0-9e < 6.1)
        (
            {
                fvRogueExceptionMac: read_data(
                    dir, "fvRogueExceptionMac.json"
                ),
                presListener: read_data(dir, "presListener-pos.json"),
            },
            "5.2(4c)",
            "6.0(9f)",
            script.NA,
        ),
        # NA Cversion is affected, Tversion is not affected (> 6.1(4h))
        (
            {
                fvRogueExceptionMac: read_data(
                    dir, "fvRogueExceptionMac.json"
                ),
                presListener: read_data(dir, "presListener-pos.json"),
            },
            "5.2(4c)",
            "6.1(4l)",
            script.NA,
        ),
        # NA, Versions affected, no Rogue  Exceptions MACs configured
        (
            {
                fvRogueExceptionMac: [],
                presListener: read_data(dir, "presListener-pos.json"),
            },
            "5.2(4c)",
            "6.0(4l)",
            script.NA,
        ),
        # PASS, Versions affected, Rogue Exception MACs present, presListeners are expected
        (
            {
                fvRogueExceptionMac: read_data(
                    dir, "fvRogueExceptionMac.json"
                ),
                presListener: read_data(dir, "presListener-neg.json"),
            },
            "5.2(4c)",
            "6.0(4l)",
            script.PASS,
        ),
        # FAIL_UF, Versions affected, Rogue Exception MACs present, presListeners are expected
        (
            {
                fvRogueExceptionMac: read_data(
                    dir, "fvRogueExceptionMac.json"
                ),
                presListener: read_data(dir, "presListener-pos.json"),
            },
            "5.2(4c)",
            "6.0(4l)",
            script.FAIL_UF,
        ),
    ],
)
def test_logic(run_check, mock_icurl, cversion, tversion, expected_result):
    result = run_check(
        cversion=script.AciVersion(cversion),
        tversion=script.AciVersion(tversion) if tversion else None,        
    )
    assert result.result == expected_result
