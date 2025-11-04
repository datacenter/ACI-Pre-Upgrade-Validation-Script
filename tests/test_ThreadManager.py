from __future__ import print_function
import importlib
import time

script = importlib.import_module("aci-preupgrade-validation-script")


def task1(data=""):
    time.sleep(2.5)
    print("Thread task1: Finishing with data {}".format(data))


def task2(data=""):
    time.sleep(0.5)
    print("Thread task2: Finishing with data {}".format(data))


def task3(data=""):
    time.sleep(0.2)
    print("Thread task3: Finishing with data {}".format(data))


def test_ThreadManager(capsys):
    tm = script.ThreadManager(
        funcs=[task1, task2, task3],
        common_kwargs={"data": "common_data"},
        monitor_timeout=1,
        callback_on_timeout=lambda x: print("Timeout. Abort {}".format(x))
    )
    tm.start()
    tm.join()

    expected_output = """\
Thread task3: Finishing with data common_data
Thread task2: Finishing with data common_data
Timeout. Abort task1
"""
    captured = capsys.readouterr()
    assert captured.out == expected_output
