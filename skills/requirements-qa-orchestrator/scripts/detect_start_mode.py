from __future__ import annotations

import argparse
import json
import re


SOURCE_PATTERNS = {
    "confluence": (
        "confluence",
        "atlassian.net/wiki",
        "space/",
        "folder/",
        "page/",
        "api token",
    ),
    "requirements_json": (
        "requirements json",
        "normalized requirements",
        "traceability json",
        "requirements-normalized.json",
    ),
    "test_cases_json": (
        "test-cases json",
        "test cases json",
        "execution subset",
        "test-cases.json",
    ),
    "markdown": (
        ".md",
        "markdown",
        "prd",
        "spec file",
        "requirements doc",
    ),
}

STAGE_PATTERNS = {
    "report": ("report", "html", "pdf", "stakeholder", "run summary"),
    "export-playwright-specs": (
        ".spec.ts",
        "playwright spec",
        "playwright specs",
        "playwright test file",
        "playwright test files",
        "reusable playwright",
    ),
    "execute": ("run", "rerun", "execute", "validate", "smoke", "high-priority", "high priority"),
    "generate-cases": (
        "test case",
        "test cases",
        "qa coverage",
        "coverage matrix",
        "scenario",
    ),
    "normalize": ("normalize", "traceability", "map requirements", "clean requirements", "normalized requirements"),
    "ingest": ("pull", "fetch", "parse", "import", "read from", "grab"),
}


def detect_start_mode(user_text: str) -> dict:
    lowered = (user_text or "").lower()
    source_mode = detect_source_mode(lowered)
    stage = detect_stage(lowered)
    playwright_specs_requested = detect_playwright_specs_requested(lowered)
    generation_scope_prompt_required = detect_generation_scope_prompt_required(lowered, stage, source_mode)
    requested_output = detect_requested_output(lowered, stage, playwright_specs_requested)
    missing_blockers = detect_missing_blockers(lowered, source_mode, stage)
    execution_subset = detect_execution_subset(lowered)
    return {
        "source_mode": source_mode,
        "stage": stage,
        "requested_output": requested_output,
        "missing_blockers": missing_blockers,
        "execution_subset": execution_subset,
        "generation_scope_prompt_required": generation_scope_prompt_required,
        "playwright_specs_requested": playwright_specs_requested,
    }


def detect_source_mode(lowered: str) -> str:
    for source_mode, patterns in SOURCE_PATTERNS.items():
        if any(pattern in lowered for pattern in patterns):
            return source_mode

    if "execution result" in lowered or "results into" in lowered:
        return "pasted_text"

    if "\n" in lowered or len(lowered.split()) > 12:
        return "pasted_text"

    return "pasted_text"


def detect_stage(lowered: str) -> str:
    explicit_priority = (
        ("report", ("html", "pdf", "stakeholder report", "qa report")),
        ("normalize", ("normalize", "traceability", "normalized requirements")),
        (
            "generate-cases",
            (
                "generate test cases",
                "create test cases",
                "turn these requirements into test cases",
                "qa coverage",
            ),
        ),
        (
            "export-playwright-specs",
            (
                ".spec.ts",
                "playwright specs",
                "playwright test files",
                "reusable playwright",
            ),
        ),
        ("execute", ("run the top", "run ", "rerun", "execute", "smoke", "high-priority", "high priority")),
        ("ingest", ("pull", "fetch", "parse", "import", "grab")),
    )
    for stage, patterns in explicit_priority:
        if any(pattern in lowered for pattern in patterns):
            return stage

    scored_matches: list[tuple[int, str]] = []
    for stage, patterns in STAGE_PATTERNS.items():
        score = sum(1 for pattern in patterns if pattern in lowered)
        if score:
            scored_matches.append((score, stage))
    if scored_matches:
        scored_matches.sort(key=lambda item: (-item[0], stage_rank(item[1])))
        return scored_matches[0][1]
    return "ingest"


def detect_requested_output(lowered: str, stage: str, playwright_specs_requested: bool) -> str:
    if "pdf" in lowered and "html" in lowered:
        return "html_and_pdf_report"
    if stage == "generate-cases":
        if playwright_specs_requested:
            return "test_cases_and_playwright_specs"
        return "test_cases"
    if stage == "export-playwright-specs":
        return "playwright_specs"
    if stage == "normalize":
        return "normalized_requirements"
    if stage == "execute":
        return "execution_results"
    if stage == "report":
        return "stakeholder_report"
    return "requirements_package"


def detect_playwright_specs_requested(lowered: str) -> bool:
    return has_any(
        lowered,
        (
            ".spec.ts",
            "playwright spec",
            "playwright specs",
            "playwright test file",
            "playwright test files",
            "reusable playwright",
        ),
    )


def detect_generation_scope_prompt_required(lowered: str, stage: str, source_mode: str) -> bool:
    if stage != "generate-cases":
        return False
    if source_mode not in {"confluence", "requirements_json", "markdown", "pasted_text"}:
        return False
    if has_any(
        lowered,
        (
            "smoke only",
            "smoke cases",
            "smoke suite",
            "full coverage",
            "all cases",
            "complete coverage",
        ),
    ):
        return False
    return True


def detect_missing_blockers(lowered: str, source_mode: str, stage: str) -> list[str]:
    blockers: list[str] = []
    if source_mode == "confluence":
        if not has_any(lowered, ("http://", "https://", "atlassian.net")):
            blockers.append("confluence_url")
        if "token" not in lowered:
            blockers.append("confluence_credentials")

    if stage == "execute":
        if not has_any(lowered, ("http://", "https://")):
            blockers.append("environment_url")
        if has_any(lowered, ("login", "sign in", "authenticated", "otp", "register")):
            blockers.append("credentials_or_test_data")

    if source_mode in {"requirements_json", "test_cases_json", "markdown"}:
        if not has_any(lowered, (".json", ".md", "/", "\\")):
            blockers.append("input_path_or_attachment")

    if stage == "report" and not has_any(lowered, ("result", "results", "run-summary", "execution")):
        blockers.append("execution_results_source")

    return blockers


def detect_execution_subset(lowered: str) -> dict:
    subset: dict = {}
    match = re.search(r"\btop\s+(\d+)\b", lowered)
    if match:
        subset["limit"] = int(match.group(1))
    if "high-priority" in lowered or "high priority" in lowered:
        subset["mode"] = "high-priority"
    elif "critical path" in lowered:
        subset["mode"] = "critical-path"
    elif "smoke" in lowered:
        subset["mode"] = "smoke"
    elif "rerun failed" in lowered:
        subset["mode"] = "rerun-failed"
    elif "rerun blocked" in lowered:
        subset["mode"] = "rerun-blocked"
    return subset


def has_any(lowered: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in lowered for pattern in patterns)


def stage_rank(stage: str) -> int:
    order = {
        "report": 0,
        "normalize": 1,
        "generate-cases": 2,
        "export-playwright-specs": 3,
        "execute": 4,
        "ingest": 5,
    }
    return order.get(stage, 99)


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect the likely source mode and active stage from a QA request.")
    parser.add_argument("--text", required=True, help="User request text to analyze.")
    args = parser.parse_args()
    print(json.dumps(detect_start_mode(args.text), indent=2))


if __name__ == "__main__":
    main()
