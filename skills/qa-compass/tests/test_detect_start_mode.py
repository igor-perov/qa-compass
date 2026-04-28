import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from detect_start_mode import detect_start_mode  # noqa: E402


class DetectStartModeTests(unittest.TestCase):
    def test_skill_metadata_names_qa_compass(self):
        skill_root = Path(__file__).resolve().parents[1]
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        openai_yaml = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("name: qa-compass", skill_text)
        self.assertIn("# QA Compass", skill_text)
        self.assertIn("Jira", skill_text)
        self.assertIn("Detect And Protect Secrets", skill_text)
        self.assertIn("never write it to artifacts", skill_text)
        self.assertIn('display_name: "QA Compass"', openai_yaml)
        self.assertIn("$qa-compass", openai_yaml)

    def test_detects_confluence_ingest_request(self):
        payload = detect_start_mode("Pull requirements from Confluence and generate test cases")
        self.assertEqual(payload["source_mode"], "confluence")
        self.assertEqual(payload["stage"], "generate-cases")
        self.assertTrue(payload["generation_scope_prompt_required"])

    def test_detects_confluence_folder_url(self):
        payload = detect_start_mode(
            "Use https://kepler-team.atlassian.net/wiki/spaces/VI/folder/1040482348 and generate QA coverage"
        )
        self.assertEqual(payload["source_mode"], "confluence_folder")
        self.assertEqual(payload["stage"], "generate-cases")

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
        self.assertIn("scope_preview_confirmation", payload["missing_blockers"])
        self.assertIn("environment_url", payload["missing_blockers"])

    def test_execute_request_with_otp_requires_otp_handling(self):
        payload = detect_start_mode("Run registration cases with OTP on https://staging.example.test")
        self.assertEqual(payload["stage"], "execute")
        self.assertIn("scope_preview_confirmation", payload["missing_blockers"])
        self.assertIn("credentials_or_test_data", payload["missing_blockers"])
        self.assertIn("otp_mfa_handling", payload["missing_blockers"])

    def test_detects_scope_preview_request(self):
        payload = detect_start_mode("Build a scope preview so I can confirm cases before execution")
        self.assertEqual(payload["stage"], "scope-preview")
        self.assertEqual(payload["requested_output"], "scope_preview")

    def test_detects_jira_source_request(self):
        payload = detect_start_mode("Use Jira Ready for QA issues and generate test cases")
        self.assertEqual(payload["source_mode"], "jira")
        self.assertEqual(payload["stage"], "generate-cases")
        self.assertTrue(payload["generation_scope_prompt_required"])

    def test_detects_mixed_jira_confluence_source_request(self):
        payload = detect_start_mode("Use Confluence requirements and linked Jira Done issues")
        self.assertEqual(payload["source_mode"], "jira_confluence")

    def test_detects_report_only_request(self):
        payload = detect_start_mode("Turn these execution results into an HTML and PDF stakeholder report")
        self.assertEqual(payload["stage"], "report")
        self.assertEqual(payload["source_mode"], "pasted_text")

    def test_detects_jira_bug_draft_request(self):
        payload = detect_start_mode("Draft Jira bugs from these failed execution results")
        self.assertEqual(payload["stage"], "draft-defects")
        self.assertEqual(payload["requested_output"], "jira_bug_drafts")

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
