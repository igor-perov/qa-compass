import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from detect_start_mode import detect_start_mode  # noqa: E402


class DetectStartModeTests(unittest.TestCase):
    def test_detects_confluence_ingest_request(self):
        payload = detect_start_mode("Pull requirements from Confluence and generate test cases")
        self.assertEqual(payload["source_mode"], "confluence")
        self.assertEqual(payload["stage"], "generate-cases")
        self.assertTrue(payload["generation_scope_prompt_required"])

    def test_detects_markdown_normalization_request(self):
        payload = detect_start_mode("Here is a PRD markdown file. Normalize it and create QA coverage")
        self.assertEqual(payload["source_mode"], "markdown")
        self.assertEqual(payload["stage"], "normalize")

    def test_detects_pasted_text_generation_request(self):
        payload = detect_start_mode("Turn these requirements into test cases:\nUsers can register with work email only.")
        self.assertEqual(payload["source_mode"], "pasted_text")
        self.assertEqual(payload["stage"], "generate-cases")
        self.assertTrue(payload["generation_scope_prompt_required"])

    def test_detects_test_cases_json_execution_request(self):
        payload = detect_start_mode("Here is a test-cases JSON file. Run the top 5 high-priority cases on staging")
        self.assertEqual(payload["source_mode"], "test_cases_json")
        self.assertEqual(payload["stage"], "execute")
        self.assertIn("environment_url", payload["missing_blockers"])

    def test_detects_report_only_request(self):
        payload = detect_start_mode("Turn these execution results into an HTML and PDF stakeholder report")
        self.assertEqual(payload["stage"], "report")
        self.assertEqual(payload["source_mode"], "pasted_text")

    def test_detects_playwright_spec_export_request(self):
        payload = detect_start_mode(
            "Generate test cases and reusable Playwright .spec.ts files from this PRD markdown file"
        )
        self.assertEqual(payload["source_mode"], "markdown")
        self.assertEqual(payload["stage"], "generate-cases")
        self.assertTrue(payload["generation_scope_prompt_required"])
        self.assertTrue(payload["playwright_specs_requested"])

    def test_detects_export_only_playwright_spec_request(self):
        payload = detect_start_mode(
            "Export reusable Playwright .spec.ts files from this test-cases JSON attachment"
        )
        self.assertEqual(payload["source_mode"], "test_cases_json")
        self.assertEqual(payload["stage"], "export-playwright-specs")
        self.assertEqual(payload["requested_output"], "playwright_specs")
        self.assertFalse(payload["generation_scope_prompt_required"])
        self.assertTrue(payload["playwright_specs_requested"])


if __name__ == "__main__":
    unittest.main()
