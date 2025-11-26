import pytest
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")


# TimeoutError is only from py3.3
try:
    TimeoutError
except NameError:
    TimeoutError = script.TimeoutError


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
        # Query timeout (90 sec) - pre-4.1
        (
            [
                {
                    "error": {
                        "attributes": {
                            "code": "503",
                            "text": "Unable to deliver the message, Resolve timeout from (type/num/svc/shard) =  apic:1:7:1,  apic:1:7:32,  apic:1:7:31,  apic:1:7:30,  apic:1:7:13,  apic:1:7:12,  apic:1:7:11,  apic:1:7:10,  apic:1:7:9,  apic:1:7:8,  apic:1:7:7,  apic:1:7:3,  apic:1:7:14,  apic:1:7:15,  apic:1:7:16,  apic:1:7:17,  apic:1:7:18,  apic:1:7:19,  apic:1:7:20,  apic:1:7:21,  apic:1:7:22,  apic:1:7:23,  apic:1:7:24,  apic:1:7:25,  apic:1:7:26,  apic:1:7:27,  apic:1:7:28,  apic:1:7:29",
                        }
                    }
                }
            ],
            TimeoutError,
        ),
        # Query timeout (90 sec) - from-4.1
        (
            [
                {
                    "error": {
                        "attributes": {
                            "code": "503",
                            "text": "Unable to deliver the message, Resolve timeout",
                        }
                    }
                }
            ],
            TimeoutError,
        ),
    ],
)
def test_icurl_error_handler(imdata, expected_exception):
    with pytest.raises(expected_exception):
        script._icurl_error_handler(imdata)
