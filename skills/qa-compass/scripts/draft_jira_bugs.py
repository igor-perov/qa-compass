from __future__ import annotations

import argparse
import json
from pathlib import Path

from io_utils import read_json, render_template, write_json, write_text


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def draft_jira_bugs(input_path: str, output_dir: str) -> dict:
    payload = read_json(input_path)
    results = payload.get("results", [])
    failed_results = [result for result in results if result.get("status") == "Failed"]
    drafts = [build_draft(index + 1, result, payload) for index, result in enumerate(failed_results)]

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    write_json(destination / "jira-bug-drafts.json", {"project_name": payload.get("project_name", ""), "drafts": drafts})
    write_text(destination / "jira-bug-drafts.md", render_drafts_markdown(drafts))

    return {
        "draft_count": len(drafts),
        "json": str(destination / "jira-bug-drafts.json"),
        "markdown": str(destination / "jira-bug-drafts.md"),
    }


def build_draft(index: int, result: dict, payload: dict) -> dict:
    failure = result.get("failure_details") or "Failed behavior was observed during QA execution."
    return {
        "draft_id": f"BUG-{index:03d}",
        "summary": f"{result.get('title', 'Failed QA case')} fails in {payload.get('environment', result.get('environment', 'target environment'))}",
        "issue_type": "Bug",
        "priority": result.get("priority") or infer_priority(result),
        "environment": result.get("environment") or payload.get("environment", ""),
        "linked_test_case_id": result.get("test_case_id", ""),
        "requirement_ids": result.get("requirement_ids", []),
        "steps_to_reproduce": result.get("executed_steps", []),
        "expected_result": "Behavior should match the linked requirement and test case expected result.",
        "actual_result": failure,
        "evidence": result.get("evidence", []),
        "notes": result.get("notes", []),
    }


def infer_priority(result: dict) -> str:
    title = str(result.get("title", "")).lower()
    if any(token in title for token in ("block", "payment", "login", "auth", "security")):
        return "High"
    return "Medium"


def render_drafts_markdown(drafts: list[dict]) -> str:
    sections = []
    for draft in drafts:
        sections.append(
            "\n".join(
                [
                    f"## Draft {draft['draft_id']}: {draft['summary']}",
                    "",
                    f"- Issue type: `{draft['issue_type']}`",
                    f"- Priority: `{draft['priority']}`",
                    f"- Environment: `{draft['environment']}`",
                    f"- Linked test case: `{draft['linked_test_case_id']}`",
                    f"- Requirement IDs: `{', '.join(draft['requirement_ids']) or 'None'}`",
                    "",
                    "### Steps To Reproduce",
                    render_numbered(draft["steps_to_reproduce"]),
                    "",
                    "### Expected Result",
                    draft["expected_result"],
                    "",
                    "### Actual Result",
                    draft["actual_result"],
                    "",
                    "### Evidence",
                    render_bullets(draft["evidence"], "No evidence paths captured."),
                    "",
                    "### Notes",
                    render_bullets(draft["notes"], "No additional notes."),
                    "",
                ]
            )
        )

    return render_template(
        TEMPLATES_DIR / "jira-bug-drafts.template.md",
        {"draft_sections": "\n".join(sections).rstrip() or "No confirmed failed cases to draft."},
    )


def render_numbered(items: list[str]) -> str:
    if not items:
        return "No executed steps captured."
    return "\n".join(f"{index + 1}. {item}" for index, item in enumerate(items))


def render_bullets(items: list[str], empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- `{item}`" for item in items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft Jira-ready bug payloads from failed QA execution results.")
    parser.add_argument("--input", required=True, help="Path to execution-results.json.")
    parser.add_argument("--output-dir", required=True, help="Directory to write jira-bug-drafts.json/md.")
    args = parser.parse_args()
    print(json.dumps(draft_jira_bugs(args.input, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
