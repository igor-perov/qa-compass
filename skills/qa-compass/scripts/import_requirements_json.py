from __future__ import annotations

import argparse
import json

from io_utils import read_json, write_json


def import_requirements_json(input_path: str) -> dict:
    payload = read_json(input_path)
    raw_requirements = payload.get("requirements") or payload.get("items") or []
    if not raw_requirements:
        raise ValueError("Input requirements JSON must contain a non-empty 'requirements' or 'items' array.")

    requirements = [canonicalize_requirement(item) for item in raw_requirements]
    return {
        "project_name": payload.get("project_name") or payload.get("project") or "Imported Requirements",
        "source_mode": "requirements_json",
        "requirements": requirements,
    }


def canonicalize_requirement(item: dict) -> dict:
    source = item.get("source") or {}
    return {
        "requirement_id": item.get("requirement_id") or item.get("id") or "",
        "feature": item.get("feature") or item.get("module") or item.get("title") or "General",
        "source_title": source.get("title") or item.get("source_title") or item.get("title") or "Imported Requirement",
        "source_url": source.get("url") or item.get("source_url") or "",
        "statement": item.get("statement") or item.get("description") or item.get("summary") or "",
        "acceptance_criteria": force_list(item.get("acceptance_criteria")),
        "roles": force_list(item.get("roles")),
        "business_rules": force_list(item.get("business_rules")),
        "dependencies": force_list(item.get("dependencies")),
        "ambiguities": force_list(item.get("ambiguities") or item.get("open_questions")),
    }


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
    parser = argparse.ArgumentParser(description="Import external requirements JSON into the canonical normalized shape.")
    parser.add_argument("--input", required=True, help="Path to the external requirements JSON file.")
    parser.add_argument("--output", required=True, help="Path to write the canonical requirements-normalized.json.")
    args = parser.parse_args()
    payload = import_requirements_json(args.input)
    write_json(args.output, payload)
    print(json.dumps({"output": args.output, "requirements": len(payload["requirements"])}, indent=2))


if __name__ == "__main__":
    main()
