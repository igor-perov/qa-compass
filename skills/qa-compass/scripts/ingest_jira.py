from __future__ import annotations

import argparse
import json
from pathlib import Path

from io_utils import read_json, write_json


def ingest_jira_json(input_path: str) -> dict:
    payload = read_json(input_path)
    issues = payload.get("issues") or payload.get("items") or []
    if not issues:
        raise ValueError("Input Jira JSON must contain a non-empty 'issues' or 'items' array.")

    return {
        "project_name": payload.get("project_name", "Jira QA Source"),
        "source_mode": "jira",
        "issues": [canonicalize_issue(issue) for issue in issues],
    }


def canonicalize_issue(issue: dict) -> dict:
    if issue.get("issue"):
        issue = issue["issue"]
    fields = issue.get("fields", issue)
    return {
        "issue_key": issue.get("key") or fields.get("key", ""),
        "summary": fields.get("summary", ""),
        "description": fields.get("description", ""),
        "status": value_name(fields.get("status")),
        "issue_type": value_name(fields.get("issuetype")),
        "priority": value_name(fields.get("priority")),
        "epic": field_value(fields, ("epic", "epic_key", "parent")),
        "sprint": field_value(fields, ("sprint", "fixVersion", "fixVersions")),
        "components": force_name_list(fields.get("components")),
        "labels": fields.get("labels") or [],
        "linked_issues": force_name_list(fields.get("issuelinks")),
        "source_urls": collect_urls(fields),
        "updated": fields.get("updated", ""),
    }


def value_name(value) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or value.get("key") or "")
    return str(value or "")


def field_value(fields: dict, names: tuple[str, ...]) -> str:
    for name in names:
        if fields.get(name):
            value = fields[name]
            if isinstance(value, list):
                return ", ".join(value_name(item) for item in value if value_name(item))
            return value_name(value)
    return ""


def force_name_list(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [value_name(item) for item in value if value_name(item)]
    return [value_name(value)] if value_name(value) else []


def collect_urls(fields: dict) -> list[str]:
    urls = []
    for key in ("source_urls", "confluence_urls", "links"):
        value = fields.get(key)
        if isinstance(value, list):
            urls.extend(str(item) for item in value if item)
        elif value:
            urls.append(str(value))
    return sorted(set(urls))


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Jira issues JSON into a canonical QA source artifact.")
    parser.add_argument("--input", required=True, help="Path to Jira issues JSON export.")
    parser.add_argument("--output", required=True, help="Path to write jira-issues.json.")
    args = parser.parse_args()
    result = ingest_jira_json(args.input)
    write_json(Path(args.output), result)
    print(json.dumps({"output": args.output, "issues": len(result["issues"])}, indent=2))


if __name__ == "__main__":
    main()
