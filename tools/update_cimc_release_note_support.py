#!/usr/bin/env python
from __future__ import print_function

import argparse
import json
import os
import re
import stat
import sys
import tempfile

try:
    from html.parser import HTMLParser
    from urllib.request import Request, urlopen
except ImportError:
    from HTMLParser import HTMLParser
    from urllib2 import Request, urlopen


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SOURCE_CONFIG = os.path.join(
    PROJECT_DIR, "tools", "cimc_release_note_sources.json"
)
DEFAULT_OUTPUT = os.path.join(PROJECT_DIR, "aci-preupgrade-validation-script.py")
GENERATED_BLOCK_START = "# BEGIN GENERATED CIMC RELEASE NOTE SUPPORT"
GENERATED_BLOCK_END = "# END GENERATED CIMC RELEASE NOTE SUPPORT"
USER_AGENT = "ACI-Pre-Upgrade-Validation-Script CIMC support updater"

CIMC_VERSION_PATTERN = re.compile(
    r"(?P<version>\d+\.\d+(?:\(\d+(?:\.\d+)?[a-z]?\)|\.\d+(?:\.\d+)?))"
    r"\s*(?:\(recommended\)\s*)?"
    r"CIMC HUU ISO",
    re.IGNORECASE,
)
APIC_MODEL_PATTERN = re.compile(
    r"APIC-(?P<primary>[A-Z]\d+)(?:/(?P<secondary>[A-Z]\d+))?",
    re.IGNORECASE,
)


class ReleaseNoteTableParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.rows = []
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("p", "li") and self._cell is not None:
            self._cell.append("\n")
        elif tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append("".join(self._cell))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)

    def handle_entityref(self, name):
        if self._cell is not None:
            self._cell.append(" " if name == "nbsp" else "&{};".format(name))

    def handle_charref(self, name):
        if self._cell is not None:
            self._cell.append(" ")


def _clean_text(value):
    return re.sub(r"[ \t\r\f\v]+", " ", value.replace(u"\xa0", " ")).strip()


def _normalize_cimc_version(version):
    if "(" in version:
        return version

    parts = version.split(".")
    if len(parts) < 3:
        raise ValueError("Unsupported CIMC version format: {}".format(version))
    return "{}.{}({})".format(parts[0], parts[1], ".".join(parts[2:]))


def _extract_cimc_cell(html):
    parser = ReleaseNoteTableParser()
    parser.feed(html)
    parser.close()

    for row in parser.rows:
        if row and _clean_text(row[0]).lower() == "cimc huu iso":
            if len(row) < 2:
                raise ValueError("CIMC HUU ISO table row has no supported-release cell")
            return "\n".join(row[1:])

    raise ValueError("Unable to find the CIMC HUU ISO release-note table row")


def extract_cimc_support(html, ignored_unqualified_versions=()):
    support = {}
    ignored_unqualified_versions = set(ignored_unqualified_versions)
    found_ignored_versions = set()
    cimc_cell = _extract_cimc_cell(html)

    for raw_entry in re.split(u"[\n\u2022\u25cf]+", cimc_cell):
        entry = _clean_text(raw_entry)
        version_match = CIMC_VERSION_PATTERN.search(entry)
        if not version_match or "deferred release" in entry.lower():
            continue

        version = _normalize_cimc_version(version_match.group("version"))
        model_matches = list(APIC_MODEL_PATTERN.finditer(entry))
        if not model_matches:
            if version in ignored_unqualified_versions:
                found_ignored_versions.add(version)
                continue
            raise ValueError(
                "Unable to identify an APIC model in release-note entry: {}".format(
                    entry
                )
            )
        for model_match in model_matches:
            models = [
                model
                for model in model_match.groups()
                if model is not None
            ]
            for model in models:
                model = model.lower()
                model_key = "apic{}".format(model)
                versions = support.setdefault(model_key, [])
                if version not in versions:
                    versions.append(version)

    missing_ignored_versions = sorted(
        ignored_unqualified_versions - found_ignored_versions
    )
    if missing_ignored_versions:
        raise ValueError(
            "Configured unqualified CIMC versions were not found: {}".format(
                ", ".join(missing_ignored_versions)
            )
        )
    if not support:
        raise ValueError("No supported CIMC versions were extracted from the release notes")
    return support


def fetch_release_note(url, timeout=30):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    response = urlopen(request, timeout=timeout)
    try:
        body = response.read()
    finally:
        response.close()
    return body.decode("utf-8")


def load_sources(path):
    with open(path, "rb") as source_file:
        sources = json.loads(source_file.read().decode("utf-8"))
    if not isinstance(sources, dict) or not sources:
        raise ValueError("Source configuration must contain target-version definitions")
    for target_version, source in sources.items():
        if not isinstance(source, dict) or not source.get("url"):
            raise ValueError(
                "Source definition for {} must contain a URL".format(target_version)
            )
    return sources


def collect_support(sources, fetcher=fetch_release_note):
    support = {}
    for target_version in sorted(sources):
        source = sources[target_version]
        release_support = extract_cimc_support(
            fetcher(source["url"]),
            source.get("ignored_unqualified_versions", ()),
        )
        missing_models = sorted(
            set(source.get("expected_models", ())) - set(release_support)
        )
        if missing_models:
            raise ValueError(
                "{} release notes are missing expected models: {}".format(
                    target_version, ", ".join(missing_models)
                )
            )
        for model, minimum_versions in source.get(
            "minimum_versions_per_model", {}
        ).items():
            version_count = len(release_support.get(model, ()))
            if version_count < minimum_versions:
                raise ValueError(
                    "{} release notes yielded {} versions for {}; expected at least {}".format(
                        target_version, version_count, model, minimum_versions
                    )
                )
        for model in sorted(release_support):
            support[(target_version, model)] = tuple(release_support[model])
    return support


def render_generated_block(support):
    lines = [
        GENERATED_BLOCK_START,
        "# Generated by tools/update_cimc_release_note_support.py; do not edit manually.",
        "CIMC_RELEASE_NOTE_SUPPORT = {",
    ]
    for target_model in sorted(support):
        target_version, model = target_model
        lines.append('    ("{}", "{}"): ('.format(target_version, model))
        for version in support[target_model]:
            lines.append('        "{}",'.format(version))
        lines.append("    ),")
    lines.extend(["}", GENERATED_BLOCK_END])
    return "\n".join(lines)


def replace_generated_block(source, generated_block):
    if source.count(GENERATED_BLOCK_START) != 1 or source.count(GENERATED_BLOCK_END) != 1:
        raise ValueError("Expected exactly one generated CIMC support block")

    start = source.index(GENERATED_BLOCK_START)
    end = source.index(GENERATED_BLOCK_END, start) + len(GENERATED_BLOCK_END)
    return source[:start] + generated_block + source[end:]


def read_text(path):
    with open(path, "rb") as input_file:
        return input_file.read().decode("utf-8")


def write_text_atomic(path, content):
    directory = os.path.dirname(path)
    file_mode = stat.S_IMODE(os.stat(path).st_mode)
    temp_file = tempfile.NamedTemporaryFile(
        prefix=".cimc-support-", dir=directory, delete=False
    )
    try:
        temp_file.write(content.encode("utf-8"))
        temp_file.close()
        os.chmod(temp_file.name, file_mode)
        os.rename(temp_file.name, path)
    finally:
        if not temp_file.closed:
            temp_file.close()
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


def update_support(source_config, output, check=False):
    sources = load_sources(source_config)
    generated_block = render_generated_block(collect_support(sources))
    current_source = read_text(output)
    updated_source = replace_generated_block(current_source, generated_block)

    if updated_source == current_source:
        print("CIMC release-note support is up to date.")
        return 0
    if check:
        print(
            "CIMC release-note support is stale. Run {}.".format(
                os.path.relpath(__file__, PROJECT_DIR)
            ),
            file=sys.stderr,
        )
        return 1

    write_text_atomic(output, updated_source)
    print("Updated CIMC release-note support in {}.".format(output))
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Refresh embedded CIMC support from Cisco APIC release notes."
    )
    parser.add_argument(
        "--source-config",
        default=DEFAULT_SOURCE_CONFIG,
        help="JSON definitions for target APIC release-note sources",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="standalone validator source to update",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="return a nonzero status instead of updating stale generated data",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        return update_support(args.source_config, args.output, args.check)
    except (IOError, ValueError) as error:
        print(
            "Unable to update CIMC release-note support: {}".format(error),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
