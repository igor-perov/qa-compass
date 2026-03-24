import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import export_playwright_specs  # noqa: E402
import import_test_cases_json  # noqa: E402
import io_utils  # noqa: E402


class ExportPlaywrightSpecsTests(unittest.TestCase):
    FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

    def test_exports_grouped_spec_files_for_automation_candidates(self):
        payload = import_test_cases_json.import_test_cases_json(
            str(self.FIXTURES_DIR / "sample_test_cases.json")
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test-cases.json"
            output_dir = Path(tmpdir) / "generated-specs"
            io_utils.write_json(input_path, payload)

            summary = export_playwright_specs.export_playwright_specs(str(input_path), str(output_dir))

            self.assertEqual(summary["generated_files"], ["auth.spec.ts", "company-data.spec.ts"])

            auth_spec = (output_dir / "auth.spec.ts").read_text(encoding="utf-8")
            company_data_spec = (output_dir / "company-data.spec.ts").read_text(encoding="utf-8")

            self.assertIn("TC-AUTH-F-001 - Register with a valid work email", auth_spec)
            self.assertIn("TC-AUTH-ERR-001 - Reject a public email domain", auth_spec)
            self.assertIn("Requirement IDs: AUTH-1", auth_spec)
            self.assertIn("test.skip(true", auth_spec)

            self.assertIn("TC-COMPANY-F-001 - Complete company data", company_data_spec)
            self.assertIn("Requirement IDs: ST1-1", company_data_spec)
            self.assertNotIn("TC-HELP-F-001", auth_spec + company_data_spec)


if __name__ == "__main__":
    unittest.main()
