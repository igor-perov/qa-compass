import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_run_diagnostics  # noqa: E402
import workspace_lifecycle  # noqa: E402


class RunDiagnosticsTests(unittest.TestCase):
    def test_builds_run_diagnostics_markdown_and_json_with_redacted_comments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace_lifecycle.init_workspace(root, project_name="Diagnostics QA")
            workspace_lifecycle.create_run_workspace(
                root,
                suite="smoke",
                mode="smoke",
                run_id="2026-05-01-smoke",
            )
            run_root = root / "runs" / "2026-05-01-smoke"
            execution_dir = run_root / "04-execution"
            reports_dir = run_root / "05-reports"
            (root / "00-overview" / "project-summary.md").write_text("# Project Summary", encoding="utf-8")
            (root / "03-generated" / "test-cases.json").write_text('{"test_cases":[]}', encoding="utf-8")
            (execution_dir / "qa-scope-preview.html").write_text("<html>preview</html>", encoding="utf-8")
            (execution_dir / "execution-results.json").write_text(
                json.dumps(
                    {
                        "environment": "https://staging.example.test",
                        "results": [
                            {"test_case_id": "TC-1", "status": "Passed"},
                            {"test_case_id": "TC-2", "status": "Failed"},
                            {"test_case_id": "TC-3", "status": "Blocked"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "run-summary.json").write_text(
                json.dumps(
                    {
                        "project_name": "Diagnostics QA",
                        "environment": "https://staging.example.test",
                        "subset_mode": "smoke",
                        "counts": {"executed": 3, "passed": 1, "failed": 1, "blocked": 1},
                        "defects": [{"test_case_id": "TC-2", "title": "Failure"}],
                        "blocked_cases": [{"test_case_id": "TC-3", "title": "Blocked"}],
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "qa-report.internal.html").write_text("<html>internal</html>", encoding="utf-8")
            (reports_dir / "qa-report.external.html").write_text("<html>external</html>", encoding="utf-8")

            result = build_run_diagnostics.build_run_diagnostics(
                workspace_root=root,
                run_id="2026-05-01-smoke",
                user_comments="OTP was slow. bearer abc.def.ghi and password=super-secret",
                source_request="Please test staging with API token: test-token-123",
            )

            md_path = Path(result["markdown"])
            json_path = Path(result["json"])
            self.assertTrue(md_path.exists())
            self.assertTrue(json_path.exists())
            self.assertEqual(md_path.parent, run_root / "06-diagnostics")

            markdown = md_path.read_text(encoding="utf-8")
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("# QA Compass Run Diagnostics", markdown)
            self.assertIn("2026-05-01-smoke", markdown)
            self.assertIn("https://staging.example.test", markdown)
            self.assertIn("qa-report.internal.html", markdown)
            self.assertIn("TC-2", markdown)
            self.assertIn("[REDACTED]", markdown)
            self.assertNotIn("abc.def.ghi", markdown)
            self.assertNotIn("super-secret", markdown)
            self.assertNotIn("test-token-123", markdown)
            self.assertEqual(payload["run"]["run_id"], "2026-05-01-smoke")
            self.assertEqual(payload["summary"]["counts"]["failed"], 1)
            self.assertEqual(payload["user_comments"], "OTP was slow. bearer [REDACTED] and password=[REDACTED]")

    def test_missing_run_artifacts_are_warnings_not_failures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace_lifecycle.init_workspace(root, project_name="Sparse QA")
            workspace_lifecycle.create_run_workspace(
                root,
                suite="custom",
                mode="custom",
                run_id="2026-05-02-custom",
            )

            result = build_run_diagnostics.build_run_diagnostics(
                workspace_root=root,
                run_id="2026-05-02-custom",
                user_comments="No extra comments",
            )

            payload = json.loads(Path(result["json"]).read_text(encoding="utf-8"))
            warning_text = "\n".join(payload["warnings"])
            self.assertIn("Missing run-summary.json", warning_text)
            self.assertIn("Missing execution-results.json", warning_text)
            self.assertTrue(Path(result["markdown"]).exists())


if __name__ == "__main__":
    unittest.main()
