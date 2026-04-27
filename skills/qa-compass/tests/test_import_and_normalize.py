import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import contracts  # noqa: E402
import ingest_markdown  # noqa: E402
import import_requirements_json  # noqa: E402
import import_test_cases_json  # noqa: E402
import io_utils  # noqa: E402
import normalize_requirements  # noqa: E402


class ContractsAndIoTests(unittest.TestCase):
    FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

    def test_project_context_contract_contains_expected_keys(self):
        for key in (
            "project_name",
            "source_mode",
            "active_stage",
            "output_dir",
            "execution_subset",
            "roles_confirmed",
            "grouping_strategy",
            "source_of_truth_policy",
        ):
            self.assertIn(key, contracts.PROJECT_CONTEXT_KEYS)

    def test_requirement_contract_contains_expected_keys(self):
        for key in (
            "requirement_id",
            "feature",
            "statement",
            "acceptance_criteria",
            "business_rules",
            "ambiguities",
        ):
            self.assertIn(key, contracts.REQUIREMENT_KEYS)

    def test_io_utils_round_trip_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "nested" / "payload.json"
            payload = {"hello": "world", "count": 2}
            io_utils.write_json(str(target), payload)
            self.assertTrue(target.exists())
            self.assertEqual(io_utils.read_json(str(target)), payload)
            raw = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(raw, payload)

    def test_import_requirements_json_maps_to_canonical_keys(self):
        payload = import_requirements_json.import_requirements_json(
            str(self.FIXTURES_DIR / "sample_requirements.json")
        )
        self.assertEqual(payload["project_name"], "Sample Valuation")
        requirement = payload["requirements"][0]
        self.assertTrue(contracts.has_required_keys(requirement, contracts.REQUIREMENT_KEYS))
        self.assertEqual(requirement["requirement_id"], "AUTH-1")
        self.assertEqual(requirement["source_title"], "Registration PRD")

    def test_import_test_cases_json_maps_to_canonical_keys(self):
        payload = import_test_cases_json.import_test_cases_json(
            str(self.FIXTURES_DIR / "sample_test_cases.json")
        )
        self.assertEqual(payload["project_name"], "Sample Valuation")
        case = payload["test_cases"][0]
        self.assertTrue(contracts.has_required_keys(case, contracts.TEST_CASE_KEYS))
        self.assertEqual(case["test_case_id"], "TC-AUTH-F-001")
        self.assertEqual(case["type"], "Functional")

    def test_normalize_requirements_builds_stable_ids_and_ambiguities(self):
        raw_payload = ingest_markdown.ingest_markdown(str(self.FIXTURES_DIR / "sample_prd.md"))
        normalized = normalize_requirements.normalize_payload(raw_payload)
        requirements = normalized["requirements"]
        self.assertGreaterEqual(len(requirements), 2)
        self.assertTrue(all(item["requirement_id"].startswith("REQ-") for item in requirements))
        self.assertTrue(any(item["ambiguities"] for item in requirements))

    def test_project_summary_template_does_not_leave_raw_placeholders(self):
        raw_payload = ingest_markdown.ingest_markdown(str(self.FIXTURES_DIR / "sample_prd.md"))
        normalized = normalize_requirements.normalize_payload(raw_payload)
        summary = normalize_requirements.build_project_summary(normalized)

        self.assertIn("What This Product Appears To Do", summary)
        self.assertIn("Testing Implications", summary)
        self.assertNotIn("$product_overview", summary)
        self.assertNotIn("$testing_implications", summary)

    def test_test_case_brief_preserves_roles_for_generation(self):
        payload = import_requirements_json.import_requirements_json(
            str(self.FIXTURES_DIR / "sample_requirements.json")
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "requirements-normalized.json"
            io_utils.write_json(input_path, payload)

            brief = __import__("prepare_test_case_brief").prepare_test_case_brief(str(input_path))

        self.assertIn("roles", brief)
        self.assertIn("Detected roles should be considered during test generation.", brief["generation_rules"]["roles"])


if __name__ == "__main__":
    unittest.main()
