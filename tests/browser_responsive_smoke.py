from __future__ import annotations

import contextlib
import http.server
import socket
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = [
    (320, 700), (375, 812), (430, 932), (768, 1024), (1024, 768),
    (1280, 600), (1280, 720), (1440, 900), (1920, 1080),
]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


@contextlib.contextmanager
def preview_server():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(ROOT), **kwargs)
    server = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try: yield f"http://127.0.0.1:{port}/"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)


def wait_for_atlas(page):
    page.wait_for_selector("#geo-map .land", state="attached", timeout=15000)
    page.wait_for_selector("#company-nodes[data-virtual-rail='true'] .company-node[data-virtual-owner]", state="attached", timeout=15000)
    page.wait_for_function("document.querySelector('#startup-status')?.hidden === true", timeout=15000)


def state(page):
    return page.evaluate("() => window.__atlasReview.snapshot().state")


def clear(page):
    page.evaluate("() => window.__atlasReview.clear()")
    page.wait_for_function("() => { const s=window.__atlasReview.snapshot().state; return !s.site && !s.filters.country && !s.filters.owner && !s.filters.route && s.filters.products.length===0; }")


def assert_layout(page, width, height):
    wait_for_atlas(page)
    metrics = page.evaluate("""() => {
      const body=document.documentElement, map=document.querySelector('#geography').getBoundingClientRect(),
      companies=document.querySelector('.company-rail').getBoundingClientRect(), methods=document.querySelector('.method-rail').getBoundingClientRect(),
      products=document.querySelector('.products-area').getBoundingClientRect(), header=document.querySelector('.masthead').getBoundingClientRect(),
      scope=document.querySelector('.atlas-top').getBoundingClientRect();
      return {scrollWidth:body.scrollWidth,clientWidth:body.clientWidth,mapW:map.width,mapH:map.height,companiesW:companies.width,
      methodsW:methods.width,productsW:products.width,headerTop:header.top,headerH:header.height,scopeTop:scope.top};
    }""")
    assert metrics["scrollWidth"] <= metrics["clientWidth"] + 1, (width,height,"horizontal body overflow",metrics)
    assert metrics["mapW"] >= 120 and metrics["mapH"] >= 220, (width,height,"map unusable",metrics)
    assert metrics["companiesW"] >= 120 and metrics["methodsW"] >= 120 and metrics["productsW"] >= 240, (width,height,"facet unusable",metrics)
    assert abs(metrics["headerTop"]) <= 1 and metrics["scopeTop"] >= metrics["headerH"] - 1, (width,height,"header overlap",metrics)


def assert_company_interaction(page):
    wait_for_atlas(page)
    company=page.locator("#company-nodes .company-node[data-virtual-owner]").first
    company.scroll_into_view_if_needed(); company.click()
    page.wait_for_selector("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open",timeout=5000)
    assert page.locator("#company-profile-card").is_hidden()
    page.locator("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open").click()
    page.wait_for_selector("#company-profile-card:not([hidden])",timeout=5000)
    page.locator("#company-profile-card .company-profile-card-close").click(); page.wait_for_timeout(50)
    assert page.locator("#company-profile-card").is_hidden()
    assert page.locator("#company-nodes .company-node[aria-pressed='true']").count()==1
    page.locator("#company-nodes .company-node[aria-pressed='true']").click()
    page.wait_for_function("document.querySelectorAll('#company-nodes .company-node[aria-pressed=\"true\"]').length===0")


def assert_state_matrix(page):
    clear(page)
    # Product -> method: both filters must coexist and the product must remain selected.
    product=page.locator("#product-nodes .product-node:not([disabled])").first
    product.click(); page.wait_for_timeout(80)
    product_id=state(page)["filters"]["products"][0]
    method=page.locator("#method-nodes .method-node:not([disabled])").first
    method.click(); page.wait_for_timeout(80)
    s=state(page); assert product_id in s["filters"]["products"] and s["filters"]["route"]
    # Toggle method off: product survives and all views recompute from remaining state.
    page.locator("#method-nodes .method-node[aria-pressed='true']").click(); page.wait_for_timeout(80)
    s=state(page); assert s["filters"]["route"] is None and product_id in s["filters"]["products"]
    # Toggle product off: return to base state.
    page.locator("#product-nodes .product-node[aria-pressed='true']").first.click(); page.wait_for_timeout(80)
    s=state(page); assert not s["filters"]["products"] and not s["filters"]["route"]

    # Company -> product: company must remain part of the central state.
    company=page.locator("#company-nodes .company-node[data-virtual-owner]").first
    company.click(); page.wait_for_timeout(80); owner=state(page)["filters"]["owner"]; assert owner
    compatible=page.locator("#product-nodes .product-node:not(.dim):not([disabled])").first
    compatible.click(); page.wait_for_timeout(80)
    s=state(page); assert s["filters"]["owner"]==owner and len(s["filters"]["products"])==1
    # Remove company only: product must remain.
    page.locator("#company-nodes .company-node[aria-pressed='true']").click(); page.wait_for_timeout(80)
    s=state(page); assert s["filters"]["owner"] is None and len(s["filters"]["products"])==1
    clear(page)

    # Site is exclusive only when incompatible: selecting a fresh site clears prior filters by design.
    page.evaluate("() => window.__atlasReview.choose('product', window.__atlasReview.model.products(window.__atlasReview.all)[0].id)")
    before=state(page); assert before["filters"]["products"]
    target=page.evaluate("""() => {
      const r=window.__atlasReview, s=r.snapshot();
      return r.all.find(p => !s.selectedIds.includes(p.id))?.id || r.all[0].id;
    }""")
    page.evaluate("id => window.__atlasReview.chooseSite(id)", target); page.wait_for_timeout(80)
    s=state(page); assert s["site"]==target
    assert not s["filters"]["products"] and s["filters"]["owner"] is None and s["filters"]["route"] is None and s["filters"]["country"] is None
    # Same site again deselects it.
    page.evaluate("id => window.__atlasReview.chooseSite(id)", target); page.wait_for_timeout(80)
    assert state(page)["site"] is None

    # Region change is a new base scope and clears all selections.
    page.evaluate("() => window.__atlasReview.choose('route','EAF')"); page.wait_for_timeout(50)
    page.evaluate("() => window.__atlasReview.setRegion('World')"); page.wait_for_timeout(80)
    s=state(page); assert s["region"]=='World' and not s["site"] and not s["filters"]["owner"] and not s["filters"]["route"] and not s["filters"]["products"] and not s["filters"]["country"]

    # Global clear is idempotent and clears every selection dimension.
    page.evaluate("() => { const r=window.__atlasReview; r.choose('route','EAF'); const p=r.model.products(r.all)[0]; r.choose('product',p.id); }")
    page.wait_for_timeout(50); assert page.locator("#clear-all").is_visible()
    page.locator("#clear-all").click(); page.wait_for_timeout(80)
    s=state(page); assert not s["site"] and not s["filters"]["country"] and not s["filters"]["owner"] and not s["filters"]["route"] and not s["filters"]["products"]
    assert page.locator("#company-profile-card").is_hidden() and page.locator("#clear-all").is_hidden()


def main():
    with preview_server() as url, sync_playwright() as p:
        browser=p.chromium.launch()
        try:
            for width,height in VIEWPORTS:
                page=browser.new_page(viewport={"width":width,"height":height}); page.goto(url,wait_until="domcontentloaded")
                assert_layout(page,width,height); page.close()
            for width,height in [(1440,900),(375,812)]:
                page=browser.new_page(viewport={"width":width,"height":height}); page.goto(url,wait_until="domcontentloaded"); wait_for_atlas(page)
                assert_company_interaction(page); assert_state_matrix(page); page.close()
        finally: browser.close()


if __name__=="__main__": main()
