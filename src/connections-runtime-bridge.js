// Runtime bridge for the relational homepage.
// It keeps the stable interaction core unchanged while supplying UI semantics that
// are easier to read in the connected view.

const EDGE_MASK_NS = 'http://www.w3.org/2000/svg';

function reviewState() {
  try {
    return globalThis.__atlasReview?.snapshot?.().state ?? null;
  } catch {
    return null;
  }
}

function hasRelationalFocus(state) {
  if (!state) return false;
  const products = state.filters?.products ?? [];
  return Boolean(
    state.site ||
    state.filters?.country ||
    state.filters?.owner ||
    state.filters?.route ||
    products.length
  );
}

// The old prototype explorer remains reachable by its direct route for internal
// reference, but it is not part of the public-facing homepage navigation.
document.querySelector('a[href="./prototype/evidence.html"]')?.remove();

// connections-core.js reads this global binding when deciding which product edges
// to draw. No selection keeps the global overview sparse. Once any dimension is
// selected, every product listed by the connected plants can receive an edge. This
// includes product-led selections: selecting "bar", for example, can reveal which
// other product descriptions occur at those same connected plants instead of
// forcing every product edge into the selected "bar" port.
var selectedProducts = {
  get size() {
    return hasRelationalFocus(reviewState()) ? 1 : 0;
  },
  has() {
    return hasRelationalFocus(reviewState());
  },
};

function numericCountText(value) {
  const match = String(value ?? '').match(/[0-9][0-9,]*/);
  return match ? match[0] : String(value ?? '').trim();
}

function alignProductBaseline() {
  const area = document.querySelector('.products-area');
  const port = document.querySelector('#product-nodes .product-port');
  if (!area || !port) return;

  const areaRect = area.getBoundingClientRect();
  const portRect = port.getBoundingClientRect();
  if (!areaRect.height || !portRect.height) return;

  const y = portRect.top + portRect.height / 2 - areaRect.top;
  area.style.setProperty('--product-baseline-y', `${y.toFixed(2)}px`);
}

function decorateProductLabels() {
  const state = reviewState();
  if (!state) return;
  const focused = hasRelationalFocus(state);
  const stage = document.querySelector('#connections-stage');
  stage?.classList.toggle('has-relational-focus', focused);

  for (const node of document.querySelectorAll('#product-nodes .product-node')) {
    const count = node.querySelector(':scope > span');
    if (!count) continue;

    if (!count.dataset.countValue) {
      count.dataset.countValue = numericCountText(count.textContent);
    }
    const value = count.dataset.countValue;
    const description = focused ? `${value} connected sites` : `${value} listed sites`;
    count.textContent = description;
    count.setAttribute('aria-label', description);
  }

  alignProductBaseline();
}

function installProductLabelObserver() {
  const productNodes = document.querySelector('#product-nodes');
  if (!productNodes || productNodes.dataset.labelObserver === 'true') return;
  productNodes.dataset.labelObserver = 'true';
  const observer = new MutationObserver(() => {
    decorateProductLabels();
    queueEdgeReadabilityMask();
  });
  observer.observe(productNodes, {childList: true});
  decorateProductLabels();
}

let edgeMaskQueued = 0;

function svgNode(name, attrs = {}) {
  const node = document.createElementNS(EDGE_MASK_NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  return node;
}

function ensureEdgeReadabilityMask() {
  const svg = document.querySelector('#connection-lines');
  const edges = document.querySelector('#edge-layer');
  if (!svg || !edges) return null;

  let defs = svg.querySelector(':scope > defs[data-edge-readability]');
  if (!defs) {
    defs = svgNode('defs', {'data-edge-readability': 'true'});
    const mask = svgNode('mask', {
      id: 'edge-readability-mask',
      maskUnits: 'userSpaceOnUse',
      x: '0',
      y: '0',
    });
    mask.style.maskType = 'luminance';
    mask.append(svgNode('rect', {
      'data-mask-base': 'true',
      x: '0',
      y: '0',
      fill: '#ffffff',
    }));
    mask.append(svgNode('g', {'data-mask-fade-zones': 'true'}));
    defs.append(mask);
    svg.prepend(defs);
  }

  edges.setAttribute('mask', 'url(#edge-readability-mask)');
  return defs.querySelector('#edge-readability-mask');
}

function updateEdgeReadabilityMask() {
  alignProductBaseline();

  const stage = document.querySelector('#connections-stage');
  const mask = ensureEdgeReadabilityMask();
  if (!stage || !mask) return;

  const stageRect = stage.getBoundingClientRect();
  if (!stageRect.width || !stageRect.height) return;

  mask.setAttribute('width', String(stageRect.width));
  mask.setAttribute('height', String(stageRect.height));

  const base = mask.querySelector('[data-mask-base]');
  base?.setAttribute('width', String(stageRect.width));
  base?.setAttribute('height', String(stageRect.height));

  const fadeZones = mask.querySelector('[data-mask-fade-zones]');
  if (!fadeZones) return;
  fadeZones.replaceChildren();

  const protectedSelectors = [
    '.country-label',
    '.plant-name',
    '.cluster-text',
    '.map-toolset',
    '.map-key',
    '.rail-heading',
    '.rail-subtitle',
    '.company-name',
    '.company-count',
    '.company-sub',
    '.method-name',
    '.method-value',
    '.method-sub',
    '.method-note',
    '.product-heading',
    '.product-node',
  ].join(',');

  for (const element of document.querySelectorAll(protectedSelectors)) {
    const rect = element.getBoundingClientRect();
    if (!rect.width || !rect.height) continue;

    const left = Math.max(0, rect.left - stageRect.left - 4);
    const top = Math.max(0, rect.top - stageRect.top - 3);
    const right = Math.min(stageRect.width, rect.right - stageRect.left + 4);
    const bottom = Math.min(stageRect.height, rect.bottom - stageRect.top + 3);
    if (right <= 0 || bottom <= 0 || left >= stageRect.width || top >= stageRect.height) continue;

    // Dark grey in a luminance mask does not remove the relationship line entirely;
    // it reduces it to roughly 18% of its normal opacity while it crosses readable UI.
    fadeZones.append(svgNode('rect', {
      x: left.toFixed(2),
      y: top.toFixed(2),
      width: Math.max(0, right - left).toFixed(2),
      height: Math.max(0, bottom - top).toFixed(2),
      rx: '3',
      fill: '#2f2f2f',
    }));
  }
}

function queueEdgeReadabilityMask() {
  if (edgeMaskQueued) return;
  edgeMaskQueued = requestAnimationFrame(() => {
    edgeMaskQueued = 0;
    updateEdgeReadabilityMask();
  });
}

function installEdgeReadabilityObserver() {
  const stage = document.querySelector('#connections-stage');
  if (!stage || stage.dataset.edgeMaskObserver === 'true') return;
  stage.dataset.edgeMaskObserver = 'true';

  const mutationObserver = new MutationObserver(queueEdgeReadabilityMask);
  mutationObserver.observe(stage, {childList: true, subtree: true, attributes: true});

  const resizeObserver = new ResizeObserver(queueEdgeReadabilityMask);
  resizeObserver.observe(stage);

  window.addEventListener('resize', queueEdgeReadabilityMask, {passive: true});
  queueEdgeReadabilityMask();
}

function applyWorldEntry() {
  const review = globalThis.__atlasReview;
  if (!review?.setRegion || !review?.snapshot) {
    requestAnimationFrame(applyWorldEntry);
    return;
  }

  if (review.snapshot().state.region !== 'World') review.setRegion('World');

  const brand = document.querySelector('#brand-home');
  if (brand) {
    brand.onclick = (event) => {
      event.preventDefault();
      review.setRegion('World');
      window.scrollTo({top: 0, behavior: 'smooth'});
    };
  }

  installProductLabelObserver();
  decorateProductLabels();
  alignProductBaseline();
  installEdgeReadabilityObserver();
  queueEdgeReadabilityMask();
}

applyWorldEntry();
