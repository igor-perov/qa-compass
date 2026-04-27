from __future__ import annotations

import argparse
import json

from contracts import PRIORITY_ORDER
from io_utils import read_json, write_json


def select_subset(cases: list[dict], mode: str, limit: int | None = None) -> list[dict]:
    normalized_mode = mode.strip().lower()
    ordered_cases = sorted(cases, key=sort_key)

    if normalized_mode == "high-priority":
        selected = [case for case in ordered_cases if case.get("priority") == "High"]
    elif normalized_mode == "smoke":
        selected = [
            case
            for case in ordered_cases
            if case.get("priority") in {"High", "Medium"}
            and case.get("automation_candidate", True)
            and case.get("type", "").lower() != "error handling"
        ]
    elif normalized_mode == "critical-path":
        selected = [
            case
            for case in ordered_cases
            if case.get("type", "").lower() == "functional"
            and case.get("priority") in {"High", "Medium"}
        ]
    elif normalized_mode == "rerun-failed":
        selected = [case for case in ordered_cases if case.get("last_status") == "Failed"]
    elif normalized_mode == "rerun-blocked":
        selected = [case for case in ordered_cases if case.get("last_status") == "Blocked"]
    else:
        selected = ordered_cases

    if limit is not None:
        return selected[:limit]
    return selected


def sort_key(case: dict) -> tuple:
    priority = PRIORITY_ORDER.get(str(case.get("priority", "Medium")).lower(), 99)
    automation_rank = 0 if case.get("automation_candidate", True) else 1
    type_rank = 0 if case.get("type", "").lower() == "functional" else 1
    return (priority, automation_rank, type_rank, case.get("test_case_id", ""))


def main() -> None:
    parser = argparse.ArgumentParser(description="Select a deterministic execution subset from canonical test cases.")
    parser.add_argument("--input", required=True, help="Path to test-cases.json")
    parser.add_argument("--mode", required=True, help="Subset mode: high-priority, smoke, critical-path, rerun-failed, rerun-blocked")
    parser.add_argument("--limit", type=int, help="Optional limit for the number of selected cases")
    parser.add_argument("--output", required=True, help="Path to write execution-subset.json")
    args = parser.parse_args()

    payload = read_json(args.input)
    cases = payload.get("test_cases") or payload.get("cases") or []
    subset = select_subset(cases, args.mode, args.limit)
    result = {
        "project_name": payload.get("project_name", "Execution Subset"),
        "mode": args.mode,
        "limit": args.limit,
        "test_cases": subset,
    }
    write_json(args.output, result)
    print(json.dumps({"output": args.output, "selected": len(subset)}, indent=2))


if __name__ == "__main__":
    main()
