#!/usr/bin/env python3
"""Publish a validated actual-version snapshot to the internal results repo."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import quote, urlsplit


ACTUAL_JOB = "test:integration:actual-current-version"
FILES = ("results.log", "results.tgz")


def read_manifest(directory):
    with (Path(directory) / "manifest.json").open() as source:
        manifest = json.load(source)
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported results manifest")
    fabrics = manifest.get("fabrics")
    if not isinstance(fabrics, list) or not fabrics:
        raise ValueError("Results must include the expected fabrics")
    folders = set()
    for fabric in fabrics:
        folder = fabric.get("directory", "")
        if (
            not isinstance(folder, str)
            or not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*", folder)
            or folder.lower() in ("readme.md", "manifest.json")
            or folder.lower() in folders
        ):
            raise ValueError("Invalid or duplicate fabric directory")
        folders.add(folder.lower())
        if not isinstance(fabric.get("name"), str) or not fabric["name"]:
            raise ValueError("Fabric name is missing")
        if fabric.get("status") not in ("pending", "running", "completed", "failed"):
            raise ValueError("Invalid fabric status")
        if not isinstance(fabric.get("errors"), list) or any(
            not isinstance(error, str) for error in fabric["errors"]
        ):
            raise ValueError("Invalid fabric errors")
    return manifest


def validate_source(manifest, environment):
    if environment.get("INTEGRATION_CHECK"):
        raise ValueError("Focused runs cannot publish release-review results")
    if any(manifest.get(key) for key in ("debug_function", "cversion", "tversion")):
        raise ValueError("Only full actual-version results may be published")
    if manifest.get("source_job_name") != ACTUAL_JOB:
        raise ValueError("Results did not originate from the actual-version job")
    for field, variable in (
        ("source_commit", "CI_COMMIT_SHA"),
        ("source_pipeline_id", "CI_PIPELINE_ID"),
        ("source_project_id", "CI_PROJECT_ID"),
    ):
        expected = environment.get(variable)
        if not expected or str(manifest.get(field)) != expected:
            raise ValueError("Results provenance mismatch: " + field)


def validator_result(report):
    """Read the validator's summary; keep check errors distinct from FAIL findings."""
    result = {"status": "not_available", "error_count": None, "fail_count": None,
              "error_checks": [], "fail_checks": []}
    if not report.is_file():
        return result
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", report.read_text(encoding="utf-8", errors="replace"))
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines)
              if re.match(r"^\[Check\s+\d+/\d+\]", line)]
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        name = re.sub(r"^\[Check\s+\d+/\d+\]\s*", "", lines[start]).split("...", 1)[0].strip()
        # Some checks print several lines before their final result marker.
        for line in lines[start:end]:
            if re.search(r"ERROR\s*!!\s*$", line):
                result["error_checks"].append({"check": name, "line": start + 1})
                break
            if re.search(r"FAIL - (?:OUTAGE WARNING|UPGRADE FAILURE)!!\s*$", line):
                result["fail_checks"].append({"check": name, "line": start + 1})
                break
    summaries = text.split("=== Summary Result ===")
    result["status"] = "unknown"
    if len(summaries) != 2:
        return result
    errors = re.findall(r"^ERROR\s*!!\s*:\s*(\d+)\s*$", summaries[1], re.MULTILINE)
    failures = re.findall(r"^FAIL - (?:OUTAGE WARNING|UPGRADE FAILURE)!!\s*:\s*(\d+)\s*$", summaries[1], re.MULTILINE)
    if len(errors) != 1 or len(failures) != 2:
        return result
    error_count, fail_count = int(errors[0]), sum(map(int, failures))
    if error_count != len(result["error_checks"]) or fail_count != len(result["fail_checks"]):
        return result
    result.update(error_count=error_count, fail_count=fail_count,
                  status="check_errors" if error_count else "check_fails" if fail_count else "no_errors_or_fail_findings")
    return result


def markdown_label(value):
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("[", "\\[").replace("]", "\\]")


def count_link(result, category, folder=""):
    count = result[category + "_count"]
    if count is None:
        return "Not available" if result["status"] == "not_available" else "Unknown"
    checks = result[category + "_checks"]
    if count and checks:
        prefix = quote(folder) + "/" if folder else ""
        return "[{}]({}results.log#L{})".format(count, prefix, checks[0]["line"])
    return str(count)


def fabric_readme(fabric, manifest, errors, result, links):
    lines = [
        "# " + markdown_label(fabric["name"]), "",
        "- GitLab pipeline: {}".format(manifest["source_pipeline_id"]),
        "- Script commit: `{}`".format(manifest["source_commit"]),
        "- Run date: {}".format(manifest.get("created_at", "")), "",
        "| Integration / collection | Validator check errors | Validator check FAILs |",
        "| --- | --- | --- |",
        "| {} | {} | {} |".format("Failed" if errors else "Completed", count_link(result, "error"), count_link(result, "fail")), "",
        "Files: " + " · ".join(links), "",
    ]
    if errors:
        lines.extend(["## Integration test failures", ""])
        lines.extend("- " + markdown_label(error) for error in errors)
        lines.append("")
    if result["status"] == "unknown":
        lines.extend(["The validator summary is missing or could not be reconciled with its check results. Review the log; unknown does not mean zero errors.", ""])
    for title, category in (("Validator check errors", "error"), ("Validator check FAILs", "fail")):
        if result[category + "_checks"]:
            lines.extend(["## " + title, ""])
            lines.extend("- [{}](results.log#L{})".format(markdown_label(check["check"]), check["line"]) for check in result[category + "_checks"])
            lines.append("")
    return "\n".join(lines)


def prepare_snapshot(source, destination, environment):
    source, destination = Path(source), Path(destination)
    manifest = read_manifest(source)
    validate_source(manifest, environment)
    destination.mkdir()
    rows = []
    for fabric in manifest["fabrics"]:
        folder = fabric["directory"]
        origin = source / folder
        if origin.is_symlink() or not origin.is_dir():
            raise ValueError("Fabric results directory is missing or unsafe")
        output = destination / folder
        output.mkdir()
        errors = list(fabric["errors"])
        links = []
        for filename in FILES:
            artifact = origin / filename
            if artifact.is_symlink():
                raise ValueError("Results artifacts cannot be symlinks")
            if artifact.exists():
                if not artifact.is_file() or artifact.stat().st_size == 0:
                    raise ValueError("Invalid artifact: " + folder + "/" + filename)
                if artifact.stat().st_size >= 100 * 1024 * 1024:
                    raise ValueError("Artifact exceeds GitHub's Git file size limit")
                shutil.copyfile(str(artifact), str(output / filename))
                links.append("[{}]({}/{})".format(filename, quote(folder), filename))
            else:
                errors.append("{} was not collected during this run.".format(filename))
        if fabric["status"] in ("pending", "running"):
            errors.append("Integration run did not finish for this fabric.")
        elif fabric["status"] == "failed" and not errors:
            errors.append("Integration failed without additional diagnostics.")
        if errors:
            (output / "error.txt").write_text(
                "Integration test failure\nPipeline: {}\nScript commit: {}\nRun date: {}\n\n{}\n".format(
                    manifest["source_pipeline_id"], manifest["source_commit"],
                    manifest.get("created_at", ""), "\n".join(errors)), encoding="utf-8"
            )
            links.append("[error.txt]({}/error.txt)".format(quote(folder)))
        result = validator_result(output / "results.log")
        fabric.update(integration_status="failed" if errors else "completed",
                      integration_errors=errors, validator_result=result)
        local_links = [link.replace("(" + quote(folder) + "/", "(") for link in links]
        (output / "README.md").write_text(fabric_readme(fabric, manifest, errors, result, local_links), encoding="utf-8")
        links.insert(0, "[summary]({}/README.md)".format(quote(folder)))
        rows.append(
            "| [{}]({}/README.md) | {} | {} | {} | {} |".format(
                markdown_label(fabric["name"]), quote(folder),
                "Failed" if errors else "Completed",
                count_link(result, "error", folder), count_link(result, "fail", folder),
                " · ".join(links),
            )
        )
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    fabrics = manifest["fabrics"]
    integration_failures = sum(fabric["integration_status"] == "failed" for fabric in fabrics)
    validator_errors = [fabric for fabric in fabrics if fabric["validator_result"]["error_count"]]
    check_fails = [fabric for fabric in fabrics if fabric["validator_result"]["fail_count"]]
    unavailable = sum(fabric["validator_result"]["status"] in ("unknown", "not_available") for fabric in fabrics)
    readme = [
        "# ACI PUV Integration Results",
        "",
        "Latest full actual-version integration snapshot for release review.",
        "",
        "- Script commit: `{}`".format(manifest["source_commit"]),
        "- Script branch: `{}`".format(manifest.get("source_branch", "")),
        "- GitLab pipeline: {}".format(manifest["source_pipeline_id"]),
        "- Actual-version job: {}".format(manifest.get("source_job_id", "")),
        "- Run date: {}".format(manifest.get("created_at", "")),
        "",
        "## Run summary",
        "",
        "- Integration / collection failures: **{} / {} fabrics**".format(integration_failures, len(fabrics)),
        "- Validator check errors: **{}** across **{} fabric{}**".format(sum(fabric["validator_result"]["error_count"] for fabric in validator_errors), len(validator_errors), "" if len(validator_errors) == 1 else "s"),
        "- Validator check FAILs: **{} FAILs across {} fabrics**".format(sum(fabric["validator_result"]["fail_count"] for fabric in check_fails), len(check_fails)),
        "- Validator summaries unavailable or unknown: **{} fabrics** (excluded from validator totals)".format(unavailable),
        "",
        "Integration / collection status describes execution and artifact collection. "
        "Validator check errors (`ERROR !!`) and validator check FAILs (`FAIL`) are shown separately; "
        "completed does not mean upgrade-ready. Missing or unrecognized summaries are not counted as zero.",
        "",
    ]
    if validator_errors:
        readme.extend(["### Fabrics with validator check errors", ""])
        readme.extend("- [{}]({}/README.md): **{} check error{}**".format(
            markdown_label(fabric["name"]), quote(fabric["directory"]), fabric["validator_result"]["error_count"],
            "" if fabric["validator_result"]["error_count"] == 1 else "s")
            for fabric in validator_errors)
        readme.append("")
    readme.extend([
        "| Fabric | Integration / collection | Validator check errors | Validator check FAILs | Files |",
        "| --- | --- | --- | --- | --- |",
    ])
    readme.extend(rows)
    readme.extend(
        [
            "",
            "After review, create a GitHub release tagging this exact results "
            "commit. Subsequent publications replace the current snapshot and "
            "preserve previously tagged results.",
            "",
        ]
    )
    (destination / "README.md").write_text("\n".join(readme), encoding="utf-8")
    return manifest


def install_snapshot(snapshot, checkout, environment):
    """Replace only folders owned by the preceding manifest, preserving repo metadata."""
    checkout, snapshot = Path(checkout), Path(snapshot)
    current = read_manifest(snapshot)
    previous_folders = set()
    if (checkout / "manifest.json").exists():
        previous = read_manifest(checkout)
        if str(previous.get("source_project_id")) == environment[
            "CI_PROJECT_ID"
        ] and int(previous["source_pipeline_id"]) > int(environment["CI_PIPELINE_ID"]):
            raise ValueError("Refusing to replace a newer pipeline's results")
        previous_folders = {fabric["directory"] for fabric in previous["fabrics"]}
    for fabric in current["fabrics"]:
        target = checkout / fabric["directory"]
        if target.exists() and fabric["directory"] not in previous_folders:
            raise ValueError(
                "Fabric folder would overwrite unmanaged repository content"
            )
    for folder in previous_folders:
        target = checkout / folder
        if target.is_symlink():
            raise ValueError("Previous results folder cannot be a symlink")
        if target.exists():
            shutil.rmtree(str(target))
    for item in snapshot.iterdir():
        target = checkout / item.name
        if item.is_dir():
            shutil.copytree(str(item), str(target))
        else:
            shutil.copyfile(str(item), str(target))


def git(arguments, environment, cwd=None):
    return subprocess.run(
        ["git"] + arguments,
        env=environment,
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    ).stdout.strip()


def destination(environment):
    repository = environment.get("RESULTS_GITHUB_REPOSITORY", "")
    parsed = urlsplit(repository)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or len(parsed.path.strip("/").split("/")) != 2
    ):
        raise ValueError(
            "RESULTS_GITHUB_REPOSITORY must be an HTTPS repository URL without credentials"
        )
    return repository, environment.get("RESULTS_GITHUB_BRANCH", "master")


def publish(source, environment):
    if not environment.get("RESULTS_GITHUB_TOKEN"):
        raise ValueError(
            "RESULTS_GITHUB_TOKEN is unavailable. Add it to GitLab CI/CD variables; "
            "if protected, run publication from a protected branch or tag."
        )
    repository, branch = destination(environment)
    with tempfile.TemporaryDirectory(prefix="puv-results-") as temporary:
        root = Path(temporary)
        snapshot, checkout = root / "snapshot", root / "repository"
        manifest = prepare_snapshot(source, snapshot, environment)
        askpass = root / "askpass.sh"
        askpass.write_text('#!/bin/sh\ncase "$1" in\n*Username*) printf \'%s\\n\' x-access-token ;;\n*) printf \'%s\\n\' "$RESULTS_GITHUB_TOKEN" ;;\nesac\n')
        askpass.chmod(0o700)
        git_environment = dict(
            environment,
            GIT_ASKPASS=str(askpass),
            GIT_TERMINAL_PROMPT="0",
            GIT_CONFIG_COUNT="1",
            GIT_CONFIG_KEY_0="credential.helper",
            GIT_CONFIG_VALUE_0="",
        )
        git(
            ["clone", "--depth", "1", "--branch", branch, repository, str(checkout)],
            git_environment,
        )
        install_snapshot(snapshot, checkout, environment)
        git(["add", "--all", "--force"], git_environment, str(checkout))
        if not git(["diff", "--cached", "--name-only"], git_environment, str(checkout)):
            print("This results snapshot is already published.")
            return
        git(
            [
                "-c",
                "user.name=ACI PUV Integration",
                "-c",
                "user.email=aci-puv-integration@users.noreply.github.com",
                "commit",
                "-m",
                "Publish actual-version results from pipeline {} ({})".format(
                    manifest["source_pipeline_id"], manifest["source_commit"][:12]
                ),
            ],
            git_environment,
            str(checkout),
        )
        git(["push", "origin", "HEAD:" + branch], git_environment, str(checkout))
        print("Published actual-version results to " + (repository[:-4] if repository.endswith(".git") else repository))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="actual-version results artifact directory")
    args = parser.parse_args()
    try:
        publish(args.source, dict(os.environ))
    except subprocess.CalledProcessError:
        # Avoid echoing credential-helper or remote responses into CI logs.
        parser.exit(
            1,
            "GitHub clone, commit or push failed; check credential access and branch rules.\n",
        )
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, "Results publication failed: {}\n".format(error))


if __name__ == "__main__":
    main()
