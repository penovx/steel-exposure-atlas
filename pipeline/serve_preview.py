#!/usr/bin/env python3
"""Serve a read-only, identifiable local snapshot of the atlas.

Uses no third-party packages and opens no remote URL. This is a development tool,
not a deployment server or publication approval. Source files are never changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import threading
import webbrowser
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    "index.html": "text/html; charset=utf-8",
    "src/app.js": "text/javascript; charset=utf-8",
    "src/styles.css": "text/css; charset=utf-8",
    "src/map/render-world.js": "text/javascript; charset=utf-8",
    "public/data/gist-plants.v1.json": "application/json; charset=utf-8",
    "public/data/ne_110m_admin_0_countries.v5.1.1.geojson": "application/geo+json; charset=utf-8",
}
REQUIRED_CONTROLS = {"zoom-in", "zoom-out", "zoom-reset", "region-select", "country-select"}
BOOT = b"""// Local preview only: open the working Production view, not the context cover.
const button = document.getElementById('production-mode');
const observer = new MutationObserver(activate);
function activate() {
  if (!button || button.disabled) return;
  observer.disconnect();
  if (!button.classList.contains('is-active')) button.click();
}
if (button) {
  observer.observe(button, {attributes: true, attributeFilter: ['disabled']});
  activate();
}
"""


class ElementIds(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.ids.update(value for key, value in attrs if key == "id" and value)


def git_value(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            check=True, timeout=5,
        )
        return result.stdout.strip() or "detached"
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def load_snapshot(root: Path) -> tuple[dict[str, tuple[bytes, str]], dict[str, object]]:
    root = root.resolve()
    files: dict[str, tuple[bytes, str]] = {}
    hashes = {}
    for relative, mime in ASSETS.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Preview file points outside the repository: {relative}")
        if not path.is_file():
            raise ValueError(f"Required local preview file is missing: {relative}")
        raw = path.read_bytes()
        files['/' + relative] = (raw, mime)
        hashes[relative] = hashlib.sha256(raw).hexdigest()

    html = files['/index.html'][0].decode('utf-8-sig')
    ids = ElementIds()
    ids.feed(html)
    missing = REQUIRED_CONTROLS - ids.ids
    if missing:
        raise ValueError(
            "This checkout does not contain the navigation update. Missing controls: "
            + ', '.join(sorted(missing))
            + ". Update branch feat/gist-publication-integration first."
        )
    if '</h1>' not in html or '</body>' not in html:
        raise ValueError('Preview could not locate the page header or body.')

    # UI identity describes served bytes, even when a checkout has local changes.
    ui_hashes = {name: digest for name, digest in hashes.items() if not name.startswith('public/')}
    ui_id = hashlib.sha256(json.dumps(ui_hashes, sort_keys=True).encode()).hexdigest()[:12]
    badge = (
        '<small id="preview-build" style="display:block;font:11px/1.4 ui-monospace,monospace;'
        'color:#aab3c0;letter-spacing:0.03em">'
        f'PREVIEW · nav-v2 · {ui_id}</small>'
    )
    html = html.replace('</h1>', badge + '</h1>', 1)
    html = html.replace('</body>', '<script type="module" src="/__preview__/boot.js"></script></body>', 1)
    files['/index.html'] = (html.encode('utf-8'), ASSETS['index.html'])
    files['/'] = files['/index.html']
    files['/__preview__/boot.js'] = (BOOT, 'text/javascript; charset=utf-8')
    info: dict[str, object] = {
        'preview': 'nav-v2', 'ui_id': ui_id,
        'branch': git_value(root, 'branch', '--show-current'),
        'commit': git_value(root, 'rev-parse', 'HEAD'),
        'source_file_sha256': hashes,
        'data_publication_approved_by_this_tool': False,
    }
    files['/__preview__/status'] = (json.dumps(info, indent=2).encode(), 'application/json; charset=utf-8')
    return files, info


def handler_for(files: dict[str, tuple[bytes, str]], ui_id: str) -> type[BaseHTTPRequestHandler]:
    class PreviewHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.respond(False)

        def do_HEAD(self) -> None:
            self.respond(True)

        def respond(self, head: bool) -> None:
            path = unquote(urlsplit(self.path).path)
            if path == '/favicon.ico':
                self.send_response(204)
                self.end_headers()
                return
            resource = files.get(path)
            if resource is None:
                self.send_error(404, 'Not a preview resource')
                return
            raw, mime = resource
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store, max-age=0')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Atlas-Preview', ui_id)
            self.end_headers()
            if not head:
                self.wfile.write(raw)

    return PreviewHandler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0, help='Default: choose a free local port.')
    parser.add_argument('--no-open', action='store_true', help='Print the URL without opening a browser.')
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535')
    try:
        files, info = load_snapshot(ROOT)
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(files, str(info['ui_id'])))
    except (OSError, ValueError) as error:
        parser.exit(1, f'PREVIEW NOT STARTED: {error}\n')
    url = f"http://127.0.0.1:{server.server_port}/?preview={info['ui_id']}"
    print(f"REPOSITORY: {ROOT}\nBRANCH: {info['branch']}\nCOMMIT: {info['commit']}", flush=True)
    print(f"PREVIEW: nav-v2 / {info['ui_id']}\nOPEN: {url}", flush=True)
    print('Read-only snapshot. Keep this window open. Press the Ctrl and C keys together to stop.', flush=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        if not args.no_open:
            try:
                if not webbrowser.open_new_tab(url):
                    print('Automatic browser opening unavailable; use the OPEN address above.', flush=True)
            except webbrowser.Error:
                print('Automatic browser opening unavailable; use the OPEN address above.', flush=True)
        while thread.is_alive():
            thread.join(0.5)
    except KeyboardInterrupt:
        print('\nPreview stopped.', flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == '__main__':
    main()
