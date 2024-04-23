import pytest
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.mark.parametrize(
    "input, major1, major2, maint, patch",
    [
        # APIC version format
        ("5.2(7f)", "5", "2", "7", "f"),
        ("5.2.7f", "5", "2", "7", "f"),
        ("5.2(7.123a)", "5", "2", "7", "123a"),
        ("5.2.7.123a", "5", "2", "7", "123a"),
        ("aci-apic-dk9.5.2.7f.iso", "5", "2", "7", "f"),
        # Switch version format
        ("15.2(7f)", "5", "2", "7", "f"),
        ("15.2.7f", "5", "2", "7", "f"),
        ("15.2(7.123a)", "5", "2", "7", "123a"),
        ("15.2.7.123a", "5", "2", "7", "123a"),
        ("aci-n9000-dk9.15.2.7f.bin", "5", "2", "7", "f"),
    ],
)
def test_basic(input, major1, major2, maint, patch):
    v = script.AciVersion(input)
    assert (
        v.major1 == major1
        and v.major2 == major2
        and v.maint == maint
        and v.patch == patch
    )


@pytest.mark.parametrize(
    "ver1, ver2, older_than, newer_than, same_as",
    [
        # APIC version format
        ("5.2(7f)", "5.2(7f)", False, False, True),
        ("5.2(7f)", "5.2(7g)", True, False, False),
        ("5.2(7f)", "5.2(7e)", False, True, False),
        ("5.2(7f)", "5.2(10f)", True, False, False),
        ("5.2(7f)", "5.2(1f)", False, True, False),
        ("5.2(7f)", "5.1(2a)", False, True, False),
        ("5.2(7f)", "5.3(2a)", True, False, False),
        ("5.2(7f)", "4.2(7l)", False, True, False),
        ("5.2(7f)", "6.0(2h)", True, False, False),
        # Switch version format
        ("15.2(7f)", "15.2(7f)", False, False, True),
        ("15.2(7f)", "15.2(7g)", True, False, False),
        ("15.2(7f)", "15.2(7e)", False, True, False),
        ("15.2(7f)", "15.2(10f)", True, False, False),
        ("15.2(7f)", "15.2(1f)", False, True, False),
        ("15.2(7f)", "15.1(2a)", False, True, False),
        ("15.2(7f)", "15.3(2a)", True, False, False),
        ("15.2(7f)", "14.2(7l)", False, True, False),
        ("15.2(7f)", "16.0(2h)", True, False, False),
    ],
)
class TestComparison:
    def test_older_than(self, ver1, ver2, older_than, newer_than, same_as):
        v = script.AciVersion(ver1)
        assert v.older_than(ver2) == older_than

    def test_newer_than(self, ver1, ver2, older_than, newer_than, same_as):
        v = script.AciVersion(ver1)
        assert v.newer_than(ver2) == newer_than

    def test_same_as(self, ver1, ver2, older_than, newer_than, same_as):
        v = script.AciVersion(ver1)
        assert v.same_as(ver2) == same_as
