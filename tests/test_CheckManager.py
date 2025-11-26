import pytest
import importlib
import logging
import time
import json
import os

script = importlib.import_module("aci-preupgrade-validation-script")
AciVersion = script.AciVersion
AciResult = script.AciResult
Result = script.Result
CheckManager = script.CheckManager
check_wrapper = script.check_wrapper


# ----------------------------
# Fixtures, Helper Functions
# ----------------------------
def assert_aci_result_file_with_error(cm, check_id, check_title, msg):
    filepath = cm.rm.get_result_filepath(check_id)
    with open(filepath, "r") as f:
        aci_result = json.load(f)
    assert aci_result["ruleId"] == check_id
    assert aci_result["name"] == check_title
    assert aci_result["ruleStatus"] == AciResult.FAIL
    assert aci_result["severity"] == "major"
    assert aci_result["reason"] == msg
    assert aci_result["failureDetails"]["failType"] == script.ERROR


@pytest.fixture
def mock_generate_thread(monkeypatch, request):
    """Mock thread in ThreadManager to raise an exception in thread.start().

    This is to test exception handleing in ThreadManager._start_thread().
    """

    check_id = request.param.get("check_id")
    exception = request.param.get("exception")

    def thread_start_with_exception(timeout=5.0):
        raise exception

    def _mock_generate_thread(self, target, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        thread = script.CustomThread(target=target, name=target.__name__, args=args, kwargs=kwargs)
        thread.daemon = True
        # Mock only a specifieid thread instance. Otherwise, exception is raised in
        # the monitoring thread which doesn't use _start_thread().
        if thread.name == check_id:
            thread.start = thread_start_with_exception
        return thread

    monkeypatch.setattr(script.ThreadManager, "_generate_thread", _mock_generate_thread)


# ----------------------------
# Tests
# ----------------------------
class TestCheckManager:
    @pytest.fixture(scope="class")
    def expected_result_objects(self, result_objects_factory):
        return result_objects_factory("fullmesh")

    @pytest.fixture(scope="class")
    def check_funcs(self, check_funcs_factory, expected_result_objects):
        return check_funcs_factory(expected_result_objects)

    @pytest.fixture(scope="class")
    def cm(self, check_funcs):
        _cm = CheckManager()
        _cm.check_funcs = check_funcs
        return _cm

    def test_initialize_checks(self, caplog, cm):
        caplog.set_level(logging.CRITICAL)  # Skip logging as it's too noisy for this

        cm.initialize_checks()

        # With init, only titles should be available
        assert cm.get_check_title("fake_0_check") == "Fake Check 0"
        assert cm.get_check_title("fake_10_check") == "Fake Check 10"
        assert cm.get_check_result("fake_0_check") is None
        assert cm.get_check_result("fake_10_check") is None

        # Check number of initialized checks in result files
        result_files = os.listdir(script.JSON_DIR)
        assert len(result_files) == cm.total_checks

        # Check the filename of result files and their `ruleStatus`
        for check_id in cm.check_ids:
            filepath = cm.rm.get_result_filepath(check_id)
            assert os.path.exists(filepath), "Missing result file: {}".format(filepath)

            with open(filepath, "r") as f:
                aci_result = json.load(f)
            # At initialize, ruleStatus must be always in-progress
            assert aci_result["ruleStatus"] == AciResult.IN_PROGRESS

    def test_run_checks(self, caplog, cm, expected_common_data, expected_result_objects):
        caplog.set_level(logging.CRITICAL)  # Skip logging as it's too noisy for this

        cm.run_checks(expected_common_data)

        # With run_checks, both titles and result obj should be available
        assert cm.get_check_title("fake_0_check") == "Fake Check 0"
        assert cm.get_check_title("fake_10_check") == "Fake Check 10"
        assert cm.get_check_result("fake_0_check") is expected_result_objects[0]
        assert cm.get_check_result("fake_10_check") is expected_result_objects[10]

        # Check the result files
        for check_id in cm.check_ids:
            filepath = cm.rm.get_result_filepath(check_id)
            assert os.path.exists(filepath), "Missing result file: {}".format(filepath)

            with open(filepath, "r") as f:
                aci_result = json.load(f)
                assert aci_result["ruleId"] == check_id
                assert aci_result["name"] == cm.get_check_title(check_id)
                assert aci_result["ruleStatus"] in (AciResult.PASS, AciResult.FAIL)
                r = cm.get_check_result(check_id)

                # recommended_action: additional note is added with a certain condition
                if aci_result["ruleStatus"] == AciResult.FAIL and r.unformatted_headers and r.unformatted_data:
                    assert aci_result["recommended_action"].startswith(r.recommended_action + "\n Note")
                else:
                    assert aci_result["recommended_action"] == r.recommended_action

                # docUrl
                assert aci_result["docUrl"] == r.doc_url

                # failureDetails: matters only when ruleStatus is FAIL
                if aci_result["ruleStatus"] == AciResult.FAIL:
                    assert aci_result["failureDetails"]["failType"] == r.result
                    try:
                        data = AciResult.convert_data(r.headers, r.data)
                        assert aci_result["failureDetails"]["header"] == r.headers
                        assert aci_result["failureDetails"]["data"] == data
                    except Exception:
                        assert aci_result["failureDetails"]["failType"] == script.ERROR
                        assert aci_result["failureDetails"]["header"] == []
                        assert aci_result["failureDetails"]["data"] == []

                    if r.unformatted_headers and r.unformatted_data:
                        try:
                            unformatted_data = AciResult.convert_data(r.unformatted_headers, r.unformatted_data)
                            assert aci_result["failureDetails"]["unformatted_header"] == r.unformatted_headers
                            assert aci_result["failureDetails"]["unformatted_data"] == unformatted_data
                        except Exception:
                            assert aci_result["failureDetails"]["failType"] == script.ERROR
                            assert aci_result["failureDetails"]["unformatted_header"] == []
                            assert aci_result["failureDetails"]["unformatted_data"] == []


@pytest.mark.parametrize(
    "api_only, debug_function, expected_total",
    [
        (False, None, len(CheckManager.api_checks) + len(CheckManager.ssh_checks) + len(CheckManager.cli_checks)),
        (True, None, len(CheckManager.api_checks)),
        (False, CheckManager.api_checks[0].__name__, 1),
        (True, CheckManager.api_checks[0].__name__, 1),
        (False, CheckManager.ssh_checks[0].__name__, 1),
        (True, CheckManager.ssh_checks[0].__name__, 0),  # api_only for non-api check = 0
    ],
)
def test_total_checks(api_only, debug_function, expected_total):
    cm = CheckManager(api_only, debug_function)
    assert cm.total_checks == expected_total


def test_exception_in_initialize():
    """Exception in initialize is not captured by CheckManager.
    The exception should go up to the script's main() and abort the script
    because there is likely some fundamental issue in the system"""
    cm = CheckManager()
    cm.initialize_check = lambda x, y: 1 / 0  # Zero Division Error for a quick exception
    with pytest.raises(ZeroDivisionError):
        cm.initialize_checks()


def test_memerror_in_check():
    @check_wrapper(check_title="Memory Error Check")
    def memerr_check(**kwargs):
        raise MemoryError

    cm = CheckManager()
    cm.check_funcs = [memerr_check]
    cm.initialize_checks()
    cm.run_checks({"fake_common_data": True})

    assert_aci_result_file_with_error(
        cm, "memerr_check", "Memory Error Check", "Not enough memory to complete this check."
    )


def test_exception_in_check():
    @check_wrapper(check_title="Bad Check")
    def bad_check(**kwargs):
        raise Exception("This is a test exception")

    cm = CheckManager()
    cm.check_funcs = [bad_check]
    cm.initialize_checks()
    cm.run_checks({"fake_common_data": True})

    assert_aci_result_file_with_error(cm, "bad_check", "Bad Check", "Unexpected Error: This is a test exception")


def test_exception_in_finalize_check_due_to_bad_check():
    """Exceptions in `finalize_check` due to bad return value from each check.

    This exception happens in `try` of `check_wrapper`, but `finalize_check`
    in the corresponding `except` works as it calls `finalize_check` again
    with a valid `Result` object with status ERROR.
    """

    @check_wrapper(check_title="Non-Result Obj Check")
    def non_result_check(**kwargs):
        return "Not Result Obj"  # instead of `Result` obj

    @check_wrapper(check_title="Invalid Result Check")
    def invalid_result_check(**kwargs):
        # length of header and each row of data must be the same
        return Result(result=script.FAIL_O, headers=["H1", "H2"], data=[["D1"], ["D2"]])

    cm = CheckManager()
    cm.check_funcs = [non_result_check, invalid_result_check]
    cm.initialize_checks()
    cm.run_checks({"fake_common_data": True})

    checks = [
        {
            "id": "non_result_check",
            "title": "Non-Result Obj Check",
            "msg": "Unexpected Error: The result of non_result_check is not a `Result` object",
        },
        {
            "id": "invalid_result_check",
            "title": "Invalid Result Check",
            "msg": "Unexpected Error: Row length (1), data: ['D1'] does not match column length (2).",
        },
    ]
    for check in checks:
        assert_aci_result_file_with_error(cm, check["id"], check["title"], check["msg"])


def test_exception_in_finalize_check():
    """Exception in `finalize_check` itself.

    This could happen when the filesystem is full, permission denied to write
    the result file etc.
    """

    # Check exception is caught in try of check_wrapper, then finalize_check
    # fails in the corresponding except.
    @check_wrapper(check_title="Bad Check With Bad Finalizer")
    def bad_check_with_bad_finalizer(**kwargs):
        raise Exception("Bad check to test finalize_check failure")

    # Check is good but finalize_check failed in try of check_wrapper, then it
    # fails in the corresponding except again.
    @check_wrapper(check_title="Good Check With Bad Finalizer")
    def good_check_with_bad_finalizer(**kwargs):
        return Result(result=script.PASS)

    cm = CheckManager()
    cm.finalize_check = lambda x, y: 1 / 0  # Zero Division Error for a quick exception
    cm.check_funcs = [bad_check_with_bad_finalizer, good_check_with_bad_finalizer]
    cm.initialize_checks()
    with pytest.raises(ZeroDivisionError):
        cm.run_checks({"fake_common_data": True})


@pytest.mark.parametrize(
    "mock_generate_thread",
    [
        {"check_id": "good_check_with_thread_start_failure", "exception": RuntimeError("can't start new thread")},
        {"check_id": "good_check_with_thread_start_failure", "exception": RuntimeError("unknown runtime error")},
        {"check_id": "good_check_with_thread_start_failure", "exception": Exception("unknown exception")},
    ],
    indirect=True,
)
def test_exception_in_starting_thread(mock_generate_thread):
    @check_wrapper(check_title="Good Check With Failure in Starting Thread")
    def good_check_with_thread_start_failure(**kwargs):
        return Result(result=script.PASS)

    cm = CheckManager()
    cm.check_funcs = [good_check_with_thread_start_failure]
    cm.initialize_checks()
    cm.run_checks({"fake_common_data": True})

    assert_aci_result_file_with_error(
        cm,
        "good_check_with_thread_start_failure",
        "Good Check With Failure in Starting Thread",
        "Skipped due to a failure in starting a thread for this check.",
    )


@pytest.mark.parametrize(
    "mock_generate_thread",
    [
        {"check_id": "good_check_with_start_failure_and_exc_in_callback", "exception": Exception("unknown exception")},
    ],
    indirect=True,
)
def test_exception_in_finalize_check_on_thread_failure(mock_generate_thread):
    """Exception in failure callback. Should not catch the exception and let the script fail"""
    @check_wrapper(check_title="Good Check With Failure in Starting Thread")
    def good_check_with_start_failure_and_exc_in_callback(**kwargs):
        return Result(result=script.PASS)

    cm = CheckManager()
    cm.finalize_check_on_thread_failure = lambda x: 1 / 0  # Zero Division Error for a quick exception
    cm.check_funcs = [good_check_with_start_failure_and_exc_in_callback]
    cm.initialize_checks()
    with pytest.raises(ZeroDivisionError):
        cm.run_checks({"fake_common_data": True})


def test_monitor_timeout():
    @check_wrapper(check_title="Timeout Check")
    def timeout_check(**kwargs):
        time.sleep(60)

    timeout = 1  # sec
    cm = CheckManager(timeout=timeout)
    cm.check_funcs = [timeout_check]
    cm.initialize_checks()
    cm.run_checks({"fake_common_data": True})
    assert cm.timeout_event.is_set()

    assert_aci_result_file_with_error(
        cm, "timeout_check", "Timeout Check", "Timeout. Unable to finish in time ({} sec).".format(timeout)
    )


def test_exception_in_finalize_check_on_thread_timeout():
    """Exception in failure callback. Should not catch the exception and let the script fail"""
    @check_wrapper(check_title="Timeout Check")
    def timeout_check_with_exc_in_callback(**kwargs):
        time.sleep(60)

    timeout = 1  # sec
    cm = CheckManager(timeout=timeout)
    cm.finalize_check_on_thread_timeout = lambda x: 1 / 0  # Zero Division Error for a quick exception
    cm.check_funcs = [timeout_check_with_exc_in_callback]
    cm.initialize_checks()
    with pytest.raises(ZeroDivisionError):
        cm.run_checks({"fake_common_data": True})
    assert cm.timeout_event.is_set()
