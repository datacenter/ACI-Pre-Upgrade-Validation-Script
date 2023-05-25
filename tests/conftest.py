import os
import sys
import pytest
import logging
import importlib

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
sys.path.append(PROJECT_DIR)

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger(__name__)


@pytest.fixture
def icurl_outputs():
    """Allows each test function to simulate the responses of icurl() with a
    test data in the form of { key: value }.

    where:
        key = icurl query parameter such as `topSystem.json`
        value = An expected result of icurl(). Should be the list under
                `imdata` in the JSON response from APIC.

    If a single check performs multiple icurl quries, provide test data as
    shown below:
    {
        "query1": "result1",
        "query2": "result2",
    }
    """
    return {
        "object_class1.json?filter1=xxx&filter2=yyy": [],
        "object_class2.json": [{"object_class": {"attributes": {}}}],
    }


@pytest.fixture
def mock_icurl(monkeypatch, icurl_outputs):
    def _mock_icurl(apitype, query):
        if icurl_outputs.get(query) is None:
            log.error("Query `%s` not found in test data", query)
        return icurl_outputs.get(query, [])

    monkeypatch.setattr(script, "icurl", _mock_icurl)
