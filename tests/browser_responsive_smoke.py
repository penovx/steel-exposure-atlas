from __future__ import annotations

import contextlib
import http.server
import socket
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
VIEWPORTS=[(320,700),(375,812),(430,932),(768,1024),(1024,768),(1280,600),(1280,720),(1440,900),(1920,1080)]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*_args): pass
@contextlib.contextmanager
def preview_server():
    with socket.socket() as sock: sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    handler=lambda *args,**kwargs: QuietHandler(*args,directory=str(ROOT),**kwargs)
    server=socketserver.ThreadingTCPServer(('127.0.0.1',port),handler); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try: yield f'http://127.0.0.1:{port}/'
    finally: server.shutdown(); server.server_close(); thread.join(timeout=2)
def wait_for_atlas(page):
    page.wait_for_selector('#geo-map .land',state='attached',timeout=15000)
    page.wait_for_selector("#company-nodes[data-virtual-rail='true'] .company-node[data-virtual-owner]",state='attached',timeout=15000)
    page.wait_for_function("document.querySelector('#startup-status')?.hidden === true",timeout=15000)
def state(page): return page.evaluate('() => window.__atlasReview.snapshot().state')
def clear(page):
    page.evaluate('() => window.__atlasReview.clear()')
    page.wait_for_function("() => {const s=window.__atlasReview.snapshot().state;return !s.site&&!s.filters.country&&!s.filters.owner&&!s.filters.route&&s.filters.products.length===0}")
def assert_layout(page,w,h):
    wait_for_atlas(page); m=page.evaluate("""() => {const b=document.documentElement,m=document.querySelector('#geography').getBoundingClientRect(),c=document.querySelector('.company-rail').getBoundingClientRect(),r=document.querySelector('.method-rail').getBoundingClientRect(),p=document.querySelector('.products-area').getBoundingClientRect(),h=document.querySelector('.masthead').getBoundingClientRect(),s=document.querySelector('.atlas-top').getBoundingClientRect();return{sw:b.scrollWidth,cw:b.clientWidth,mw:m.width,mh:m.height,cw2:c.width,rw:r.width,pw:p.width,ht:h.top,hh:h.height,st:s.top}}""")
    assert m['sw']<=m['cw']+1,(w,h,'overflow',m); assert m['mw']>=120 and m['mh']>=220,(w,h,'map',m); assert m['cw2']>=120 and m['rw']>=120 and m['pw']>=240,(w,h,'facets',m); assert abs(m['ht'])<=1 and m['st']>=m['hh']-1,(w,h,'header',m)
def assert_company_interaction(page):
    company=page.locator('#company-nodes .company-node[data-virtual-owner]').first; company.scroll_into_view_if_needed(); company.click(); page.wait_for_selector("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open",timeout=5000)
    assert page.locator('#company-profile-card').is_hidden(); page.locator("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open").click(); page.wait_for_selector('#company-profile-card:not([hidden])',timeout=5000); page.locator('#company-profile-card .company-profile-card-close').click(); assert page.locator("#company-nodes .company-node[aria-pressed='true']").count()==1
    page.locator("#company-nodes .company-node[aria-pressed='true']").click(); page.wait_for_function("document.querySelectorAll('#company-nodes .company-node[aria-pressed=\"true\"]').length===0")
def assert_state_matrix(page):
    clear(page); product=page.locator('#product-nodes .product-node:not([disabled])').first; product.click(); page.wait_for_timeout(80); pid=state(page)['filters']['products'][0]; method=page.locator('#method-nodes .method-node:not([disabled])').first; method.click(); page.wait_for_timeout(80); s=state(page); assert pid in s['filters']['products'] and s['filters']['route']
    page.locator("#method-nodes .method-node[aria-pressed='true']").click(); page.wait_for_timeout(80); s=state(page); assert s['filters']['route'] is None and pid in s['filters']['products']; page.locator("#product-nodes .product-node[aria-pressed='true']").first.click(); page.wait_for_timeout(80)
    company=page.locator('#company-nodes .company-node[data-virtual-owner]').first; company.click(); page.wait_for_timeout(80); owner=state(page)['filters']['owner']; page.locator('#product-nodes .product-node:not(.dim):not([disabled])').first.click(); page.wait_for_timeout(80); s=state(page); assert s['filters']['owner']==owner and len(s['filters']['products'])==1
    page.locator("#company-nodes .company-node[aria-pressed='true']").click(); page.wait_for_timeout(80); s=state(page); assert s['filters']['owner'] is None and len(s['filters']['products'])==1; clear(page)
    page.evaluate("() => window.__atlasReview.choose('product',window.__atlasReview.model.products(window.__atlasReview.all)[0].id)"); target=page.evaluate("() => {const r=window.__atlasReview,s=r.snapshot();return r.all.find(p=>!s.selectedIds.includes(p.id))?.id||r.all[0].id}"); page.evaluate('id=>window.__atlasReview.chooseSite(id)',target); page.wait_for_timeout(80); s=state(page); assert s['site']==target and not s['filters']['products'] and s['filters']['owner'] is None and s['filters']['route'] is None and s['filters']['country'] is None
    page.evaluate('id=>window.__atlasReview.chooseSite(id)',target); assert state(page)['site'] is None; page.evaluate("() => window.__atlasReview.choose('route','EAF')"); page.evaluate("() => window.__atlasReview.setRegion('World')"); page.wait_for_timeout(80); s=state(page); assert s['region']=='World' and not s['site'] and not s['filters']['owner'] and not s['filters']['route'] and not s['filters']['products'] and not s['filters']['country']
    page.evaluate("() => {const r=window.__atlasReview;r.choose('route','EAF');r.choose('product',r.model.products(r.all)[0].id)}"); page.locator('#clear-all').click(); page.wait_for_timeout(80); s=state(page); assert not s['site'] and not s['filters']['country'] and not s['filters']['owner'] and not s['filters']['route'] and not s['filters']['products']
def assert_keyboard(page):
    clear(page); search=page.locator('#company-search-input'); search.focus(); search.fill('Nucor'); assert page.locator('#company-nodes .company-node[data-virtual-owner]').count()>=1
    search.press('Escape'); page.wait_for_timeout(50); assert search.input_value()==''
    company=page.locator('#company-nodes .company-node[data-virtual-owner]').first; company.focus(); company.press('Enter'); page.wait_for_selector("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open",timeout=5000)
    opener=page.locator("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open"); opener.focus(); opener.press('Enter'); page.wait_for_selector('#company-profile-card:not([hidden])',timeout=5000)
    close=page.locator('#company-profile-card .company-profile-card-close'); close.focus(); close.press('Enter'); assert page.locator('#company-profile-card').is_hidden(); page.locator("#company-nodes .company-node[aria-pressed='true']").focus(); page.keyboard.press('Space'); page.wait_for_function("document.querySelectorAll('#company-nodes .company-node[aria-pressed=\"true\"]').length===0")
    product=page.locator('#product-nodes .product-node:not([disabled])').first; product.focus(); product.press('Enter'); assert state(page)['filters']['products']; page.locator('#clear-all').focus(); page.keyboard.press('Enter'); assert not state(page)['filters']['products']
def assert_touch(browser,url):
    context=browser.new_context(viewport={'width':375,'height':812},has_touch=True,is_mobile=True); page=context.new_page(); page.goto(url,wait_until='domcontentloaded'); wait_for_atlas(page)
    company=page.locator('#company-nodes .company-node[data-virtual-owner]').first; company.tap(); page.wait_for_selector("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open",timeout=5000); page.locator("#company-nodes .company-node[aria-pressed='true'] + .company-profile-open").tap(); page.wait_for_selector('#company-profile-card:not([hidden])',timeout=5000)
    box=page.locator('#company-profile-card').bounding_box(); assert box and box['width']<=375 and box['x']>=-1 and box['x']+box['width']<=376
    page.locator('#company-profile-card .company-profile-card-close').tap(); page.locator("#company-nodes .company-node[aria-pressed='true']").tap(); page.wait_for_function("document.querySelectorAll('#company-nodes .company-node[aria-pressed=\"true\"]').length===0")
    product=page.locator('#product-nodes .product-node:not([disabled])').first; product.tap(); assert state(page)['filters']['products']; page.locator('#clear-all').tap(); assert not state(page)['filters']['products']; context.close()
def main():
    with preview_server() as url,sync_playwright() as p:
        browser=p.chromium.launch()
        try:
            for w,h in VIEWPORTS:
                page=browser.new_page(viewport={'width':w,'height':h}); page.goto(url,wait_until='domcontentloaded'); assert_layout(page,w,h); page.close()
            for w,h in [(1440,900),(375,812)]:
                page=browser.new_page(viewport={'width':w,'height':h}); page.goto(url,wait_until='domcontentloaded'); wait_for_atlas(page); assert_company_interaction(page); assert_state_matrix(page); assert_keyboard(page); page.close()
            assert_touch(browser,url)
        finally: browser.close()
if __name__=='__main__': main()
