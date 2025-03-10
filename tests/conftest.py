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
    test data in the form of { query: test_data }.

    where:
        query = icurl query parameter such as `topSystem.json`
        test_data = An expected result of icurl().
                    This can take different forms in the test data. See below for details.

    If a single check performs multiple icurl quries, provide test data as
    shown below:
    {
        "query1": "test_data1",
        "query2": "test_data2",
    }

    Examples)

    Option 1 - test_data is the content of imdata:
        {
            "object_class1.json?filter1=xxx&filter2=yyy": [],
            "object_class2.json": [{"object_class": {"attributes": {}}}],
        }

    Option 2 - test_data is the whole response of an API query:
        {
            "object_class1.json?filter1=xxx&filter2=yyy": {
                "totalCount": "0",
                "imdata": [],
            },
            "object_class2.json": {
                "totalCount": "1",
                "imdata": [{"object_class": {"attributes": {}}}],
            }
        }

    Option 3 - test_data is the bundle of API queries with multiple pages:
        {
            "object_class1.json?filter1=xxx&filter2=yyy": [
                {
                    "totalCount": "0",
                    "imdata": [],
                }
            ],
            "object_class2.json": [
                {
                    "totalCount": "199000",
                    "imdata": [
                        {"object_class": {"attributes": {...}}},
                        ...
                    ],
                },
                {
                    "totalCount": "199000",
                    "imdata": [
                        {"object_class": {"attributes": {...}}},
                        ...
                    ],
                },
            ]
        }
    """
    return {
        "object_class1.json?filter1=xxx&filter2=yyy": [],
        "object_class2.json": [{"object_class": {"attributes": {}}}],
    }


@pytest.fixture
def mock_icurl(monkeypatch, icurl_outputs):
    def _mock_icurl(apitype, query, page=0, page_size=100000):
        output = icurl_outputs.get(query)
        if output is None:
            log.error("Query `%s` not found in test data", query)
            data = {"totalCount": "0", "imdata": []}
        elif isinstance(output, list):
            # icurl_outputs option 1 - output is imdata which is empty
            if not output:
                data = {"totalCount": "0", "imdata": []}
            # icurl_outputs option 1 - output is imdata
            elif output[0].get("totalCount") is None:
                data = {"totalCount": str(len(output)), "imdata": output}
            # icurl_outputs option 3 - output is each page of icurl
            elif len(output) > page:
                data = output[page]
            # icurl_outputs option 3 - output is each page of icurl
            # page after the last page which is empty
            else:
                data = {"totalCount": output[0]["totalCount"], "imdata": []}
        # icurl_outputs option 2 - output is full response of icurl without pages
        elif isinstance(output, dict):
            if page == 0:
                data = output
            else:
                data = {"totalCount": output["totalCount"], "imdata": []}

        script._icurl_error_handler(data['imdata'])
        return data

    monkeypatch.setattr(script, "_icurl", _mock_icurl)
