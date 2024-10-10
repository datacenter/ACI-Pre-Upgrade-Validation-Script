import pytest
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")

# icurl queries
fabricNodePEps = "fabricNodePEp.json"

data = [
    {
        "fabricNodePEp": {
            "attributes": {
                "dn": "uni/fabric/protpol/expgep-101-103/nodepep-101",
                "id": "101",
            }
        }
    },
    {
        "fabricNodePEp": {
            "attributes": {
                "dn": "uni/fabric/protpol/expgep-204-206/nodepep-206",
                "id": "206",
            }
        }
    },
    {
        "fabricNodePEp": {
            "attributes": {
                "dn": "uni/fabric/protpol/expgep-101-103/nodepep-103",
                "id": "103",
            }
        }
    },
    {
        "fabricNodePEp": {
            "attributes": {
                "dn": "uni/fabric/protpol/expgep-204-206/nodepep-204",
                "id": "204",
            }
        }
    },
]
long_data = data * 25000  # 100K entries
long_data_all = long_data * 2 + data


@pytest.mark.parametrize(
    "apitype, query, icurl_outputs, expected_result",
    [
        # option 1: test_data is imdata
        (
            "class",
            "fabricNodePEp.json",
            {"fabricNodePEp.json": data},
            data,
        ),
        # option 2: test_data is the whole response of an API query (totalCount + imdata)
        (
            "class",
            "fabricNodePEp.json",
            {"fabricNodePEp.json": {"totalCount": str(len(data)), "imdata": data}},
            data,
        ),
        # option 3: test_data is the bundle of API queries with multiple pages
        (
            "class",
            "fabricNodePEp.json",
            {
                "fabricNodePEp.json": [
                    {  # page 0
                        "totalCount": str(len(long_data_all)),
                        "imdata": long_data,
                    },
                    {  # page 1
                        "totalCount": str(len(long_data_all)),
                        "imdata": long_data,
                    },
                    {  # page 2
                        "totalCount": str(len(long_data_all)),
                        "imdata": data,
                    },
                ]
            },
            long_data_all,
        ),
    ],
)
def test_icurl(mock_icurl, apitype, query, expected_result):
    assert script.icurl(apitype, query) == expected_result


@pytest.mark.parametrize(
    "imdata, expected_exception",
    [
        # /api/class/faultInfo.json?query-target-filter=eq(faultInst.cod,"F2109")
        (
            [
                {
                    "error": {
                        "attributes": {
                            "code": "121",
                            "text": "Prop 'cod' not found in class 'faultInst' property table",
                        }
                    }
                }
            ],
            script.OldVerPropNotFound,
        ),
        # /api/class/faultInf.json?query-target-filter=eq(faultInst.code,"F2109")
        (
            [
                {
                    "error": {
                        "attributes": {
                            "code": "400",
                            "text": "Request failed, unresolved class for faultInf",
                        }
                    }
                }
            ],
            script.OldVerClassNotFound,
        ),
        # /api/class/faultInfo.json?query-target-filter=eq(faultIns.code,"F2109")
        (
            [
                {
                    "error": {
                        "attributes": {
                            "code": "122",
                            "text": "class faultIns not found",
                        }
                    }
                }
            ],
            script.OldVerClassNotFound,
        ),
    ],
)
def test_icurl_error_handler(imdata, expected_exception):
    with pytest.raises(expected_exception):
        script._icurl_error_handler(imdata)
