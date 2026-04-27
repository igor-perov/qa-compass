from __future__ import annotations

import argparse
import base64
import json
import re
import urllib.error
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

from io_utils import write_json, write_text


DETAIL_ENDPOINTS = {
    "folder": "/wiki/api/v2/folders/{id}",
    "page": "/wiki/api/v2/pages/{id}?body-format=storage",
    "whiteboard": "/wiki/api/v2/whiteboards/{id}",
    "database": "/wiki/api/v2/databases/{id}",
    "embed": "/wiki/api/v2/embeds/{id}",
}

CHILDREN_ENDPOINTS = {
    "folder": "/wiki/api/v2/folders/{id}/direct-children?limit=100",
    "page": "/wiki/api/v2/pages/{id}/direct-children?limit=100",
    "whiteboard": "/wiki/api/v2/whiteboards/{id}/direct-children?limit=100",
    "database": "/wiki/api/v2/databases/{id}/direct-children?limit=100",
    "embed": "/wiki/api/v2/embeds/{id}/direct-children?limit=100",
}


class StorageToTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.list_stack: list[str] = []
        self.pending_cell = False

    def append(self, text: str) -> None:
        if text:
            self.parts.append(text)

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"p", "div", "section"}:
            self.append("\n\n")
        elif tag == "br":
            self.append("\n")
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.append("\n\n" + ("#" * int(tag[1])) + " ")
        elif tag == "li":
            bullet = "1. " if self.list_stack and self.list_stack[-1] == "ol" else "- "
            self.append("\n" + bullet)
        elif tag in {"ul", "ol"}:
            self.list_stack.append(tag)
        elif tag == "tr":
            self.append("\n")
        elif tag in {"td", "th"}:
            if self.pending_cell:
                self.append(" | ")
            self.pending_cell = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"ul", "ol"} and self.list_stack:
            self.list_stack.pop()
            self.append("\n")
        elif tag in {"p", "div", "section", "li", "table"}:
            self.append("\n")
        elif tag == "tr":
            self.pending_cell = False

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data)
        if text.strip():
            self.append(text.strip())

    def get_text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return unescape(text).strip()


def auth_header(email: str, token: str) -> dict[str, str]:
    encoded = base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("ascii")
    return {
        "Authorization": f"Basic {encoded}",
        "Accept": "application/json",
    }


def absolute_url(base_url: str, path_or_url: str) -> str:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    return f"{base_url.rstrip('/')}{path_or_url}"


def api_get(base_url: str, email: str, token: str, path_or_url: str) -> dict:
    request = urllib.request.Request(absolute_url(base_url, path_or_url), headers=auth_header(email, token))
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{exc.code} {exc.reason} for {path_or_url}: {body}") from exc


def get_detail(base_url: str, email: str, token: str, node_type: str, node_id: str) -> dict:
    detail = api_get(base_url, email, token, DETAIL_ENDPOINTS[node_type].format(id=node_id))
    detail.setdefault("id", node_id)
    detail.setdefault("type", node_type)
    return detail


def get_children(base_url: str, email: str, token: str, node_type: str, node_id: str) -> list[dict]:
    if node_type not in CHILDREN_ENDPOINTS:
        return []
    results: list[dict] = []
    next_url = CHILDREN_ENDPOINTS[node_type].format(id=node_id)
    while next_url:
        payload = api_get(base_url, email, token, next_url)
        results.extend(payload.get("results", []))
        next_url = payload.get("_links", {}).get("next")
    return results


def storage_to_text(storage_value: str) -> str:
    parser = StorageToTextParser()
    parser.feed(storage_value or "")
    return parser.get_text()


def build_web_url(base_url: str, links: dict | None) -> str | None:
    if not links:
        return None
    webui = links.get("webui")
    if not webui:
        return None
    base = links.get("base", base_url.rstrip("/"))
    return f"{base}{webui}"


def walk_tree(base_url: str, email: str, token: str, root_type: str, root_id: str) -> list[dict]:
    root_detail = get_detail(base_url, email, token, root_type, root_id)
    nodes: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def visit(detail: dict, depth: int, path_titles: list[str]) -> None:
        node_key = (detail["type"], str(detail["id"]))
        if node_key in seen:
            return
        seen.add(node_key)

        children = get_children(base_url, email, token, detail["type"], str(detail["id"]))
        record = {
            "id": str(detail["id"]),
            "type": detail["type"],
            "title": detail.get("title", ""),
            "depth": depth,
            "path": path_titles + [detail.get("title", "")],
            "webUrl": build_web_url(base_url, detail.get("_links")),
            "bodyStorage": detail.get("body", {}).get("storage", {}).get("value", ""),
            "bodyText": storage_to_text(detail.get("body", {}).get("storage", {}).get("value", "")),
            "children": [{"id": str(child["id"]), "type": child["type"], "title": child.get("title", "")} for child in children],
        }
        nodes.append(record)
        for child in children:
            child_detail = get_detail(base_url, email, token, child["type"], str(child["id"]))
            visit(child_detail, depth + 1, path_titles + [detail.get("title", "")])

    visit(root_detail, 0, [])
    return nodes


def build_raw_payload(base_url: str, root_type: str, root_id: str, nodes: list[dict]) -> dict:
    documents = []
    for node in nodes:
        if node["type"] != "page":
            continue
        documents.append(
            {
                "document_id": node["id"],
                "title": node["title"],
                "source_url": node["webUrl"],
                "headings": [],
                "body_blocks": [node["bodyText"]] if node["bodyText"] else [],
                "acceptance_criteria": [],
                "business_rules": [],
                "roles": [],
                "path": node["path"],
                "full_text": node["bodyText"],
            }
        )

    return {
        "source_mode": "confluence",
        "source": {
            "base_url": base_url,
            "root_type": root_type,
            "root_id": root_id,
        },
        "documents": documents,
        "nodes": nodes,
    }


def render_tree_markdown(nodes: list[dict]) -> str:
    lines = ["# Confluence Tree", ""]
    for node in nodes:
        indent = "  " * node["depth"]
        suffix = f" - {node['webUrl']}" if node.get("webUrl") else ""
        lines.append(f"{indent}- [{node['type']}] {node['title']} (ID: {node['id']}){suffix}")
    return "\n".join(lines) + "\n"


def parse_root_reference(root_ref: str) -> tuple[str, str]:
    if root_ref.isdigit():
        return "folder", root_ref
    match = re.search(r"/(folder|pages?|whiteboards|databases|embeds)/(\d+)", root_ref)
    if not match:
        raise ValueError("Could not infer Confluence root type and id from the provided root reference.")
    raw_type = match.group(1)
    normalized_type = {
        "pages": "page",
        "page": "page",
        "folder": "folder",
        "whiteboards": "whiteboard",
        "databases": "database",
        "embeds": "embed",
    }[raw_type]
    return normalized_type, match.group(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a Confluence subtree into canonical raw requirement artifacts.")
    parser.add_argument("--base-url", required=True, help="Confluence base URL, for example https://example.atlassian.net")
    parser.add_argument("--email", required=True, help="Confluence login email")
    parser.add_argument("--token", required=True, help="Confluence API token")
    parser.add_argument("--root", required=True, help="Root folder/page id or URL")
    parser.add_argument("--output-dir", required=True, help="Directory to write confluence-tree.md and requirements-raw.json")
    args = parser.parse_args()

    root_type, root_id = parse_root_reference(args.root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    nodes = walk_tree(args.base_url, args.email, args.token, root_type, root_id)
    raw_payload = build_raw_payload(args.base_url, root_type, root_id, nodes)

    write_json(output_dir / "requirements-raw.json", raw_payload)
    write_text(output_dir / "confluence-tree.md", render_tree_markdown(nodes))
    print(json.dumps({"output_dir": str(output_dir), "documents": len(raw_payload["documents"]), "nodes": len(nodes)}, indent=2))


if __name__ == "__main__":
    main()
