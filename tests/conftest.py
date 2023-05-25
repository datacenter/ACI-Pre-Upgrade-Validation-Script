import os
import sys
import pytest
import importlib

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
sys.path.append(PROJECT_DIR)

script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.fixture
def icurl_outputs():
    return {
        "object_class1.json?filter1=xxx&filter2=yyy": [],
        "object_class2.json": [{"object_class": {"attributes": {}}}]
    }


@pytest.fixture
def mock_icurl(monkeypatch, icurl_outputs):
    def _mock_icurl(apitype, query):
        return icurl_outputs.get(query, [])

    monkeypatch.setattr(script, "icurl", _mock_icurl)
