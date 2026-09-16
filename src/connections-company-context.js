(() => {
  let contextOpenOwnerId = null;
  let loadedPayloads = {eu: null, ofac: null};
  let loadedTradePayload = null;
  let offerSyncQueued = false;

  const ROUTES = [
    {id: 'BOF', name: 'Basic oxygen furnace', field: 'bof_steel_capacity_ttpa'},
    {id: 'EAF', name: 'Electric arc furnace', field: 'eaf_steel_capacity_ttpa'},
    {id: 'IF', name: 'Induction furnace', field: 'if_steel_capacity_ttpa'},
    {id: 'Other', name: 'Other steelmaking', field: 'other_steel_capacity_ttpa'},
  ];

  function reviewApi() {
    try {
      return globalThis.__atlasReview ?? null;
    } catch {
      return null;
    }
  }

  function statusFor(payload, ownerId) {
    return payload?.statuses?.find?.((item) => item.company_id === ownerId) ?? null;
  }

  function selectedOwnerId(review) {
    const state = review?.snapshot?.()?.state;
    if (!state) return null;
    if (state.filters?.owner) return state.filters.owner;
    if (!state.site) return null;
    return review.all?.find?.((plant) => plant.id === state.site)?.ownerId ?? null;
  }

  function ownerName(review, ownerId) {
    return review.all?.find?.((plant) => plant.ownerId === ownerId)?.owner ?? ownerId;
  }

  function plantsAttributedToOwnerInView(review, ownerId) {
    const snapshot = review?.snapshot?.();
    const selected = new Set(Array.isArray(snapshot?.selectedIds) ? snapshot.selectedIds : []);
    return review.all.filter((plant) => plant.ownerId === ownerId && selected.has(plant.id));
  }

  function siteIdsAttributedToOwnerInView(review, ownerId) {
    return plantsAttributedToOwnerInView(review, ownerId).map((plant) => plant.id);
  }

  function formatCapacity(capacity) {
    if (capacity?.known === null || capacity?.known === undefined) return '—';
    const value = capacity.known / 1000;
    return `${value.toLocaleString('en-GB', {maximumFractionDigits: value < 10 ? 2 : 1})}${capacity.positive ? '+' : ''} Mtpa`;
  }

  function placeName(plant) {
    if (plant.city && plant.city !== 'unknown') return plant.city;
    return String(plant.name ?? '').replace(/\s+steel plant$/i, '') || plant.id;
  }

  function placeLabel(plant) {
    return `${placeName(plant)} · ${plant.country}`;
  }

  function companyScopeSummary(review, ownerId) {
    const plants = plantsAttributedToOwnerInView(review, ownerId);
    const countries = new Map();
    for (const plant of plants) {
      if (!plant.country) continue;
      countries.set(plant.country, (countries.get(plant.country) ?? 0) + 1);
    }
    let capacity = null;
    try {
      capacity = review.model?.total?.(plants) ?? null;
    } catch {
      capacity = null;
    }
    return {
      plants,
      siteCount: plants.length,
      countryCount: countries.size,
      countries: [...countries.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'en')),
      capacityText: formatCapacity(capacity),
    };
  }

  function productSummary(plants) {
    const groups = new Map();
    for (const plant of plants) {
      for (const product of new Set(plant.products?.values ?? [])) {
        if (!groups.has(product)) groups.set(product, []);
        groups.get(product).push(plant);
      }
    }
    return [...groups.entries()]
      .map(([name, productPlants]) => ({name, plants: productPlants}))
      .sort((a, b) => b.plants.length - a.plants.length || a.name.localeCompare(b.name, 'en'));
  }

  function routeSummary(review, plants) {
    return ROUTES.map((route) => {
      const routePlants = plants.filter((plant) => review.model?.hasRoute?.(plant, route.id));
      if (!routePlants.length) return null;
      let capacity = null;
      try {
        capacity = review.model?.total?.(plants, route.field) ?? null;
      } catch {
        capacity = null;
      }
      return {
        id: route.id,
        name: route.name,
        plants: routePlants,
        capacityText: formatCapacity(capacity),
      };
    }).filter(Boolean);
  }

  function formatDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value ?? ''))) return String(value ?? '');
    const [year, month, day] = value.split('-').map(Number);
    return new Intl.DateTimeFormat('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC',
    }).format(new Date(Date.UTC(year, month - 1, day)));
  }

  function text(parent, tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = value;
    parent.append(node);
    return node;
  }

  function link(parent, className, label, href) {
    const node = document.createElement('a');
    if (className) node.className = className;
    node.textContent = label;
    node.href = href;
    node.target = '_blank';
    node.rel = 'noreferrer';
    parent.append(node);
    return node;
  }

  function ensureCard(stage) {
    let card = stage.querySelector('#company-context-card');
    if (card) return card;
    card = document.createElement('aside');
    card.id = 'company-context-card';
    card.className = 'company-context-card';
    card.setAttribute('aria-live', 'polite');
    card.setAttribute('aria-label', 'Company brief');
    card.hidden = true;
    stage.append(card);
    return card;
  }

  function addMetric(parent, value, label) {
    const item = document.createElement('div');
    item.className = 'company-context-metric';
    text(item, 'strong', '', value);
    text(item, 'span', '', label);
    parent.append(item);
  }

  function addSection(parent, label, title = '') {
    const section = document.createElement('section');
    section.className = 'company-brief-section';
    text(section, 'span', 'company-brief-section-label', label);
    if (title) text(section, 'h4', 'company-brief-section-title', title);
    parent.append(section);
    return section;
  }

  function countryDistributionText(scope) {
    return scope.countries.map(([country, count]) =>
      `${count} ${count === 1 ? 'site' : 'sites'} in ${country}`
    ).join(' · ');
  }

  function addSitesAndCountries(section, scope, companyName) {
    text(
      section,
      'p',
      'company-brief-interpretation',
      `GEM names ${companyName} as the immediate owner or operator of ${scope.siteCount} ${scope.siteCount === 1 ? 'site' : 'sites'} in this view, across ${scope.countryCount} ${scope.countryCount === 1 ? 'country' : 'countries'}.`
    );
    if (scope.countries.length) {
      text(section, 'p', 'company-brief-footprint-line', countryDistributionText(scope));
    }

    const list = document.createElement('div');
    list.className = 'company-brief-site-list';
    for (const plant of scope.plants) {
      text(list, 'div', 'company-brief-site-row', placeLabel(plant));
    }
    section.append(list);
  }

  function summarizedPlaces(plants, limit = 4) {
    const labels = plants.map(placeLabel);
    if (labels.length <= limit) return labels.join('; ');

    const countries = new Map();
    for (const plant of plants) {
      countries.set(plant.country, (countries.get(plant.country) ?? 0) + 1);
    }
    const distribution = [...countries.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'en'))
      .map(([country, count]) => `${count} ${count === 1 ? 'site' : 'sites'} in ${country}`)
      .join(' · ');
    return distribution;
  }

  function addProductRows(section, products, limit = 7) {
    const list = document.createElement('div');
    list.className = 'company-brief-ranked-list';
    for (const product of products.slice(0, limit)) {
      const row = document.createElement('div');
      row.className = 'company-brief-ranked-row';
      text(row, 'span', 'company-brief-ranked-name', product.name);
      text(row, 'span', 'company-brief-ranked-value', `Listed at ${summarizedPlaces(product.plants)}`);
      list.append(row);
    }
    if (products.length > limit) {
      text(list, 'p', 'company-brief-more', `${products.length - limit} additional product labels are available in the underlying site records.`);
    }
    section.append(list);
  }

  function addRouteRows(section, routes) {
    const list = document.createElement('div');
    list.className = 'company-brief-ranked-list';
    for (const route of routes) {
      const row = document.createElement('div');
      row.className = 'company-brief-ranked-row';
      text(row, 'span', 'company-brief-ranked-name', route.name);
      const detail = route.capacityText === '—'
        ? `Used at ${summarizedPlaces(route.plants)}`
        : `${route.capacityText} known operating capacity · ${summarizedPlaces(route.plants)}`;
      text(row, 'span', 'company-brief-ranked-value', detail);
      list.append(row);
    }
    section.append(list);
  }

  function signal(parent, {label, state, title, detail, consequence = '', kind = ''}) {
    const row = document.createElement('div');
    row.className = `company-context-signal${kind ? ` company-context-signal-${kind}` : ''}`;
    const top = document.createElement('div');
    top.className = 'company-context-signal-top';
    text(top, 'span', 'company-context-signal-label', label);
    text(top, 'span', 'company-context-signal-state', state);
    row.append(top);
    text(row, 'strong', 'company-context-signal-title', title);
    if (detail) text(row, 'p', 'company-context-signal-detail', detail);
    if (consequence) text(row, 'p', 'company-context-signal-consequence', consequence);
    parent.append(row);
  }

  function ofacSummary(status) {
    const matches = Array.isArray(status?.reviewed_matches) ? status.reviewed_matches : [];
    const listed = [...new Set(matches.map((item) => item.listed_since).filter(Boolean))];
    const contexts = [...new Set(matches.map((item) => item.designation_summary).filter(Boolean))];
    const programmes = [...new Set(matches.flatMap((item) => Array.isArray(item.programmes) ? item.programmes : []))];
    const since = listed.length ? `Listed since ${listed.map(formatDate).join(', ')}` : '';
    const detail = [since, contexts.join(' · '), programmes.length ? `Program: ${programmes.join(', ')}` : '']
      .filter(Boolean)
      .join(' · ');
    return {title: 'Listed by OFAC', detail};
  }

  function listSummary(values, limit = 4) {
    const unique = [...new Set(values.filter(Boolean))];
    if (unique.length <= limit) return unique.join(', ');
    return `${unique.slice(0, limit).join(', ')} +${unique.length - limit}`;
  }

  function tradeRowsFor(payload, siteIds) {
    if (!payload?.plants || !Array.isArray(payload.plants) || !siteIds.length) return [];
    const ids = new Set(siteIds);
    return payload.plants.filter((row) => ids.has(row.plant_id));
  }

  function tradeSummary(rows) {
    if (!rows.length) return null;
    const origins = rows.map((row) => row.origin).filter(Boolean);
    const families = rows.flatMap((row) => Array.isArray(row.product_families) ? row.product_families : []);
    const sites = rows.map((row) => row.plant_name).filter(Boolean);
    const routes = new Set(rows.map((row) => row.quota_route).filter(Boolean));
    const hasBroadFamilyMapping = rows.some((row) => row.product_family_state === 'family_requires_confirmation');
    const routeLabel = routes.size > 1
      ? 'Multiple quota routes'
      : routes.has('origin_specific') ? 'Origin-specific quota' : 'Pooled / residual quota';
    return {
      origins: listSummary(origins),
      families: listSummary(families),
      sites: listSummary(sites, 3),
      routeLabel,
      mappingLabel: hasBroadFamilyMapping ? 'Broad product-family mapping' : 'Product-family mapping',
    };
  }

  function renderTradeEvidence(tradePayload, rows) {
    for (const node of document.querySelectorAll('#reading-detail .trade-context')) node.remove();
    const readingDetail = document.querySelector('#reading-detail');
    if (!readingDetail || !rows.length) return;
    const summary = tradeSummary(rows);
    if (!summary) return;

    const section = document.createElement('section');
    section.className = 'trade-context';
    section.setAttribute('aria-label', 'EU import context');
    const top = document.createElement('div');
    top.className = 'trade-context-top';
    text(top, 'span', 'trade-context-eyebrow', 'EU IMPORT CONTEXT');
    text(top, 'span', 'trade-context-state', `${rows.length} ${rows.length === 1 ? 'site' : 'sites'} in this view`);
    section.append(top);
    text(section, 'h3', 'trade-context-title', 'If steel from these sites were imported into the EU');
    text(section, 'p', 'trade-context-intro', 'GIST origin and product labels for these sites map to the current EU steel import measure.');

    const facts = document.createElement('dl');
    facts.className = 'trade-context-facts';
    for (const [label, value] of [
      ['Sites', summary.sites],
      ['Origin', summary.origins],
      ['GIST product labels map to', summary.families],
      ['Mapping', summary.mappingLabel],
      ['Quota route', summary.routeLabel],
      ['Additional duty after quota exhaustion', '50%'],
    ]) {
      if (!value) continue;
      const row = document.createElement('div');
      text(row, 'dt', '', label);
      text(row, 'dd', '', value);
      facts.append(row);
    }
    section.append(facts);

    const sources = document.createElement('p');
    sources.className = 'trade-context-source';
    text(sources, 'span', '', 'European Union · ');
    link(sources, '', 'Regulation 2026/1384', 'https://eur-lex.europa.eu/eli/reg/2026/1384/oj/eng');
    text(sources, 'span', '', ' · ');
    link(sources, '', 'Implementing Regulation 2026/1457', 'https://eur-lex.europa.eu/eli/reg_impl/2026/1457/oj/eng');
    if (rows.some((row) => row.legal_route === 'bilateral_safeguard_2026_1930')) {
      text(sources, 'span', '', ' · ');
      link(sources, '', 'Implementing Regulation 2026/1930', 'https://eur-lex.europa.eu/eli/reg_impl/2026/1930/oj/eng');
    }
    section.append(sources);
    readingDetail.append(section);
  }

  function syncCompanyBriefOffer() {
    const review = reviewApi();
    const selected = selectedOwnerId(review);
    for (const row of document.querySelectorAll('#company-nodes .company-node[data-owner]')) {
      const isSelected = Boolean(selected && row.dataset.owner === selected);
      let offer = row.querySelector('.company-brief-offer');

      if (!isSelected) {
        offer?.remove();
        row.classList.remove('has-company-brief-offer');
        continue;
      }

      if (!offer) {
        offer = document.createElement('span');
        offer.className = 'company-brief-offer';
        offer.setAttribute('aria-hidden', 'true');
        row.append(offer);
      }
      offer.textContent = contextOpenOwnerId === selected ? 'Company brief open ↑' : 'View company brief →';
      row.classList.add('has-company-brief-offer');
      const name = row.querySelector('.company-name')?.textContent?.trim() ?? 'Company';
      row.setAttribute('aria-label', `${name}, selected. Click again to ${contextOpenOwnerId === selected ? 'close' : 'view'} company brief.`);
    }
  }

  function queueCompanyBriefOfferSync() {
    if (offerSyncQueued) return;
    offerSyncQueued = true;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      offerSyncQueued = false;
      syncCompanyBriefOffer();
    }));
  }

  function renderCard(payloads = loadedPayloads, tradePayload = loadedTradePayload) {
    const review = reviewApi();
    const stage = document.querySelector('#connections-stage');
    if (!review?.snapshot || !stage) return null;

    const card = ensureCard(stage);
    const ownerId = selectedOwnerId(review);
    if (!ownerId) {
      card.hidden = true;
      card.removeAttribute('data-owner');
      queueCompanyBriefOfferSync();
      return null;
    }

    const companyName = ownerName(review, ownerId);
    const scope = companyScopeSummary(review, ownerId);
    const products = productSummary(scope.plants);
    const routes = routeSummary(review, scope.plants);
    const siteIds = scope.plants.map((plant) => plant.id);
    const tradeRows = tradeRowsFor(tradePayload, siteIds);
    const trade = tradeSummary(tradeRows);

    card.replaceChildren();
    card.dataset.owner = ownerId;
    card.hidden = contextOpenOwnerId !== ownerId;

    const header = document.createElement('div');
    header.className = 'company-context-header';
    const heading = document.createElement('div');
    text(heading, 'span', 'company-context-eyebrow', 'COMPANY BRIEF');
    text(heading, 'h3', 'company-context-title', companyName);
    text(heading, 'p', 'company-context-role', 'GEM names this company as the immediate owner or operator of the sites shown in this view.');
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'company-context-close';
    close.setAttribute('aria-label', 'Close company brief');
    close.textContent = '×';
    close.addEventListener('click', () => {
      contextOpenOwnerId = null;
      card.hidden = true;
      syncCompanyBriefOffer();
    });
    header.append(heading, close);
    card.append(header);

    const metrics = document.createElement('div');
    metrics.className = 'company-context-metrics';
    addMetric(metrics, scope.siteCount.toLocaleString('en-GB'), 'Sites in this view');
    addMetric(metrics, scope.countryCount.toLocaleString('en-GB'), 'Countries represented');
    addMetric(metrics, scope.capacityText, 'Known operating crude-steel capacity');
    card.append(metrics);

    const overview = document.createElement('div');
    overview.className = 'company-brief-overview';
    const geography = addSection(overview, 'SITES & COUNTRIES');
    addSitesAndCountries(geography, scope, companyName);
    const productsSection = addSection(overview, 'PRODUCT-TO-SITE RELATION', `${products.length} product labels across the sites in this view`);
    addProductRows(productsSection, products);
    const methodsSection = addSection(overview, 'PRODUCTION PROFILE', `${routes.length} production methods represented across these sites`);
    addRouteRows(methodsSection, routes);
    card.append(overview);

    const euStatus = statusFor(payloads.eu, ownerId);
    const ofacStatus = statusFor(payloads.ofac, ownerId);
    const hasEuFinding = ['direct_list_match', 'review_required'].includes(euStatus?.state);
    const hasOfacFinding = ['direct_list_match', 'review_required'].includes(ofacStatus?.state);
    const hasRegulatoryContext = hasEuFinding || hasOfacFinding || Boolean(trade);

    if (hasRegulatoryContext) {
      const body = document.createElement('div');
      body.className = 'company-context-body';
      text(body, 'span', 'company-brief-section-label company-brief-regulatory-label', 'REGULATORY CONTEXT');

      if (euStatus?.state === 'direct_list_match') {
        signal(body, {
          label: 'EU sanctions list',
          state: 'Listed',
          title: 'Company identity listed by the EU',
          detail: 'European Commission financial sanctions source.',
          kind: 'sanctions',
        });
      } else if (euStatus?.state === 'review_required') {
        signal(body, {
          label: 'EU sanctions identity evidence',
          state: 'Unresolved match',
          title: 'Candidate identity match in the EU source data',
          detail: 'The reviewed identity link remains unresolved.',
          kind: 'sanctions',
        });
      }

      if (ofacStatus?.state === 'direct_list_match') {
        const summary = ofacSummary(ofacStatus);
        signal(body, {
          label: 'U.S. sanctions list',
          state: 'Listed',
          title: summary.title,
          detail: summary.detail,
          kind: 'sanctions',
        });
      } else if (ofacStatus?.state === 'review_required') {
        signal(body, {
          label: 'U.S. sanctions identity evidence',
          state: 'Unresolved match',
          title: 'Candidate identity match in the OFAC source data',
          detail: 'The reviewed identity link remains unresolved.',
          kind: 'sanctions',
        });
      }

      if (trade) {
        const detail = [
          `Sites: ${trade.sites}`,
          `Origin: ${trade.origins}`,
          `GIST product labels map to: ${trade.families}`,
          trade.mappingLabel,
        ].filter(Boolean).join(' · ');
        signal(body, {
          label: 'EU steel import measure',
          state: 'EU import context',
          title: trade.routeLabel,
          detail,
          consequence: 'If imported into the EU, the additional duty is 50% after the applicable quota is exhausted.',
          kind: 'trade',
        });
      }

      card.append(body);
    }

    const footer = document.createElement('div');
    footer.className = 'company-brief-footer';
    if (hasRegulatoryContext) {
      const evidence = document.createElement('button');
      evidence.type = 'button';
      evidence.className = 'company-context-evidence';
      evidence.textContent = 'View evidence ↓';
      evidence.addEventListener('click', () => {
        const target = document.querySelector('#reading-detail .sanctions-context, #reading-detail .trade-context, #reading-detail .sanctions-secondary-result');
        target?.scrollIntoView({behavior: 'smooth', block: 'start'});
      });
      footer.append(evidence);
    }
    text(footer, 'span', 'company-brief-footer-note', 'Public-data interpretation · no supplier ranking');
    card.append(footer);

    syncCompanyBriefOffer();
    return ownerId;
  }

  function installSecondClickGate() {
    document.addEventListener('click', (event) => {
      const button = event.target.closest?.('#company-nodes .company-node[data-owner]');
      if (!button) return;
      const review = reviewApi();
      const selected = selectedOwnerId(review);
      const clicked = button.dataset.owner;

      if (!selected || clicked !== selected) {
        contextOpenOwnerId = null;
        queueCompanyBriefOfferSync();
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      contextOpenOwnerId = contextOpenOwnerId === clicked ? null : clicked;
      renderCard();
    }, true);
  }

  async function init() {
    installSecondClickGate();
    const [payloads, tradePayload] = await Promise.all([
      globalThis.__ATLAS_SANCTIONS_PROMISE__ ?? Promise.resolve({eu: null, ofac: null}),
      globalThis.__ATLAS_TRADE_PROMISE__ ?? Promise.resolve(null),
    ]);
    loadedPayloads = payloads ?? {eu: null, ofac: null};
    loadedTradePayload = tradePayload;
    let lastOwnerId = null;

    const wait = () => {
      const review = reviewApi();
      const selectionPath = document.querySelector('#selection-path');
      const stage = document.querySelector('#connections-stage');
      const companyNodes = document.querySelector('#company-nodes');
      if (!review?.snapshot || !selectionPath || !stage || !companyNodes) {
        requestAnimationFrame(wait);
        return;
      }

      const reconcile = () => {
        const ownerId = selectedOwnerId(review);
        if (ownerId !== lastOwnerId) contextOpenOwnerId = null;
        lastOwnerId = ownerId;
        const siteIds = ownerId ? siteIdsAttributedToOwnerInView(review, ownerId) : [];
        renderTradeEvidence(loadedTradePayload, tradeRowsFor(loadedTradePayload, siteIds));
        renderCard();
        queueCompanyBriefOfferSync();
      };

      new MutationObserver(reconcile).observe(selectionPath, {childList: true, subtree: true});
      new MutationObserver(queueCompanyBriefOfferSync).observe(companyNodes, {childList: true});
      reconcile();
    };

    wait();
  }

  init();
})();
