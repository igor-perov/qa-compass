from __future__ import annotations

PROJECT_CONTEXT_KEYS = [
    "project_name",
    "source_mode",
    "active_stage",
    "requested_output",
    "environment_url",
    "credentials_status",
    "output_dir",
    "report_style",
    "execution_subset",
    "generation_scope_prompt_required",
    "playwright_specs_requested",
]

REQUIREMENT_KEYS = [
    "requirement_id",
    "feature",
    "source_title",
    "source_url",
    "statement",
    "acceptance_criteria",
    "roles",
    "business_rules",
    "dependencies",
    "ambiguities",
]

TEST_CASE_KEYS = [
    "test_case_id",
    "title",
    "feature",
    "requirement_ids",
    "priority",
    "type",
    "preconditions",
    "steps",
    "expected_results",
    "automation_candidate",
]

RESULT_KEYS = [
    "test_case_id",
    "title",
    "status",
    "environment",
    "executed_steps",
    "notes",
    "failure_details",
    "blocker_details",
    "evidence",
    "requirement_ids",
]

PRIORITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

STATUS_VALUES = {
    "Passed",
    "Failed",
    "Blocked",
}

SOURCE_MODES = {
    "confluence",
    "requirements_json",
    "test_cases_json",
    "markdown",
    "pasted_text",
}

STAGES = {
    "ingest",
    "normalize",
    "generate-cases",
    "export-playwright-specs",
    "execute",
    "report",
}


def has_required_keys(payload: dict, required_keys: list[str]) -> bool:
    return all(key in payload for key in required_keys)
