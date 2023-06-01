import os
import sys
import pytest
import importlib

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
sys.path.append(PROJECT_DIR)

script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("10.0.0.1", "00001010000000000000000000000001"),
        ("10.255.200.99", "00001010111111111100100001100011"),
        ("172.16.10.123", "10101100000100000000101001111011"),
        ("172.17.0.1", "10101100000100010000000000000001"),
        ("172.17.10.123", "10101100000100010000101001111011"),
        ("192.168.1.1", "11000000101010000000000100000001"),
    ],
)
def test_ip_to_binary(ip, expected):
    result = script.IPAddress.ip_to_binary(ip)
    assert result == expected


@pytest.mark.parametrize(
    "ip, pfxlen, expected",
    [
        ("10.0.0.1", 8, "00001010"),
        ("10.255.200.99", 12, "000010101111"),
        ("172.16.10.123", 16, "1010110000010000"),
        ("172.17.0.1", 24, "101011000001000100000000"),
        ("172.17.10.123", 28, "1010110000010001000010100111"),
        ("192.168.1.1", 30, "110000001010100000000001000000"),
    ],
)
def test_get_network_binary(ip, pfxlen, expected):
    result = script.IPAddress.get_network_binary(ip, pfxlen)
    assert result == expected


@pytest.mark.parametrize(
    "ip, subnet, expected",
    [
        ("10.0.0.1", "172.17.0.1/16", False),
        ("10.0.0.1", "172.17.0.10/16", False),
        ("172.17.0.1", "172.17.0.10/16", True),
        ("172.17.0.1", "172.18.0.1/16", False),
        ("172.17.0.1", "172.17.0.1/24", True),
        ("172.17.0.1", "172.17.1.1/24", False),
    ],
)
def test_ip_in_subnet(ip, subnet, expected):
    result = script.IPAddress.ip_in_subnet(ip, subnet)
    assert result == expected
