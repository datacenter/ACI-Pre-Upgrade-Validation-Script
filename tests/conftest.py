import os
import sys
import pytest
import logging
import importlib

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
sys.path.append(PROJECT_DIR)

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger()


@pytest.fixture(scope="session", autouse=True)
def init():
    script.initialize()


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


@pytest.fixture
def conn_failure():
    return False


@pytest.fixture
def conn_cmds():
    '''
    Set of test parameters for mocked `Connection.cmd()`.

    ex)
    ```
    {
        <apic_ip>: [{
            "cmd": "ls -aslh /firmware/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin",
            "output": """\
    ls -aslh /firmware/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin
    6.1G -rwxr-xr-x 1 root root 6.1G Apr  3 16:36 /firmware/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin
    f2-apic1#
    """,
            "exception": None
        }]
    }
    ```

    The real output from `Connection.cmd()` (i.e. `Connection.output`) contains many ANSI characters. In this fixture, those characters are not considered.
    '''
    return {}


class MockConnection(script.Connection):
    conn_failure = False
    conn_cmds = None

    def connect(self):
        """
        `Connection.connect()` is just instantiating `pexepect.spawn()` which does not
        initiate the SSH connection yet. Not exception likely happens here.
        """
        if self.conn_failure:
            raise Exception("Simulated exception at connect()")

    def cmd(self, command, **kargs):
        """
        `Connection.cmd()` initiates the SSH connection (if not done yet) and sends the command.
        Each check typically has multiple `cmd()` with different commands.
        To cover that, this mock func uses a dictionary `conn_cmds` as the test data.
        """
        _conn_cmds = self.conn_cmds[self.hostname]
        for conn_cmd in _conn_cmds:
            if command == conn_cmd["cmd"]:
                if conn_cmd["exception"]:
                    raise conn_cmd["exception"]
                self.output = conn_cmd["output"]
                break
        else:
            log.error("Command `%s` not found in test data `conn_cmds`", command)
            raise Exception("FAILURE IN PYTEST")


@pytest.fixture
def mock_conn(monkeypatch, conn_failure, conn_cmds):
    MockConnection.conn_failure = conn_failure
    MockConnection.conn_cmds = conn_cmds
    monkeypatch.setattr(script, "Connection", MockConnection)


@pytest.fixture
def cmd_outputs():
    """
    Mocked output for `run_cmd` function.
    This is used to avoid executing real commands in tests.
    """
    return {
        "ls -aslh /firmware/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin": {
            "splitlines": False,
            "output": "6.1G -rwxr-xr-x 1 root root 6.1G Apr  3 16:36 /firmware/fwrepos/fwrepo/aci-apic-dk9.6.0.5h.bin\napic1#",
        }
    }


@pytest.fixture
def mock_run_cmd(monkeypatch, cmd_outputs):
    """
    Mock the `run_cmd` function to avoid executing real commands.
    This is useful for tests that do not require actual command execution.
    """
    def _mock_run_cmd(cmd, splitlines=False):
        details = cmd_outputs.get(cmd)
        if details is None:
            log.error("Command `%s` not found in test data", cmd)
            return ""
        splitlines = details.get("splitlines", False)

        output = details.get("output")
        if output is None:
            log.error("Output for cmd `%s` not found in test data", cmd)
            output = ""

        log.debug("Mocked run_cmd called with args: %s, kwargs: %s", cmd, splitlines)
        if splitlines:
            return output.splitlines()
        else:
            return output
    monkeypatch.setattr(script, "run_cmd", _mock_run_cmd)
