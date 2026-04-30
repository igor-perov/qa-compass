import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_artifact_manifest  # noqa: E402


class ArtifactManifestTests(unittest.TestCase):
    def test_builds_manifest_and_legend_for_known_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "workspace-index.json").write_text("{}", encoding="utf-8")
            (run_dir / "project-profile.json").write_text("{}", encoding="utf-8")
            (run_dir / "00-overview").mkdir()
            (run_dir / "03-generated").mkdir()
            (run_dir / "history").mkdir()
            (run_dir / "04-execution").mkdir()
            (run_dir / "05-reports").mkdir()
            (run_dir / "06-diagnostics").mkdir()
            (run_dir / "00-overview" / "project-summary.md").write_text("# Project", encoding="utf-8")
            (run_dir / "01-sources").mkdir()
            (run_dir / "01-sources" / "confluence-intake-diagnostics.json").write_text("{}", encoding="utf-8")
            (run_dir / "03-generated" / "test-cases.json").write_text("{}", encoding="utf-8")
            (run_dir / "history" / "case-history.json").write_text("{}", encoding="utf-8")
            (run_dir / "04-execution" / "qa-scope-preview.html").write_text("<html></html>", encoding="utf-8")
            (run_dir / "05-reports" / "qa-report.internal.html").write_text("<html></html>", encoding="utf-8")
            (run_dir / "06-diagnostics" / "qa-compass-run-diagnostics.md").write_text("# Diagnostics", encoding="utf-8")
            (run_dir / "06-diagnostics" / "qa-compass-run-diagnostics.json").write_text("{}", encoding="utf-8")

            summary = build_artifact_manifest.build_artifact_manifest(str(run_dir))

            self.assertEqual(summary["artifact_count"], 10)
            manifest_path = run_dir / "00-overview" / "artifact-manifest.json"
            legend_path = run_dir / "00-overview" / "artifact-legend.md"
            self.assertTrue(manifest_path.exists())
            self.assertTrue(legend_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            test_cases = next(item for item in manifest["artifacts"] if item["path"] == "03-generated/test-cases.json")
            self.assertEqual(test_cases["label"], "Canonical test cases")
            self.assertEqual(test_cases["created_by"], "ai_generated")
            self.assertTrue(test_cases["source_of_truth"])
            scope_preview = next(
                item for item in manifest["artifacts"] if item["path"] == "04-execution/qa-scope-preview.html"
            )
            self.assertEqual(scope_preview["label"], "QA scope preview")
            self.assertFalse(scope_preview["source_of_truth"])
            diagnostics = next(
                item for item in manifest["artifacts"] if item["path"] == "01-sources/confluence-intake-diagnostics.json"
            )
            self.assertEqual(diagnostics["label"], "Confluence intake diagnostics")
            self.assertFalse(diagnostics["source_of_truth"])
            workspace_index = next(item for item in manifest["artifacts"] if item["path"] == "workspace-index.json")
            self.assertEqual(workspace_index["label"], "Workspace index")
            self.assertTrue(workspace_index["source_of_truth"])
            case_history = next(item for item in manifest["artifacts"] if item["path"] == "history/case-history.json")
            self.assertEqual(case_history["label"], "Case history")
            self.assertTrue(case_history["source_of_truth"])
            run_diagnostics = next(
                item
                for item in manifest["artifacts"]
                if item["path"] == "06-diagnostics/qa-compass-run-diagnostics.md"
            )
            self.assertEqual(run_diagnostics["label"], "QA Compass run diagnostics")
            self.assertFalse(run_diagnostics["source_of_truth"])

            legend = legend_path.read_text(encoding="utf-8")
            self.assertIn("Generated Files And Artifact Legend", legend)
            self.assertIn("workspace-index.json", legend)
            self.assertIn("history/case-history.json", legend)
            self.assertIn("03-generated/test-cases.json", legend)
            self.assertIn("04-execution/qa-scope-preview.html", legend)
            self.assertIn("01-sources/confluence-intake-diagnostics.json", legend)
            self.assertIn("06-diagnostics/qa-compass-run-diagnostics.md", legend)
            self.assertIn("Source of truth for generated QA coverage", legend)


if __name__ == "__main__":
    unittest.main()
