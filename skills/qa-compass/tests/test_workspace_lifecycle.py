import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import workspace_lifecycle  # noqa: E402


class WorkspaceLifecycleTests(unittest.TestCase):
    def test_detects_empty_and_initializes_workspace_v2(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            empty_state = workspace_lifecycle.detect_workspace(root)
            self.assertEqual(empty_state["layout"], "empty")

            state = workspace_lifecycle.init_workspace(root, project_name="Sample QA")

            self.assertEqual(state["layout"], "workspace_v2")
            self.assertEqual(state["schema_version"], workspace_lifecycle.WORKSPACE_SCHEMA_VERSION)
            self.assertTrue((root / "workspace-index.json").exists())
            self.assertTrue((root / "project-profile.json").exists())
            self.assertTrue((root / "03-generated" / "suites").is_dir())
            self.assertTrue((root / "03-generated" / "versions").is_dir())
            self.assertTrue((root / "runs").is_dir())
            self.assertTrue((root / "history" / "runs-index.json").exists())
            self.assertTrue((root / "history" / "case-history.json").exists())

            index = json.loads((root / "workspace-index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["project_name"], "Sample QA")
            self.assertEqual(index["active_test_cases"], "03-generated/test-cases.json")

    def test_migrates_legacy_single_run_without_regenerating_reusable_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "00-overview").mkdir()
            (root / "03-generated").mkdir()
            (root / "04-execution").mkdir()
            (root / "05-reports").mkdir()
            (root / "00-overview" / "project-summary.md").write_text("# Existing summary", encoding="utf-8")
            (root / "03-generated" / "test-cases.json").write_text('{"test_cases":[]}', encoding="utf-8")
            (root / "04-execution" / "execution-results.json").write_text('{"results":[]}', encoding="utf-8")
            (root / "05-reports" / "qa-report.internal.html").write_text("<html></html>", encoding="utf-8")

            state = workspace_lifecycle.migrate_legacy_workspace(
                root,
                project_name="Migrated QA",
                run_id="2026-04-30-smoke",
            )

            self.assertEqual(state["layout"], "workspace_v2")
            self.assertEqual(
                (root / "03-generated" / "test-cases.json").read_text(encoding="utf-8"),
                '{"test_cases":[]}',
            )
            self.assertFalse((root / "04-execution").exists())
            self.assertFalse((root / "05-reports").exists())
            self.assertTrue((root / "runs" / "2026-04-30-smoke" / "04-execution" / "execution-results.json").exists())
            self.assertTrue((root / "runs" / "2026-04-30-smoke" / "05-reports" / "qa-report.internal.html").exists())

            report = json.loads((root / "history" / "migration-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["source_layout"], "legacy_single_run")
            self.assertIn("04-execution", report["moved_paths"])
            self.assertIn("05-reports", report["moved_paths"])
            self.assertIn("03-generated/test-cases.json", report["reused_artifacts"])

    def test_create_run_workspace_appends_runs_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace_lifecycle.init_workspace(root, project_name="Repeatable QA")

            run = workspace_lifecycle.create_run_workspace(
                root,
                suite="smoke",
                mode="smoke",
                run_id="2026-05-01-smoke",
            )

            self.assertEqual(run["run_id"], "2026-05-01-smoke")
            self.assertTrue((root / "runs" / "2026-05-01-smoke" / "04-execution").is_dir())
            self.assertTrue((root / "runs" / "2026-05-01-smoke" / "05-reports").is_dir())
            self.assertTrue((root / "runs" / "2026-05-01-smoke" / "evidence").is_dir())
            self.assertTrue((root / "runs" / "2026-05-01-smoke" / "run-config.json").exists())

            runs_index = json.loads((root / "history" / "runs-index.json").read_text(encoding="utf-8"))
            self.assertEqual(runs_index["runs"][0]["run_id"], "2026-05-01-smoke")
            self.assertEqual(runs_index["runs"][0]["suite"], "smoke")
            self.assertEqual(runs_index["runs"][0]["mode"], "smoke")

    def test_update_case_history_records_latest_statuses(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace_lifecycle.init_workspace(root, project_name="History QA")
            workspace_lifecycle.create_run_workspace(root, suite="smoke", mode="smoke", run_id="2026-05-01-smoke")
            results_path = root / "runs" / "2026-05-01-smoke" / "04-execution" / "execution-results.json"
            results_path.write_text(
                json.dumps(
                    {
                        "results": [
                            {"test_case_id": "TC-1", "status": "Passed"},
                            {"test_case_id": "TC-2", "status": "Failed"},
                            {"test_case_id": "TC-3", "status": "Blocked"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            summary = workspace_lifecycle.update_case_history(root, run_id="2026-05-01-smoke", results_path=results_path)

            self.assertEqual(summary["updated"], 3)
            history = json.loads((root / "history" / "case-history.json").read_text(encoding="utf-8"))
            self.assertEqual(history["cases"]["TC-2"]["last_status"], "Failed")
            self.assertEqual(history["cases"]["TC-2"]["failed_count"], 1)
            self.assertEqual(history["cases"]["TC-3"]["blocked_count"], 1)
            self.assertEqual(history["cases"]["TC-1"]["last_run_id"], "2026-05-01-smoke")


if __name__ == "__main__":
    unittest.main()
