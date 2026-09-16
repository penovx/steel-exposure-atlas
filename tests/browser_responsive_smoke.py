from __future__ import annotations

import contextlib
import http.server
import socket
import socketserver
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = [
    (320, 700),
    (375, 812),
    (430, 932),
    (768, 1024),
    (1024, 768),
    (1280, 600),
    (1280, 720),
    (1440, 900),
    (1920, 1080),
]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextlib.contextmanager
def preview_server():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(ROOT), **kwargs)
    server = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def wait_ready(page):
    page.goto(page.url if page.url.startswith("http") else page.url, wait_until="domcontentloaded")


def assert_layout(page, width, height):
    page.wait_for_selector("#geo-map .land", state="attached", timeout=15000)
    page.wait_for_selector("#company-nodes .company-node", state="attached", timeout=15000)
    page.wait_for_function("document.querySelector('#startup-status')?.hidden === true", timeout=15000)

    metrics = page.evaluate("""() => {
      const body = document.documentElement;
      const map = document.querySelector('#geography').getBoundingClientRect();
      const companies = document.querySelector('.company-rail').getBoundingClientRect();
      const methods = document.querySelector('.method-rail').getBoundingClientRect();
      const products = document.querySelector('.products-area').getBoundingClientRect();
      const header = document.querySelector('.masthead').getBoundingClientRect();
      const scope = document.querySelector('.atlas-top').getBoundingClientRect();
      return {
        scrollWidth: body.scrollWidth,
        clientWidth: body.clientWidth,
        mapW: map.width, mapH: map.height,
        companiesW: companies.width, methodsW: methods.width,
        productsW: products.width,
        headerTop: header.top, headerH: header.height,
        scopeTop: scope.top,
      };
    }""")
    assert metrics["scrollWidth"] <= metrics["clientWidth"] + 1, (width, height, "horizontal body overflow", metrics)
    assert metrics["mapW"] >= 120, (width, height, "map too narrow", metrics)
    assert metrics["mapH"] >= 220, (width, height, "map too short", metrics)
    assert metrics["companiesW"] >= 120, (width, height, "company rail unusable", metrics)
    assert metrics["methodsW"] >= 120, (width, height, "method rail unusable", metrics)
    assert metrics["productsW"] >= 240, (width, height, "products unusable", metrics)
    assert abs(metrics["headerTop"]) <= 1, (width, height, "fixed header moved", metrics)
    assert metrics["scopeTop"] >= metrics["headerH"] - 1, (width, height, "scope hidden behind header", metrics)


def assert_company_interaction(page):
    company = page.locator("#company-nodes .company-node").first
    company.scroll_into_view_if_needed()
    company.click()
    page.wait_for_timeout(100)
    assert company.get_attribute("aria-pressed") == "true"
    opener = company.locator(".company-profile-open")
    assert opener.count() == 1
    assert page.locator("#company-profile-card").is_hidden()

    opener.click()
    page.wait_for_selector("#company-profile-card:not([hidden])", timeout=5000)
    page.locator("#company-profile-card .company-profile-card-close").click()
    page.wait_for_timeout(50)
    assert page.locator("#company-profile-card").is_hidden()
    assert company.get_attribute("aria-pressed") == "true"

    company.click()
    page.wait_for_timeout(100)
    assert page.locator("#company-nodes .company-node[aria-pressed='true']").count() == 0
    assert page.locator("#company-profile-card").is_hidden()


def assert_filter_sync_and_clear(page):
    product = page.locator("#product-nodes .product-node:not([disabled])").first
    product.scroll_into_view_if_needed()
    product.click()
    page.wait_for_timeout(100)
    assert product.get_attribute("aria-pressed") == "true"
    assert page.locator("#clear-all").is_visible()

    method = page.locator("#method-nodes .method-node:not([disabled])").first
    method.click()
    page.wait_for_timeout(100)
    assert page.locator("#method-nodes .method-node[aria-pressed='true']").count() == 1
    assert page.locator("#product-nodes .product-node[aria-pressed='true']").count() >= 1

    page.locator("#clear-all").click()
    page.wait_for_timeout(100)
    assert page.locator("#company-nodes .company-node[aria-pressed='true']").count() == 0
    assert page.locator("#product-nodes .product-node[aria-pressed='true']").count() == 0
    assert page.locator("#method-nodes .method-node[aria-pressed='true']").count() == 0
    assert page.locator("#company-profile-card").is_hidden()
    assert page.locator("#clear-all").is_hidden()


def main():
    with preview_server() as url, sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto(url, wait_until="domcontentloaded")
                assert_layout(page, width, height)
                page.close()

            for width, height in [(1440, 900), (375, 812)]:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_selector("#company-nodes .company-node", timeout=15000)
                assert_company_interaction(page)
                assert_filter_sync_and_clear(page)
                page.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
