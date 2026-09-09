import pytest

from tools import update_cimc_release_note_support as updater


RELEASE_NOTE_HTML = """
<html>
  <body>
    <table>
      <tr><th>Product</th><th>Supported Release</th></tr>
      <tr>
        <td>CIMC HUU ISO</td>
        <td>
          <p>Note: Install only the CIMC versions mentioned here.</p>
          <p>6.0.2.260143 (recommended) CIMC HUU ISO for UCS C225 M8 (APIC-G5)</p>
          <p>4.3.6.250053 CIMC HUU ISO (recommended) for UCS C225 M6 (APIC-L4/M4)</p>
          <p>4.1(1g) CIMC HUU ISO for UCS C220/C240 M4 (APIC-L2/M2) and M5 (APIC-L3/M3)</p>
          <p>4.1(1d) CIMC HUU ISO for UCS C220 M5 (APIC-L3/M3)</p>
          <p>4.0(2g) CIMC HUU ISO for UCS C220/C240 M4 and M5 (APIC-L2/M2 and APIC-L3/M3)</p>
          <p>2.0(13i) CIMC HUU ISO</p>
          <p>4.1(2a) CIMC HUU ISO for UCS C220 M4 (APIC-L2/M2) (deferred release)</p>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def test_extract_cimc_support_maps_models_and_normalizes_versions():
    support = updater.extract_cimc_support(
        RELEASE_NOTE_HTML, ignored_unqualified_versions=["2.0(13i)"]
    )

    assert support["apicg5"] == ["6.0(2.260143)"]
    assert support["apicl4"] == ["4.3(6.250053)"]
    assert support["apicm4"] == ["4.3(6.250053)"]
    assert support["apicl3"] == ["4.1(1g)", "4.1(1d)", "4.0(2g)"]
    assert support["apicm3"] == ["4.1(1g)", "4.1(1d)", "4.0(2g)"]
    assert support["apicl2"] == ["4.1(1g)", "4.0(2g)"]
    assert support["apicm2"] == ["4.1(1g)", "4.0(2g)"]


def test_extract_cimc_support_rejects_missing_table():
    with pytest.raises(ValueError):
        updater.extract_cimc_support("<html><body>No compatibility table</body></html>")


def test_extract_cimc_support_rejects_unknown_unqualified_version():
    with pytest.raises(ValueError):
        updater.extract_cimc_support(RELEASE_NOTE_HTML)


def test_collect_support_rejects_model_specific_version_loss():
    sources = {
        "6.1(5)": {
            "url": "https://example.invalid/release-notes",
            "expected_models": ["apicl3"],
            "minimum_versions_per_model": {"apicl3": 4},
            "ignored_unqualified_versions": ["2.0(13i)"],
        }
    }

    with pytest.raises(ValueError):
        updater.collect_support(sources, fetcher=lambda url: RELEASE_NOTE_HTML)


def test_replace_generated_block_requires_exact_markers():
    with pytest.raises(ValueError):
        updater.replace_generated_block("CIMC_RELEASE_NOTE_SUPPORT = {}", "generated")


def test_render_generated_block_is_deterministic():
    support = {
        ("6.1(5)", "apicl3"): ("4.1(1g)", "4.1(1d)"),
        ("6.1(5)", "apicg5"): ("6.0(2.260143)",),
    }

    generated = updater.render_generated_block(support)

    assert generated.index('"apicg5"') < generated.index('"apicl3"')
    assert generated.index('"4.1(1g)"') < generated.index('"4.1(1d)"')
