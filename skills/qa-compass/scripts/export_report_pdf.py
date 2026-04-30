from __future__ import annotations

import argparse
import contextlib
import http.server
import os
import shutil
import socketserver
import subprocess
import tempfile
import threading
import uuid
from pathlib import Path


def resolve_playwright_command() -> list[str]:
    if shutil.which("playwright-cli"):
        return ["playwright-cli"]
    if shutil.which("npx"):
        return ["npx", "-y", "@playwright/cli@latest"]
    raise RuntimeError(
        "playwright-cli is not installed and npx is unavailable. Install it with: npm install -g @playwright/cli@latest"
    )


def export_report_pdf(html_path: str, pdf_path: str, landscape: bool = False) -> Path:
    html_file = Path(html_path).resolve()
    if not html_file.exists():
        raise FileNotFoundError(f"HTML report not found: {html_file}")

    pdf_file = Path(pdf_path).resolve()
    pdf_file.parent.mkdir(parents=True, exist_ok=True)
    cli: list[str] | None = None
    session: str | None = None

    with served_directory(html_file.parent) as base_url:
        rendered_file = prepare_render_file(html_file, landscape)
        try:
            cli = resolve_playwright_command()
            session = f"rqo-pdf-{uuid.uuid4().hex[:8]}"
            url = f"{base_url}/{rendered_file.name}"
            run_cli(cli + [f"-s={session}", "open", url], cwd=pdf_file.parent)
            run_cli(cli + [f"-s={session}", "pdf", f"--filename={pdf_file.name}"], cwd=pdf_file.parent)
        finally:
            if cli and session:
                with contextlib.suppress(Exception):
                    run_cli(cli + [f"-s={session}", "close"], cwd=pdf_file.parent)
            if rendered_file != html_file:
                rendered_file.unlink(missing_ok=True)
    return pdf_file


def run_cli(command: list[str], cwd: Path) -> None:
    env = os.environ.copy()
    env.setdefault("PLAYWRIGHT_MCP_CAPS", "pdf")
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def prepare_render_file(html_file: Path, landscape: bool) -> Path:
    if not landscape:
        return html_file
    content = html_file.read_text(encoding="utf-8")
    injected = "<style>@page { size: letter landscape; margin: 14mm; }</style>"
    if "@page" in content and "landscape" in content:
        return html_file
    rendered = html_file.with_name(f"{html_file.stem}.landscape{html_file.suffix}")
    rendered.write_text(content.replace("</head>", f"  {injected}\n</head>"), encoding="utf-8")
    return rendered


@contextlib.contextmanager
def served_directory(directory: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, format, *args):  # noqa: A003
            return

    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_address[1]}"
        finally:
            server.shutdown()
            thread.join(timeout=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export an HTML QA report to PDF using playwright-cli.")
    parser.add_argument("--html", required=True, help="Path to the HTML report, usually qa-report.external.html")
    parser.add_argument("--pdf", required=True, help="Path to write qa-report.pdf")
    parser.add_argument("--landscape", action="store_true", help="Force landscape print CSS before export")
    args = parser.parse_args()
    pdf_path = export_report_pdf(args.html, args.pdf, landscape=args.landscape)
    print(pdf_path)


if __name__ == "__main__":
    main()
