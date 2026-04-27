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
    expected_results = force_list(result.get("expected_results") or result.get("expected_result"))
    return {
        "draft_id": f"BUG-{index:03d}",
        "summary": f"{result.get('title', 'Failed QA case')} fails in {payload.get('environment', result.get('environment', 'target environment'))}",
        "issue_type": "Bug",
        "priority": result.get("priority") or infer_priority(result),
        "environment": result.get("environment") or payload.get("environment", ""),
        "linked_test_case_id": result.get("test_case_id", ""),
        "requirement_ids": result.get("requirement_ids", []),
        "steps_to_reproduce": result.get("executed_steps", []),
        "expected_result": "\n".join(expected_results) or "Behavior should match the linked requirement and test case expected result.",
        "actual_result": result.get("actual_result") or failure,
        "console_errors": force_list(result.get("console_errors")),
        "network_errors": force_list(result.get("network_errors")),
        "browser_context": build_browser_context(result),
        "diagnostic_details": result.get("diagnostic_details", {}),
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
                    "### Console Errors",
                    render_bullets(draft["console_errors"], "No console errors captured."),
                    "",
                    "### Network / API Errors",
                    render_bullets(draft["network_errors"], "No network or API errors captured."),
                    "",
                    "### Browser Context",
                    render_mapping(draft["browser_context"], "No browser context captured."),
                    "",
                    "### Diagnostic Details",
                    render_mapping(draft["diagnostic_details"], "No extra diagnostic details captured."),
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
    return "\n".join(f"- `{format_value(item)}`" for item in items)


def render_mapping(items: dict, empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- `{key}`: `{format_value(value)}`" for key, value in items.items() if value not in (None, "", [], {}))


def force_list(value) -> list:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


def build_browser_context(result: dict) -> dict:
    context = result.get("browser_context") or {}
    if not isinstance(context, dict):
        return {"details": context}

    aliases = {
        "current_url": ("current_url", "page_url", "url"),
        "browser": ("browser", "browser_name"),
        "viewport": ("viewport", "viewport_size"),
        "role": ("role", "user_role"),
        "account": ("account", "test_account"),
    }
    merged = {key: value for key, value in context.items() if value not in (None, "", [], {})}
    for canonical, keys in aliases.items():
        if canonical in merged:
            continue
        for key in keys:
            value = result.get(key)
            if value not in (None, "", [], {}):
                merged[canonical] = value
                break
    return merged


def format_value(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft Jira-ready bug payloads from failed QA execution results.")
    parser.add_argument("--input", required=True, help="Path to execution-results.json.")
    parser.add_argument("--output-dir", required=True, help="Directory to write jira-bug-drafts.json/md.")
    args = parser.parse_args()
    print(json.dumps(draft_jira_bugs(args.input, args.output_dir), indent=2))


if __name__ == "__main__":
    main()
