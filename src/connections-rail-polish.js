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
    const api = review();
    const state = snapshot()?.state;
    const container = document.querySelector('#company-nodes');
    if (!api?.choose || !state || !container) return;

    const existing = new Set(
      [...container.querySelectorAll('[data-owner]')].map((node) => node.dataset.owner),
    );

    for (const group of ownerGroups()) {
      if (existing.has(group.id)) continue;
      const button = document.createElement('button');
      button.className = 'company-node bridge-extra-owner';
      button.type = 'button';
      button.dataset.owner = group.id;
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
      button.addEventListener('click', () => api.choose('owner', group.id));
      container.append(button);
    }
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

  function pathEnd(path) {
    const values = String(path.getAttribute('d') ?? '')
      .match(/-?\d+(?:\.\d+)?(?:e[-+]?\d+)?/gi)
      ?.map(Number);
    if (!values || values.length < 4 || values.some((value) => !Number.isFinite(value))) return null;
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

  let queued = false;
  function sync() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      appendScrollableOwners();
      removeMisleadingSublines();
      removeInlineProductDescriptions();
      sentenceCaseInlineProductLabels();
      decorateProductPickerDescriptions();
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

    new MutationObserver(sync).observe(companyNodes, {childList: true});
    new MutationObserver(sync).observe(productNodes, {childList: true});
    new MutationObserver(sync).observe(methodNodes, {childList: true, subtree: true});
    new MutationObserver(sync).observe(browseResult, {childList: true, subtree: true});
    new MutationObserver(sync).observe(edges, {childList: true, subtree: true, attributes: true, attributeFilter: ['d']});
    new ResizeObserver(sync).observe(stage);
    window.addEventListener('resize', sync, {passive: true});
    sync();
  }

  install();
})();
