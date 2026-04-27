from __future__ import annotations

import argparse
import json
from collections import defaultdict

from io_utils import read_json, write_json


def prepare_test_case_brief(input_path: str) -> dict:
    payload = read_json(input_path)
    features_map: dict[str, list[dict]] = defaultdict(list)
    roles = sorted({role for requirement in payload.get("requirements", []) for role in requirement.get("roles", [])})

    for requirement in payload.get("requirements", []):
        features_map[requirement["feature"]].append(
            {
                "requirement_id": requirement["requirement_id"],
                "statement": requirement["statement"],
                "acceptance_criteria": requirement.get("acceptance_criteria", []),
                "roles": requirement.get("roles", []),
                "business_rules": requirement.get("business_rules", []),
                "ambiguities": requirement.get("ambiguities", []),
            }
        )

    features = [
        {"feature": feature, "requirements": requirements}
        for feature, requirements in sorted(features_map.items(), key=lambda item: item[0].lower())
    ]
    return {
        "project_name": payload.get("project_name", "Requirements Package"),
        "roles": roles,
        "features": features,
        "generation_rules": {
            "happy_path": True,
            "edge_cases": True,
            "error_handling": True,
            "state_transitions": True,
            "roles": "Detected roles should be considered during test generation.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a compact test-case generation brief from normalized requirements.")
    parser.add_argument("--input", required=True, help="Path to requirements-normalized.json")
    parser.add_argument("--output", required=True, help="Path to write test-case-brief.json")
    args = parser.parse_args()
    payload = prepare_test_case_brief(args.input)
    write_json(args.output, payload)
    print(json.dumps({"output": args.output, "features": len(payload["features"])}, indent=2))


if __name__ == "__main__":
    main()
