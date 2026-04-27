import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import draft_jira_bugs  # noqa: E402


class DraftJiraBugsTests(unittest.TestCase):
    FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

    def test_drafts_jira_bugs_from_failed_results_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            summary = draft_jira_bugs.draft_jira_bugs(
                str(self.FIXTURES_DIR / "sample_execution_results.json"),
                str(output_dir),
            )

            self.assertEqual(summary["draft_count"], 1)
            json_path = output_dir / "jira-bug-drafts.json"
            md_path = output_dir / "jira-bug-drafts.md"
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

            drafts = json.loads(json_path.read_text(encoding="utf-8"))["drafts"]
            draft = drafts[0]
            self.assertEqual(draft["linked_test_case_id"], "TC-AUTH-ERR-001")
            self.assertEqual(draft["requirement_ids"], ["AUTH-1"])
            self.assertEqual(draft["environment"], "https://develop.example.test")
            self.assertEqual(draft["priority"], "High")
            self.assertIn("Open the landing page", draft["steps_to_reproduce"])
            self.assertIn("public email domain", draft["actual_result"])
            self.assertIn("evidence/public-email-failure.png", draft["evidence"])

            markdown = md_path.read_text(encoding="utf-8")
            self.assertIn("Draft BUG-001", markdown)
            self.assertIn("TC-AUTH-ERR-001", markdown)
            self.assertIn("evidence/public-email-failure.png", markdown)


if __name__ == "__main__":
    unittest.main()
