from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from io_utils import read_json, render_template, write_json, write_text

try:
    import workspace_lifecycle
except ImportError:  # pragma: no cover - direct script fallback
    workspace_lifecycle = None


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

REDACTION_PATTERNS = (
    (re.compile(r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(api[_\s-]?token\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(atlassian[_\s-]?token\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(session[_\s-]?token\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(password\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(cookie\s*[:=]\s*)[^\n]+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(otp\s*[:=]\s*)\d{4,10}"), r"\1[REDACTED]"),
)


def build_run_diagnostics(
    workspace_root: str | Path,
    run_id: str | None = None,
    run_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    user_comments: str = "",
    user_comments_file: str | Path | None = None,
    source_request: str = "",
) -> dict:
    root = Path(workspace_root)
    selected_run_id, run_root = resolve_run(root, run_id=run_id, run_dir=run_dir)
    diagnostics_dir = Path(output_dir) if output_dir else run_root / "06-diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)

    comments = user_comments
    if user_comments_file:
        comments = Path(user_comments_file).read_text(encoding="utf-8")

    warnings: list[str] = []
    workspace_state = detect_workspace(root)
    run_config = load_json(run_root / "run-config.json", "run-config.json", warnings)
    run_summary = load_json(run_root / "05-reports" / "run-summary.json", "run-summary.json", warnings)
    execution_results = load_json(run_root / "04-execution" / "execution-results.json", "execution-results.json", warnings)
    case_history = load_json(root / "history" / "case-history.json", "case-history.json", warnings, required=False)
    migration_report = load_json(root / "history" / "migration-report.json", "migration-report.json", warnings, required=False)
    confluence_diagnostics = load_json(
        root / "01-sources" / "confluence-intake-diagnostics.json",
        "confluence-intake-diagnostics.json",
        warnings,
        required=False,
    )

    counts = summary_counts(run_summary, execution_results)
    artifact_links = collect_artifact_links(root, run_root)
    issues = collect_issues(
        warnings=warnings,
        run_summary=run_summary,
        confluence_diagnostics=confluence_diagnostics,
        migration_report=migration_report,
    )
    generated_at = now_iso()

    payload = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "workspace": workspace_state,
        "run": {
            "run_id": selected_run_id,
            "run_root": relpath(run_root, root),
            "suite": run_config.get("suite", ""),
            "mode": run_config.get("mode", ""),
            "created_at": run_config.get("created_at", ""),
        },
        "source_request": source_request,
        "user_comments": comments or "No user comments were provided.",
        "summary": {
            "project_name": run_summary.get("project_name") or workspace_state.get("project_name", ""),
            "environment": run_summary.get("environment") or execution_results.get("environment", ""),
            "subset_mode": run_summary.get("subset_mode") or run_config.get("mode", ""),
            "counts": counts,
            "defects": summarize_items(run_summary.get("defects", [])),
            "blocked_cases": summarize_items(run_summary.get("blocked_cases", [])),
        },
        "artifacts": artifact_links,
        "issues": issues,
        "case_history": summarize_case_history(case_history),
        "local_context": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cwd": str(Path.cwd()),
            "executable": sys.executable,
        },
        "warnings": warnings,
    }
    payload = redact_value(payload)

    json_path = diagnostics_dir / "qa-compass-run-diagnostics.json"
    markdown_path = diagnostics_dir / "qa-compass-run-diagnostics.md"
    write_json(json_path, payload)
    write_text(markdown_path, render_markdown(payload))
    return {
        "markdown": str(markdown_path),
        "json": str(json_path),
        "warnings": payload["warnings"],
    }


def resolve_run(root: Path, run_id: str | None = None, run_dir: str | Path | None = None) -> tuple[str, Path]:
    if run_dir:
        run_root = Path(run_dir)
        return run_root.name, run_root
    if run_id:
        return run_id, root / "runs" / run_id

    runs_index_path = root / "history" / "runs-index.json"
    if runs_index_path.exists():
        runs_index = read_json(runs_index_path)
        runs = runs_index.get("runs", [])
        if runs:
            latest = runs[-1]
            latest_run_id = str(latest.get("run_id") or "")
            if latest_run_id:
                return latest_run_id, root / "runs" / latest_run_id
    raise ValueError("run_id or run_dir is required when no run exists in history/runs-index.json")


def detect_workspace(root: Path) -> dict:
    if workspace_lifecycle:
        return workspace_lifecycle.detect_workspace(root)
    index_path = root / "workspace-index.json"
    return {
        "workspace_root": str(root),
        "layout": "workspace_v2" if index_path.exists() else "unknown",
        "schema_version": "",
        "project_name": "",
    }


def load_json(path: Path, label: str, warnings: list[str], required: bool = True) -> dict:
    if not path.exists():
        if required:
            warnings.append(f"Missing {label}: {path}")
        return {}
    try:
        return read_json(path)
    except (json.JSONDecodeError, OSError) as exc:
        warnings.append(f"Could not read {label}: {exc}")
        return {}


def summary_counts(run_summary: dict, execution_results: dict) -> dict:
    counts = run_summary.get("counts")
    if isinstance(counts, dict):
        return {
            "executed": int(counts.get("executed", 0)),
            "passed": int(counts.get("passed", 0)),
            "failed": int(counts.get("failed", 0)),
            "blocked": int(counts.get("blocked", 0)),
        }

    results = execution_results.get("results", [])
    return {
        "executed": len(results),
        "passed": sum(1 for item in results if item.get("status") == "Passed"),
        "failed": sum(1 for item in results if item.get("status") == "Failed"),
        "blocked": sum(1 for item in results if item.get("status") == "Blocked"),
    }


def collect_artifact_links(root: Path, run_root: Path) -> list[dict]:
    candidates = [
        root / "workspace-index.json",
        root / "project-profile.json",
        root / "00-overview" / "project-summary.md",
        root / "00-overview" / "artifact-manifest.json",
        root / "01-sources" / "source-index.json",
        root / "01-sources" / "confluence-intake-diagnostics.json",
        root / "02-normalized" / "requirements-normalized.json",
        root / "02-normalized" / "roles.json",
        root / "02-normalized" / "grouping-proposal.json",
        root / "03-generated" / "test-cases.json",
        root / "03-generated" / "traceability.json",
        root / "history" / "runs-index.json",
        root / "history" / "case-history.json",
        root / "history" / "migration-report.json",
        run_root / "run-config.json",
        run_root / "04-execution" / "qa-scope-preview.html",
        run_root / "04-execution" / "qa-scope-preview.json",
        run_root / "04-execution" / "execution-results.json",
        run_root / "04-execution" / "execution-progress.json",
        run_root / "04-execution" / "remaining-cases.json",
        run_root / "05-reports" / "run-summary.json",
        run_root / "05-reports" / "qa-report.internal.html",
        run_root / "05-reports" / "qa-report.external.html",
        run_root / "05-reports" / "qa-report.external.pdf",
    ]
    return [
        {
            "path": relpath(path, root),
            "exists": path.exists(),
        }
        for path in candidates
        if path.exists()
    ]


def collect_issues(
    warnings: list[str],
    run_summary: dict,
    confluence_diagnostics: dict,
    migration_report: dict,
) -> list[str]:
    issues = list(warnings)
    defects = run_summary.get("defects", [])
    blocked_cases = run_summary.get("blocked_cases", [])
    if defects:
        issues.append(f"Confirmed defects recorded: {len(defects)}")
        for defect in summarize_items(defects):
            issues.append(f"Defect case: {defect['test_case_id']} - {defect['title']}")
    if blocked_cases:
        issues.append(f"Blocked cases recorded: {len(blocked_cases)}")
        for blocked_case in summarize_items(blocked_cases):
            issues.append(f"Blocked case: {blocked_case['test_case_id']} - {blocked_case['title']}")
    for warning in confluence_diagnostics.get("warnings", []) if confluence_diagnostics else []:
        issues.append(f"Confluence intake warning: {warning}")
    for warning in migration_report.get("warnings", []) if migration_report else []:
        issues.append(f"Migration warning: {warning}")
    if not issues:
        issues.append("No diagnostic warnings were detected from available artifacts.")
    return issues


def summarize_items(items: list[dict]) -> list[dict]:
    summaries = []
    for item in items:
        summaries.append(
            {
                "test_case_id": item.get("test_case_id", ""),
                "title": item.get("title", ""),
                "details": item.get("failure_details") or item.get("blocker_details") or "",
            }
        )
    return summaries


def summarize_case_history(case_history: dict) -> dict:
    cases = case_history.get("cases", {}) if case_history else {}
    return {
        "tracked_cases": len(cases),
        "last_failed": sorted(case_id for case_id, item in cases.items() if item.get("last_status") == "Failed"),
        "last_blocked": sorted(case_id for case_id, item in cases.items() if item.get("last_status") == "Blocked"),
    }


def render_markdown(payload: dict) -> str:
    counts = payload["summary"]["counts"]
    run_metadata = "\n".join(
        [
            f"- Workspace: `{payload['workspace'].get('workspace_root', '')}`",
            f"- Workspace layout: `{payload['workspace'].get('layout', '')}`",
            f"- Workspace schema: `{payload['workspace'].get('schema_version', '')}`",
            f"- Project: `{payload['summary'].get('project_name', '')}`",
            f"- Run ID: `{payload['run'].get('run_id', '')}`",
            f"- Suite: `{payload['run'].get('suite', '')}`",
            f"- Mode: `{payload['run'].get('mode', '')}`",
            f"- Environment: `{payload['summary'].get('environment', '')}`",
            f"- Generated at: `{payload['generated_at']}`",
        ]
    )
    execution_summary = "\n".join(
        [
            f"- Executed: `{counts['executed']}`",
            f"- Passed: `{counts['passed']}`",
            f"- Failed: `{counts['failed']}`",
            f"- Blocked: `{counts['blocked']}`",
            f"- Defects in summary: `{len(payload['summary']['defects'])}`",
            f"- Blocked cases in summary: `{len(payload['summary']['blocked_cases'])}`",
            f"- Cases tracked in history: `{payload['case_history']['tracked_cases']}`",
        ]
    )
    return render_template(
        TEMPLATES_DIR / "run-diagnostics.template.md",
        {
            "run_metadata": run_metadata,
            "source_request_section": block_or_empty(payload.get("source_request", ""), "No source request was provided."),
            "user_comments_section": block_or_empty(payload.get("user_comments", ""), "No user comments were provided."),
            "execution_summary": execution_summary,
            "issues_section": bullet_list(payload.get("issues", [])),
            "artifact_links": artifact_list(payload.get("artifacts", [])),
            "local_context": bullet_map(payload.get("local_context", {})),
        },
    )


def block_or_empty(value: str, fallback: str) -> str:
    return value.strip() if value and value.strip() else fallback


def bullet_list(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def artifact_list(artifacts: list[dict]) -> str:
    if not artifacts:
        return "- No known artifacts were found."
    return "\n".join(f"- `{artifact['path']}`" for artifact in artifacts)


def bullet_map(values: dict) -> str:
    if not values:
        return "- None"
    return "\n".join(f"- {key}: `{value}`" for key, value in values.items())


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        result = value
        for pattern, replacement in REDACTION_PATTERNS:
            result = pattern.sub(replacement, result)
        return result
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value


def relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a developer-facing QA Compass run diagnostics package.")
    parser.add_argument("--workspace-root", required=True, help="QA Compass workspace root.")
    parser.add_argument("--run-id", help="Run id under runs/<run-id>. Defaults to latest run in runs-index when available.")
    parser.add_argument("--run-dir", help="Explicit run directory. Overrides --run-id.")
    parser.add_argument("--output-dir", help="Optional output directory. Defaults to runs/<run-id>/06-diagnostics.")
    parser.add_argument("--user-comments", default="", help="Optional user-supplied comments to include after redaction.")
    parser.add_argument("--user-comments-file", help="Optional file containing user-supplied comments.")
    parser.add_argument("--source-request", default="", help="Optional original user request summary to include after redaction.")
    args = parser.parse_args()
    result = build_run_diagnostics(
        workspace_root=args.workspace_root,
        run_id=args.run_id,
        run_dir=args.run_dir,
        output_dir=args.output_dir,
        user_comments=args.user_comments,
        user_comments_file=args.user_comments_file,
        source_request=args.source_request,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
