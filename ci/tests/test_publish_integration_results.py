import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

if sys.version_info[0] >= 3:
    import importlib.util
    from pathlib import Path
    from unittest.mock import patch

    spec = importlib.util.spec_from_file_location(
        "publish_results",
        str(Path(__file__).resolve().parents[1] / "publish_integration_results.py"),
    )
    publisher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(publisher)


@unittest.skipIf(sys.version_info[0] < 3, "Results publication uses Python 3")
class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.environment = dict(
            os.environ,
            CI_PROJECT_ID="123",
            CI_PIPELINE_ID="456",
            CI_COMMIT_SHA="a" * 40,
            RESULTS_GITHUB_TOKEN="fixture-token",
            RESULTS_GITHUB_REPOSITORY="https://github.example.test/example/results.git",
        )
        self.environment.pop("INTEGRATION_CHECK", None)
        self.manifest = {
            "schema_version": 1,
            "source_job_name": publisher.ACTUAL_JOB,
            "source_commit": "a" * 40,
            "source_project_id": "123",
            "source_pipeline_id": "456",
            "complete": True,
            "fabrics": [
                {
                    "name": "fabric-a",
                    "directory": "fabric-a",
                    "status": "completed",
                    "errors": [],
                }
            ],
        }
        folder = self.source / "fabric-a"
        folder.mkdir()
        (folder / "results.log").write_bytes(
            b"[Check 1/2] NTP Status... FAIL - UPGRADE FAILURE!!\n"
            b"=== Summary Result ===\n"
            b"FAIL - OUTAGE WARNING!! : 0\n"
            b"FAIL - UPGRADE FAILURE!! : 1\n"
            b"ERROR !! : 0\n"
        )
        (folder / "results.tgz").write_bytes(b"unchanged bundle")
        self.write_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def write_manifest(self):
        (self.source / "manifest.json").write_text(json.dumps(self.manifest))

    def prepare(self):
        target = self.root / "snapshot"
        publisher.prepare_snapshot(self.source, target, self.environment)
        return target

    def test_preserves_validator_artifacts_without_error_for_findings(self):
        snapshot = self.prepare()
        self.assertEqual(
            (snapshot / "fabric-a/results.log").read_bytes(),
            (self.source / "fabric-a/results.log").read_bytes(),
        )
        self.assertFalse((snapshot / "fabric-a/error.txt").exists())
        result = json.loads((snapshot / "manifest.json").read_text())["fabrics"][0]
        self.assertEqual(result["integration_status"], "completed")
        self.assertEqual(result["validator_result"]["error_count"], 0)
        self.assertEqual(result["validator_result"]["fail_count"], 1)

    def test_check_errors_are_separate_and_linked_without_integration_error_file(self):
        (self.source / "fabric-a/results.log").write_text(
            "[Check 1/2] APIC Database Size... ERROR !!\n"
            "[Check 2/2] APIC OOB Connectivity... diagnostic commands\n"
            "command output FAIL - UPGRADE FAILURE!!\n"
            "=== Summary Result ===\n"
            "FAIL - OUTAGE WARNING!! : 0\n"
            "FAIL - UPGRADE FAILURE!! : 1\n"
            "ERROR !! : 1\n"
        )
        snapshot = self.prepare()
        record = json.loads((snapshot / "manifest.json").read_text())["fabrics"][0]
        self.assertEqual(record["integration_status"], "completed")
        self.assertEqual(record["validator_result"]["status"], "check_errors")
        self.assertEqual(record["validator_result"]["error_count"], 1)
        self.assertEqual(record["validator_result"]["fail_count"], 1)
        self.assertFalse((snapshot / "fabric-a/error.txt").exists())
        self.assertIn("results.log#L1", (snapshot / "fabric-a/README.md").read_text())
        self.assertIn("results.log#L2", (snapshot / "fabric-a/README.md").read_text())
        self.assertIn("Validator check errors: **1** across **1 fabric**", (snapshot / "README.md").read_text())

    def test_unknown_validator_summary_does_not_claim_zero_errors(self):
        for report in (
            "[Check 1/2] Example... ERROR !!\n",
            "[Check 1/2] Example... ERROR !!\n=== Summary Result ===\n"
            "ERROR !! : 0\nFAIL - OUTAGE WARNING!! : 0\nFAIL - UPGRADE FAILURE!! : 0\n",
        ):
            (self.source / "fabric-a/results.log").write_text(report)
            result = publisher.validator_result(self.source / "fabric-a/results.log")
            self.assertEqual(result["status"], "unknown")
            self.assertIsNone(result["error_count"])
        snapshot = self.prepare()
        self.assertIn("Unknown", (snapshot / "fabric-a/README.md").read_text())

    def test_identical_connection_failure_has_new_per_fabric_provenance(self):
        for filename in publisher.FILES:
            (self.source / "fabric-a" / filename).unlink()
        self.manifest["fabrics"][0].update(status="failed", errors=["Socket Timeout Error"])
        self.write_manifest()
        first = self.prepare()
        self.environment["CI_PIPELINE_ID"] = "457"
        self.manifest["source_pipeline_id"] = "457"
        self.write_manifest()
        second = self.root / "second"
        publisher.prepare_snapshot(self.source, second, self.environment)
        for filename in ("README.md", "error.txt"):
            self.assertNotEqual((first / "fabric-a" / filename).read_bytes(),
                                (second / "fabric-a" / filename).read_bytes())
        record = json.loads((second / "manifest.json").read_text())["fabrics"][0]
        self.assertEqual(record["integration_status"], "failed")
        self.assertEqual(record["validator_result"]["status"], "not_available")

    def test_optional_auth_failure_has_folder_and_error_without_fake_log(self):
        self.manifest["fabrics"].append(
            {
                "name": "lossy",
                "directory": "lossy",
                "status": "failed",
                "errors": ["SSH Authentication Error: denied"],
                "connection_required": False,
            }
        )
        (self.source / "lossy").mkdir()
        self.write_manifest()
        snapshot = self.prepare()
        self.assertIn(
            "SSH Authentication Error", (snapshot / "lossy/error.txt").read_text()
        )
        self.assertFalse((snapshot / "lossy/results.log").exists())

    def test_incomplete_run_keeps_available_artifacts_and_marks_error(self):
        self.manifest["complete"] = False
        self.manifest["fabrics"][0]["status"] = "running"
        (self.source / "fabric-a/results.log").unlink()
        self.write_manifest()
        snapshot = self.prepare()
        self.assertTrue((snapshot / "fabric-a/results.tgz").exists())
        self.assertIn("did not finish", (snapshot / "fabric-a/error.txt").read_text())

    def test_rejects_wrong_pipeline_focused_and_override_runs(self):
        for key, value in (
            ("source_pipeline_id", "455"),
            ("debug_function", "one_check"),
            ("source_job_name", "test:integration:override"),
            ("cversion", "5.2(4d)"),
        ):
            with self.subTest(key=key):
                modified = dict(self.manifest)
                modified[key] = value
                with self.assertRaises(ValueError):
                    publisher.validate_source(modified, self.environment)

    def test_rejects_symlink_artifacts_and_directory_traversal(self):
        (self.source / "fabric-a/results.log").unlink()
        (self.source / "fabric-a/results.log").symlink_to(
            self.source / "fabric-a/results.tgz"
        )
        with self.assertRaises(ValueError):
            self.prepare()
        self.manifest["fabrics"][0]["directory"] = "../outside"
        self.write_manifest()
        with self.assertRaises(ValueError):
            publisher.read_manifest(self.source)

    def test_replacement_removes_old_fabrics_and_stale_errors_preserves_metadata(self):
        snapshot = self.prepare()
        checkout = self.root / "checkout"
        shutil.copytree(str(snapshot), str(checkout))
        (checkout / "fabric-a/error.txt").write_text("previous failure")
        previous = json.loads((checkout / "manifest.json").read_text())
        previous["fabrics"].append(
            {
                "name": "old",
                "directory": "old",
                "status": "failed",
                "errors": ["timeout"],
            }
        )
        (checkout / "old").mkdir()
        (checkout / "manifest.json").write_text(json.dumps(previous))
        (checkout / "LICENSE").write_text("keep")
        publisher.install_snapshot(snapshot, checkout, self.environment)
        self.assertFalse((checkout / "old").exists())
        self.assertFalse((checkout / "fabric-a/error.txt").exists())
        self.assertEqual((checkout / "LICENSE").read_text(), "keep")

    def test_older_pipeline_cannot_replace_newer_snapshot(self):
        snapshot = self.prepare()
        checkout = self.root / "checkout"
        shutil.copytree(str(snapshot), str(checkout))
        previous = json.loads((checkout / "manifest.json").read_text())
        previous["source_pipeline_id"] = "457"
        (checkout / "manifest.json").write_text(json.dumps(previous))
        with self.assertRaisesRegex(ValueError, "newer pipeline"):
            publisher.install_snapshot(snapshot, checkout, self.environment)
        self.assertEqual(
            json.loads((checkout / "manifest.json").read_text())["source_pipeline_id"],
            "457",
        )

    def test_destination_requires_https_repository_without_credentials(self):
        for repository in (
            "", "http://github.example.test/example/results.git",
            "https://token@github.example.test/example/results.git",
            "https://github.example.test/example/results.git?token=secret",
            "https://github.example.test/example/results.git#secret",
        ):
            with self.subTest(repository=repository):
                with self.assertRaises(ValueError):
                    publisher.destination(dict(self.environment, RESULTS_GITHUB_REPOSITORY=repository))
        environment = dict(self.environment, RESULTS_GITHUB_BRANCH="review")
        self.assertEqual(
            publisher.destination(environment),
            (self.environment["RESULTS_GITHUB_REPOSITORY"], "review"),
        )

    def test_credential_helper_executes_without_embedding_token(self):
        def fake_git(arguments, environment, cwd=None):
            helper = Path(environment["GIT_ASKPASS"])
            self.assertNotIn("fixture-token", helper.read_text())
            username = subprocess.check_output(
                [str(helper), "Username for HTTPS:"], env=environment
            )
            password = subprocess.check_output(
                [str(helper), "Password for HTTPS:"], env=environment
            )
            self.assertEqual(username, b"x-access-token\n")
            self.assertEqual(password, b"fixture-token\n")
            if arguments[0] == "clone":
                Path(arguments[-1]).mkdir()
            return "README.md" if arguments[0] == "diff" else ""

        with patch.object(publisher, "git", side_effect=fake_git):
            publisher.publish(str(self.source), self.environment)

    @unittest.skipUnless(
        sys.version_info[0] >= 3 and shutil.which("git"),
        "Local Git publication fixture requires Git",
    )
    def test_publishes_to_local_git_and_retry_is_idempotent(self):
        remote, seed = self.root / "remote.git", self.root / "seed"
        subprocess.run(
            ["git", "init", "--bare", str(remote)], check=True, capture_output=True
        )
        subprocess.run(["git", "init", str(seed)], check=True, capture_output=True)
        (seed / "README.md").write_text("starter")
        subprocess.run(
            ["git", "-C", str(seed), "add", "."], check=True, capture_output=True
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(seed),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.test",
                "commit",
                "-m",
                "Initialize",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(seed), "push", str(remote), "HEAD:master"],
            check=True,
            capture_output=True,
        )
        with patch.object(publisher, "destination", return_value=(str(remote), "master")):
            publisher.publish(str(self.source), self.environment)
            first = subprocess.check_output(
                ["git", "--git-dir", str(remote), "rev-parse", "master"]
            )
            publisher.publish(str(self.source), self.environment)
            self.assertEqual(
                first,
                subprocess.check_output(
                    ["git", "--git-dir", str(remote), "rev-parse", "master"]
                ),
            )
        tree = subprocess.check_output(
            ["git", "--git-dir", str(remote), "ls-tree", "-r", "master"]
        )
        self.assertIn(b"fabric-a/results.log", tree)


if __name__ == "__main__":
    unittest.main()
