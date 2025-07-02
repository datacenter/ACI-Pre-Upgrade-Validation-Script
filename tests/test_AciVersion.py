import pytest
import importlib

script = importlib.import_module("aci-preupgrade-validation-script")


@pytest.mark.parametrize(
    "input, major1, major2, maint, patch1, patch2, version",
    [
        # APIC version format
        ("5.2(7f)", "5", "2", "7", "f", "", "5.2(7f)"),
        ("5.2.7f", "5", "2", "7", "f", "", "5.2(7f)"),
        ("5.2(7.123a)", "5", "2", "7", "123", "a", "5.2(7.123a)"),
        ("5.2.7.123a", "5", "2", "7", "123", "a", "5.2(7.123a)"),
        ("5.2(7.123)", "5", "2", "7", "123", "", "5.2(7.123)"),
        ("5.2.7.123", "5", "2", "7", "123", "", "5.2(7.123)"),
        ("aci-apic-dk9.5.2.7f.iso", "5", "2", "7", "f", "", "5.2(7f)"),
        # Switch version format
        ("15.2(7f)", "5", "2", "7", "f", "", "5.2(7f)"),
        ("15.2.7f", "5", "2", "7", "f", "", "5.2(7f)"),
        ("15.2(7.123a)", "5", "2", "7", "123", "a", "5.2(7.123a)"),
        ("15.2.7.123a", "5", "2", "7", "123", "a", "5.2(7.123a)"),
        ("15.2(7.123)", "5", "2", "7", "123", "", "5.2(7.123)"),
        ("15.2.7.123", "5", "2", "7", "123", "", "5.2(7.123)"),
        ("aci-n9000-dk9.15.2.7f.bin", "5", "2", "7", "f", "", "5.2(7f)"),
    ],
)
def test_basic(input, major1, major2, maint, patch1, patch2, version):
    v = script.AciVersion(input)
    assert (
        v.major1 == major1
        and v.major2 == major2
        and v.maint == maint
        and v.patch1 == patch1
        and v.patch2 == patch2
    )
    assert str(v) == version


@pytest.mark.parametrize(
    "ver1, ver2, expected_result",
    [
        # APIC version format
        ("5.2(7f)", "5.2(7f)", "same"),
        ("5.2(7f)", "5.2(7g)", "old"),  # patch1
        ("5.2(7f)", "5.2(7e)", "new"),  # patch1
        ("5.2(7f)", "5.2(10f)", "old"),  # maint
        ("5.2(7f)", "5.2(1f)", "new"),  # maint
        ("5.2(7f)", "5.3(2a)", "old"),  # major2
        ("5.2(7f)", "5.1(2a)", "new"),  # major2
        ("5.2(7f)", "6.0(2h)", "old"),  # major1
        ("5.2(7f)", "4.2(7l)", "new"),  # major1
        ("5.2(7.123b)", "5.2(7.123b)", "same"),
        ("5.2(7.123b)", "5.2(7.123c)", "old"),  # QA patch2
        ("5.2(7.123b)", "5.2(7.123a)", "new"),  # QA patch2
        ("5.2(7.123b)", "5.2(7.124b)", "old"),  # QA patch1
        ("5.2(7.123b)", "5.2(7.90b)", "new"),  # QA patch1
        ("5.2(7.123)", "5.2(7.123)", "same"),
        ("5.2(7.123)", "5.2(7.124)", "old"),  # QA patch1
        ("5.2(7.123)", "5.2(7.90)", "new"),  # QA patch1
        ("5.2(7.123)", "5.2(7.123a)", "old"),  # None vs QA patch2
        ("5.2(7.123a)", "5.2(7.123)", "new"),  # QA patch2 vs None
        ("5.2(7f)", "5.2(7.90a)", "old"),   # CCO patch1 vs QA patch1
        ("5.2(7.90a)", "5.2(7f)", "new"),   # QA patch1 vs CCO patch1
        # Switch version format
        ("15.2(7f)", "15.2(7f)", "same"),
        ("15.2(7f)", "15.2(7g)", "old"),
        ("15.2(7f)", "15.2(7e)", "new"),
        ("15.2(7f)", "15.2(10f)", "old"),
        ("15.2(7f)", "15.2(1f)", "new"),
        ("15.2(7f)", "15.1(2a)", "new"),
        ("15.2(7f)", "15.3(2a)", "old"),
        ("15.2(7f)", "14.2(7l)", "new"),
        ("15.2(7f)", "16.0(2h)", "old"),
    ],
)
class TestComparison:
    def test_older_than(self, ver1, ver2, expected_result):
        result = True if expected_result == "old" else False
        v1 = script.AciVersion(ver1)
        v2 = script.AciVersion(ver2)
        assert v1.older_than(ver2) == result
        assert v1.older_than(v2) == result

    def test_newer_than(self, ver1, ver2, expected_result):
        result = True if expected_result == "new" else False
        v1 = script.AciVersion(ver1)
        v2 = script.AciVersion(ver2)
        assert v1.newer_than(ver2) == result
        assert v1.newer_than(v2) == result

    def test_same_as(self, ver1, ver2, expected_result):
        result = True if expected_result == "same" else False
        v1 = script.AciVersion(ver1)
        v2 = script.AciVersion(ver2)
        assert v1.same_as(ver2) == result
        assert v1.same_as(v2) == result


def test_invalid_version():
    with pytest.raises(ValueError):
        script.AciVersion("invalid_version")

    with pytest.raises(ValueError):
        script.AciVersion("5.2(7)")
