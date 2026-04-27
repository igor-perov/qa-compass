import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_jira_jql import build_jira_query_plan  # noqa: E402


class BuildJiraJqlTests(unittest.TestCase):
    def test_builds_ready_for_qa_query_with_default_statuses(self):
        plan = build_jira_query_plan(project_key="QA", mode="ready-for-qa")

        self.assertIn('project = "QA"', plan["jql"])
        self.assertIn('status in ("Ready for QA", "Ready for Regression", "Ready for Release")', plan["jql"])
        self.assertEqual(plan["maxResults"], 50)
        self.assertIn("summary", plan["fields"])
        self.assertIn("status", plan["fields"])
        self.assertIn("_searchjiraissuesusingjql", plan["connector_tool"])

    def test_builds_current_sprint_query(self):
        plan = build_jira_query_plan(project_key="QA", mode="current-sprint")

        self.assertIn('project = "QA"', plan["jql"])
        self.assertIn("sprint in openSprints()", plan["jql"])
        self.assertIn("ORDER BY priority DESC, updated DESC", plan["jql"])

    def test_builds_issue_keys_query(self):
        plan = build_jira_query_plan(project_key="QA", mode="issue-keys", issue_keys=["QA-1", "QA-2"])

        self.assertIn('issuekey in ("QA-1", "QA-2")', plan["jql"])
        self.assertIn("description", plan["fields"])

    def test_builds_custom_status_query(self):
        plan = build_jira_query_plan(
            project_key="QA",
            mode="status",
            statuses=["In QA", "QA Review"],
            max_results=25,
        )

        self.assertIn('status in ("In QA", "QA Review")', plan["jql"])
        self.assertEqual(plan["maxResults"], 25)


if __name__ == "__main__":
    unittest.main()
