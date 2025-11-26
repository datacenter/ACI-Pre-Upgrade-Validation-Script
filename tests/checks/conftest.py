import pytest
import logging
import importlib
from subprocess import CalledProcessError

script = importlib.import_module("aci-preupgrade-validation-script")

log = logging.getLogger()


@pytest.fixture
def run_check(request):
    def _run_check(**kwargs):
        test_function = getattr(request.module, "test_function")
        cm = script.CheckManager(debug_function=test_function, monitor_interval=0.01)
        cm.initialize_checks()

        err = "Unable to find test_function ({}) in CheckManager".format(test_function)
        assert test_function in cm.check_ids, err

        cm.run_checks(common_data=kwargs)

        result = cm.get_check_result(test_function)
        assert isinstance(result, script.Result)

        return result

    return _run_check


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
        if details.get("CalledProcessError"):
            raise CalledProcessError(127, cmd)

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
