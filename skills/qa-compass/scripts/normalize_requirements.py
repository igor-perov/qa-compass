from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from io_utils import read_json, render_template, write_json, write_text


GENERIC_TITLES = {
    "overview",
    "user roles",
    "roles",
    "acceptance criteria",
    "business rules",
}

SECTION_TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


def normalize_payload(raw_payload: dict) -> dict:
    documents = raw_payload.get("documents") or []
    global_roles = collect_global_items(documents, {"user roles", "roles"})
    global_rules = collect_global_items(documents, {"business rules"})

    counters: dict[str, int] = defaultdict(int)
    requirements: list[dict] = []
    for document in documents:
        requirements.extend(normalize_document(document, counters, global_roles, global_rules))

    return {
        "project_name": raw_payload.get("project_name") or infer_project_name(documents) or "Requirements Package",
        "source_mode": raw_payload.get("source_mode") or "unknown",
        "requirements": requirements,
    }


def normalize_document(
    raw_doc: dict,
    counters: dict[str, int],
    global_roles: list[str] | None = None,
    global_rules: list[str] | None = None,
) -> list[dict]:
    global_roles = global_roles or []
    global_rules = global_rules or []
    title = raw_doc.get("title", "Untitled")
    candidates = extract_requirement_candidates(raw_doc)
    requirements = []
    for statement in candidates:
        feature = infer_feature(raw_doc, statement)
        counters[feature] += 1
        requirement_id = assign_requirement_id(feature, counters[feature])
        acceptance_criteria = list(raw_doc.get("acceptance_criteria") or [])
        business_rules = dedupe(list(raw_doc.get("business_rules") or []) + list(global_rules))
        roles = dedupe(list(raw_doc.get("roles") or []) + list(global_roles))
        ambiguities = collect_ambiguities(raw_doc, statement, acceptance_criteria, business_rules)
        requirements.append(
            {
                "requirement_id": requirement_id,
                "feature": feature,
                "source_title": title,
                "source_url": raw_doc.get("source_url") or raw_doc.get("source_path") or "",
                "statement": statement,
                "acceptance_criteria": acceptance_criteria,
                "roles": roles,
                "business_rules": business_rules,
                "dependencies": detect_dependencies(statement, acceptance_criteria, business_rules),
                "ambiguities": ambiguities,
            }
        )
    return requirements


def assign_requirement_id(feature: str, index: int) -> str:
    slug = slugify(feature).upper()[:16] or "GENERAL"
    return f"REQ-{slug}-{index:03d}"


def collect_ambiguities(raw_doc: dict, statement: str, acceptance_criteria: list[str], business_rules: list[str]) -> list[str]:
    ambiguities: list[str] = []
    joined = " ".join([statement] + acceptance_criteria + business_rules).lower()
    if not acceptance_criteria:
        ambiguities.append("Acceptance criteria are not explicit in this source section.")
    if "resend timer" in joined and not re.search(r"\b\d+\b", joined):
        ambiguities.append("Resend timer duration is not specified.")
    if "required field" in joined and "company data" in joined:
        ambiguities.append("The required company data field list is not specified.")
    if raw_doc.get("title", "").strip().lower() == "overview":
        ambiguities.append("Overview text is broad and may need feature-level decomposition.")
    return dedupe(ambiguities)


def extract_requirement_candidates(raw_doc: dict) -> list[str]:
    title = raw_doc.get("title", "").strip()
    acceptance_criteria = [item.strip() for item in raw_doc.get("acceptance_criteria") or [] if item.strip()]
    if title.lower() == "acceptance criteria" and acceptance_criteria:
        return acceptance_criteria

    bullet_items = []
    for block in raw_doc.get("body_blocks") or []:
        bullet_items.extend(extract_bullets(block))
    if bullet_items:
        return dedupe(bullet_items)

    full_text = (raw_doc.get("full_text") or "").strip()
    if full_text:
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", full_text) if item.strip()]
        return sentences[:1]

    return [title] if title else []


def collect_global_items(documents: list[dict], titles: set[str]) -> list[str]:
    items: list[str] = []
    for document in documents:
        title = document.get("title", "").strip().lower()
        if title not in titles:
            continue
        for block in document.get("body_blocks") or []:
            items.extend(extract_bullets(block))
    return dedupe(items)


def infer_feature(raw_doc: dict, statement: str) -> str:
    candidates = raw_doc.get("headings") or []
    for heading in reversed(candidates):
        if heading.strip().lower() not in GENERIC_TITLES:
            return heading.strip()

    lowered = f"{raw_doc.get('title', '')} {statement}".lower()
    if any(token in lowered for token in ("registration", "work email", "otp", "verification")):
        return "Registration"
    if any(token in lowered for token in ("stage 1", "company data")):
        return "Stage 1"
    return raw_doc.get("title") or "General"


def detect_dependencies(statement: str, acceptance_criteria: list[str], business_rules: list[str]) -> list[str]:
    joined = " ".join([statement] + acceptance_criteria + business_rules).lower()
    dependencies = []
    if any(token in joined for token in ("otp", "verification code", "email")):
        dependencies.append("Email verification service")
    if "public email" in joined:
        dependencies.append("Public email validation")
    return dependencies


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        clean = item.strip()
        if not clean:
            continue
        key = clean.lower()
        if key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def extract_bullets(block: str) -> list[str]:
    return [line[2:].strip() for line in block.splitlines() if line.strip().startswith("- ")]


def slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-") or "GENERAL"


def infer_project_name(documents: list[dict]) -> str:
    if documents:
        first = documents[0].get("source_path") or documents[0].get("source_url") or ""
        if first:
            return Path(first).stem.replace("-", " ").replace("_", " ").title()
    return "Requirements Package"


def render_requirements_blocks(requirements: list[dict]) -> str:
    blocks = []
    for requirement in requirements:
        block = [
            f"## {requirement['requirement_id']} — {requirement['feature']}",
            f"- Source: {requirement['source_title']}" + (f" ({requirement['source_url']})" if requirement["source_url"] else ""),
            f"- Statement: {requirement['statement']}",
            "- Acceptance criteria:",
        ]
        block.extend([f"  - {item}" for item in requirement["acceptance_criteria"]] or ["  - None captured"])
        block.append(f"- Roles: {', '.join(requirement['roles']) if requirement['roles'] else 'Not specified'}")
        block.append(f"- Rules: {', '.join(requirement['business_rules']) if requirement['business_rules'] else 'None captured'}")
        block.append(
            f"- Dependencies: {', '.join(requirement['dependencies']) if requirement['dependencies'] else 'None identified'}"
        )
        block.append(
            f"- Ambiguities: {', '.join(requirement['ambiguities']) if requirement['ambiguities'] else 'None identified'}"
        )
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def build_project_summary(payload: dict) -> str:
    requirements = payload["requirements"]
    features = sorted({item["feature"] for item in requirements})
    roles = sorted({role for item in requirements for role in item.get("roles", [])})
    rules = sorted({rule for item in requirements for rule in item.get("business_rules", [])})
    ambiguity_count = sum(1 for item in requirements if item["ambiguities"])
    template_path = SECTION_TEMPLATES / "project-summary.template.md"
    return render_template(
        template_path,
        {
            "product_overview": "Pending AI-generated product summary. Use the normalized requirements as source material before relying on this overview.",
            "main_user_roles": render_bullets(roles, "No explicit user roles were detected in the source material."),
            "core_business_flows": render_bullets(features, "No clear feature or flow grouping was detected."),
            "important_domain_rules": render_bullets(rules, "No explicit domain rules were captured."),
            "covered_areas": render_bullets(features, "No covered areas were detected."),
            "unclear_areas": f"{ambiguity_count} requirement records contain ambiguities or missing details.",
            "testing_implications": "Generate the final testing implications with AI after reviewing roles, flows, business rules, and ambiguities.",
            "project_name": payload["project_name"],
            "source_mode": payload["source_mode"],
            "documents_count": len(requirements),
            "requirements_count": len(requirements),
            "features": ", ".join(features),
            "ambiguity_count": ambiguity_count,
        },
    )


def render_bullets(items: list[str], empty_text: str) -> str:
    if not items:
        return empty_text
    return "\n".join(f"- {item}" for item in items)


def build_requirements_markdown(payload: dict) -> str:
    template_path = SECTION_TEMPLATES / "requirements-normalized.template.md"
    return render_template(
        template_path,
        {
            "project_name": payload["project_name"],
            "requirements_blocks": render_requirements_blocks(payload["requirements"]),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize raw requirement documents into canonical QA-ready requirements.")
    parser.add_argument("--input", required=True, help="Path to requirements-raw.json.")
    parser.add_argument("--output-dir", required=True, help="Directory to write normalized outputs.")
    args = parser.parse_args()

    payload = normalize_payload(read_json(args.input))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "requirements-normalized.json", payload)
    write_text(output_dir / "project-summary.md", build_project_summary(payload))
    write_text(output_dir / "requirements-normalized.md", build_requirements_markdown(payload))
    print(json.dumps({"output_dir": str(output_dir), "requirements": len(payload["requirements"])}, indent=2))


if __name__ == "__main__":
    main()
