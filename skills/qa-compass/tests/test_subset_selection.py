import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import import_test_cases_json  # noqa: E402
from select_execution_subset import select_subset  # noqa: E402


class SubsetSelectionTests(unittest.TestCase):
    FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

    def setUp(self):
        payload = import_test_cases_json.import_test_cases_json(
            str(self.FIXTURES_DIR / "sample_test_cases.json")
        )
        self.cases = payload["test_cases"] + [
            {
                "test_case_id": "TC-ST1-F-001",
                "title": "Complete company data",
                "requirement_ids": ["ST1-1"],
                "priority": "Medium",
                "type": "Functional",
                "preconditions": ["User is logged in"],
                "steps": ["Open company data", "Fill all required fields", "Continue"],
                "expected_results": ["Stage 1 progresses"],
                "automation_candidate": True,
                "last_status": "Failed",
            },
            {
                "test_case_id": "TC-ST1-ERR-001",
                "title": "Block continuation when required field is empty",
                "requirement_ids": ["ST1-1"],
                "priority": "Medium",
                "type": "Error Handling",
                "preconditions": ["User is logged in"],
                "steps": ["Open company data", "Leave a required field empty", "Continue"],
                "expected_results": ["Validation is shown"],
                "automation_candidate": True,
                "last_status": "Blocked",
            },
            {
                "test_case_id": "TC-LOW-F-001",
                "title": "Open help tooltip",
                "requirement_ids": ["UX-1"],
                "priority": "Low",
                "type": "Functional",
                "preconditions": [],
                "steps": ["Open tooltip"],
                "expected_results": ["Tooltip is visible"],
                "automation_candidate": False,
                "last_status": "Passed",
            },
        ]

    def test_selects_top_n_by_priority(self):
        subset = select_subset(self.cases, mode="high-priority", limit=2)
        self.assertEqual(len(subset), 2)
        self.assertTrue(all(case["priority"] == "High" for case in subset))

    def test_selects_smoke_subset_without_low_value_cases(self):
        subset = select_subset(self.cases, mode="smoke")
        ids = [case["test_case_id"] for case in subset]
        self.assertIn("TC-AUTH-F-001", ids)
        self.assertNotIn("TC-LOW-F-001", ids)

    def test_selects_critical_path_subset(self):
        subset = select_subset(self.cases, mode="critical-path")
        ids = [case["test_case_id"] for case in subset]
        self.assertIn("TC-AUTH-F-001", ids)
        self.assertIn("TC-ST1-F-001", ids)

    def test_selects_full_regression_subset(self):
        subset = select_subset(self.cases, mode="full-regression")
        self.assertEqual(len(subset), len(self.cases))
        self.assertEqual(subset[0]["priority"], "High")

    def test_selects_rerun_failed_subset(self):
        subset = select_subset(self.cases, mode="rerun-failed")
        self.assertEqual([case["test_case_id"] for case in subset], ["TC-ST1-F-001"])

    def test_selects_rerun_blocked_subset(self):
        subset = select_subset(self.cases, mode="rerun-blocked")
        self.assertEqual([case["test_case_id"] for case in subset], ["TC-ST1-ERR-001"])

    def test_selects_rerun_subset_from_case_history(self):
        case_history = {
            "cases": {
                "TC-AUTH-F-001": {"last_status": "Failed", "last_run_id": "2026-05-01-smoke"},
                "TC-AUTH-ERR-001": {"last_status": "Blocked", "last_run_id": "2026-05-01-smoke"},
            }
        }

        failed_subset = select_subset(self.cases, mode="rerun-failed", case_history=case_history)
        blocked_subset = select_subset(self.cases, mode="rerun-blocked", case_history=case_history)

        self.assertEqual([case["test_case_id"] for case in failed_subset], ["TC-AUTH-F-001"])
        self.assertEqual([case["test_case_id"] for case in blocked_subset], ["TC-AUTH-ERR-001"])


if __name__ == "__main__":
    unittest.main()
