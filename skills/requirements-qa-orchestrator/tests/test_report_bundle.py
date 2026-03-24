import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_report_bundle  # noqa: E402


class ReportBundleTests(unittest.TestCase):
    FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

    def test_build_report_bundle_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = self.FIXTURES_DIR / "sample_execution_results.json"
            build_report_bundle.build_report_bundle(str(payload_path), tmpdir)
            generated = {path.name for path in Path(tmpdir).iterdir()}
            self.assertIn("execution-plan.md", generated)
            self.assertIn("execution-results.md", generated)
            self.assertIn("run-summary.json", generated)
            self.assertIn("qa-report.html", generated)

            summary = json.loads((Path(tmpdir) / "run-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["counts"]["failed"], 1)
            self.assertEqual(summary["counts"]["blocked"], 1)
            self.assertEqual(len(summary["defects"]), 1)
            self.assertEqual(summary["defects"][0]["test_case_id"], "TC-AUTH-ERR-001")

            html = (Path(tmpdir) / "qa-report.html").read_text(encoding="utf-8")
            self.assertIn("pie-chart", html)
            self.assertIn("conic-gradient", html)
            self.assertIn("Execution Overview", html)
            self.assertIn("Confirmed Defects", html)
            self.assertIn("Evidence Gallery", html)
            self.assertIn("TC-AUTH-ERR-001", html)
            self.assertIn("The flow accepted a public email domain and allowed progression.", html)
            self.assertIn("evidence/public-email-failure.png", html)


if __name__ == "__main__":
    unittest.main()
