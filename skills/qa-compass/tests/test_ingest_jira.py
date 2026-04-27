import tempfile
import unittest
from pathlib import Path
import sys


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ingest_jira import ingest_jira_json  # noqa: E402
from io_utils import write_json  # noqa: E402


class IngestJiraTests(unittest.TestCase):
    def test_ingests_rovo_style_wrapped_issue_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "jira.raw.json"
            write_json(
                input_path,
                {
                    "issues": [
                        {
                            "issue": {
                                "key": "QA-7",
                                "fields": {
                                    "summary": "User can approve invoice",
                                    "description": "Approval flow should support finance managers.",
                                    "status": {"name": "Ready for QA"},
                                    "issuetype": {"name": "Story"},
                                    "priority": {"name": "High"},
                                    "labels": ["finance"],
                                },
                            }
                        }
                    ]
                },
            )

            result = ingest_jira_json(str(input_path))

        self.assertEqual(result["source_mode"], "jira")
        self.assertEqual(result["issues"][0]["issue_key"], "QA-7")
        self.assertEqual(result["issues"][0]["status"], "Ready for QA")
        self.assertEqual(result["issues"][0]["priority"], "High")


if __name__ == "__main__":
    unittest.main()
