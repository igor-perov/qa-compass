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
            self.assertEqual(summary["defects"][0]["roles"], ["Anonymous visitor"])
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
            self.assertIn('class="artifact-list"', internal_html)
            self.assertIn('href="execution-plan.md"', internal_html)
            self.assertIn('href="qa-report.external.html"', internal_html)
            self.assertIn('href="qa-report.html"', internal_html)
            self.assertIn("Legacy combined HTML QA report.", internal_html)
            self.assertLess(
                internal_html.index("Generated files and artifact legend"),
                internal_html.index("Execution Overview"),
            )
            self.assertIn("Detected Roles", internal_html)
            self.assertIn("Anonymous visitor", internal_html)
            self.assertIn("Registered user", internal_html)
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
            self.assertIn('data-label="Roles"', internal_html)
            self.assertIn("role-chip", internal_html)
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
            self.assertIn("@page { size: A4 landscape; margin: 8mm; }", external_html)
            self.assertIn("@media print", external_html)
            self.assertIn("print-color-adjust: exact", external_html)
            self.assertIn("break-inside: avoid", external_html)
            self.assertIn("Run Snapshot", external_html)
            self.assertIn("Confirmed defects", external_html)
            self.assertIn("TC-AUTH-ERR-001", external_html)
            self.assertIn("@media (max-width: 760px)", external_html)
            self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", external_html)
            self.assertNotIn("Evidence Gallery", external_html)

    def test_report_bundle_copies_local_evidence_and_lists_all_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_dir = root / "input"
            source_evidence_dir = input_dir / "evidence"
            source_evidence_dir.mkdir(parents=True)
            (source_evidence_dir / "screen shot.png").write_bytes(b"fake-png")

            payload = json.loads((self.FIXTURES_DIR / "sample_execution_results.json").read_text(encoding="utf-8"))
            payload["results"][0]["evidence"] = ["evidence/screen shot.png"]
            payload_path = input_dir / "execution-results.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")

            output_dir = root / "report"
            build_report_bundle.build_report_bundle(str(payload_path), str(output_dir))

            copied = output_dir / "evidence" / "screen shot.png"
            self.assertTrue(copied.exists())

            internal_html = (output_dir / "qa-report.internal.html").read_text(encoding="utf-8")
            self.assertIn("evidence/", internal_html)
            self.assertIn("screen shot.png", internal_html)
            self.assertIn('src="evidence/screen%20shot.png"', internal_html)
            self.assertIn('href="evidence/screen%20shot.png"', internal_html)
            self.assertIn("Generated run artifact.", internal_html)

    def test_report_bundle_promotes_screenshot_fields_into_evidence_gallery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_dir = root / "input"
            screenshot_dir = input_dir / "screenshots"
            screenshot_dir.mkdir(parents=True)
            (screenshot_dir / "failure.png").write_bytes(b"fake-png")

            payload = json.loads((self.FIXTURES_DIR / "sample_execution_results.json").read_text(encoding="utf-8"))
            payload["results"][1]["evidence"] = []
            payload["results"][1]["screenshot_path"] = "screenshots/failure.png"
            payload_path = input_dir / "execution-results.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")

            output_dir = root / "report"
            build_report_bundle.build_report_bundle(str(payload_path), str(output_dir))

            self.assertTrue((output_dir / "evidence" / "failure.png").exists())
            summary = json.loads((output_dir / "run-summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["defects"][0]["evidence"], ["evidence/failure.png"])

            internal_html = (output_dir / "qa-report.internal.html").read_text(encoding="utf-8")
            self.assertIn('src="evidence/failure.png"', internal_html)
            self.assertIn("failure.png", internal_html)

    def test_report_bundle_resolves_run_root_relative_screenshots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            execution_dir = run_dir / "04-execution" / "screenshots"
            report_dir = run_dir / "05-report"
            execution_dir.mkdir(parents=True)
            report_dir.mkdir(parents=True)
            (execution_dir / "blocked.png").write_bytes(b"fake-png")

            payload = json.loads((self.FIXTURES_DIR / "sample_execution_results.json").read_text(encoding="utf-8"))
            payload["results"][2]["evidence"] = []
            payload["results"][2]["attachments"] = [
                {"type": "screenshot", "path": "04-execution/screenshots/blocked.png"}
            ]
            payload_path = report_dir / "execution-results.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")

            build_report_bundle.build_report_bundle(str(payload_path), str(report_dir))

            self.assertTrue((report_dir / "evidence" / "blocked.png").exists())
            internal_html = (report_dir / "qa-report.internal.html").read_text(encoding="utf-8")
            self.assertIn('src="evidence/blocked.png"', internal_html)

    def test_report_bundle_reads_parent_manifest_for_full_run_artifact_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            overview_dir = run_dir / "00-overview"
            sources_dir = run_dir / "01-sources"
            report_dir = run_dir / "05-report"
            overview_dir.mkdir(parents=True)
            sources_dir.mkdir(parents=True)
            (sources_dir / "requirements-raw.json").write_text("{}", encoding="utf-8")
            (overview_dir / "artifact-manifest.json").write_text(
                json.dumps(
                    {
                        "run_dir": str(run_dir),
                        "artifacts": [
                            {
                                "path": "01-sources/requirements-raw.json",
                                "description": "Imported source requirements.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            build_report_bundle.build_report_bundle(
                str(self.FIXTURES_DIR / "sample_execution_results.json"),
                str(report_dir),
            )

            internal_html = (report_dir / "qa-report.internal.html").read_text(encoding="utf-8")
            self.assertIn("01-sources", internal_html)
            self.assertIn("requirements-raw.json", internal_html)
            self.assertIn('href="../01-sources/requirements-raw.json"', internal_html)
            self.assertIn("Imported source requirements.", internal_html)


if __name__ == "__main__":
    unittest.main()
