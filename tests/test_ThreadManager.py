from __future__ import print_function
import importlib
import time

script = importlib.import_module("aci-preupgrade-validation-script")


global_timeout = False


def task1(data=""):
    time.sleep(2.5)
    if not global_timeout:
        print("Thread task1: Finishing with data {}".format(data))


def task2(data=""):
    time.sleep(2.5)
    if not global_timeout:
        print("Thread task2: Finishing with data {}".format(data))


def task3(data=""):
    time.sleep(.7)
    if not global_timeout:
        print("Thread task3: Finishing with data {}".format(data))


def task4(data=""):
    time.sleep(5)
    if not global_timeout:
        print("Thread task4: Finishing with data {}".format(data))


def task5(data=""):
    time.sleep(5)
    if not global_timeout:
        print("Thread task5: Finishing with data {}".format(data))


def test_ThreadManager(capsys):
    global global_timeout
    tm = script.ThreadManager(
        funcs=[task1, task2, task3, task4, task5],
        common_kwargs={"data": "common_data"},
        monitor_timeout=1,
        max_threads=2,
        callback_on_timeout=lambda x: print("Timeout. Abort {}".format(x))
    )
    tm.start()
    tm.join()

    if tm.is_timeout():
        global_timeout = True

    expected_output = """\
Timeout. Abort task1
Timeout. Abort task2
Thread task2: Finishing with data common_data
"""
    captured = capsys.readouterr()
    assert captured.out == expected_output
