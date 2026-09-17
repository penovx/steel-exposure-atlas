from __future__ import annotations

import contextlib
import http.server
import socket
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = [(320,700),(375,812),(430,932),(768,1024),(1024,768),(1280,600),(1280,720),(1440,900),(1920,1080)]

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*_args): pass

@contextlib.contextmanager
def preview_server():
    with socket.socket() as sock: sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    handler=lambda *a,**k: QuietHandler(*a,directory=str(ROOT),**k)
    server=socketserver.ThreadingTCPServer(('127.0.0.1',port),handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    try: yield f'http://127.0.0.1:{port}/'
    finally: server.shutdown(); server.server_close(); thread.join(timeout=2)

def runtime_diagnostics(page):
    return page.evaluate("""async () => {
      const status=document.querySelector('#startup-status');
      let gistHash=null, gistError=null;
      try {
        const response=await fetch('./public/data/gist-plants.v1.json',{cache:'no-store'});
        const bytes=await response.arrayBuffer();
        const digest=await crypto.subtle.digest('SHA-256',bytes);
        gistHash=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('').toUpperCase();
      } catch (error) { gistError=String(error); }
      return {
        statusText:status?.textContent||null,
        statusClass:status?.className||null,
        atlasData:Boolean(window.__ATLAS_DATA__),
        atlasReview:Boolean(window.__atlasReview),
        gistHash,
        gistError,
        landCount:document.querySelectorAll('#geo-map .land').length,
      };
    }""")

def wait_for_atlas(page):
    try:
        page.wait_for_selector('#geo-map .land',state='attached',timeout=15000)
        page.wait_for_selector("#company-nodes[data-virtual-rail='true'] .company-node[data-virtual-owner]",state='attached',timeout=15000)
    except PlaywrightTimeoutError as error:
        raise AssertionError(f'Atlas failed to render: {runtime_diagnostics(page)}') from error
    page.wait_for_timeout(80)

def state(page): return page.evaluate('() => window.__atlasReview.snapshot().state')
def clear(page): page.evaluate('() => window.__atlasReview.clear()'); page.wait_for_timeout(80)

def assert_layout(page,w,h):
    wait_for_atlas(page)
    m=page.evaluate("""() => {const b=document.documentElement,m=document.querySelector('#geography').getBoundingClientRect(),c=document.querySelector('.company-rail').getBoundingClientRect(),r=document.querySelector('.method-rail').getBoundingClientRect(),p=document.querySelector('.products-area').getBoundingClientRect(),h=document.querySelector('.masthead').getBoundingClientRect(),s=document.querySelector('.atlas-top').getBoundingClientRect();return{sw:b.scrollWidth,cw:b.clientWidth,mw:m.width,mh:m.height,cw2:c.width,rw:r.width,pw:p.width,ht:h.top,hh:h.height,st:s.top}}""")
    assert m['sw']<=m['cw']+1,(w,h,'overflow',m); assert m['mw']>=120 and m['mh']>=220,(w,h,'map',m); assert m['cw2']>=120 and m['rw']>=120 and m['pw']>=240,(w,h,'facets',m); assert abs(m['ht'])<=1 and m['st']>=m['hh']-1,(w,h,'header',m)

def assert_company_interaction(page):
    c=page.locator('#company-nodes .company-node[data-virtual-owner]').first
    c.scroll_into_view_if_needed(); c.click()
    page.wait_for_selector("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open",timeout=5000)
    assert page.locator('#company-profile-card').is_hidden()
    page.locator("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open").click()
    page.wait_for_selector('#company-profile-card:not([hidden])',timeout=5000)
    page.locator('#company-profile-card .company-profile-card-close').click()
    assert page.locator("#company-nodes .company-node[aria-pressed='true']").count()==1
    page.locator("#company-nodes .company-node[aria-pressed='true']").click(); page.wait_for_timeout(80)
    assert page.locator("#company-nodes .company-node[aria-pressed='true']").count()==0

def assert_state_matrix(page):
    clear(page); p=page.locator('#product-nodes .product-node:not([disabled])').first; p.click(); page.wait_for_timeout(80); pid=state(page)['filters']['products'][0]; m=page.locator('#method-nodes .method-node:not([disabled])').first; m.click(); page.wait_for_timeout(80); s=state(page); assert pid in s['filters']['products'] and s['filters']['route']; page.locator("#method-nodes .method-node[aria-pressed='true']").click(); page.wait_for_timeout(80); s=state(page); assert s['filters']['route'] is None and pid in s['filters']['products']; page.locator("#product-nodes .product-node[aria-pressed='true']").first.click(); page.wait_for_timeout(80)
    c=page.locator('#company-nodes .company-node[data-virtual-owner]').first; c.click(); page.wait_for_timeout(80); owner=state(page)['filters']['owner']; page.locator('#product-nodes .product-node:not(.dim):not([disabled])').first.click(); page.wait_for_timeout(80); s=state(page); assert s['filters']['owner']==owner and len(s['filters']['products'])==1; page.locator("#company-nodes .company-node[aria-pressed='true']").click(); page.wait_for_timeout(80); s=state(page); assert s['filters']['owner'] is None and len(s['filters']['products'])==1; clear(page)
    page.evaluate("() => window.__atlasReview.choose('product',window.__atlasReview.model.products(window.__atlasReview.all)[0].id)"); target=page.evaluate("() => {const r=window.__atlasReview,s=r.snapshot();return r.all.find(p=>!s.selectedIds.includes(p.id))?.id||r.all[0].id}"); page.evaluate('id=>window.__atlasReview.chooseSite(id)',target); page.wait_for_timeout(80); s=state(page); assert s['site']==target and not s['filters']['products'] and s['filters']['owner'] is None and s['filters']['route'] is None and s['filters']['country'] is None; page.evaluate('id=>window.__atlasReview.chooseSite(id)',target); assert state(page)['site'] is None
    page.evaluate("() => window.__atlasReview.choose('route','EAF')"); page.evaluate("() => window.__atlasReview.setRegion('World')"); page.wait_for_timeout(80); s=state(page); assert s['region']=='World' and not s['site'] and not s['filters']['owner'] and not s['filters']['route'] and not s['filters']['products'] and not s['filters']['country']
    page.evaluate("() => {const r=window.__atlasReview;r.choose('route','EAF');r.choose('product',r.model.products(r.all)[0].id)}"); page.locator('#clear-all').click(); page.wait_for_timeout(80); s=state(page); assert not s['site'] and not s['filters']['country'] and not s['filters']['owner'] and not s['filters']['route'] and not s['filters']['products']

def main():
    with preview_server() as url,sync_playwright() as p:
        browser=p.chromium.launch()
        try:
            for w,h in VIEWPORTS:
                page=browser.new_page(viewport={'width':w,'height':h}); page.goto(url,wait_until='domcontentloaded'); assert_layout(page,w,h); page.close()
            for w,h in [(1440,900),(375,812)]:
                page=browser.new_page(viewport={'width':w,'height':h}); page.goto(url,wait_until='domcontentloaded'); wait_for_atlas(page); assert_company_interaction(page); assert_state_matrix(page); page.close()
        finally: browser.close()

if __name__=='__main__': main()
