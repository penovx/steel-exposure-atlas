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

function scopeProductCount(productId, state) {
  const review = globalThis.__atlasReview;
  const all = Array.isArray(review?.all) ? review.all : [];
  const scoped = state?.region === 'World'
    ? all
    : all.filter((plant) => plant.region === state?.region);
  return scoped.reduce(
    (count, plant) => count + (plant.products?.values?.includes(productId) ? 1 : 0),
    0,
  );
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

    if (!count.dataset.coreCount) {
      count.dataset.coreCount = numericCountText(count.textContent);
    }

    const connected = Number(count.dataset.coreCount.replace(/,/g, ''));
    const listed = scopeProductCount(node.dataset.product, state);
    const hasConnectedSites = focused && !node.classList.contains('dim') && connected > 0;
    const value = (hasConnectedSites ? connected : listed).toLocaleString('en-GB');
    const description = hasConnectedSites
      ? `${value} connected sites`
      : `${value} listed sites`;

    count.textContent = description;
    count.setAttribute('aria-label', description);
  }
}

// Product ports use a dedicated structural axis at the top edge of the second grid
// row. The axis is independent of product-label padding and scroll-strip geometry.
// This deliberately replaces the previous offset/measurement approach.
function ensureProductAxis() {
  const area = document.querySelector('.products-area');
  if (!area) return null;

  let axis = area.querySelector(':scope > .product-axis');
  if (!axis) {
    axis = document.createElement('div');
    axis.className = 'product-axis';
    axis.setAttribute('aria-hidden', 'true');
    area.prepend(axis);
  }
  return axis;
}

function productTargets(stageRect) {
  return [...document.querySelectorAll('#product-nodes .product-node')].map((node) => {
    const rect = node.getBoundingClientRect();
    return {
      id: node.dataset.product,
      node,
      x: rect.left + rect.width / 2 - stageRect.left,
    };
  });
}

function pathEndpoints(path) {
  const values = String(path.getAttribute('d') ?? '')
    .match(/-?\d+(?:\.\d+)?(?:e[-+]?\d+)?/gi)
    ?.map(Number);
  if (!values || values.length < 4 || values.some((value) => !Number.isFinite(value))) return null;
  return {
    start: {x: values[0], y: values[1]},
    end: {x: values[values.length - 2], y: values[values.length - 1]},
  };
}

function syncProductAxis() {
  const stage = document.querySelector('#connections-stage');
  const area = document.querySelector('.products-area');
  const axis = ensureProductAxis();
  if (!stage || !area || !axis) return;

  const stageRect = stage.getBoundingClientRect();
  const areaRect = area.getBoundingClientRect();
  if (!stageRect.width || !areaRect.width) return;

  const targets = productTargets(stageRect);
  const liveIds = new Set(targets.map((target) => target.id));
  const existing = new Map(
    [...axis.querySelectorAll('[data-axis-product]')].map((port) => [port.dataset.axisProduct, port]),
  );

  for (const target of targets) {
    let port = existing.get(target.id);
    if (!port) {
      port = document.createElement('i');
      port.className = 'product-axis-port';
      port.dataset.axisProduct = target.id;
      axis.append(port);
    }
    port.style.left = `${target.x - (areaRect.left - stageRect.left)}px`;
    port.classList.toggle('is-selected', target.node.classList.contains('is-selected'));
    port.classList.toggle('dim', target.node.classList.contains('dim'));
  }

  for (const [id, port] of existing) {
    if (!liveIds.has(id)) port.remove();
  }

  // Re-anchor the core-generated product paths to the exact structural axis.
  // Start points remain the core's plant coordinates. End points use the measured
  // horizontal centre of the matching product label and the grid-row boundary.
  const axisY = areaRect.top - stageRect.top;
  for (const edge of document.querySelectorAll('#edge-layer .connection-edge.product')) {
    const points = pathEndpoints(edge);
    if (!points || !targets.length) continue;
    const target = targets.reduce((best, candidate) =>
      Math.abs(candidate.x - points.end.x) < Math.abs(best.x - points.end.x) ? candidate : best,
    );
    const a = points.start;
    const to = {x: target.x, y: axisY};
    const d = `M${a.x},${a.y} C${a.x},${a.y + (to.y - a.y) * .45} ${to.x},${a.y + (to.y - a.y) * .8} ${to.x},${to.y}`;
    edge.setAttribute('d', d);
    edge.dataset.productTarget = target.id;
  }
}

function installProductAxisObservers() {
  const productNodes = document.querySelector('#product-nodes');
  const edgeLayer = document.querySelector('#edge-layer');
  const stage = document.querySelector('#connections-stage');
  if (!productNodes || !edgeLayer || !stage || stage.dataset.productAxisObserver === 'true') return;
  stage.dataset.productAxisObserver = 'true';

  const queue = () => requestAnimationFrame(() => {
    syncProductAxis();
    queueEdgeReadabilityMask();
  });

  const productsObserver = new MutationObserver(queue);
  productsObserver.observe(productNodes, {childList: true});

  const edgesObserver = new MutationObserver(queue);
  edgesObserver.observe(edgeLayer, {childList: true});

  const resizeObserver = new ResizeObserver(queue);
  resizeObserver.observe(stage);

  productNodes.addEventListener('scroll', queue, {passive: true});
  window.addEventListener('resize', queue, {passive: true});
  queue();
}

function installProductLabelObserver() {
  const productNodes = document.querySelector('#product-nodes');
  if (!productNodes || productNodes.dataset.labelObserver === 'true') return;
  productNodes.dataset.labelObserver = 'true';
  const observer = new MutationObserver(() => {
    decorateProductLabels();
    syncProductAxis();
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
  installProductAxisObservers();
  syncProductAxis();
  installEdgeReadabilityObserver();
  queueEdgeReadabilityMask();
}

applyWorldEntry();
