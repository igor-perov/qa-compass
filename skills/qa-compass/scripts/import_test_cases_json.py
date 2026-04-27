from __future__ import annotations

import argparse
import json

from io_utils import read_json, write_json


def import_test_cases_json(input_path: str) -> dict:
    payload = read_json(input_path)
    raw_cases = payload.get("test_cases") or payload.get("cases") or []
    if not raw_cases:
        raise ValueError("Input test-cases JSON must contain a non-empty 'test_cases' or 'cases' array.")

    test_cases = [canonicalize_case(item) for item in raw_cases]
    return {
        "project_name": payload.get("project_name") or payload.get("project") or "Imported Test Cases",
        "source_mode": "test_cases_json",
        "test_cases": test_cases,
    }


def canonicalize_case(item: dict) -> dict:
    return {
        "test_case_id": item.get("test_case_id") or item.get("id") or "",
        "title": item.get("title") or item.get("name") or "Imported Test Case",
        "feature": item.get("feature") or item.get("module") or item.get("suite") or "",
        "requirement_ids": force_list(item.get("requirement_ids") or item.get("requirements")),
        "priority": normalize_priority(item.get("priority")),
        "type": item.get("type") or item.get("category") or "Functional",
        "preconditions": force_list(item.get("preconditions")),
        "steps": force_list(item.get("steps")),
        "expected_results": force_list(item.get("expected_results") or item.get("expected")),
        "automation_candidate": bool(item.get("automation_candidate", True)),
    }


def normalize_priority(value) -> str:
    if not value:
        return "Medium"
    lowered = str(value).strip().lower()
    if lowered == "high":
        return "High"
    if lowered == "low":
        return "Low"
    return "Medium"


def force_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        clean = value.strip()
        return [clean] if clean else []
    return [str(value).strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Import external test-cases JSON into the canonical test-cases shape.")
    parser.add_argument("--input", required=True, help="Path to the external test-cases JSON file.")
    parser.add_argument("--output", required=True, help="Path to write the canonical test-cases.json.")
    args = parser.parse_args()
    payload = import_test_cases_json(args.input)
    write_json(args.output, payload)
    print(json.dumps({"output": args.output, "test_cases": len(payload["test_cases"])}, indent=2))


if __name__ == "__main__":
    main()
