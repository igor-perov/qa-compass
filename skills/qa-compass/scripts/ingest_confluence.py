from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable

from io_utils import write_json, write_text


ApiGetter = Callable[[str, str, str, str], dict]

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

SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*)(basic|bearer)\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(token=)[^&\s]+"),
    re.compile(r"(?i)(api[_-]?token[\"'\s:=]+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(password[\"'\s:=]+)[^\s,;]+"),
    re.compile(r"(?i)(cookie[\"'\s:=]+)[^,;\n]+"),
    re.compile(r"\bATATT[0-9A-Za-z._~+/=-]{8,}\b"),
    re.compile(r"\b[A-Z0-9]{6}\b(?=.*\bOTP\b)", re.IGNORECASE),
)


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
        raise RuntimeError(redact_sensitive(f"{exc.code} {exc.reason} for {path_or_url}: {body}")) from exc


def parse_confluence_reference(input_url: str, base_url: str | None = None, mode: str = "auto") -> dict:
    value = (input_url or "").strip()
    if not value:
        raise ValueError("Confluence input URL or ID is required.")

    if value.isdigit():
        root_type = "page" if mode in {"auto", "page"} else "folder"
        return {
            "input_url": value,
            "base_url": (base_url or "").rstrip("/"),
            "space_key": "",
            "root_type": root_type,
            "root_id": value,
            "source_type": f"confluence_{root_type}",
        }

    parsed = urllib.parse.urlparse(value)
    path = parsed.path
    detected_base = base_url or f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else base_url
    patterns = (
        (r"/(?:wiki/)?spaces/([^/]+)/folder/(\d+)", "folder"),
        (r"/(?:wiki/)?spaces/([^/]+)/pages/(\d+)", "page"),
        (r"/(?:wiki/)?pages/(\d+)", "page"),
    )
    for pattern, root_type in patterns:
        match = re.search(pattern, path)
        if match:
            if root_type == "page" and len(match.groups()) == 1:
                space_key = ""
                root_id = match.group(1)
            else:
                space_key = match.group(1)
                root_id = match.group(2)
            if mode != "auto" and mode != root_type:
                root_type = mode
            return {
                "input_url": value,
                "base_url": (detected_base or "").rstrip("/"),
                "space_key": space_key,
                "root_type": root_type,
                "root_id": root_id,
                "source_type": f"confluence_{root_type}",
            }

    legacy_match = re.search(r"/(folder|pages?|whiteboards|databases|embeds)/(\d+)", path)
    if legacy_match:
        raw_type = legacy_match.group(1)
        root_type = {
            "pages": "page",
            "page": "page",
            "folder": "folder",
            "whiteboards": "whiteboard",
            "databases": "database",
            "embeds": "embed",
        }[raw_type]
        if mode != "auto":
            root_type = mode
        return {
            "input_url": value,
            "base_url": (detected_base or "").rstrip("/"),
            "space_key": "",
            "root_type": root_type,
            "root_id": legacy_match.group(2),
            "source_type": f"confluence_{root_type}",
        }

    raise ValueError("Could not infer Confluence source type and id from the provided input.")


def parse_root_reference(root_ref: str) -> tuple[str, str]:
    parsed = parse_confluence_reference(root_ref)
    return parsed["root_type"], parsed["root_id"]


def ingest_confluence(
    input_url: str,
    output_dir: str,
    email: str = "",
    token: str = "",
    base_url: str | None = None,
    mode: str = "auto",
    diagnostics: bool = True,
    strict: bool = False,
    api_getter: ApiGetter = api_get,
) -> dict:
    parsed = parse_confluence_reference(input_url, base_url=base_url, mode=mode)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    intake = initial_diagnostics(parsed)
    nodes: list[dict] = []
    warnings: list[str] = []

    if parsed["root_type"] == "folder":
        nodes = discover_folder(parsed, email, token, api_getter, intake)
    else:
        nodes = attempt_page_tree(parsed, email, token, api_getter, intake)

    if not nodes:
        warnings.append(
            "No Confluence pages were fetched. Provide connector-accessible pages, a page export, or a narrower page URL."
        )

    raw_payload = build_raw_payload(parsed, nodes)
    source_index = build_source_index(parsed, nodes)
    write_json(output / "requirements-raw.json", raw_payload)
    write_json(output / "source-index.json", source_index)
    write_text(output / "confluence-tree.md", render_tree_markdown(nodes))

    intake["discovered_page_count"] = sum(1 for node in nodes if node.get("type") == "page")
    intake["fetched_page_count"] = len(raw_payload["documents"])
    intake["warnings"] = warnings
    if diagnostics:
        write_json(output / "confluence-intake-diagnostics.json", redact_sensitive(intake))

    summary = {
        "output_dir": str(output),
        "documents": len(raw_payload["documents"]),
        "nodes": len(nodes),
        "diagnostics": str(output / "confluence-intake-diagnostics.json") if diagnostics else "",
    }
    if strict and not raw_payload["documents"]:
        raise RuntimeError("Strict Confluence ingest failed: no pages were fetched.")
    return summary


def initial_diagnostics(parsed: dict) -> dict:
    return {
        "input_url": parsed["input_url"],
        "base_url": parsed["base_url"],
        "space_key": parsed["space_key"],
        "folder_id": parsed["root_id"] if parsed["root_type"] == "folder" else "",
        "page_id": parsed["root_id"] if parsed["root_type"] == "page" else "",
        "detected_source_type": parsed["source_type"],
        "discovery_methods": [],
        "discovered_page_count": 0,
        "fetched_page_count": 0,
        "warnings": [],
    }


def discover_folder(parsed: dict, email: str, token: str, api_getter: ApiGetter, intake: dict) -> list[dict]:
    record_attempt(intake, "connector_rovo", "skipped", "Connector discovery must be performed by the agent when Rovo data is available.")

    nodes = attempt_rest_folder_children(parsed, email, token, api_getter, intake)
    if nodes:
        return nodes

    nodes = attempt_space_search(parsed, email, token, api_getter, intake)
    return nodes


def attempt_page_tree(parsed: dict, email: str, token: str, api_getter: ApiGetter, intake: dict) -> list[dict]:
    method = "rest_page_tree"
    try:
        nodes = walk_tree(parsed["base_url"], email, token, "page", parsed["root_id"], api_getter)
        status = "success" if nodes else "failed"
        record_attempt(intake, method, status, "" if nodes else "No pages returned.")
        return nodes
    except Exception as exc:  # noqa: BLE001 - diagnostic boundary
        record_attempt(intake, method, "failed", str(exc))
        return []


def attempt_rest_folder_children(parsed: dict, email: str, token: str, api_getter: ApiGetter, intake: dict) -> list[dict]:
    method = "rest_folder_children"
    try:
        children = get_children(parsed["base_url"], email, token, "folder", parsed["root_id"], api_getter)
        nodes = []
        for child in children:
            child_type = child.get("type", "")
            if child_type == "page":
                detail = get_detail(parsed["base_url"], email, token, "page", str(child["id"]), api_getter)
                nodes.extend(walk_detail(parsed["base_url"], email, token, detail, api_getter, 0, ["Folder"]))
            elif child_type in CHILDREN_ENDPOINTS:
                detail = get_detail(parsed["base_url"], email, token, child_type, str(child["id"]), api_getter)
                nodes.extend(walk_detail(parsed["base_url"], email, token, detail, api_getter, 0, ["Folder"]))
        status = "success" if nodes else "failed"
        record_attempt(intake, method, status, "" if nodes else "Folder children discovery returned no pages.")
        return nodes
    except Exception as exc:  # noqa: BLE001 - diagnostic boundary
        record_attempt(intake, method, "failed", str(exc))
        return []


def attempt_space_search(parsed: dict, email: str, token: str, api_getter: ApiGetter, intake: dict) -> list[dict]:
    method = "rest_space_search"
    if not parsed.get("space_key"):
        record_attempt(intake, method, "skipped", "No space key parsed from input.")
        return []
    try:
        cql = f'space="{parsed["space_key"]}" and type=page'
        path = "/wiki/rest/api/content/search?" + urllib.parse.urlencode(
            {"cql": cql, "limit": "100", "expand": "body.storage,ancestors,_links"}
        )
        payload = api_getter(parsed["base_url"], email, token, path)
        nodes = [node_from_detail(parsed["base_url"], item, depth=0, path_titles=ancestor_titles(item)) for item in payload.get("results", [])]
        status = "success" if nodes else "failed"
        record_attempt(intake, method, status, "" if nodes else "Search returned no pages.")
        return nodes
    except Exception as exc:  # noqa: BLE001 - diagnostic boundary
        record_attempt(intake, method, "failed", str(exc))
        return []


def record_attempt(intake: dict, method: str, status: str, message: str) -> None:
    intake["discovery_methods"].append(
        {
            "method": method,
            "status": status,
            "error_summary": redact_sensitive(message) if message else "",
        }
    )


def get_detail(base_url: str, email: str, token: str, node_type: str, node_id: str, api_getter: ApiGetter = api_get) -> dict:
    detail = api_getter(base_url, email, token, DETAIL_ENDPOINTS[node_type].format(id=node_id))
    detail.setdefault("id", node_id)
    detail.setdefault("type", node_type)
    return detail


def get_children(base_url: str, email: str, token: str, node_type: str, node_id: str, api_getter: ApiGetter = api_get) -> list[dict]:
    if node_type not in CHILDREN_ENDPOINTS:
        return []
    results: list[dict] = []
    next_url = CHILDREN_ENDPOINTS[node_type].format(id=node_id)
    while next_url:
        payload = api_getter(base_url, email, token, next_url)
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


def walk_tree(base_url: str, email: str, token: str, root_type: str, root_id: str, api_getter: ApiGetter = api_get) -> list[dict]:
    detail = get_detail(base_url, email, token, root_type, root_id, api_getter)
    return walk_detail(base_url, email, token, detail, api_getter, 0, [])


def walk_detail(
    base_url: str,
    email: str,
    token: str,
    detail: dict,
    api_getter: ApiGetter,
    depth: int,
    path_titles: list[str],
    seen: set[tuple[str, str]] | None = None,
) -> list[dict]:
    seen = seen or set()
    node_type = detail.get("type", "")
    node_id = str(detail.get("id", ""))
    node_key = (node_type, node_id)
    if node_key in seen:
        return []
    seen.add(node_key)

    try:
        children = get_children(base_url, email, token, node_type, node_id, api_getter)
    except Exception:  # noqa: BLE001 - children are best effort after a page/detail fetch succeeds
        children = []
    record = node_from_detail(base_url, detail, depth, path_titles)
    record["children"] = [{"id": str(child["id"]), "type": child["type"], "title": child.get("title", "")} for child in children]
    nodes = [record]
    for child in children:
        child_detail = get_detail(base_url, email, token, child["type"], str(child["id"]), api_getter)
        nodes.extend(walk_detail(base_url, email, token, child_detail, api_getter, depth + 1, record["path"], seen))
    return nodes


def node_from_detail(base_url: str, detail: dict, depth: int, path_titles: list[str]) -> dict:
    storage = detail.get("body", {}).get("storage", {}).get("value", "")
    title = detail.get("title", "")
    return {
        "id": str(detail.get("id", "")),
        "type": detail.get("type", "page"),
        "title": title,
        "depth": depth,
        "path": [item for item in path_titles + [title] if item],
        "webUrl": build_web_url(base_url, detail.get("_links")),
        "bodyStorage": storage,
        "bodyText": storage_to_text(storage),
        "children": [],
    }


def ancestor_titles(detail: dict) -> list[str]:
    return [item.get("title", "") for item in detail.get("ancestors", []) if item.get("title")]


def build_raw_payload(parsed: dict, nodes: list[dict]) -> dict:
    documents = []
    for node in nodes:
        if node["type"] != "page":
            continue
        documents.append(
            {
                "document_id": node["id"],
                "title": node["title"],
                "source_url": node["webUrl"],
                "parent_path": node["path"][:-1],
                "source_section": " / ".join(node["path"][:-1]),
                "feature": infer_feature_from_path(node["path"]),
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
        "source_mode": parsed["source_type"],
        "source": {
            "base_url": parsed["base_url"],
            "space_key": parsed["space_key"],
            "root_type": parsed["root_type"],
            "root_id": parsed["root_id"],
        },
        "documents": documents,
        "nodes": nodes,
    }


def build_source_index(parsed: dict, nodes: list[dict]) -> dict:
    return {
        "source_mode": parsed["source_type"],
        "base_url": parsed["base_url"],
        "space_key": parsed["space_key"],
        "root_type": parsed["root_type"],
        "root_id": parsed["root_id"],
        "entries": [
            {
                "id": node["id"],
                "type": node["type"],
                "title": node["title"],
                "source_url": node.get("webUrl"),
                "parent_path": node.get("path", [])[:-1],
            }
            for node in nodes
        ],
    }


def infer_feature_from_path(path: list[str]) -> str:
    if len(path) >= 2:
        return path[-2]
    return path[0] if path else "Confluence"


def render_tree_markdown(nodes: list[dict]) -> str:
    lines = ["# Confluence Tree", ""]
    if not nodes:
        lines.append("_No Confluence pages were fetched._")
        return "\n".join(lines) + "\n"
    for node in nodes:
        indent = "  " * node["depth"]
        suffix = f" - {node['webUrl']}" if node.get("webUrl") else ""
        lines.append(f"{indent}- [{node['type']}] {node['title']} (ID: {node['id']}){suffix}")
    return "\n".join(lines) + "\n"


def redact_sensitive(value):
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if str(key).lower() in {"token", "authorization", "cookie", "password", "otp", "api_token", "api-token"}:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if not isinstance(value, str):
        return value

    text = value
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1) if match.groups() else ''}[REDACTED]", text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Confluence pages or folders into canonical raw requirement artifacts.")
    parser.add_argument("--input-url", help="Confluence page/folder URL or ID.")
    parser.add_argument("--output-dir", required=True, help="Directory to write Confluence source artifacts.")
    parser.add_argument("--mode", choices=("auto", "page", "folder"), default="auto", help="Input mode. Defaults to auto.")
    parser.add_argument("--diagnostics", action="store_true", default=True, help="Write confluence-intake-diagnostics.json.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if no pages are fetched.")
    parser.add_argument("--base-url", help="Confluence base URL, for example https://example.atlassian.net")
    parser.add_argument("--email", default="", help="Confluence login email")
    parser.add_argument("--token", default="", help="Confluence API token")
    parser.add_argument("--root", help="Legacy alias for --input-url.")
    args = parser.parse_args()

    input_url = args.input_url or args.root
    if not input_url:
        parser.error("--input-url is required unless legacy --root is supplied.")

    try:
        summary = ingest_confluence(
            input_url=input_url,
            output_dir=args.output_dir,
            email=args.email,
            token=args.token,
            base_url=args.base_url,
            mode=args.mode,
            diagnostics=args.diagnostics,
            strict=args.strict,
        )
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(json.dumps({"error": redact_sensitive(str(exc))}, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
