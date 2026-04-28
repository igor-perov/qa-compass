#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FLAGSHIP_ROOT = REPO_ROOT / "skills" / "qa-compass"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a lightweight validation pass for the shareable requirements QA orchestrator repo."
    )
    parser.add_argument(
        "--with-pdf",
        action="store_true",
        help="Also export the sample external HTML report to qa-report.external.pdf with playwright-cli or npx.",
    )
    return parser.parse_args()


def run(command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=str(cwd or REPO_ROOT), text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    if result.stdout.strip():
        print(result.stdout.strip())


def require_paths() -> None:
    required = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "LICENSE",
        REPO_ROOT / "scripts" / "install_local_skills.py",
        REPO_ROOT / "scripts" / "smoke_validate.py",
        FLAGSHIP_ROOT / "SKILL.md",
        FLAGSHIP_ROOT / "agents" / "openai.yaml",
        FLAGSHIP_ROOT / "scripts" / "build_jira_jql.py",
        FLAGSHIP_ROOT / "scripts" / "ingest_jira.py",
        REPO_ROOT / "skills" / "confluence-qa-orchestrator" / "SKILL.md",
        REPO_ROOT / "skills" / "confluence-qa-orchestrator" / "agents" / "openai.yaml",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required packaged files:\n" + "\n".join(missing))


def main() -> None:
    args = parse_args()
    require_paths()

    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            str(FLAGSHIP_ROOT / "tests"),
            "-v",
        ]
    )

    with tempfile.TemporaryDirectory(prefix="rqo-shareable-") as tmpdir:
        tmp_root = Path(tmpdir)
        report_dir = tmp_root / "report"
        spec_dir = tmp_root / "playwright-specs"
        preview_dir = tmp_root / "scope-preview"

        run(
            [
                sys.executable,
                str(FLAGSHIP_ROOT / "scripts" / "build_report_bundle.py"),
                "--input",
                str(FLAGSHIP_ROOT / "tests" / "fixtures" / "sample_execution_results.json"),
                "--output-dir",
                str(report_dir),
            ]
        )

        run(
            [
                sys.executable,
                str(FLAGSHIP_ROOT / "scripts" / "import_test_cases_json.py"),
                "--input",
                str(FLAGSHIP_ROOT / "tests" / "fixtures" / "sample_test_cases.json"),
                "--output",
                str(tmp_root / "test-cases.json"),
            ]
        )

        run(
            [
                sys.executable,
                str(FLAGSHIP_ROOT / "scripts" / "build_jira_jql.py"),
                "--project-key",
                "QA",
                "--mode",
                "ready-for-qa",
            ]
        )

        run(
            [
                sys.executable,
                str(FLAGSHIP_ROOT / "scripts" / "export_playwright_specs.py"),
                "--input",
                str(tmp_root / "test-cases.json"),
                "--output-dir",
                str(spec_dir),
            ]
        )

        run(
            [
                sys.executable,
                str(FLAGSHIP_ROOT / "scripts" / "build_scope_preview.py"),
                "--test-cases",
                str(tmp_root / "test-cases.json"),
                "--output-dir",
                str(preview_dir),
            ]
        )

        if args.with_pdf:
            run(
                [
                    sys.executable,
                    str(FLAGSHIP_ROOT / "scripts" / "export_report_pdf.py"),
                    "--html",
                    str(report_dir / "qa-report.external.html"),
                    "--pdf",
                    str(report_dir / "qa-report.external.pdf"),
                    "--landscape",
                ]
            )
        print(f"Smoke validation artifacts: {report_dir}")
        print(f"Generated scope preview: {preview_dir}")
        print(f"Generated starter specs: {spec_dir}")


if __name__ == "__main__":
    main()
