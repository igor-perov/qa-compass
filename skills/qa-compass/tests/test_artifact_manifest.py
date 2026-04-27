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
            (run_dir / "00-overview").mkdir()
            (run_dir / "03-generated").mkdir()
            (run_dir / "05-reports").mkdir()
            (run_dir / "00-overview" / "project-summary.md").write_text("# Project", encoding="utf-8")
            (run_dir / "03-generated" / "test-cases.json").write_text("{}", encoding="utf-8")
            (run_dir / "05-reports" / "qa-report.internal.html").write_text("<html></html>", encoding="utf-8")

            summary = build_artifact_manifest.build_artifact_manifest(str(run_dir))

            self.assertEqual(summary["artifact_count"], 3)
            manifest_path = run_dir / "00-overview" / "artifact-manifest.json"
            legend_path = run_dir / "00-overview" / "artifact-legend.md"
            self.assertTrue(manifest_path.exists())
            self.assertTrue(legend_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            test_cases = next(item for item in manifest["artifacts"] if item["path"] == "03-generated/test-cases.json")
            self.assertEqual(test_cases["label"], "Canonical test cases")
            self.assertEqual(test_cases["created_by"], "ai_generated")
            self.assertTrue(test_cases["source_of_truth"])

            legend = legend_path.read_text(encoding="utf-8")
            self.assertIn("Generated Files And Artifact Legend", legend)
            self.assertIn("03-generated/test-cases.json", legend)
            self.assertIn("Source of truth for generated QA coverage", legend)


if __name__ == "__main__":
    unittest.main()
