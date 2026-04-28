from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from html import escape
from pathlib import Path

from io_utils import read_json, render_template, write_json, write_text


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
AUTH_KEYWORDS = (
    "account",
    "authenticate",
    "authenticated",
    "credentials",
    "log in",
    "logged in",
    "login",
    "password",
    "register",
    "registration",
    "sign in",
    "sign-in",
    "signup",
    "user is logged in",
)
OTP_KEYWORDS = (
    "2fa",
    "email code",
    "magic link",
    "mfa",
    "one-time",
    "one time",
    "otp",
    "sms code",
    "verification code",
)


def build_scope_preview(
    test_cases_path: str,
    output_dir: str,
    subset_path: str | None = None,
    requirements_path: str | None = None,
    roles_path: str | None = None,
    grouping_path: str | None = None,
) -> dict:
    test_cases_payload = read_json(test_cases_path)
    subset_payload = read_optional_json(subset_path)
    requirements_payload = read_optional_json(requirements_path)
    roles_payload = read_optional_json(roles_path)
    grouping_payload = read_optional_json(grouping_path)

    all_cases = canonical_cases(test_cases_payload)
    selected_cases = canonical_cases(subset_payload) if subset_payload else all_cases
    grouping_strategy = infer_grouping_strategy(
        subset_payload,
        test_cases_payload,
        grouping_payload,
        selected_cases,
    )
    project_name = first_value(
        subset_payload,
        test_cases_payload,
        requirements_payload,
        key="project_name",
        default="QA Scope Preview",
    )
    subset_mode = first_value(subset_payload, test_cases_payload, key="mode", default="full-suite")
    source_mode = first_value(test_cases_payload, requirements_payload, key="source_mode", default="test_cases")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    groups = build_groups(selected_cases, grouping_strategy)
    roles = build_roles(selected_cases, test_cases_payload, roles_payload)
    coverage = build_coverage(all_cases, selected_cases, groups)
    warnings = build_warnings(all_cases, selected_cases, roles)
    execution_readiness = build_execution_readiness(
        selected_cases,
        subset_payload,
        test_cases_payload,
        requirements_payload,
    )
    preview_payload = {
        "project_name": project_name,
        "source_mode": source_mode,
        "subset_mode": subset_mode,
        "grouping_strategy": grouping_strategy,
        "total_cases": len(all_cases),
        "selected_cases": len(selected_cases),
        "coverage": coverage,
        "roles": roles,
        "warnings": warnings,
        "execution_readiness": execution_readiness,
        "artifact_links": {
            "test_cases": relative_href(test_cases_path, destination),
            "execution_subset": relative_href(subset_path, destination) if subset_path else "",
        },
    }

    write_json(destination / "qa-scope-preview.json", preview_payload)
    write_text(destination / "qa-scope-preview.md", render_markdown_preview(preview_payload))
    write_text(destination / "qa-scope-preview.html", render_html_preview(preview_payload))

    return {
        "output_dir": str(destination),
        "html": str(destination / "qa-scope-preview.html"),
        "markdown": str(destination / "qa-scope-preview.md"),
        "json": str(destination / "qa-scope-preview.json"),
        "total_cases": len(all_cases),
        "selected_cases": len(selected_cases),
        "grouping_strategy": grouping_strategy,
        "groups": len(groups),
        "warnings": len(warnings),
    }


def read_optional_json(path: str | None) -> dict:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.exists():
        return {}
    return read_json(candidate)


def canonical_cases(payload: dict) -> list[dict]:
    raw_cases = payload.get("test_cases") or payload.get("cases") or []
    return [canonical_case(item) for item in raw_cases]


def canonical_case(item: dict) -> dict:
    return {
        "test_case_id": item.get("test_case_id") or item.get("id") or "",
        "title": item.get("title") or item.get("name") or "Untitled test case",
        "feature": item.get("feature") or item.get("module") or item.get("suite") or "",
        "module": item.get("module") or item.get("feature") or "",
        "role": item.get("role") or "",
        "roles": force_list(item.get("roles") or item.get("role")),
        "source_section": item.get("source_section") or "",
        "jira_epic": item.get("jira_epic") or item.get("epic") or "",
        "jira_component": item.get("jira_component") or item.get("component") or "",
        "group": item.get("group") or item.get("custom_group") or "",
        "requirement_ids": force_list(item.get("requirement_ids") or item.get("requirements")),
        "priority": item.get("priority") or "Medium",
        "type": item.get("type") or item.get("category") or "Functional",
        "preconditions": force_list(item.get("preconditions")),
        "steps": force_list(item.get("steps")),
        "expected_results": force_list(item.get("expected_results") or item.get("expected")),
        "automation_candidate": bool(item.get("automation_candidate", True)),
    }


def infer_grouping_strategy(*payloads_and_cases) -> str:
    selected_cases = payloads_and_cases[-1]
    payloads = payloads_and_cases[:-1]
    for payload in payloads:
        strategy = normalize_grouping_strategy(str(payload.get("grouping_strategy") or "").strip().lower())
        if strategy:
            return strategy
        strategy = normalize_grouping_strategy(str(payload.get("selected") or payload.get("recommended") or "").strip().lower())
        if strategy:
            return strategy
    if any(case.get("feature") for case in selected_cases):
        return "feature"
    return "custom"


def normalize_grouping_strategy(strategy: str) -> str:
    aliases = {
        "features": "feature",
        "modules": "module",
        "roles": "role",
        "epic": "jira_epic",
        "component": "jira_component",
        "source": "source_section",
        "section": "source_section",
    }
    return aliases.get(strategy, strategy)


def build_groups(cases: list[dict], grouping_strategy: str) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for case in cases:
        for name in group_names(case, grouping_strategy):
            grouped.setdefault(name, []).append(case)
    return [
        {
            "name": name,
            "case_count": len(items),
            "priority_counts": dict(Counter(item["priority"] for item in items)),
            "type_counts": dict(Counter(item["type"] for item in items)),
            "roles": sorted({role for item in items for role in role_names(item)}),
            "requirement_ids": sorted({req for item in items for req in item["requirement_ids"]}),
            "cases": sorted(items, key=lambda item: item["test_case_id"]),
        }
        for name, items in sorted(grouped.items(), key=lambda entry: entry[0].lower())
    ]


def group_names(case: dict, grouping_strategy: str) -> list[str]:
    fields = {
        "feature": "feature",
        "module": "module",
        "role": "roles",
        "source_section": "source_section",
        "jira_epic": "jira_epic",
        "jira_component": "jira_component",
        "custom": "group",
    }
    field = fields.get(grouping_strategy, "feature")
    values = force_list(case.get(field))
    names = [str(value).strip() for value in values if str(value).strip()]
    return names or ["Ungrouped"]


def build_roles(selected_cases: list[dict], test_cases_payload: dict, roles_payload: dict) -> dict:
    declared = set(force_list(test_cases_payload.get("roles")))
    raw_roles = roles_payload.get("roles") or roles_payload.get("detected_roles") or []
    for item in raw_roles:
        if isinstance(item, dict):
            declared.add(str(item.get("name") or item.get("role") or "").strip())
        else:
            declared.add(str(item).strip())
    declared.discard("")

    covered = sorted({role for case in selected_cases for role in role_names(case)} | declared)
    return {
        "covered": covered,
        "declared": sorted(declared),
        "missing_from_cases": sorted(declared - {role for case in selected_cases for role in role_names(case)}),
    }


def role_names(case: dict) -> list[str]:
    roles = force_list(case.get("roles") or case.get("role"))
    return [role for role in roles if role]


def build_coverage(all_cases: list[dict], selected_cases: list[dict], groups: list[dict]) -> dict:
    requirement_ids = sorted({req for case in selected_cases for req in case["requirement_ids"]})
    return {
        "priority_counts": dict(Counter(case["priority"] for case in selected_cases)),
        "type_counts": dict(Counter(case["type"] for case in selected_cases)),
        "requirement_ids": requirement_ids,
        "requirements_covered": len(requirement_ids),
        "automation_candidates": sum(1 for case in selected_cases if case["automation_candidate"]),
        "not_selected_cases": max(len(all_cases) - len(selected_cases), 0),
        "groups": groups,
    }


def build_warnings(all_cases: list[dict], selected_cases: list[dict], roles: dict) -> list[str]:
    warnings = []
    no_requirement_links = [case["test_case_id"] for case in selected_cases if not case["requirement_ids"]]
    if no_requirement_links:
        warnings.append(f"{len(no_requirement_links)} selected cases have no linked requirement IDs.")
    no_expected_results = [case["test_case_id"] for case in selected_cases if not case["expected_results"]]
    if no_expected_results:
        warnings.append(f"{len(no_expected_results)} selected cases have no expected result.")
    if roles["missing_from_cases"]:
        warnings.append("Declared roles are not attached to individual selected cases: " + ", ".join(roles["missing_from_cases"]))
    if len(selected_cases) < len(all_cases):
        warnings.append(f"{len(all_cases) - len(selected_cases)} cases are outside this execution subset.")
    return warnings


def render_html_preview(preview: dict) -> str:
    return render_template(
        TEMPLATES_DIR / "scope-preview.template.html",
        {
            "project_name": escape(preview["project_name"]),
            "source_mode": escape(preview["source_mode"]),
            "subset_mode": escape(preview["subset_mode"]),
            "grouping_label": escape(grouping_label(preview["grouping_strategy"])),
            "total_cases": preview["total_cases"],
            "selected_cases": preview["selected_cases"],
            "requirements_covered": preview["coverage"]["requirements_covered"],
            "groups_count": len(preview["coverage"]["groups"]),
            "priority_chips": render_count_chips(preview["coverage"]["priority_counts"]),
            "type_chips": render_count_chips(preview["coverage"]["type_counts"]),
            "confirmation_gate_section": render_confirmation_gate(preview["execution_readiness"]),
            "warnings_section": render_warnings_section(preview["warnings"]),
            "artifact_links_section": render_artifact_links(preview["artifact_links"]),
            "groups_section": render_groups_section(preview["coverage"]["groups"]),
        },
    )


def render_markdown_preview(preview: dict) -> str:
    return render_template(
        TEMPLATES_DIR / "scope-preview.template.md",
        {
            "project_name": preview["project_name"],
            "source_mode": preview["source_mode"],
            "subset_mode": preview["subset_mode"],
            "grouping_label": grouping_label(preview["grouping_strategy"]),
            "total_cases": preview["total_cases"],
            "selected_cases": preview["selected_cases"],
            "requirements_covered": preview["coverage"]["requirements_covered"],
            "confirmation_gate": render_markdown_confirmation_gate(preview["execution_readiness"]),
            "warnings": render_markdown_list(preview["warnings"], "No scope warnings detected."),
            "artifact_links": render_markdown_artifact_links(preview["artifact_links"]),
            "groups": render_markdown_groups(preview["coverage"]["groups"]),
        },
    )


def render_count_chips(counts: dict) -> str:
    if not counts:
        return '<span class="chip muted-chip">None</span>'
    return "".join(f'<span class="chip">{escape(str(name))}: {count}</span>' for name, count in sorted(counts.items()))


def render_warnings_section(warnings: list[str]) -> str:
    if not warnings:
        return '<div class="ready-state">Ready for execution review</div>'
    items = "".join(f"<li>{escape(item)}</li>" for item in warnings)
    return f'<div class="ready-state warning-state">Ready for execution review</div><ul class="warning-list">{items}</ul>'


def render_confirmation_gate(readiness: dict) -> str:
    questions = "".join(f"<li>{escape(item)}</li>" for item in readiness["blocking_questions"])
    flags = [
        ("Environment", readiness["environment"] or "Needs confirmation"),
        ("Auth / access", "Needed" if readiness["requires_auth"] else "Not detected"),
        ("OTP / MFA", "User-assisted" if readiness["requires_otp"] else "Not detected"),
    ]
    chips = "".join(f'<span class="chip">{escape(label)}: {escape(value)}</span>' for label, value in flags)
    return (
        '<div class="confirmation-gate">'
        '<div class="ready-state hold-state">Confirmation Required</div>'
        '<p>Do not start browser execution until the user confirms this scope and answers the blockers below.</p>'
        f'<div class="chip-row">{chips}</div>'
        f'<ul class="warning-list">{questions}</ul>'
        "</div>"
    )


def render_markdown_confirmation_gate(readiness: dict) -> str:
    lines = [
        "- Status: `Confirmation Required`",
        "- Stop rule: Do not start browser execution until the user confirms this scope.",
        f"- Environment: `{readiness['environment'] or 'Needs confirmation'}`",
        f"- Auth/access needed: `{yes_no(readiness['requires_auth'])}`",
        f"- OTP/MFA handling needed: `{yes_no(readiness['requires_otp'])}`",
        "",
        "Questions before execution:",
    ]
    lines.extend(f"- {item}" for item in readiness["blocking_questions"])
    return "\n".join(lines)


def render_artifact_links(artifact_links: dict) -> str:
    links = [
        f'<a class="artifact-link" href="{escape(artifact_links["test_cases"])}">Open full test-cases.json</a>'
    ]
    if artifact_links.get("execution_subset"):
        links.append(
            f'<a class="artifact-link secondary-link" href="{escape(artifact_links["execution_subset"])}">Open execution-subset.json</a>'
        )
    return '<div class="artifact-links">' + "".join(links) + "</div>"


def render_groups_section(groups: list[dict]) -> str:
    if not groups:
        return '<div class="empty-state">No test cases were selected.</div>'
    return "\n".join(render_group(group) for group in groups)


def render_group(group: dict) -> str:
    requirements = ", ".join(group["requirement_ids"]) or "No requirement links"
    case_rows = "".join(render_case_row(case) for case in group["cases"])
    return (
        '<section class="scope-group">'
        '<div class="scope-group-head">'
        f'<div><h3>{escape(group["name"])}</h3></div>'
        f'<span>{group["case_count"]} selected</span>'
        "</div>"
        '<div class="group-meta">'
        f"<span>Requirements: {escape(requirements)}</span>"
        f"<span>Priority: {escape(format_counts(group['priority_counts']))}</span>"
        f"<span>Types: {escape(format_counts(group['type_counts']))}</span>"
        "</div>"
        f'<div class="case-list">{case_rows}</div>'
        "</section>"
    )


def render_case_row(case: dict) -> str:
    requirements = ", ".join(case["requirement_ids"]) or "No requirements"
    return (
        '<div class="case-row">'
        f'<span class="case-id">{escape(case["test_case_id"])}</span>'
        f'<span class="case-title">{escape(case["title"])}</span>'
        '<span class="case-tags">'
        f'<b>{escape(case["priority"])}</b>'
        f'<em>{escape(case["type"])}</em>'
        f'<small>{escape(requirements)}</small>'
        "</span>"
        "</div>"
    )


def render_markdown_groups(groups: list[dict]) -> str:
    if not groups:
        return "No test cases were selected."
    sections = []
    for group in groups:
        cases = "\n".join(f"- `{case['test_case_id']}` {case['title']} ({case['priority']})" for case in group["cases"])
        sections.append(
            "\n".join(
                [
                    f"## {group['name']}",
                    f"- Selected cases: {group['case_count']}",
                    f"- Requirements: {', '.join(group['requirement_ids']) or 'None'}",
                    "",
                    cases,
                ]
            )
        )
    return "\n\n".join(sections)


def render_markdown_list(items: list[str], empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def render_markdown_artifact_links(artifact_links: dict) -> str:
    rows = [f"- Full test cases: {artifact_links['test_cases']}"]
    if artifact_links.get("execution_subset"):
        rows.append(f"- Execution subset: {artifact_links['execution_subset']}")
    return "\n".join(rows)


def build_execution_readiness(selected_cases: list[dict], *payloads: dict) -> dict:
    environment = first_available_key(
        payloads,
        ("environment", "environment_url", "target_url", "base_url", "url"),
    )
    auth_required = any(case_has_keywords(case, AUTH_KEYWORDS) for case in selected_cases)
    otp_required = any(case_has_keywords(case, OTP_KEYWORDS) for case in selected_cases)

    questions = [
        "Confirm that this scope and selected cases are correct, or describe what should change before execution.",
    ]
    if not environment:
        questions.append("Provide the exact environment URL to test.")
    if auth_required:
        questions.append("Confirm the test account, role, credentials/access path, and any required test data.")
    if otp_required:
        questions.append(
            "Confirm OTP/MFA handling. If the code is sent to your email or phone, stay available and provide the current code when QA Compass stops and asks for it."
        )
    questions.append("Confirm any feature flags, seed data, allowlists, or access constraints that could block the run.")

    return {
        "confirmation_required": True,
        "must_stop_before_execution": True,
        "environment": environment,
        "requires_auth": auth_required,
        "requires_otp": otp_required,
        "blocking_questions": questions,
    }


def first_available_key(payloads: tuple[dict, ...], keys: tuple[str, ...]) -> str:
    for payload in payloads:
        for key in keys:
            value = payload.get(key)
            if value not in (None, "", [], {}):
                return str(value)
    return ""


def case_has_keywords(case: dict, keywords: tuple[str, ...]) -> bool:
    lowered = " ".join(
        [
            case.get("title", ""),
            case.get("type", ""),
            case.get("feature", ""),
            case.get("module", ""),
            " ".join(case.get("preconditions", [])),
            " ".join(case.get("steps", [])),
            " ".join(case.get("expected_results", [])),
        ]
    ).lower()
    return any(keyword in lowered for keyword in keywords)


def grouping_label(strategy: str) -> str:
    labels = {
        "feature": "Grouped by Feature",
        "module": "Grouped by Module",
        "role": "Grouped by Role",
        "source_section": "Grouped by Source Section",
        "jira_epic": "Grouped by Jira Epic",
        "jira_component": "Grouped by Jira Component",
        "custom": "Grouped by Custom Scope",
    }
    return labels.get(strategy, "Grouped by Feature")


def format_counts(counts: dict) -> str:
    return ", ".join(f"{name} {count}" for name, count in sorted(counts.items())) or "None"


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def first_value(*payloads: dict, key: str, default: str) -> str:
    for payload in payloads:
        value = payload.get(key)
        if value not in (None, "", [], {}):
            return str(value)
    return default


def relative_href(path: str | None, output_dir: Path) -> str:
    if not path:
        return ""
    try:
        return Path(os.path.relpath(Path(path).resolve(), output_dir.resolve())).as_posix()
    except ValueError:
        return Path(path).resolve().as_uri()


def force_list(value) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pre-execution QA scope preview artifacts from test cases.")
    parser.add_argument("--test-cases", required=True, help="Path to canonical test-cases.json.")
    parser.add_argument("--output-dir", required=True, help="Directory to write qa-scope-preview artifacts.")
    parser.add_argument("--subset", help="Optional execution-subset.json.")
    parser.add_argument("--requirements", help="Optional requirements-normalized.json.")
    parser.add_argument("--roles", help="Optional roles.json.")
    parser.add_argument("--grouping", help="Optional grouping-proposal.json.")
    args = parser.parse_args()
    print(
        json.dumps(
            build_scope_preview(
                args.test_cases,
                args.output_dir,
                subset_path=args.subset,
                requirements_path=args.requirements,
                roles_path=args.roles,
                grouping_path=args.grouping,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
