// Runtime bridge for the relational homepage.
// It keeps the stable interaction core unchanged while supplying UI semantics that
// are easier to read in the connected view.

const EDGE_MASK_NS = 'http://www.w3.org/2000/svg';

const PRODUCT_DESCRIPTIONS = new Map([
  ['billet', 'Semi-finished long steel'],
  ['rebar', 'Reinforcing bar'],
  ['bar', 'Finished long steel bar'],
  ['wire rod', 'Rod for wire drawing'],
  ['coil', 'Coiled flat steel'],
  ['plate', 'Heavy flat steel'],
  ['wire', 'Drawn steel wire'],
  ['hot rolled', 'Hot-rolled flat steel'],
  ['cold rolled', 'Cold-rolled flat steel'],
  ['pipe', 'Steel pipe or tube'],
  ['slab', 'Semi-finished flat steel'],
  ['sheet', 'Thin flat steel'],
  ['sections', 'Structural steel sections'],
  ['section', 'Structural steel section'],
  ['profile', 'Shaped steel profile'],
  ['profiles', 'Shaped steel profiles'],
  ['tube', 'Steel tube'],
  ['seamless pipe', 'Seamless steel pipe'],
  ['tinplate', 'Tin-coated sheet steel'],
  ['galvanized', 'Zinc-coated steel'],
]);

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
// selected, every product listed by the connected plants can receive an edge.
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

function productDescription(productId) {
  const key = String(productId ?? '').trim().toLowerCase();
  return PRODUCT_DESCRIPTIONS.get(key) ?? 'GIST-listed steel product category';
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

    let descriptionNode = node.querySelector(':scope > .product-description');
    if (!descriptionNode) {
      descriptionNode = document.createElement('small');
      descriptionNode.className = 'product-description';
      count.before(descriptionNode);
    }
    descriptionNode.textContent = productDescription(node.dataset.product);

    if (!count.dataset.coreCount) {
      count.dataset.coreCount = numericCountText(count.textContent);
    }

    const connected = Number(count.dataset.coreCount.replace(/,/g, ''));
    const listed = scopeProductCount(node.dataset.product, state);
    const hasConnectedSites = focused && !node.classList.contains('dim') && connected > 0;
    const value = (hasConnectedSites ? connected : listed).toLocaleString('en-GB');
    const countDescription = hasConnectedSites
      ? `${value} connected sites`
      : `${value} listed sites`;

    count.textContent = countDescription;
    count.classList.add('product-count');
    count.setAttribute('aria-label', countDescription);
  }
}

function svgNode(name, attrs = {}) {
  const node = document.createElementNS(EDGE_MASK_NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  return node;
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

// Product ports share the SVG coordinate system with their relationship paths.
// The Y coordinate comes from the single structural divider between grid rows.
function ensureProductPortLayer() {
  const svg = document.querySelector('#connection-lines');
  const edgeLayer = document.querySelector('#edge-layer');
  if (!svg || !edgeLayer) return null;

  let layer = svg.querySelector('#product-port-layer');
  if (!layer) {
    layer = svgNode('g', {id: 'product-port-layer', 'aria-hidden': 'true'});
    edgeLayer.after(layer);
  }
  return layer;
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

function syncProductPorts() {
  const stage = document.querySelector('#connections-stage');
  const divider = document.querySelector('.product-divider');
  const layer = ensureProductPortLayer();
  if (!stage || !divider || !layer) return;

  const stageRect = stage.getBoundingClientRect();
  const dividerRect = divider.getBoundingClientRect();
  if (!stageRect.width || !dividerRect.width) return;

  const axisY = dividerRect.top + dividerRect.height / 2 - stageRect.top;
  const targets = productTargets(stageRect);
  const existing = new Map(
    [...layer.querySelectorAll('[data-axis-product]')].map((port) => [port.dataset.axisProduct, port]),
  );
  const liveIds = new Set(targets.map((target) => target.id));

  for (const target of targets) {
    let port = existing.get(target.id);
    if (!port) {
      port = svgNode('circle', {
        class: 'product-axis-port',
        'data-axis-product': target.id,
        r: '4.5',
      });
      layer.append(port);
    }
    port.setAttribute('cx', target.x.toFixed(2));
    port.setAttribute('cy', axisY.toFixed(2));
    port.classList.toggle('is-selected', target.node.classList.contains('is-selected'));
    port.classList.toggle('dim', target.node.classList.contains('dim'));
  }

  for (const [id, port] of existing) {
    if (!liveIds.has(id)) port.remove();
  }

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

function ensureMethodPorts() {
  for (const node of document.querySelectorAll('#method-nodes .method-node')) {
    if (node.querySelector(':scope > .method-port')) continue;
    const port = document.createElement('i');
    port.className = 'method-port';
    port.setAttribute('aria-hidden', 'true');
    node.prepend(port);
  }
}

function syncMethodPorts() {
  ensureMethodPorts();

  const stage = document.querySelector('#connections-stage');
  const geography = document.querySelector('#geography');
  if (!stage || !geography) return;

  const stageRect = stage.getBoundingClientRect();
  const geoRect = geography.getBoundingClientRect();
  if (!stageRect.width) return;

  const targets = new Map();
  for (const node of document.querySelectorAll('#method-nodes .method-node')) {
    const marker = node.querySelector(':scope > .method-port');
    if (!marker || !node.dataset.route) continue;
    const rect = marker.getBoundingClientRect();
    targets.set(node.dataset.route, {
      x: rect.left + rect.width / 2 - stageRect.left,
      y: rect.top + rect.height / 2 - stageRect.top,
    });
  }

  for (const edge of document.querySelectorAll('#edge-layer .connection-edge')) {
    const routeClass = [...edge.classList].find((value) => value.startsWith('route-'));
    if (!routeClass) continue;
    const routeId = routeClass.slice('route-'.length);
    const to = targets.get(routeId);
    const points = pathEndpoints(edge);
    if (!to || !points) continue;

    const a = points.start;
    let d;
    if (stageRect.width <= 760) {
      const spine = stageRect.width / 2 + 5;
      const bottom = geoRect.bottom - stageRect.top;
      d = `M${a.x},${a.y} C${a.x},${a.y + 35} ${spine},${bottom - 25} ${spine},${bottom + 8} L${spine},${to.y - 14} Q${spine},${to.y} ${to.x},${to.y}`;
    } else {
      d = `M${a.x},${a.y} C${a.x + (to.x - a.x) * .45},${a.y} ${to.x - (to.x - a.x) * .2},${to.y} ${to.x},${to.y}`;
    }
    edge.setAttribute('d', d);
    edge.dataset.routeTarget = routeId;
  }
}

function syncStructuralPorts() {
  syncProductPorts();
  syncMethodPorts();
}

function installStructuralPortObservers() {
  const productNodes = document.querySelector('#product-nodes');
  const methodNodes = document.querySelector('#method-nodes');
  const edgeLayer = document.querySelector('#edge-layer');
  const stage = document.querySelector('#connections-stage');
  if (!productNodes || !methodNodes || !edgeLayer || !stage || stage.dataset.structuralPortObserver === 'true') return;
  stage.dataset.structuralPortObserver = 'true';

  const queue = () => requestAnimationFrame(() => {
    syncStructuralPorts();
    queueEdgeReadabilityMask();
  });

  const productsObserver = new MutationObserver(queue);
  productsObserver.observe(productNodes, {childList: true});

  const methodsObserver = new MutationObserver(queue);
  methodsObserver.observe(methodNodes, {childList: true});

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
    syncStructuralPorts();
    queueEdgeReadabilityMask();
  });
  observer.observe(productNodes, {childList: true});
  decorateProductLabels();
}

let edgeMaskQueued = 0;

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
  installStructuralPortObservers();
  syncStructuralPorts();
  installEdgeReadabilityObserver();
  queueEdgeReadabilityMask();
}

applyWorldEntry();
