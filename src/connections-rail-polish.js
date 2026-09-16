(() => {
  const NS = 'http://www.w3.org/2000/svg';
  const ROUTE_COLORS = new Map([
    ['BOF', '#8ebbd8'],
    ['EAF', '#c9bbf0'],
    ['IF', '#e8cd96'],
    ['Other', '#a2b0bb'],
  ]);
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

  function review() {
    return globalThis.__atlasReview ?? null;
  }

  function snapshot() {
    try {
      return review()?.snapshot?.() ?? null;
    } catch {
      return null;
    }
  }

  function scopedPlants() {
    const api = review();
    const state = snapshot()?.state;
    if (!api?.all || !state) return [];
    return state.region === 'World'
      ? api.all
      : api.all.filter((plant) => plant.region === state.region);
  }

  function ownerGroups() {
    const groups = new Map();
    for (const plant of scopedPlants()) {
      const id = String(plant.ownerId ?? '').trim();
      const name = String(plant.owner ?? '').trim();
      if (!/^E\d+$/.test(id) || !name || ['unknown', 'n/a'].includes(name.toLowerCase())) continue;
      if (!groups.has(id)) groups.set(id, {id, name, count: 0});
      groups.get(id).count += 1;
    }
    return [...groups.values()].sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'en'));
  }

  function appendScrollableOwners() {
    const state = snapshot()?.state;
    const container = document.querySelector('#company-nodes');
    if (!state || !container) return;

    const existing = new Set(
      [...container.querySelectorAll('[data-owner]')].map((node) => node.dataset.owner),
    );
    const fragment = document.createDocumentFragment();
    let added = 0;

    for (const group of ownerGroups()) {
      if (existing.has(group.id)) continue;
      const button = document.createElement('button');
      button.className = 'company-node bridge-extra-owner';
      button.type = 'button';
      button.dataset.owner = group.id;
      button.dataset.port = `owner:${group.id}`;
      button.dataset.bridgeExtraOwner = 'true';
      button.setAttribute('aria-pressed', 'false');
      button.setAttribute('aria-label', `${group.name}, ${group.count} sites in ${state.region}`);

      const name = document.createElement('span');
      name.className = 'company-name';
      name.textContent = group.name;
      const count = document.createElement('span');
      count.className = 'company-count';
      count.textContent = group.count.toLocaleString('en-GB');
      button.append(name, count);
      fragment.append(button);
      added += 1;
    }
    if (added) container.append(fragment);
  }

  function restoreStableOwnerOrder(container) {
    if (!container) return;
    const nodes = new Map(
      [...container.querySelectorAll('.company-node[data-owner]')]
        .map((node) => [node.dataset.owner, node]),
    );
    const desired = ownerGroups().map((group) => nodes.get(group.id)).filter(Boolean);
    const current = [...container.querySelectorAll('.company-node[data-owner]')];
    const alreadyStable = desired.length === current.length
      && desired.every((node, index) => node === current[index]);
    if (!alreadyStable) {
      const fragment = document.createDocumentFragment();
      for (const node of desired) fragment.append(node);
      container.append(fragment);
    }
  }

  function installOwnerSelectionBridge(companyNodes, api) {
    if (companyNodes.dataset.ownerSelectionBridge === 'true') return;
    companyNodes.dataset.ownerSelectionBridge = 'true';

    companyNodes.addEventListener('click', (event) => {
      const button = event.target.closest?.('.company-node[data-owner]');
      if (!button || !companyNodes.contains(button)) return;

      const scrollTop = companyNodes.scrollTop;
      const pageX = window.scrollX;
      const pageY = window.scrollY;
      event.preventDefault();
      event.stopPropagation();

      // Core selection is synchronous. Let its map frame complete before the
      // MutationObserver rebuilds the long public company rail. This avoids doing
      // the same large DOM rebuild twice inside the click handler.
      companyNodes.dataset.restoreScrollTop = String(scrollTop);
      api.choose('owner', button.dataset.owner);
      requestAnimationFrame(() => requestAnimationFrame(() => {
        window.scrollTo({left: pageX, top: pageY, behavior: 'auto'});
      }));
    }, true);
  }

  function removeMisleadingSublines() {
    for (const node of document.querySelectorAll('#company-nodes .company-sub')) node.remove();
    document.querySelector('#method-nodes .method-node[data-route="Other"] .method-sub')?.remove();
  }

  function removeInlineProductDescriptions() {
    for (const node of document.querySelectorAll('#product-nodes .product-description')) node.remove();
  }

  function sentenceCaseProductLabel(value) {
    const text = String(value ?? '').trim();
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
  }

  function sentenceCaseInlineProductLabels() {
    for (const node of document.querySelectorAll('#product-nodes .product-node')) {
      const labelNode = [...node.childNodes].find(
        (child) => child.nodeType === Node.TEXT_NODE && child.textContent.trim(),
      );
      if (!labelNode) continue;
      const displayName = sentenceCaseProductLabel(node.dataset.product);
      if (labelNode.textContent.trim() !== displayName) labelNode.textContent = displayName;
    }
  }

  function decorateProductPickerDescriptions() {
    for (const item of document.querySelectorAll('#browse-result .browse-item[data-browse-kind="product"]')) {
      const labelNode = item.querySelector('span > strong');
      const descriptionNode = item.querySelector('span > small');
      const key = String(item.dataset.browseId ?? '').trim().toLowerCase();
      if (labelNode) {
        const displayName = sentenceCaseProductLabel(key);
        if (labelNode.textContent !== displayName) labelNode.textContent = displayName;
      }
      if (!descriptionNode) continue;
      const description = PRODUCT_DESCRIPTIONS.get(key) ?? 'GIST-listed steel product category';
      if (descriptionNode.textContent !== description) descriptionNode.textContent = description;
    }
  }

  function pathNumbers(path) {
    return String(path.getAttribute('d') ?? '')
      .match(/-?\d+(?:\.\d+)?(?:e[-+]?\d+)?/gi)
      ?.map(Number) ?? [];
  }

  function pathEnd(path) {
    const values = pathNumbers(path);
    if (values.length < 4 || values.some((value) => !Number.isFinite(value))) return null;
    return {x: values.at(-2), y: values.at(-1)};
  }

  function svgCircle(attrs) {
    const circle = document.createElementNS(NS, 'circle');
    for (const [key, value] of Object.entries(attrs)) circle.setAttribute(key, String(value));
    return circle;
  }

  function renderMethodEndpointDots() {
    const svg = document.querySelector('#connection-lines');
    const edges = document.querySelector('#edge-layer');
    const stage = document.querySelector('#connections-stage');
    if (!svg || !edges || !stage) return;

    let layer = svg.querySelector('#method-endpoint-layer');
    if (!layer) {
      layer = document.createElementNS(NS, 'g');
      layer.id = 'method-endpoint-layer';
      layer.setAttribute('aria-hidden', 'true');
      edges.after(layer);
    }
    layer.replaceChildren();

    const stageRect = stage.getBoundingClientRect();
    for (const [route, color] of ROUTE_COLORS) {
      const edge = edges.querySelector(`.connection-edge.route-${CSS.escape(route)}`);
      let point = edge ? pathEnd(edge) : null;
      const node = document.querySelector(`#method-nodes .method-node[data-route="${route}"]`);

      if (!point && node) {
        const nodeRect = node.getBoundingClientRect();
        const labelRect = node.querySelector('.method-name')?.getBoundingClientRect() ?? nodeRect;
        point = {
          x: nodeRect.left - stageRect.left - 5,
          y: labelRect.top + labelRect.height / 2 - stageRect.top,
        };
      }
      if (!point) continue;

      const selected = node?.classList.contains('is-selected');
      layer.append(svgCircle({
        class: `method-endpoint-port route-${route}${selected ? ' is-selected' : ''}`,
        'data-route-port': route,
        cx: point.x.toFixed(2),
        cy: point.y.toFixed(2),
        r: '5',
        fill: selected ? color : '#0c1821',
        stroke: color,
        'stroke-width': selected ? '1.8' : '1.4',
      }));
    }
  }

  function syncCompanyEdgeAnchors() {
    const api = review();
    const stage = document.querySelector('#connections-stage');
    const geography = document.querySelector('#geography');
    const companyNodes = document.querySelector('#company-nodes');
    if (!api?.all || !stage || !geography || !companyNodes) return;

    const stageRect = stage.getBoundingClientRect();
    const geoRect = geography.getBoundingClientRect();
    const companyViewport = companyNodes.getBoundingClientRect();
    const ownerBySite = new Map(api.all.map((plant) => [plant.id, plant.ownerId]));

    for (const edge of document.querySelectorAll('#edge-layer .connection-edge.company')) {
      const values = pathNumbers(edge);
      if (values.length < 4) continue;
      const ownerId = ownerBySite.get(edge.dataset.site);
      const ownerNode = ownerId
        ? document.querySelector(`#company-nodes .company-node[data-owner="${CSS.escape(ownerId)}"]`)
        : null;
      if (!ownerNode) {
        edge.style.visibility = 'hidden';
        edge.dataset.ownerTargetVisibility = 'missing';
        continue;
      }

      const rect = ownerNode.getBoundingClientRect();
      const targetCenter = rect.top + rect.height / 2;
      const targetVisible = !ownerNode.hidden
        && targetCenter >= companyViewport.top
        && targetCenter <= companyViewport.bottom;
      edge.style.visibility = targetVisible ? '' : 'hidden';
      edge.dataset.ownerTargetVisibility = targetVisible ? 'visible' : 'offscreen';
      if (!targetVisible) continue;

      const from = {x: values[0], y: values[1]};
      const to = {
        x: rect.right - stageRect.left + 4,
        y: rect.top - stageRect.top + rect.height / 2,
      };

      let d;
      if (stageRect.width <= 760) {
        const spine = stageRect.width / 2 - 5;
        const bottom = geoRect.bottom - stageRect.top;
        d = `M${from.x},${from.y} C${from.x},${from.y + 35} ${spine},${bottom - 25} ${spine},${bottom + 8} L${spine},${to.y - 14} Q${spine},${to.y} ${to.x},${to.y}`;
      } else {
        d = `M${from.x},${from.y} C${from.x + (to.x - from.x) * .45},${from.y} ${to.x - (to.x - from.x) * .2},${to.y} ${to.x},${to.y}`;
      }
      if (edge.getAttribute('d') !== d) edge.setAttribute('d', d);
    }
  }

  let queued = false;
  function sync() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      const companyNodes = document.querySelector('#company-nodes');
      appendScrollableOwners();
      restoreStableOwnerOrder(companyNodes);
      if (companyNodes?.dataset.restoreScrollTop !== undefined) {
        companyNodes.scrollTop = Number(companyNodes.dataset.restoreScrollTop) || 0;
        delete companyNodes.dataset.restoreScrollTop;
      }
      removeMisleadingSublines();
      removeInlineProductDescriptions();
      sentenceCaseInlineProductLabels();
      decorateProductPickerDescriptions();
      syncCompanyEdgeAnchors();
      renderMethodEndpointDots();
    });
  }

  function install() {
    const api = review();
    const stage = document.querySelector('#connections-stage');
    const companyNodes = document.querySelector('#company-nodes');
    const productNodes = document.querySelector('#product-nodes');
    const methodNodes = document.querySelector('#method-nodes');
    const browseResult = document.querySelector('#browse-result');
    const edges = document.querySelector('#edge-layer');
    if (!api?.snapshot || !stage || !companyNodes || !productNodes || !methodNodes || !browseResult || !edges) {
      requestAnimationFrame(install);
      return;
    }

    installOwnerSelectionBridge(companyNodes, api);
    new MutationObserver(sync).observe(companyNodes, {childList: true});
    new MutationObserver(sync).observe(productNodes, {childList: true});
    new MutationObserver(sync).observe(methodNodes, {childList: true, subtree: true});
    new MutationObserver(sync).observe(browseResult, {childList: true, subtree: true});
    new MutationObserver(sync).observe(edges, {childList: true, subtree: true, attributes: true, attributeFilter: ['d']});
    new ResizeObserver(sync).observe(stage);
    companyNodes.addEventListener('scroll', sync, {passive: true});
    window.addEventListener('resize', sync, {passive: true});
    sync();
  }

  install();
})();
