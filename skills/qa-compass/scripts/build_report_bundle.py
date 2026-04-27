from __future__ import annotations

import argparse
import json
import os
import shutil
from html import escape
from pathlib import Path
from urllib.parse import quote, urlparse

from io_utils import read_json, render_template, write_json, write_text

try:
    from build_artifact_manifest import KNOWN_ARTIFACTS, default_metadata
except ImportError:  # pragma: no cover - direct script fallback
    KNOWN_ARTIFACTS = {}

    def default_metadata(filename: str) -> dict:
        return {
            "label": filename,
            "description": "Generated run artifact.",
            "created_by": "unknown",
            "source_of_truth": False,
        }


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")


def build_counts(results: list[dict]) -> dict:
    return {
        "executed": len(results),
        "passed": sum(1 for item in results if item.get("status") == "Passed"),
        "failed": sum(1 for item in results if item.get("status") == "Failed"),
        "blocked": sum(1 for item in results if item.get("status") == "Blocked"),
    }


def classify_defects(results: list[dict]) -> list[dict]:
    defects = []
    defect_index = 1
    for result in results:
        if result.get("status") != "Failed":
            continue
        evidence = result.get("evidence") or []
        defects.append(
            {
                "defect_id": f"BUG-{defect_index:03d}",
                "test_case_id": result.get("test_case_id", ""),
                "title": result.get("title", "Unnamed failed case"),
                "requirement_ids": result.get("requirement_ids", []),
                "roles": role_names(result),
                "executed_steps": result.get("executed_steps", []),
                "expected_results": force_list(result.get("expected_results") or result.get("expected_result")),
                "actual_result": result.get("actual_result", ""),
                "failure_details": result.get("failure_details", ""),
                "console_errors": force_list(result.get("console_errors")),
                "network_errors": force_list(result.get("network_errors")),
                "browser_context": build_browser_context(result),
                "diagnostic_details": result.get("diagnostic_details", {}),
                "notes": result.get("notes", []),
                "evidence": evidence,
                "primary_screenshot": first_image_reference(evidence),
            }
        )
        defect_index += 1
    return defects


def build_report_bundle(input_path: str, output_dir: str) -> dict:
    payload = read_json(input_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    results = payload.get("results", [])
    prepare_evidence_assets(results, Path(input_path).resolve().parent, destination)
    counts = build_counts(results)
    defects = classify_defects(results)
    blocked_cases = [item for item in results if item.get("status") == "Blocked"]
    report_input = {
        "project_name": payload.get("project_name", "QA Report"),
        "run_date": payload.get("run_date", ""),
        "environment": payload.get("environment", ""),
        "subset_mode": payload.get("subset_mode", "custom"),
        "grouping_strategy": infer_grouping_strategy(payload, results),
        "requirements_count": payload.get("requirements_count", 0),
        "test_cases_count": payload.get("test_cases_count", len(results)),
        "results": results,
        "counts": counts,
        "defects": defects,
        "blocked_cases": blocked_cases,
    }

    execution_plan = render_execution_plan(report_input)
    execution_results = render_execution_results(report_input)
    run_summary = build_run_summary(report_input)
    external_html_report = render_external_html_report(report_input)

    write_text(destination / "execution-plan.md", execution_plan)
    write_text(destination / "execution-results.md", execution_results)
    write_json(destination / "run-summary.json", run_summary)
    write_text(destination / "qa-report.external.html", external_html_report)
    internal_html_report = render_internal_html_report(report_input, destination)
    write_text(destination / "qa-report.internal.html", internal_html_report)
    write_text(destination / "qa-report.html", internal_html_report)
    return run_summary


def build_run_summary(report_input: dict) -> dict:
    return {
        "project_name": report_input["project_name"],
        "run_date": report_input["run_date"],
        "environment": report_input["environment"],
        "subset_mode": report_input["subset_mode"],
        "grouping_strategy": report_input["grouping_strategy"],
        "counts": report_input["counts"],
        "defects": report_input["defects"],
        "blocked_cases": [
            {
                "test_case_id": item.get("test_case_id"),
                "title": item.get("title"),
                "roles": role_names(item),
                "blocker_details": item.get("blocker_details", ""),
            }
            for item in report_input["blocked_cases"]
        ],
    }


def render_execution_plan(report_input: dict) -> str:
    planned_cases = "\n".join(
        f"- `{item.get('test_case_id')}` — {item.get('title')} ({item.get('status')})"
        for item in report_input["results"]
    )
    return render_template(
        TEMPLATES_DIR / "execution-plan.template.md",
        {
            "project_name": report_input["project_name"],
            "environment": report_input["environment"],
            "subset_mode": report_input["subset_mode"],
            "planned_cases": planned_cases,
        },
    )


def render_execution_results(report_input: dict) -> str:
    summary_bullets = "\n".join(
        [
            f"- Environment: `{report_input['environment']}`",
            f"- Executed: `{report_input['counts']['executed']}`",
            f"- Passed: `{report_input['counts']['passed']}`",
            f"- Failed: `{report_input['counts']['failed']}`",
            f"- Blocked: `{report_input['counts']['blocked']}`",
        ]
    )
    case_sections = "\n\n".join(render_case_section(item) for item in report_input["results"])
    return render_template(
        TEMPLATES_DIR / "execution-results.template.md",
        {
            "summary_bullets": summary_bullets,
            "case_sections": case_sections,
        },
    )


def render_case_section(item: dict) -> str:
    lines = [
        f"## {item.get('test_case_id')} — {item.get('title')}",
        f"- Status: {item.get('status')}",
        f"- Priority: {item.get('priority', 'Unknown')}",
        f"- Type: {item.get('type', 'Unknown')}",
        "- Steps executed:",
    ]
    lines.extend([f"  {index + 1}. {step}" for index, step in enumerate(item.get("executed_steps", []))])
    if item.get("notes"):
        lines.append("- Notes:")
        lines.extend([f"  - {note}" for note in item["notes"]])
    if item.get("failure_details"):
        lines.append(f"- Failure: {item['failure_details']}")
    if item.get("blocker_details"):
        lines.append(f"- Blocker: {item['blocker_details']}")
    if item.get("evidence"):
        lines.append("- Evidence:")
        lines.extend([f"  - {ref}" for ref in item["evidence"]])
    return "\n".join(lines)


def render_html_report(report_input: dict) -> str:
    counts = report_input["counts"]
    return render_template(
        TEMPLATES_DIR / "report.template.html",
        {
            "project_name": escape(report_input["project_name"]),
            "run_date": escape(report_input["run_date"]),
            "environment": escape(report_input["environment"]),
            "subset_mode": escape(report_input["subset_mode"]),
            "requirements_count": counts_or_zero(report_input.get("requirements_count")),
            "test_cases_count": counts_or_zero(report_input.get("test_cases_count")),
            "executed_count": counts["executed"],
            "passed_count": counts["passed"],
            "failed_count": counts["failed"],
            "blocked_count": counts["blocked"],
            "defect_count": len(report_input["defects"]),
            "blocked_case_count": len(report_input["blocked_cases"]),
            "pie_chart_style": build_pie_chart_style(counts),
            "grouping_label": escape(grouping_label(report_input["grouping_strategy"])),
            "roles_overview_section": render_roles_overview(report_input["results"]),
            "results_sections": render_results_sections(report_input["results"], report_input["grouping_strategy"]),
            "blocked_cases_section": render_blocked_section(report_input["blocked_cases"]),
            "defect_section": render_defect_section(report_input["defects"]),
            "evidence_panels": render_evidence_panels(report_input["results"]),
        },
    )


def render_internal_html_report(report_input: dict, output_dir: Path | None = None) -> str:
    html = render_html_report(report_input)
    legend = render_artifact_details(output_dir)
    return html.replace('    <div class="dashboard">', f"{legend}\n\n    <div class=\"dashboard\">", 1)


def render_external_html_report(report_input: dict) -> str:
    counts = report_input["counts"]
    return render_template(
        TEMPLATES_DIR / "external-report.template.html",
        {
            "project_name": escape(report_input["project_name"]),
            "run_date": escape(report_input["run_date"]),
            "environment": escape(report_input["environment"]),
            "subset_mode": escape(report_input["subset_mode"]),
            "executed_count": counts["executed"],
            "passed_count": counts["passed"],
            "failed_count": counts["failed"],
            "blocked_count": counts["blocked"],
            "defect_count": len(report_input["defects"]),
            "pie_chart_style": build_pie_chart_style(counts),
            "external_defect_summary": render_external_defect_summary(report_input["defects"]),
            "external_blocker_summary": render_external_blocker_summary(report_input["blocked_cases"]),
        },
    )


def render_artifact_details(output_dir: Path | None = None) -> str:
    artifacts = discover_report_artifacts(output_dir)
    rows = render_artifact_list(artifacts)
    return (
        '<details class="section-card artifact-legend">'
        "<summary><strong>Generated files and artifact legend</strong></summary>"
        f"{rows}"
        "</details>"
    )


def discover_report_artifacts(output_dir: Path | None = None) -> list[tuple[str, str]]:
    expected_report_artifacts = [
        "execution-plan.md",
        "execution-results.md",
        "run-summary.json",
        "qa-report.external.html",
        "qa-report.internal.html",
        "qa-report.html",
    ]
    if output_dir is None:
        return [(path, artifact_description(path)) for path in expected_report_artifacts]

    artifacts: dict[str, str] = {}
    for manifest_path, manifest_root in artifact_manifest_paths(output_dir):
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for artifact in manifest.get("artifacts", []):
            path = str(artifact.get("path") or "").strip()
            if path:
                link_path = relative_artifact_link(manifest_root / path, output_dir)
                artifacts[link_path] = str(artifact.get("description") or artifact_description(path))

    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            relative_path = path.relative_to(output_dir).as_posix()
            artifacts.setdefault(relative_path, artifact_description(relative_path))

    for path in expected_report_artifacts:
        if (output_dir / path).exists() or path in {"qa-report.internal.html", "qa-report.html"}:
            artifacts.setdefault(path, artifact_description(path))

    return sorted(artifacts.items(), key=lambda item: item[0].lower())


def artifact_manifest_paths(output_dir: Path) -> list[tuple[Path, Path]]:
    return [
        (output_dir / "artifact-manifest.json", output_dir),
        (output_dir / "00-overview" / "artifact-manifest.json", output_dir),
        (output_dir.parent / "artifact-manifest.json", output_dir.parent),
        (output_dir.parent / "00-overview" / "artifact-manifest.json", output_dir.parent),
    ]


def relative_artifact_link(artifact_path: Path, output_dir: Path) -> str:
    return Path(os.path.relpath(artifact_path, output_dir)).as_posix()


def artifact_description(path: str) -> str:
    metadata = KNOWN_ARTIFACTS.get(Path(path).name, default_metadata(Path(path).name))
    return metadata["description"]


def render_artifact_list(artifacts: list[tuple[str, str]]) -> str:
    items = []
    for path, description in artifacts:
        items.append(
            "<li class=\"artifact-item\">"
            f'<a href="{escape(url_ref(path))}">{escape(path)}</a>'
            f'<span class="artifact-description">{escape(description)}</span>'
            "</li>"
        )
    return f'<ul class="artifact-list">{"".join(items)}</ul>'


def render_external_defect_summary(defects: list[dict]) -> str:
    if not defects:
        return '<p class="muted">No confirmed defects were recorded in this run.</p>'
    cards = []
    for defect in defects:
        cards.append(
            '<article class="issue">'
            f"<h3>{escape(defect['test_case_id'])}: {escape(defect['title'])}</h3>"
            f"<p>{escape(defect['failure_details'] or 'Failure details were not captured.')}</p>"
            "</article>"
        )
    return "\n".join(cards)


def render_external_blocker_summary(blocked_cases: list[dict]) -> str:
    if not blocked_cases:
        return '<p class="muted">No blocked cases were recorded in this run.</p>'
    cards = []
    for item in blocked_cases:
        cards.append(
            '<article class="issue">'
            f"<h3>{escape(item.get('test_case_id', ''))}: {escape(item.get('title', ''))}</h3>"
            f"<p>{escape(item.get('blocker_details') or 'Blocked without additional details.')}</p>"
            "</article>"
        )
    return "\n".join(cards)


def render_results_rows(results: list[dict]) -> str:
    rows = []
    for item in results:
        rows.append(
            "<tr>"
            f"<td data-label=\"ID\">{escape(item.get('test_case_id', ''))}</td>"
            f"<td data-label=\"Title\">{escape(item.get('title', ''))}</td>"
            f"<td data-label=\"Roles\">{render_role_chips(role_names(item))}</td>"
            f"<td data-label=\"Priority\">{escape(item.get('priority', 'Medium'))}</td>"
            f"<td data-label=\"Time\">{escape(item.get('duration', '-'))}</td>"
            f"<td data-label=\"Status\"><span class=\"status {escape(item.get('status', 'Unknown'))}\">{escape(item.get('status', 'Unknown'))}</span></td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_results_sections(results: list[dict], grouping_strategy: str) -> str:
    groups = group_results(results, grouping_strategy)
    sections = []
    for group_name, group_results_list in groups:
        rows = render_results_rows(group_results_list)
        count_label = "case" if len(group_results_list) == 1 else "cases"
        sections.append(
            "<section class=\"execution-group\">"
            "<div class=\"execution-group-head\">"
            f"<h3>{escape(group_name)}</h3>"
            f"<span>{len(group_results_list)} {count_label}</span>"
            "</div>"
            "<table>"
            "<thead><tr><th>ID</th><th>Title</th><th>Roles</th><th>Priority</th><th>Time</th><th>Status</th></tr></thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
            "</section>"
        )
    return "\n".join(sections)


def group_results(results: list[dict], grouping_strategy: str) -> list[tuple[str, list[dict]]]:
    grouped: dict[str, list[dict]] = {}
    for item in results:
        for group_name in result_group_names(item, grouping_strategy):
            grouped.setdefault(group_name, []).append(item)
    return sorted(grouped.items(), key=lambda entry: entry[0].lower())


def result_group_names(item: dict, grouping_strategy: str) -> list[str]:
    value = item.get(grouping_field(grouping_strategy))
    if grouping_strategy == "module" and not value:
        value = item.get("feature")
    if grouping_strategy == "custom" and not value:
        value = item.get("custom_group") or item.get("group")
    if grouping_strategy == "role" and not value:
        value = item.get("roles")

    values = force_list(value)
    names = [str(entry).strip() for entry in values if str(entry).strip()]
    return names or ["Ungrouped"]


def grouping_field(grouping_strategy: str) -> str:
    fields = {
        "feature": "feature",
        "module": "module",
        "role": "role",
        "source_section": "source_section",
        "jira_epic": "jira_epic",
        "jira_component": "jira_component",
        "custom": "group",
    }
    return fields.get(grouping_strategy, "feature")


def infer_grouping_strategy(payload: dict, results: list[dict]) -> str:
    strategy = str(payload.get("grouping_strategy") or "").strip().lower()
    if strategy:
        return normalize_grouping_strategy(strategy)
    if any(str(item.get("feature", "")).strip() for item in results):
        return "feature"
    return "custom"


def normalize_grouping_strategy(strategy: str) -> str:
    aliases = {
        "features": "feature",
        "product_feature": "feature",
        "product module": "module",
        "modules": "module",
        "roles": "role",
        "source": "source_section",
        "section": "source_section",
        "epic": "jira_epic",
        "component": "jira_component",
    }
    return aliases.get(strategy, strategy)


def grouping_label(grouping_strategy: str) -> str:
    labels = {
        "feature": "Grouped by Feature",
        "module": "Grouped by Module",
        "role": "Grouped by Role",
        "source_section": "Grouped by Source Section",
        "jira_epic": "Grouped by Jira Epic",
        "jira_component": "Grouped by Jira Component",
        "custom": "Grouped by Custom Scope",
    }
    return labels.get(grouping_strategy, "Grouped by Feature")


def render_blocked_section(blocked_cases: list[dict]) -> str:
    if not blocked_cases:
        return '<div class="empty-state">No blocked cases in this run.</div>'

    cards = []
    for item in blocked_cases:
        cards.append(
            "<article class=\"issue-card blocked\">"
            f"<div class=\"issue-head\"><h3>{escape(item.get('test_case_id', ''))}</h3><span class=\"status Blocked\">Blocked</span></div>"
            f"<h4>{escape(item.get('title', ''))}</h4>"
            f"{render_case_meta_chips(item)}"
            f"<p class=\"issue-summary\">{escape(item.get('blocker_details', 'Blocked without additional details.'))}</p>"
            "<div class=\"detail-block\">"
            "<span class=\"detail-label\">Steps executed</span>"
            f"{render_step_list(item.get('executed_steps', []))}"
            "</div>"
            f"{render_notes_block(item.get('notes', []))}"
            f"{render_evidence_block(item.get('evidence', []))}"
            "</article>"
        )
    return "\n".join(cards)


def render_defect_section(defects: list[dict]) -> str:
    if not defects:
        return '<div class="empty-state">No confirmed defects were recorded in this run.</div>'

    cards = []
    for defect in defects:
        cards.append(
            "<article class=\"issue-card defect\">"
            f"<div class=\"issue-head\"><h3>{escape(defect['defect_id'])}</h3><span class=\"status Failed\">Failed</span></div>"
            f"<h4>{escape(defect['title'])}</h4>"
            "<div class=\"meta-chips\">"
            f"<span class=\"chip\">Test Case: {escape(defect['test_case_id'])}</span>"
            f"<span class=\"chip\">Requirements: {escape(', '.join(defect['requirement_ids']) or 'None')}</span>"
            f"{render_role_chips(defect.get('roles', []), prefix='Roles: ')}"
            "</div>"
            f"<p class=\"issue-summary\">{escape(defect['failure_details'] or 'Failure details were not captured.')}</p>"
            f"{render_detail_list_block('Expected result', defect.get('expected_results', []))}"
            f"{render_detail_text_block('Actual result', defect.get('actual_result', ''))}"
            "<div class=\"detail-block\">"
            "<span class=\"detail-label\">Executed steps</span>"
            f"{render_step_list(defect['executed_steps'])}"
            "</div>"
            f"{render_diagnostic_list_block('Console errors', defect.get('console_errors', []))}"
            f"{render_diagnostic_list_block('Network / API errors', defect.get('network_errors', []))}"
            f"{render_context_block('Browser context', defect.get('browser_context', {}))}"
            f"{render_context_block('Diagnostic details', defect.get('diagnostic_details', {}))}"
            f"{render_notes_block(defect.get('notes', []))}"
            f"{render_evidence_block(defect['evidence'])}"
            "</article>"
        )
    return "\n".join(cards)


def render_evidence_panels(results: list[dict]) -> str:
    panels = []
    for item in results:
        evidence = item.get("evidence") or []
        if not evidence:
            continue
        panels.append(
            "<article class=\"evidence-panel\">"
            f"<div class=\"issue-head\"><h3>{escape(item.get('test_case_id', ''))}</h3><span class=\"status {escape(item.get('status', 'Unknown'))}\">{escape(item.get('status', 'Unknown'))}</span></div>"
            f"<h4>{escape(item.get('title', ''))}</h4>"
            f"{render_case_meta_chips(item)}"
            f"{render_evidence_gallery(evidence, item.get('title', 'Evidence'))}"
            "</article>"
        )
    if not panels:
        return '<div class="empty-state">No evidence references were captured.</div>'
    return "\n".join(panels)


def render_step_list(steps: list[str]) -> str:
    if not steps:
        return '<div class="muted">No executed steps were recorded.</div>'
    items = "".join(f"<li>{escape(step)}</li>" for step in steps)
    return f"<ol class=\"step-list\">{items}</ol>"


def render_detail_text_block(label: str, value: str) -> str:
    if not value:
        return ""
    return (
        "<div class=\"detail-block\">"
        f"<span class=\"detail-label\">{escape(label)}</span>"
        f"<p class=\"detail-text\">{escape(str(value))}</p>"
        "</div>"
    )


def render_detail_list_block(label: str, values: list) -> str:
    values = force_list(values)
    if not values:
        return ""
    items = "".join(f"<li>{escape(format_diagnostic_item(value))}</li>" for value in values)
    return (
        "<div class=\"detail-block\">"
        f"<span class=\"detail-label\">{escape(label)}</span>"
        f"<ul class=\"note-list\">{items}</ul>"
        "</div>"
    )


def render_diagnostic_list_block(label: str, values: list) -> str:
    values = force_list(values)
    if not values:
        return ""
    items = "".join(f"<li>{escape(format_diagnostic_item(value))}</li>" for value in values)
    return (
        "<div class=\"detail-block\">"
        f"<span class=\"detail-label\">{escape(label)}</span>"
        f"<ul class=\"diagnostic-list\">{items}</ul>"
        "</div>"
    )


def render_context_block(label: str, context: dict | list | str) -> str:
    if not context:
        return ""
    if isinstance(context, dict):
        rows = [
            f"<li><strong>{escape(str(key))}:</strong> {escape(format_diagnostic_item(value))}</li>"
            for key, value in context.items()
            if value not in (None, "", [], {})
        ]
        if not rows:
            return ""
        body = "".join(rows)
    else:
        body = "".join(f"<li>{escape(format_diagnostic_item(value))}</li>" for value in force_list(context))
    return (
        "<div class=\"detail-block\">"
        f"<span class=\"detail-label\">{escape(label)}</span>"
        f"<ul class=\"diagnostic-list\">{body}</ul>"
        "</div>"
    )


def render_notes_block(notes: list[str]) -> str:
    if not notes:
        return ""
    items = "".join(f"<li>{escape(note)}</li>" for note in notes)
    return (
        "<div class=\"detail-block\">"
        "<span class=\"detail-label\">Notes</span>"
        f"<ul class=\"note-list\">{items}</ul>"
        "</div>"
    )


def render_evidence_block(evidence: list[str]) -> str:
    if not evidence:
        return ""
    return (
        "<div class=\"detail-block\">"
        "<span class=\"detail-label\">Evidence</span>"
        f"{render_evidence_gallery(evidence, 'Evidence reference')}"
        "</div>"
    )


def render_evidence_gallery(evidence: list[str], title: str) -> str:
    items = []
    for ref in evidence:
        safe_ref = escape(url_ref(ref))
        label = escape(Path(ref).name or ref)
        if is_image_reference(ref):
            items.append(
                "<figure class=\"evidence-item image\">"
                f"<a href=\"{safe_ref}\"><img src=\"{safe_ref}\" alt=\"{escape(title)}\" /></a>"
                f"<figcaption>{label}</figcaption>"
                "</figure>"
            )
        else:
            items.append(
                "<div class=\"evidence-item reference\">"
                f"<a class=\"reference-pill\" href=\"{safe_ref}\">{label}</a>"
                "</div>"
            )
    return f"<div class=\"evidence-gallery\">{''.join(items)}</div>"


def force_list(value) -> list:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


def role_names(item: dict) -> list[str]:
    roles = force_list(item.get("roles") or item.get("role") or item.get("user_role"))
    return sorted({str(role).strip() for role in roles if str(role).strip()})


def render_roles_overview(results: list[dict]) -> str:
    roles = sorted({role for item in results for role in role_names(item)})
    if not roles:
        return ""
    chips = render_role_chips(roles)
    return (
        '<div class="section-card roles-overview">'
        "<h2>Detected Roles</h2>"
        '<p class="muted">Roles captured from the executed cases and shown on each case row below.</p>'
        f'<div class="meta-chips">{chips}</div>'
        "</div>"
    )


def render_case_meta_chips(item: dict) -> str:
    roles = render_role_chips(role_names(item), prefix="Roles: ")
    requirements = ", ".join(force_list(item.get("requirement_ids"))) or "None"
    return (
        '<div class="meta-chips">'
        f'<span class="chip">Requirements: {escape(requirements)}</span>'
        f"{roles}"
        "</div>"
    )


def render_role_chips(roles: list[str], prefix: str = "") -> str:
    if not roles:
        return '<span class="muted">Not specified</span>'
    return "".join(f'<span class="chip role-chip">{escape(prefix + role)}</span>' for role in roles)


def prepare_evidence_assets(results: list[dict], input_dir: Path, output_dir: Path) -> None:
    evidence_dir = output_dir / "evidence"
    copied: dict[Path, str] = {}
    used_names: set[str] = set()
    for item in results:
        rewritten = []
        for reference in force_list(item.get("evidence")):
            ref = str(reference)
            rewritten.append(copy_evidence_reference(ref, input_dir, output_dir, evidence_dir, copied, used_names))
        if rewritten:
            item["evidence"] = rewritten


def copy_evidence_reference(
    reference: str,
    input_dir: Path,
    output_dir: Path,
    evidence_dir: Path,
    copied: dict[Path, str],
    used_names: set[str],
) -> str:
    if not reference or is_remote_reference(reference):
        return reference

    source = Path(reference).expanduser()
    if not source.is_absolute():
        candidate = input_dir / source
        if candidate.exists():
            source = candidate
        elif (output_dir / source).exists():
            return source.as_posix()
        else:
            return reference

    if not source.exists() or not source.is_file():
        return reference

    resolved = source.resolve()
    if resolved in copied:
        return copied[resolved]

    evidence_dir.mkdir(parents=True, exist_ok=True)
    target_name = unique_evidence_name(source.name, used_names)
    target = evidence_dir / target_name
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    relative = target.relative_to(output_dir).as_posix()
    copied[resolved] = relative
    return relative


def unique_evidence_name(filename: str, used_names: set[str]) -> str:
    path = Path(filename)
    stem = path.stem or "evidence"
    suffix = path.suffix
    candidate = path.name or "evidence"
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}-{counter}{suffix}"
        counter += 1
    used_names.add(candidate)
    return candidate


def is_remote_reference(reference: str) -> bool:
    parsed = urlparse(reference)
    return parsed.scheme in {"http", "https", "data", "blob"}


def url_ref(reference: str) -> str:
    if is_remote_reference(reference):
        return reference
    return quote(reference, safe="/._-#%")


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


def format_diagnostic_item(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def build_pie_chart_style(counts: dict) -> str:
    total = counts.get("executed", 0)
    if total <= 0:
        return "background: conic-gradient(#dbe5ef 0deg 360deg);"

    passed_end = round((counts["passed"] / total) * 360, 1)
    failed_end = round(((counts["passed"] + counts["failed"]) / total) * 360, 1)
    return (
        "background: conic-gradient("
        f"var(--passed) 0deg {passed_end}deg, "
        f"var(--failed) {passed_end}deg {failed_end}deg, "
        f"var(--blocked) {failed_end}deg 360deg"
        ");"
    )


def is_image_reference(reference: str) -> bool:
    lowered = str(reference).lower()
    return lowered.endswith(IMAGE_EXTENSIONS)


def first_image_reference(evidence: list[str]) -> str:
    for reference in evidence:
        if is_image_reference(reference):
            return reference
    return ""


def counts_or_zero(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Build markdown, JSON, and HTML report artifacts from execution results.")
    parser.add_argument("--input", required=True, help="Path to execution results JSON.")
    parser.add_argument("--output-dir", required=True, help="Directory to write the report bundle.")
    args = parser.parse_args()
    summary = build_report_bundle(args.input, args.output_dir)
    print(json.dumps({"output_dir": args.output_dir, "counts": summary["counts"]}, indent=2))


if __name__ == "__main__":
    main()
