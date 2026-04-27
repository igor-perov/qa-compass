import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import build_scope_preview  # noqa: E402
import import_test_cases_json  # noqa: E402


class ScopePreviewTests(unittest.TestCase):
    FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

    def test_builds_pre_execution_scope_preview_grouped_by_feature(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            canonical_cases = import_test_cases_json.import_test_cases_json(
                str(self.FIXTURES_DIR / "sample_test_cases.json")
            )
            canonical_cases["grouping_strategy"] = "feature"
            canonical_cases["roles"] = ["Anonymous visitor", "Registered user"]
            cases_path = tmp_root / "test-cases.json"
            cases_path.write_text(json.dumps(canonical_cases), encoding="utf-8")

            subset_path = tmp_root / "execution-subset.json"
            subset_path.write_text(
                json.dumps(
                    {
                        "project_name": "Sample Valuation",
                        "mode": "high-priority",
                        "test_cases": canonical_cases["test_cases"][:2],
                    }
                ),
                encoding="utf-8",
            )

            summary = build_scope_preview.build_scope_preview(
                str(cases_path),
                str(tmp_root / "preview"),
                subset_path=str(subset_path),
            )

            self.assertEqual(summary["selected_cases"], 2)
            self.assertEqual(summary["total_cases"], 4)
            self.assertEqual(summary["grouping_strategy"], "feature")
            self.assertTrue((tmp_root / "preview" / "qa-scope-preview.html").exists())
            self.assertTrue((tmp_root / "preview" / "qa-scope-preview.md").exists())
            self.assertTrue((tmp_root / "preview" / "qa-scope-preview.json").exists())

            preview = json.loads((tmp_root / "preview" / "qa-scope-preview.json").read_text(encoding="utf-8"))
            self.assertEqual(preview["coverage"]["priority_counts"]["High"], 2)
            self.assertEqual(preview["coverage"]["groups"][0]["name"], "Auth")
            self.assertEqual(preview["coverage"]["groups"][0]["case_count"], 2)
            self.assertIn("Anonymous visitor", preview["roles"]["covered"])
            self.assertEqual(preview["artifact_links"]["test_cases"], "../test-cases.json")

            html = (tmp_root / "preview" / "qa-scope-preview.html").read_text(encoding="utf-8")
            self.assertIn("QA Scope Preview", html)
            self.assertIn("Ready for execution review", html)
            self.assertIn('href="../test-cases.json"', html)
            self.assertIn("Open full test-cases.json", html)
            self.assertIn("Grouped by Feature", html)
            self.assertIn("Auth", html)
            self.assertIn("TC-AUTH-F-001", html)
            self.assertIn("Reject a public email domain", html)
            self.assertIn("Functional", html)
            self.assertNotIn("View all cases", html)
            self.assertNotIn("Expected:", html)
            self.assertNotIn("Roles Covered", html)
            self.assertIn("2 selected", html)

            markdown = (tmp_root / "preview" / "qa-scope-preview.md").read_text(encoding="utf-8")
            self.assertIn("# QA Scope Preview", markdown)
            self.assertIn("Selected cases: 2 / 4", markdown)
            self.assertIn("Full test cases: ../test-cases.json", markdown)
            self.assertIn("## Auth", markdown)


if __name__ == "__main__":
    unittest.main()
