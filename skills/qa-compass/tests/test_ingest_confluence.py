import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import ingest_confluence  # noqa: E402


class IngestConfluenceTests(unittest.TestCase):
    def test_parses_confluence_folder_url(self):
        parsed = ingest_confluence.parse_confluence_reference(
            "https://kepler-team.atlassian.net/wiki/spaces/VI/folder/1040482348"
        )

        self.assertEqual(parsed["base_url"], "https://kepler-team.atlassian.net")
        self.assertEqual(parsed["space_key"], "VI")
        self.assertEqual(parsed["root_type"], "folder")
        self.assertEqual(parsed["root_id"], "1040482348")
        self.assertEqual(parsed["source_type"], "confluence_folder")

    def test_parses_confluence_page_url(self):
        parsed = ingest_confluence.parse_confluence_reference(
            "https://kepler-team.atlassian.net/wiki/spaces/VI/pages/123456789/Product+Requirements"
        )

        self.assertEqual(parsed["space_key"], "VI")
        self.assertEqual(parsed["root_type"], "page")
        self.assertEqual(parsed["root_id"], "123456789")
        self.assertEqual(parsed["source_type"], "confluence_page")

    def test_folder_ingest_does_not_fetch_folder_id_as_page_body(self):
        requested_paths = []

        def fake_api_get(_base_url, _email, _token, path_or_url):
            requested_paths.append(path_or_url)
            if path_or_url == "/wiki/api/v2/folders/1040482348/direct-children?limit=100":
                return {"results": [{"id": "200", "type": "page", "title": "Child Requirement"}]}
            if path_or_url == "/wiki/api/v2/pages/200?body-format=storage":
                return {
                    "id": "200",
                    "type": "page",
                    "title": "Child Requirement",
                    "body": {"storage": {"value": "<p>Requirement body</p>"}},
                    "_links": {"base": "https://kepler-team.atlassian.net", "webui": "/wiki/spaces/VI/pages/200"},
                }
            raise AssertionError(f"Unexpected path: {path_or_url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            summary = ingest_confluence.ingest_confluence(
                input_url="https://kepler-team.atlassian.net/wiki/spaces/VI/folder/1040482348",
                output_dir=tmpdir,
                email="qa@example.com",
                token="SECRET-TOKEN",
                api_getter=fake_api_get,
            )

        self.assertEqual(summary["documents"], 1)
        self.assertNotIn("/wiki/api/v2/pages/1040482348?body-format=storage", requested_paths)

    def test_folder_fallback_order_and_diagnostics_redact_secrets(self):
        token = "ATATT3xFfGF0-secret-token"

        def fake_api_get(_base_url, _email, _token, path_or_url):
            if "/direct-children" in path_or_url:
                raise RuntimeError(f"401 Unauthorized bearer {token}")
            if "/wiki/rest/api/content/search" in path_or_url:
                return {
                    "results": [
                        {
                            "id": "300",
                            "type": "page",
                            "title": "Search Fallback Page",
                            "body": {"storage": {"value": "<h1>Fallback</h1><p>Requirement</p>"}},
                            "_links": {"base": "https://kepler-team.atlassian.net", "webui": "/wiki/spaces/VI/pages/300"},
                        }
                    ]
                }
            raise AssertionError(f"Unexpected path: {path_or_url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            summary = ingest_confluence.ingest_confluence(
                input_url="https://kepler-team.atlassian.net/wiki/spaces/VI/folder/1040482348?token=SHOULD-NOT-LEAK",
                output_dir=str(output_dir),
                email="qa@example.com",
                token=token,
                api_getter=fake_api_get,
                strict=False,
            )

            diagnostics_text = (output_dir / "confluence-intake-diagnostics.json").read_text(encoding="utf-8")
            diagnostics = json.loads(diagnostics_text)

        self.assertEqual(summary["documents"], 1)
        self.assertEqual(
            [attempt["method"] for attempt in diagnostics["discovery_methods"]],
            ["connector_rovo", "rest_folder_children", "rest_space_search"],
        )
        self.assertEqual(diagnostics["discovery_methods"][1]["status"], "failed")
        self.assertEqual(diagnostics["discovery_methods"][2]["status"], "success")
        self.assertNotIn(token, diagnostics_text)
        self.assertNotIn("SHOULD-NOT-LEAK", diagnostics_text)
        self.assertIn("[REDACTED]", diagnostics_text)

    def test_partial_failure_writes_diagnostics_and_empty_artifacts(self):
        def fake_api_get(_base_url, _email, _token, path_or_url):
            raise RuntimeError(f"404 Not Found for {path_or_url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            summary = ingest_confluence.ingest_confluence(
                input_url="https://kepler-team.atlassian.net/wiki/spaces/VI/folder/1040482348",
                output_dir=str(output_dir),
                email="qa@example.com",
                token="token",
                api_getter=fake_api_get,
                strict=False,
            )

            diagnostics = json.loads((output_dir / "confluence-intake-diagnostics.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["documents"], 0)
            self.assertTrue((output_dir / "requirements-raw.json").exists())
            self.assertTrue((output_dir / "source-index.json").exists())
            self.assertTrue((output_dir / "confluence-tree.md").exists())
            self.assertTrue(diagnostics["warnings"])


if __name__ == "__main__":
    unittest.main()
