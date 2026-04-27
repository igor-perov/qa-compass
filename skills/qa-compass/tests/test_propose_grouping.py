import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import io_utils  # noqa: E402
import propose_grouping  # noqa: E402


class ProposeGroupingTests(unittest.TestCase):
    def test_proposes_roles_features_and_source_sections(self):
        payload = {
            "project_name": "Sample Platform",
            "requirements": [
                {
                    "requirement_id": "AUTH-1",
                    "feature": "Authentication",
                    "source_title": "Auth / Login",
                    "roles": ["Admin", "Client"],
                },
                {
                    "requirement_id": "DOC-1",
                    "feature": "Documents",
                    "source_title": "Documents / Upload",
                    "roles": ["Client"],
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "requirements-normalized.json"
            output_path = Path(tmpdir) / "grouping-proposal.json"
            io_utils.write_json(input_path, payload)

            proposal = propose_grouping.propose_grouping(str(input_path), str(output_path))

            self.assertEqual(proposal["roles"], ["Admin", "Client"])
            self.assertEqual(proposal["recommended"], "feature")
            self.assertTrue(output_path.exists())

            feature_option = next(item for item in proposal["grouping_options"] if item["type"] == "feature")
            role_option = next(item for item in proposal["grouping_options"] if item["type"] == "role")
            source_option = next(item for item in proposal["grouping_options"] if item["type"] == "source_section")

            self.assertEqual([item["name"] for item in feature_option["groups"]], ["Authentication", "Documents"])
            self.assertEqual([item["name"] for item in role_option["groups"]], ["Admin", "Client"])
            self.assertEqual([item["name"] for item in source_option["groups"]], ["Auth", "Documents"])


if __name__ == "__main__":
    unittest.main()
