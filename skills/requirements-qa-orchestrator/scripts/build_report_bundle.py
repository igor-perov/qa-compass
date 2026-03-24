from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path

from io_utils import read_json, render_template, write_json, write_text


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
                "executed_steps": result.get("executed_steps", []),
                "failure_details": result.get("failure_details", ""),
                "notes": result.get("notes", []),
                "evidence": evidence,
                "primary_screenshot": first_image_reference(evidence),
            }
        )
        defect_index += 1
    return defects


def build_report_bundle(input_path: str, output_dir: str) -> dict:
    payload = read_json(input_path)
    results = payload.get("results", [])
    counts = build_counts(results)
    defects = classify_defects(results)
    blocked_cases = [item for item in results if item.get("status") == "Blocked"]
    report_input = {
        "project_name": payload.get("project_name", "QA Report"),
        "run_date": payload.get("run_date", ""),
        "environment": payload.get("environment", ""),
        "subset_mode": payload.get("subset_mode", "custom"),
        "requirements_count": payload.get("requirements_count", 0),
        "test_cases_count": payload.get("test_cases_count", len(results)),
        "results": results,
        "counts": counts,
        "defects": defects,
        "blocked_cases": blocked_cases,
    }

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    execution_plan = render_execution_plan(report_input)
    execution_results = render_execution_results(report_input)
    run_summary = build_run_summary(report_input)
    html_report = render_html_report(report_input)

    write_text(destination / "execution-plan.md", execution_plan)
    write_text(destination / "execution-results.md", execution_results)
    write_json(destination / "run-summary.json", run_summary)
    write_text(destination / "qa-report.html", html_report)
    return run_summary


def build_run_summary(report_input: dict) -> dict:
    return {
        "project_name": report_input["project_name"],
        "run_date": report_input["run_date"],
        "environment": report_input["environment"],
        "subset_mode": report_input["subset_mode"],
        "counts": report_input["counts"],
        "defects": report_input["defects"],
        "blocked_cases": [
            {
                "test_case_id": item.get("test_case_id"),
                "title": item.get("title"),
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
            "results_rows": render_results_rows(report_input["results"]),
            "blocked_cases_section": render_blocked_section(report_input["blocked_cases"]),
            "defect_section": render_defect_section(report_input["defects"]),
            "evidence_panels": render_evidence_panels(report_input["results"]),
        },
    )


def render_results_rows(results: list[dict]) -> str:
    rows = []
    for item in results:
        rows.append(
            "<tr>"
            f"<td>{escape(item.get('test_case_id', ''))}</td>"
            f"<td>{escape(item.get('title', ''))}</td>"
            f"<td>{escape(item.get('priority', 'Medium'))}</td>"
            f"<td>{escape(item.get('duration', '-'))}</td>"
            f"<td><span class=\"status {escape(item.get('status', 'Unknown'))}\">{escape(item.get('status', 'Unknown'))}</span></td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_blocked_section(blocked_cases: list[dict]) -> str:
    if not blocked_cases:
        return '<div class="empty-state">No blocked cases in this run.</div>'

    cards = []
    for item in blocked_cases:
        cards.append(
            "<article class=\"issue-card blocked\">"
            f"<div class=\"issue-head\"><h3>{escape(item.get('test_case_id', ''))}</h3><span class=\"status Blocked\">Blocked</span></div>"
            f"<h4>{escape(item.get('title', ''))}</h4>"
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
            "</div>"
            f"<p class=\"issue-summary\">{escape(defect['failure_details'] or 'Failure details were not captured.')}</p>"
            "<div class=\"detail-block\">"
            "<span class=\"detail-label\">Executed steps</span>"
            f"{render_step_list(defect['executed_steps'])}"
            "</div>"
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
        safe_ref = escape(ref)
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
