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
            self.assertIn("qa-report.internal.html", generated)
            self.assertIn("qa-report.external.html", generated)

            summary = json.loads((Path(tmpdir) / "run-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["counts"]["failed"], 1)
            self.assertEqual(summary["counts"]["blocked"], 1)
            self.assertEqual(summary["grouping_strategy"], "feature")
            self.assertEqual(len(summary["defects"]), 1)
            self.assertEqual(summary["defects"][0]["test_case_id"], "TC-AUTH-ERR-001")
            self.assertIn("Public email domains are rejected", summary["defects"][0]["expected_results"][0])
            self.assertIn("Continue button became active", summary["defects"][0]["actual_result"])
            self.assertIn("ValidationPolicyError", summary["defects"][0]["console_errors"][0])
            self.assertIn("POST /api/signup/validate-email", summary["defects"][0]["network_errors"][0])
            self.assertEqual(summary["defects"][0]["browser_context"]["browser"], "Chrome")

            html = (Path(tmpdir) / "qa-report.html").read_text(encoding="utf-8")
            self.assertIn("pie-chart", html)
            self.assertIn("conic-gradient", html)
            self.assertIn("Execution Overview", html)
            self.assertIn("Grouped by Feature", html)
            self.assertIn("Authentication", html)
            self.assertIn("Company Data", html)
            self.assertIn("Confirmed Defects", html)
            self.assertIn("Evidence Gallery", html)
            self.assertIn("TC-AUTH-ERR-001", html)
            self.assertIn("The flow accepted a public email domain and allowed progression.", html)
            self.assertIn("evidence/public-email-failure.png", html)

            internal_html = (Path(tmpdir) / "qa-report.internal.html").read_text(encoding="utf-8")
            self.assertIn("<details", internal_html)
            self.assertIn("Generated files and artifact legend", internal_html)
            self.assertIn('class="section-card artifact-legend"', internal_html)
            self.assertIn('href="execution-plan.md"', internal_html)
            self.assertIn('href="qa-report.external.html"', internal_html)
            self.assertLess(
                internal_html.index("Generated files and artifact legend"),
                internal_html.index("Execution Overview"),
            )
            self.assertNotIn("<h3>Defects</h3>", internal_html)
            self.assertNotIn("<h3>Blocked Cases</h3>", internal_html)
            self.assertIn('<details class="section-card issue-details">', internal_html)
            self.assertIn("<summary><h2>Blocked Cases</h2>", internal_html)
            self.assertIn("<summary><h2>Confirmed Defects</h2>", internal_html)
            self.assertIn(".issue-list {\n      margin-top: 18px;", internal_html)
            self.assertIn("transform: rotate(45deg);", internal_html)
            self.assertIn("transform: rotate(-135deg);", internal_html)
            self.assertNotIn('content: "Open"', internal_html)
            self.assertNotIn('content: "Close"', internal_html)
            self.assertIn("Evidence Gallery", internal_html)
            self.assertIn("TC-AUTH-ERR-001", internal_html)
            self.assertIn('<section class="execution-group">', internal_html)
            self.assertIn("2 cases", internal_html)
            self.assertLess(
                internal_html.index("Authentication"),
                internal_html.index("TC-AUTH-F-001"),
            )
            self.assertLess(
                internal_html.index("Company Data"),
                internal_html.index("TC-ST1-F-001"),
            )
            self.assertIn('data-label="Status"', internal_html)
            self.assertIn("content: attr(data-label)", internal_html)
            self.assertIn("Expected result", internal_html)
            self.assertIn("Actual result", internal_html)
            self.assertIn("Console errors", internal_html)
            self.assertIn("Network / API errors", internal_html)
            self.assertIn("Browser context", internal_html)
            self.assertIn("ValidationPolicyError", internal_html)
            self.assertIn("POST /api/signup/validate-email returned 200", internal_html)
            self.assertIn("https://develop.example.test/signup", internal_html)

            external_html = (Path(tmpdir) / "qa-report.external.html").read_text(encoding="utf-8")
            self.assertIn("Executive QA Dashboard", external_html)
            self.assertIn("outcome-chart", external_html)
            self.assertIn("conic-gradient", external_html)
            self.assertIn("Run Snapshot", external_html)
            self.assertIn("Confirmed defects", external_html)
            self.assertIn("TC-AUTH-ERR-001", external_html)
            self.assertIn("@media (max-width: 760px)", external_html)
            self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", external_html)
            self.assertNotIn("Evidence Gallery", external_html)


if __name__ == "__main__":
    unittest.main()
