from __future__ import annotations

import argparse
import json


DEFAULT_READY_STATUSES = ("Ready for QA", "Ready for Regression", "Ready for Release")

DEFAULT_FIELDS = [
    "key",
    "summary",
    "description",
    "status",
    "issuetype",
    "priority",
    "parent",
    "sprint",
    "fixVersions",
    "components",
    "labels",
    "issuelinks",
    "updated",
]


def build_jira_query_plan(
    project_key: str,
    mode: str,
    statuses: list[str] | None = None,
    issue_keys: list[str] | None = None,
    epic_key: str | None = None,
    fix_version: str | None = None,
    component: str | None = None,
    max_results: int = 50,
) -> dict:
    project_clause = f'project = {jql_quote(project_key)}'
    normalized_mode = mode.strip().lower()

    if normalized_mode == "ready-for-qa":
        selected_statuses = statuses or list(DEFAULT_READY_STATUSES)
        scope_clause = f"status in ({quote_list(selected_statuses)})"
        notes = "Use this for conventional Ready for QA style workflows."
    elif normalized_mode == "current-sprint":
        scope_clause = "sprint in openSprints()"
        notes = "Use this when the user wants the active sprint scope."
    elif normalized_mode == "status":
        if not statuses:
            raise ValueError("status mode requires at least one status.")
        scope_clause = f"status in ({quote_list(statuses)})"
        notes = "Use this when the user supplied project-specific QA statuses."
    elif normalized_mode == "issue-keys":
        if not issue_keys:
            raise ValueError("issue-keys mode requires at least one issue key.")
        project_clause = ""
        scope_clause = f"issuekey in ({quote_list(issue_keys)})"
        notes = "Use this when the user supplied exact Jira issue keys."
    elif normalized_mode == "epic":
        if not epic_key:
            raise ValueError("epic mode requires an epic key.")
        scope_clause = f'(parent = {jql_quote(epic_key)} OR "Epic Link" = {jql_quote(epic_key)})'
        notes = "Use this for epic-scoped QA intake."
    elif normalized_mode == "release":
        if not fix_version:
            raise ValueError("release mode requires a fix version.")
        scope_clause = f"fixVersion = {jql_quote(fix_version)}"
        notes = "Use this for release or fixVersion-scoped QA intake."
    elif normalized_mode == "component":
        if not component:
            raise ValueError("component mode requires a component name.")
        scope_clause = f"component = {jql_quote(component)}"
        notes = "Use this for component-scoped QA intake."
    else:
        raise ValueError(f"Unsupported Jira query mode: {mode}")

    clauses = [clause for clause in (project_clause, scope_clause) if clause]
    jql = " AND ".join(clauses) + " ORDER BY priority DESC, updated DESC"
    return {
        "connector_tool": "mcp__codex_apps__atlassian_rovo._searchjiraissuesusingjql",
        "jql": jql,
        "fields": DEFAULT_FIELDS,
        "maxResults": max_results,
        "mode": normalized_mode,
        "notes": notes,
    }


def jql_quote(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def quote_list(values: list[str] | tuple[str, ...]) -> str:
    return ", ".join(jql_quote(value) for value in values)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a Jira JQL intake plan for QA Compass.")
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--status", action="append", dest="statuses")
    parser.add_argument("--issue-key", action="append", dest="issue_keys")
    parser.add_argument("--epic-key")
    parser.add_argument("--fix-version")
    parser.add_argument("--component")
    parser.add_argument("--max-results", type=int, default=50)
    args = parser.parse_args()
    plan = build_jira_query_plan(
        project_key=args.project_key,
        mode=args.mode,
        statuses=args.statuses,
        issue_keys=args.issue_keys,
        epic_key=args.epic_key,
        fix_version=args.fix_version,
        component=args.component,
        max_results=args.max_results,
    )
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
