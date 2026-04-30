from __future__ import annotations

import argparse
import json
from pathlib import Path

from io_utils import render_template, write_json, write_text


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

KNOWN_ARTIFACTS = {
    "workspace-index.json": {
        "label": "Workspace index",
        "description": "Machine-readable QA Compass workspace v2 index with reusable paths, run history paths, and active canonical test case location.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "project-profile.json": {
        "label": "Project profile",
        "description": "Project-level metadata for repeated QA runs.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "project-summary.md": {
        "label": "Project summary",
        "description": "AI-generated product understanding based on the source requirements.",
        "created_by": "ai_generated",
        "source_of_truth": False,
    },
    "artifact-legend.md": {
        "label": "Artifact legend",
        "description": "Human-readable explanation of generated files and how to use them.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "artifact-manifest.json": {
        "label": "Artifact manifest",
        "description": "Machine-readable index of generated files for this QA run.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "requirements-raw.json": {
        "label": "Raw requirements",
        "description": "Source content imported before normalization.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "confluence-tree.md": {
        "label": "Confluence tree",
        "description": "Readable snapshot of the imported Confluence page tree.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "confluence-intake-diagnostics.json": {
        "label": "Confluence intake diagnostics",
        "description": "Non-sensitive diagnostics for Confluence folder/page discovery attempts and fallback results.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "jira-issues.json": {
        "label": "Jira issues",
        "description": "Imported Jira issue payloads used as source material.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "source-index.json": {
        "label": "Source index",
        "description": "Cross-source map for requirements, Jira issues, Confluence pages, and freshness flags.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "requirements-normalized.json": {
        "label": "Normalized requirements",
        "description": "Canonical machine-readable requirement package.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "requirements-normalized.md": {
        "label": "Normalized requirements summary",
        "description": "Readable rendering of canonical normalized requirements.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "roles.json": {
        "label": "Detected roles",
        "description": "Machine-readable role layer detected from source materials.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "roles-and-groups.md": {
        "label": "Roles and groups",
        "description": "Readable role coverage and grouping proposal summary.",
        "created_by": "ai_generated",
        "source_of_truth": False,
    },
    "grouping-proposal.json": {
        "label": "Grouping proposal",
        "description": "Machine-readable grouping options for features, roles, epics, components, and source sections.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "test-cases.json": {
        "label": "Canonical test cases",
        "description": "Source of truth for generated QA coverage and execution subset selection.",
        "created_by": "ai_generated",
        "source_of_truth": True,
    },
    "test-cases.md": {
        "label": "Readable test cases",
        "description": "Human-readable rendering of generated test cases.",
        "created_by": "ai_generated",
        "source_of_truth": False,
    },
    "traceability.json": {
        "label": "Traceability map",
        "description": "Requirement to test-case mapping.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "coverage-gaps.md": {
        "label": "Coverage gaps",
        "description": "Readable notes about uncovered or unclear requirement areas.",
        "created_by": "ai_generated",
        "source_of_truth": False,
    },
    "reusable-test-plan.md": {
        "label": "Reusable test plan",
        "description": "Compact plan for future QA runs that should reduce repeated context and token spend.",
        "created_by": "ai_generated",
        "source_of_truth": False,
    },
    "execution-plan.md": {
        "label": "Execution plan",
        "description": "Readable plan for the selected test execution subset.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "execution-subset.json": {
        "label": "Execution subset",
        "description": "Machine-readable selected test cases for this execution run.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "qa-scope-preview.html": {
        "label": "QA scope preview",
        "description": "Pre-execution HTML review of selected scope, groups, roles, warnings, and test cases.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-scope-preview.md": {
        "label": "Readable QA scope preview",
        "description": "Markdown summary of the selected execution scope before testing starts.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-scope-preview.json": {
        "label": "QA scope preview payload",
        "description": "Machine-readable pre-execution scope review payload.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "execution-results.json": {
        "label": "Execution results",
        "description": "Machine-readable execution results.",
        "created_by": "ai_generated",
        "source_of_truth": True,
    },
    "execution-results.md": {
        "label": "Readable execution results",
        "description": "Readable execution details for the team.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "execution-progress.json": {
        "label": "Execution progress",
        "description": "Resume state for completed, skipped, blocked, and remaining cases.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "remaining-cases.json": {
        "label": "Remaining cases",
        "description": "Cases not yet executed and suitable for future continuation runs.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "run-summary.json": {
        "label": "Run summary",
        "description": "Machine-readable report summary and metrics.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "qa-compass-run-diagnostics.md": {
        "label": "QA Compass run diagnostics",
        "description": "Developer-facing Markdown handoff for diagnosing QA Compass run issues and local execution context.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-compass-run-diagnostics.json": {
        "label": "QA Compass run diagnostics payload",
        "description": "Machine-readable source payload for the developer-facing run diagnostics report.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "run-config.json": {
        "label": "Run configuration",
        "description": "Machine-readable configuration for a specific execution run under runs/<run-id>.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "runs-index.json": {
        "label": "Runs index",
        "description": "Machine-readable history of repeated QA runs in this workspace.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "case-history.json": {
        "label": "Case history",
        "description": "Machine-readable latest status and counters per test case for rerun failed/blocked flows.",
        "created_by": "script_generated",
        "source_of_truth": True,
    },
    "migration-report.json": {
        "label": "Migration report",
        "description": "Non-destructive record of how a legacy single-run layout was converted into workspace v2.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-report.html": {
        "label": "Legacy QA report",
        "description": "Legacy combined HTML report from older QA Compass runs; new runs use separate internal and external reports.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-report.internal.html": {
        "label": "Internal QA report",
        "description": "Detailed team-facing report with steps, evidence, source links, and generated file legend.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-report.external.html": {
        "label": "External QA report",
        "description": "Client-facing executive QA report.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-report.internal.pdf": {
        "label": "Internal QA report PDF",
        "description": "Experimental PDF export of the detailed internal report; HTML is the canonical output.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-report.external.pdf": {
        "label": "External QA report PDF",
        "description": "Required client-shareable PDF snapshot exported from the external HTML report.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "qa-report.pdf": {
        "label": "QA report PDF",
        "description": "Legacy experimental combined PDF QA report; HTML is the canonical output.",
        "created_by": "script_generated",
        "source_of_truth": False,
    },
    "jira-bug-drafts.md": {
        "label": "Jira bug drafts",
        "description": "Readable Jira-ready defect drafts for user review.",
        "created_by": "ai_generated",
        "source_of_truth": False,
    },
    "jira-bug-drafts.json": {
        "label": "Jira bug draft payloads",
        "description": "Machine-readable draft-first defect payloads.",
        "created_by": "ai_generated",
        "source_of_truth": False,
    },
}


def build_artifact_manifest(run_dir: str) -> dict:
    root = Path(run_dir)
    overview_dir = root / "00-overview"
    overview_dir.mkdir(parents=True, exist_ok=True)

    artifacts = [describe_artifact(path, root) for path in sorted(root.rglob("*")) if path.is_file()]
    artifacts = [
        artifact
        for artifact in artifacts
        if artifact["path"] not in {"00-overview/artifact-manifest.json", "00-overview/artifact-legend.md"}
    ]

    manifest = {
        "run_dir": str(root),
        "artifacts": artifacts,
    }
    write_json(overview_dir / "artifact-manifest.json", manifest)
    write_text(overview_dir / "artifact-legend.md", render_legend(artifacts))

    return {
        "artifact_count": len(artifacts),
        "manifest": str(overview_dir / "artifact-manifest.json"),
        "legend": str(overview_dir / "artifact-legend.md"),
    }


def describe_artifact(path: Path, root: Path) -> dict:
    relative_path = path.relative_to(root).as_posix()
    metadata = KNOWN_ARTIFACTS.get(path.name, default_metadata(path.name))
    return {
        "path": relative_path,
        "label": metadata["label"],
        "description": metadata["description"],
        "created_by": metadata["created_by"],
        "source_of_truth": metadata["source_of_truth"],
    }


def default_metadata(filename: str) -> dict:
    return {
        "label": filename,
        "description": "Generated run artifact.",
        "created_by": "unknown",
        "source_of_truth": False,
    }


def render_legend(artifacts: list[dict]) -> str:
    rows = []
    for artifact in artifacts:
        source_flag = "yes" if artifact["source_of_truth"] else "no"
        rows.append(
            "\n".join(
                [
                    f"## {artifact['label']}",
                    "",
                    f"- Path: `{artifact['path']}`",
                    f"- Created by: `{artifact['created_by']}`",
                    f"- Source of truth: `{source_flag}`",
                    f"- Purpose: {artifact['description']}",
                    "",
                ]
            )
        )

    return render_template(
        TEMPLATES_DIR / "artifact-legend.template.md",
        {"artifact_rows": "\n".join(rows).rstrip()},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build artifact-manifest.json and artifact-legend.md for a QA run.")
    parser.add_argument("--run-dir", required=True, help="QA run directory to scan.")
    args = parser.parse_args()
    print(json.dumps(build_artifact_manifest(args.run_dir), indent=2))


if __name__ == "__main__":
    main()
