from __future__ import annotations

import argparse
import json
from collections import defaultdict

from io_utils import read_json, write_json


def propose_grouping(input_path: str, output_path: str | None = None) -> dict:
    payload = read_json(input_path)
    requirements = payload.get("requirements", [])

    proposal = {
        "project_name": payload.get("project_name", "QA Compass Run"),
        "roles": collect_roles(requirements),
        "grouping_options": [
            build_grouping_option("feature", requirements, feature_name),
            build_grouping_option("role", requirements, role_names),
            build_grouping_option("source_section", requirements, source_section_name),
        ],
        "recommended": recommended_grouping(requirements),
    }

    if output_path:
        write_json(output_path, proposal)
    return proposal


def collect_roles(requirements: list[dict]) -> list[str]:
    return sorted({role for requirement in requirements for role in requirement.get("roles", [])})


def build_grouping_option(group_type: str, requirements: list[dict], key_fn) -> dict:
    grouped: dict[str, list[str]] = defaultdict(list)
    for requirement in requirements:
        names = key_fn(requirement)
        for name in names:
            grouped[name].append(requirement.get("requirement_id", ""))

    groups = [
        {
            "name": name,
            "requirement_ids": sorted(requirement_id for requirement_id in ids if requirement_id),
            "requirement_count": len([requirement_id for requirement_id in ids if requirement_id]),
        }
        for name, ids in sorted(grouped.items(), key=lambda item: item[0].lower())
    ]
    return {"type": group_type, "groups": groups}


def feature_name(requirement: dict) -> list[str]:
    feature = str(requirement.get("feature", "")).strip()
    return [feature] if feature else ["Ungrouped"]


def role_names(requirement: dict) -> list[str]:
    roles = [str(role).strip() for role in requirement.get("roles", []) if str(role).strip()]
    return roles or ["Role not specified"]


def source_section_name(requirement: dict) -> list[str]:
    title = str(requirement.get("source_title", "")).strip()
    if not title:
        return ["Source not specified"]
    section = title.split("/")[0].strip()
    return [section or title]


def recommended_grouping(requirements: list[dict]) -> str:
    if any(str(requirement.get("feature", "")).strip() for requirement in requirements):
        return "feature"
    if collect_roles(requirements):
        return "role"
    return "source_section"


def main() -> None:
    parser = argparse.ArgumentParser(description="Propose QA grouping options from normalized requirements.")
    parser.add_argument("--input", required=True, help="Path to requirements-normalized.json.")
    parser.add_argument("--output", required=True, help="Path to write grouping-proposal.json.")
    args = parser.parse_args()
    print(json.dumps(propose_grouping(args.input, args.output), indent=2))


if __name__ == "__main__":
    main()
