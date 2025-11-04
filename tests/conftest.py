import os
import sys
import pytest
import logging
import importlib
from itertools import product

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
sys.path.append(PROJECT_DIR)

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger()


@pytest.fixture(scope="session", autouse=True)
def init():
    script.init_system()


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

        script._icurl_error_handler(data["imdata"])
        return data

    monkeypatch.setattr(script, "_icurl", _mock_icurl)


@pytest.fixture
def expected_common_data(request):
    data = {  # default
        "username": "admin",
        "password": "mypassword",
        "cversion": script.AciVersion("6.1(1a)"),
        "tversion": script.AciVersion("6.2(1a)"),
        "sw_cversion": script.AciVersion("6.0(9d)"),
        "vpc_node_ids": ["101", "102"],
    }
    param = getattr(request, "param", {})
    for key in data:
        if param.get(key, "non_falsy_default") != "non_falsy_default":
            data[key] = param[key]
    return data


@pytest.fixture(scope="session")
def result_objects_factory():
    def _result_objects_factory(profile, requested_status=None):
        result_props = [
            # result (status)
            [
                script.PASS,
                script.FAIL_O,
                script.FAIL_UF,
                script.MANUAL,
                script.POST,
                script.NA,
                script.ERROR,
            ],
            # msg
            [
                "",
                "test msg",
                "long test msg " + "x" * 120,  # > 120 char
            ],
            # headers
            [
                [],
                ["H1", "H2", "H3"],
            ],
            # data
            [
                [],
                [["Data1", "Data2", "Data3"], ["Data4", "Data5", "Data6"], ["Loooooong Data7", "Data8", "Data9"]],
            ],
            # unformatted_headers
            [
                [],
                ["Unformatted_H1"],
            ],
            # unformatted_data
            [
                [],
                [["Data1"], ["Data2"]],
            ],
            # recommended_action
            [
                "",
                "This is your recommendation to remediate the issue",
            ],
            # doc_url
            [
                "",
                "https://fake_doc_url.local/path1/#section1",
            ],
        ]

        def _generate_result_obj(result_prop):
            return script.Result(
                result=result_prop[0],
                msg=result_prop[1],
                headers=result_prop[2],
                data=result_prop[3],
                unformatted_headers=result_prop[4],
                unformatted_data=result_prop[5],
                recommended_action=result_prop[6],
                doc_url=result_prop[7],
            )

        def _get_requested_status(requested_status):
            if not isinstance(requested_status, list):
                requested_status = [requested_status]
            all_status = result_props[0]
            if not requested_status:
                return all_status
            return [status for status in all_status if status in requested_status]

        if profile == "fullmesh":
            raw_product = product(*result_props)
            return [_generate_result_obj(prop) for prop in raw_product]
        elif profile == "fail_full":
            # All props populated (mainly for FAIL_O, FAIL_UF, MANUAL)
            status_list = [script.FAIL_O, script.FAIL_UF, script.MANUAL]
            if requested_status:
                status_list = _get_requested_status(requested_status)
            return [
                _generate_result_obj(
                    [
                        status,  # result
                        result_props[1][1],  # msg
                        result_props[2][1],  # headers
                        result_props[3][1],  # data
                        result_props[4][1],  # unformatted_headers
                        result_props[5][1],  # unformatted_data
                        result_props[6][1],  # recommended_action
                        result_props[7][1],  # doc_url
                    ]
                )
                for status in status_list
            ]
        elif profile == "fail_simple":
            # No msg nor unformatted_headers/data (mojority of FAIL_O, FAIL_UF, MANUAL)
            status_list = [script.FAIL_O, script.FAIL_UF, script.MANUAL]
            if requested_status:
                status_list = _get_requested_status(requested_status)
            return [
                _generate_result_obj(
                    [
                        status,  # result
                        result_props[1][0],  # msg
                        result_props[2][1],  # headers
                        result_props[3][1],  # data
                        result_props[4][0],  # unformatted_headers
                        result_props[5][0],  # unformatted_data
                        result_props[6][1],  # recommended_action
                        result_props[7][1],  # doc_url
                    ]
                )
                for status in status_list
            ]
        elif profile == "pass":
            # Only rec_action and doc (mainly for PASS)
            status_list = [script.PASS]
            if requested_status:
                status_list = _get_requested_status(requested_status)
            return [
                _generate_result_obj(
                    [
                        status,  # result
                        result_props[1][0],  # msg
                        result_props[2][0],  # headers
                        result_props[3][0],  # data
                        result_props[4][0],  # unformatted_headers
                        result_props[5][0],  # unformatted_data
                        result_props[6][1],  # recommended_action
                        result_props[7][1],  # doc_url
                    ]
                )
                for status in status_list
            ]
        elif profile == "only_msg":
            # Only msg (mainly for PASS, NA, MANUAL, POST, ERROR)
            status_list = [script.PASS, script.NA, script.MANUAL, script.POST, script.ERROR]
            if requested_status:
                status_list = _get_requested_status(requested_status)
            return [
                _generate_result_obj(
                    [
                        status,  # result
                        result_props[1][1],  # msg
                        result_props[2][0],  # headers
                        result_props[3][0],  # data
                        result_props[4][0],  # unformatted_headers
                        result_props[5][0],  # unformatted_data
                        result_props[6][0],  # recommended_action
                        result_props[7][0],  # doc_url
                    ]
                )
                for status in status_list
            ]
        elif profile == "only_long_msg":
            # Only long msg (mainly for NA and ERROR)
            status_list = [script.NA, script.ERROR]
            if requested_status:
                status_list = _get_requested_status(requested_status)
            return [
                _generate_result_obj(
                    [
                        status,  # result
                        result_props[1][2],  # msg
                        result_props[2][0],  # headers
                        result_props[3][0],  # data
                        result_props[4][0],  # unformatted_headers
                        result_props[5][0],  # unformatted_data
                        result_props[6][0],  # recommended_action
                        result_props[7][0],  # doc_url
                    ]
                )
                for status in status_list
            ]
        else:
            raise ValueError("Unexpected profile - {}".format(profile))

    return _result_objects_factory


@pytest.fixture(scope="session")
def check_factory():
    def _check_factory(check_id, check_title, result_obj):
        @script.check_wrapper(check_title=check_title)
        def _check(**kwargs):
            if result_obj.result == script.ERROR:
                raise Exception(result_obj.msg)
            else:
                return result_obj

        _check.__name__ = check_id  # Set the function name for the check
        return _check
    return _check_factory


@pytest.fixture(scope="session")
def check_funcs_factory(check_factory):
    def _check_funcs_factory(result_objects):
        check_funcs = []
        for idx, result_obj in enumerate(result_objects):
            check_id = "fake_{}_check".format(idx)
            check_title = "Fake Check {}".format(idx)
            check_func = check_factory(check_id, check_title, result_obj)
            check_funcs.append(check_func)
        return check_funcs

    return _check_funcs_factory
