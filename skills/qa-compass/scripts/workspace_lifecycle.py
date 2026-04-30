from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from io_utils import read_json, write_json


WORKSPACE_SCHEMA_VERSION = "2.0"

REUSABLE_DIRS = (
    "00-overview",
    "01-sources",
    "02-normalized",
    "03-generated",
)

WORKSPACE_DIRS = REUSABLE_DIRS + (
    "03-generated/suites",
    "03-generated/versions",
    "runs",
    "history",
)

LEGACY_RUN_DIRS = (
    "04-execution",
    "05-reports",
    "05-report",
)

REUSABLE_ARTIFACTS = (
    "00-overview/project-summary.md",
    "00-overview/artifact-manifest.json",
    "00-overview/artifact-legend.md",
    "01-sources/source-index.json",
    "01-sources/requirements-raw.json",
    "01-sources/confluence-tree.md",
    "01-sources/confluence-intake-diagnostics.json",
    "02-normalized/requirements-normalized.json",
    "02-normalized/roles.json",
    "02-normalized/grouping-proposal.json",
    "03-generated/test-cases.json",
    "03-generated/test-cases.md",
    "03-generated/traceability.json",
    "03-generated/reusable-test-plan.md",
)


def detect_workspace(root: str | Path) -> dict:
    workspace_root = Path(root)
    index_path = workspace_root / "workspace-index.json"
    if index_path.exists():
        try:
            index = read_json(index_path)
        except (json.JSONDecodeError, OSError):
            index = {}
        return {
            "workspace_root": str(workspace_root),
            "layout": "workspace_v2",
            "schema_version": str(index.get("schema_version") or WORKSPACE_SCHEMA_VERSION),
            "project_name": index.get("project_name", ""),
            "index_path": str(index_path),
        }

    if any((workspace_root / path).exists() for path in REUSABLE_DIRS + LEGACY_RUN_DIRS):
        return {
            "workspace_root": str(workspace_root),
            "layout": "legacy_single_run",
            "schema_version": "legacy",
            "project_name": "",
        }

    return {
        "workspace_root": str(workspace_root),
        "layout": "empty",
        "schema_version": "",
        "project_name": "",
    }


def init_workspace(root: str | Path, project_name: str = "") -> dict:
    workspace_root = Path(root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    for relative_dir in WORKSPACE_DIRS:
        (workspace_root / relative_dir).mkdir(parents=True, exist_ok=True)

    now = now_iso()
    profile_path = workspace_root / "project-profile.json"
    if profile_path.exists():
        profile = read_json(profile_path)
        if project_name:
            profile["project_name"] = project_name
        else:
            profile.setdefault("project_name", project_name)
        profile["updated_at"] = now
    else:
        profile = {
            "schema_version": WORKSPACE_SCHEMA_VERSION,
            "project_name": project_name,
            "created_at": now,
            "updated_at": now,
        }
    write_json(profile_path, profile)

    index = {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "project_name": project_name or profile.get("project_name", ""),
        "created_at": profile.get("created_at", now),
        "updated_at": now,
        "reusable_paths": {
            "overview": "00-overview",
            "sources": "01-sources",
            "normalized": "02-normalized",
            "generated": "03-generated",
            "suites": "03-generated/suites",
            "generated_versions": "03-generated/versions",
            "runs": "runs",
            "history": "history",
        },
        "active_test_cases": "03-generated/test-cases.json",
        "runs_index": "history/runs-index.json",
        "case_history": "history/case-history.json",
    }
    write_json(workspace_root / "workspace-index.json", index)
    ensure_json_file(workspace_root / "history" / "runs-index.json", {"schema_version": WORKSPACE_SCHEMA_VERSION, "runs": []})
    ensure_json_file(workspace_root / "history" / "case-history.json", {"schema_version": WORKSPACE_SCHEMA_VERSION, "cases": {}})

    return detect_workspace(workspace_root)


def migrate_legacy_workspace(root: str | Path, project_name: str = "", run_id: str | None = None) -> dict:
    workspace_root = Path(root)
    previous_state = detect_workspace(workspace_root)
    if previous_state["layout"] == "workspace_v2":
        return previous_state

    run_id = run_id or default_run_id("migrated")
    init_workspace(workspace_root, project_name=project_name)
    run_root = workspace_root / "runs" / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    moved_paths: list[str] = []
    for legacy_dir in LEGACY_RUN_DIRS:
        source = workspace_root / legacy_dir
        if not source.exists():
            continue
        destination_name = "05-reports" if legacy_dir == "05-report" else legacy_dir
        move_path(source, run_root / destination_name)
        moved_paths.append(legacy_dir)

    (run_root / "04-execution").mkdir(parents=True, exist_ok=True)
    (run_root / "05-reports").mkdir(parents=True, exist_ok=True)
    (run_root / "evidence").mkdir(parents=True, exist_ok=True)

    run_config = {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "run_id": run_id,
        "suite": "migrated",
        "mode": "migrated",
        "created_at": now_iso(),
        "migrated_from": "legacy_single_run",
    }
    write_json(run_root / "run-config.json", run_config)
    append_run_index(workspace_root, run_config)

    migration_report = {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "source_layout": previous_state["layout"],
        "run_id": run_id,
        "moved_paths": moved_paths,
        "reused_artifacts": reusable_artifacts_present(workspace_root),
        "warnings": [],
    }
    write_json(workspace_root / "history" / "migration-report.json", migration_report)

    return detect_workspace(workspace_root)


def create_run_workspace(
    root: str | Path,
    suite: str,
    mode: str,
    run_id: str | None = None,
) -> dict:
    workspace_root = Path(root)
    if detect_workspace(workspace_root)["layout"] != "workspace_v2":
        init_workspace(workspace_root)

    run_id = run_id or default_run_id(suite or mode or "run")
    run_root = workspace_root / "runs" / run_id
    for relative_dir in ("04-execution", "05-reports", "evidence"):
        (run_root / relative_dir).mkdir(parents=True, exist_ok=True)

    run_config = {
        "schema_version": WORKSPACE_SCHEMA_VERSION,
        "run_id": run_id,
        "suite": suite,
        "mode": mode,
        "created_at": now_iso(),
        "workspace_root": str(workspace_root),
        "reuses": {
            "test_cases": "03-generated/test-cases.json",
            "roles": "02-normalized/roles.json",
            "grouping": "02-normalized/grouping-proposal.json",
            "case_history": "history/case-history.json",
        },
    }
    write_json(run_root / "run-config.json", run_config)
    append_run_index(workspace_root, run_config)
    return {
        "run_id": run_id,
        "run_root": str(run_root),
        "execution_dir": str(run_root / "04-execution"),
        "reports_dir": str(run_root / "05-reports"),
        "evidence_dir": str(run_root / "evidence"),
    }


def update_case_history(root: str | Path, run_id: str, results_path: str | Path) -> dict:
    workspace_root = Path(root)
    history_path = workspace_root / "history" / "case-history.json"
    ensure_json_file(history_path, {"schema_version": WORKSPACE_SCHEMA_VERSION, "cases": {}})
    history = read_json(history_path)
    cases = history.setdefault("cases", {})
    results_payload = read_json(results_path)
    results = results_payload.get("results", [])
    updated = 0

    for result in results:
        test_case_id = str(result.get("test_case_id") or result.get("id") or "").strip()
        status = str(result.get("status") or "").strip()
        if not test_case_id or not status:
            continue
        entry = cases.setdefault(
            test_case_id,
            {
                "passed_count": 0,
                "failed_count": 0,
                "blocked_count": 0,
            },
        )
        entry["last_status"] = status
        entry["last_run_id"] = run_id
        entry["last_executed_at"] = now_iso()
        increment_status_count(entry, status)
        updated += 1

    write_json(history_path, history)
    return {"updated": updated, "case_history": str(history_path)}


def ensure_json_file(path: Path, payload: dict) -> None:
    if not path.exists():
        write_json(path, payload)


def append_run_index(workspace_root: Path, run_config: dict) -> None:
    runs_index_path = workspace_root / "history" / "runs-index.json"
    ensure_json_file(runs_index_path, {"schema_version": WORKSPACE_SCHEMA_VERSION, "runs": []})
    runs_index = read_json(runs_index_path)
    runs = runs_index.setdefault("runs", [])
    if not any(run.get("run_id") == run_config["run_id"] for run in runs):
        runs.append(
            {
                "run_id": run_config["run_id"],
                "suite": run_config.get("suite", ""),
                "mode": run_config.get("mode", ""),
                "created_at": run_config.get("created_at", ""),
                "path": f"runs/{run_config['run_id']}",
            }
        )
    write_json(runs_index_path, runs_index)


def move_path(source: Path, destination: Path) -> None:
    if destination.exists() and source.is_dir() and destination.is_dir():
        for child in source.iterdir():
            move_path(child, destination / child.name)
        source.rmdir()
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


def reusable_artifacts_present(workspace_root: Path) -> list[str]:
    return [path for path in REUSABLE_ARTIFACTS if (workspace_root / path).exists()]


def increment_status_count(entry: dict, status: str) -> None:
    normalized = status.strip().lower()
    key = f"{normalized}_count"
    if key in {"passed_count", "failed_count", "blocked_count"}:
        entry[key] = int(entry.get(key, 0)) + 1


def default_run_id(label: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{slugify(label)}"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "run"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage QA Compass workspace v2 lifecycle.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect", help="Detect workspace layout.")
    detect_parser.add_argument("--root", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize workspace v2.")
    init_parser.add_argument("--root", required=True)
    init_parser.add_argument("--project-name", default="")

    migrate_parser = subparsers.add_parser("migrate", help="Migrate a legacy single-run workspace.")
    migrate_parser.add_argument("--root", required=True)
    migrate_parser.add_argument("--project-name", default="")
    migrate_parser.add_argument("--run-id")

    run_parser = subparsers.add_parser("create-run", help="Create a run workspace under runs/<run-id>.")
    run_parser.add_argument("--root", required=True)
    run_parser.add_argument("--suite", required=True)
    run_parser.add_argument("--mode", required=True)
    run_parser.add_argument("--run-id")

    history_parser = subparsers.add_parser("update-history", help="Update case-history.json from execution results.")
    history_parser.add_argument("--root", required=True)
    history_parser.add_argument("--run-id", required=True)
    history_parser.add_argument("--results", required=True)

    args = parser.parse_args()
    if args.command == "detect":
        result = detect_workspace(args.root)
    elif args.command == "init":
        result = init_workspace(args.root, project_name=args.project_name)
    elif args.command == "migrate":
        result = migrate_legacy_workspace(args.root, project_name=args.project_name, run_id=args.run_id)
    elif args.command == "create-run":
        result = create_run_workspace(args.root, suite=args.suite, mode=args.mode, run_id=args.run_id)
    else:
        result = update_case_history(args.root, run_id=args.run_id, results_path=args.results)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
