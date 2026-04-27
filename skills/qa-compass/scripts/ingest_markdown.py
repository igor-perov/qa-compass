from __future__ import annotations

import argparse
import json
from pathlib import Path

from io_utils import write_json


def ingest_markdown(input_path: str) -> dict:
    path = Path(input_path)
    content = path.read_text(encoding="utf-8")
    documents = build_documents(content, str(path))
    return {
        "source_mode": "markdown",
        "source_path": str(path),
        "project_name": path.stem.replace("-", " ").replace("_", " ").title(),
        "documents": documents,
    }


def build_documents(content: str, source_path: str) -> list[dict]:
    sections = split_sections(content)
    documents: list[dict] = []
    current_title = None
    current_headings: list[str] = []
    current_blocks: list[str] = []

    for level, heading, body in sections:
        if level <= 2:
            if current_title is not None:
                documents.append(make_document(current_title, current_headings, current_blocks, source_path))
            current_title = heading
            current_headings = [heading]
            current_blocks = [body] if body else []
            continue

        if current_title is None:
            current_title = heading
        current_headings.append(heading)
        if body:
            current_blocks.append(body)

    if current_title is not None:
        documents.append(make_document(current_title, current_headings, current_blocks, source_path))

    if not documents:
        documents.append(make_document("Imported Markdown", ["Imported Markdown"], [content.strip()], source_path))

    return documents


def split_sections(content: str) -> list[tuple[int, str, str]]:
    lines = content.splitlines()
    sections: list[tuple[int, str, str]] = []
    current_level = None
    current_heading = None
    body_lines: list[str] = []

    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("#"):
            if current_heading is not None:
                sections.append((current_level, current_heading, "\n".join(body_lines).strip()))
            hashes, heading = stripped.split(" ", 1)
            current_level = len(hashes)
            current_heading = heading.strip()
            body_lines = []
            continue
        body_lines.append(line)

    if current_heading is not None:
        sections.append((current_level, current_heading, "\n".join(body_lines).strip()))

    return sections


def make_document(title: str, headings: list[str], body_blocks: list[str], source_path: str) -> dict:
    clean_blocks = [block.strip() for block in body_blocks if block.strip()]
    joined = "\n".join(clean_blocks)
    bullets = extract_bullets(joined)
    lowered_title = title.strip().lower()
    return {
        "title": title,
        "source_path": source_path,
        "headings": headings,
        "body_blocks": clean_blocks,
        "acceptance_criteria": bullets if lowered_title == "acceptance criteria" else extract_list_items(joined, ("acceptance criteria",)),
        "business_rules": bullets if lowered_title == "business rules" else extract_list_items(joined, ("business rules",)),
        "roles": bullets if lowered_title in {"user roles", "roles"} else extract_list_items(joined, ("user roles", "roles")),
        "full_text": joined,
    }


def extract_list_items(text: str, heading_terms: tuple[str, ...]) -> list[str]:
    lines = text.splitlines()
    capture = False
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        lowered = stripped.lower().rstrip(":")
        if lowered in heading_terms:
            capture = True
            continue
        if capture and stripped.startswith("#"):
            break
        if capture and stripped.startswith("- "):
            items.append(stripped[2:].strip())
        elif capture and stripped and not stripped.startswith("-"):
            capture = False
    return items


def extract_bullets(text: str) -> list[str]:
    return [line[2:].strip() for line in text.splitlines() if line.strip().startswith("- ")]


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a markdown or PRD file into canonical raw requirement documents.")
    parser.add_argument("--input", required=True, help="Path to the markdown/PRD file.")
    parser.add_argument("--output", required=True, help="Path to write requirements-raw.json.")
    args = parser.parse_args()
    payload = ingest_markdown(args.input)
    write_json(args.output, payload)
    print(json.dumps({"output": args.output, "documents": len(payload["documents"])}, indent=2))


if __name__ == "__main__":
    main()
