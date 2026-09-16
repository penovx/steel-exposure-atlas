(() => {
  const ROUTES = [
    {id: 'BOF', name: 'Basic oxygen furnace', field: 'bof_steel_capacity_ttpa'},
    {id: 'EAF', name: 'Electric arc furnace', field: 'eaf_steel_capacity_ttpa'},
    {id: 'IF', name: 'Induction furnace', field: 'if_steel_capacity_ttpa'},
    {id: 'Other', name: 'Other steelmaking', field: 'other_steel_capacity_ttpa'},
  ];
  const STATUS_ORDER = [
    'operating', 'operating pre-retirement', 'construction', 'announced',
    'mothballed', 'mothballed pre-retirement', 'retired', 'cancelled',
  ];
  const SITE_LIMIT = 6;

  function reviewApi() {
    try { return globalThis.__atlasReview ?? null; } catch { return null; }
  }

  function addText(parent, tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = value;
    parent.append(node);
    return node;
  }

  function addLink(parent, label, href) {
    const node = document.createElement('a');
    node.className = 'selection-profile-link';
    node.href = href;
    node.target = '_blank';
    node.rel = 'noreferrer';
    node.textContent = label;
    parent.append(node);
    return node;
  }

  function sentenceCase(value) {
    const text = String(value ?? '').trim();
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : '';
  }

  function unique(values) {
    return [...new Set(values.filter(Boolean))];
  }

  function plantStatuses(plant) {
    const statuses = unique((plant.tranches ?? []).map((row) => String(row.status ?? '').trim()));
    return statuses.sort((a, b) => {
      const ai = STATUS_ORDER.indexOf(a);
      const bi = STATUS_ORDER.indexOf(b);
      return (ai === -1 ? STATUS_ORDER.length : ai) - (bi === -1 ? STATUS_ORDER.length : bi)
        || a.localeCompare(b, 'en');
    });
  }

  function formatCapacity(result) {
    if (!result) return 'Not quantified';
    const known = result.known;
    if (known !== null && known !== undefined) {
      const value = Number(known) / 1000;
      return `${value.toLocaleString('en-GB', {maximumFractionDigits: value < 10 ? 2 : 1})}${result.positive ? '+' : ''} Mtpa`;
    }
    return result.positive ? '>0 Mtpa · not numerically quantified' : 'Not quantified';
  }

  function capacityFor(review, plants, field = 'crude_steel_capacity_ttpa') {
    try { return review.model?.total?.(plants, field) ?? null; } catch { return null; }
  }

  function scopedCompanyPlants(review, ownerId) {
    const region = review.snapshot()?.state?.region ?? 'World';
    return (review.all ?? []).filter((plant) =>
      plant.ownerId === ownerId && (region === 'World' || plant.region === region)
    );
  }

  function selectedPlants(review) {
    const ids = new Set(review.snapshot()?.selectedIds ?? []);
    return (review.all ?? []).filter((plant) => ids.has(plant.id));
  }

  function ownerName(review, ownerId) {
    return review.all?.find?.((plant) => plant.ownerId === ownerId)?.owner ?? ownerId;
  }

  function selectionModel(review) {
    const snapshot = review.snapshot?.();
    const state = snapshot?.state;
    if (!state) return null;
    const filters = state.filters ?? {};
    const products = Array.isArray(filters.products) ? filters.products : [];

    if (state.site) {
      const plant = review.all?.find?.((item) => item.id === state.site);
      if (!plant) return null;
      return {
        kind: 'site', eyebrow: 'SITE', title: plant.name,
        subtitle: [plant.country, plant.city && plant.city !== 'unknown' ? plant.city : ''].filter(Boolean).join(' · '),
        plants: [plant], ownerIds: unique([plant.ownerId]), plant,
      };
    }

    if (filters.owner) {
      const plants = scopedCompanyPlants(review, filters.owner);
      return {
        kind: 'company', eyebrow: 'COMPANY', title: ownerName(review, filters.owner),
        subtitle: 'Immediate owner or operator named by GEM',
        plants, ownerIds: [filters.owner], ownerId: filters.owner,
      };
    }

    const plants = selectedPlants(review);
    if (products.length) {
      const labels = products.map(sentenceCase);
      return {
        kind: 'product', eyebrow: products.length === 1 ? 'PRODUCT' : 'PRODUCTS',
        title: labels.length === 1 ? labels[0] : `${labels.length} selected products`,
        subtitle: labels.length > 1 ? labels.join(' · ') : 'GIST-listed plant product description',
        plants, ownerIds: unique(plants.map((plant) => plant.ownerId)), products,
      };
    }

    if (filters.route) {
      const route = ROUTES.find((item) => item.id === filters.route);
      return {
        kind: 'method', eyebrow: 'PRODUCTION METHOD', title: route?.name ?? filters.route,
        subtitle: 'Positive operating steelmaking capacity in the current selection',
        plants, ownerIds: unique(plants.map((plant) => plant.ownerId)), route,
      };
    }

    if (filters.country) {
      return {
        kind: 'area', eyebrow: 'AREA', title: filters.country,
        subtitle: state.region === 'World' ? 'Country / area in the GIST dataset' : `${state.region} · GIST country / area`,
        plants, ownerIds: unique(plants.map((plant) => plant.ownerId)),
      };
    }

    return null;
  }

  function section(parent, label) {
    const node = document.createElement('section');
    node.className = 'selection-profile-section';
    addText(node, 'span', 'selection-profile-section-label', label);
    parent.append(node);
    return node;
  }

  function metric(parent, value, label) {
    const node = document.createElement('div');
    node.className = 'selection-profile-metric';
    addText(node, 'strong', '', value);
    addText(node, 'span', '', label);
    parent.append(node);
  }

  function renderMetrics(root, model, review) {
    const metrics = document.createElement('div');
    metrics.className = 'selection-profile-metrics';
    const countries = unique(model.plants.map((plant) => plant.country));
    const companies = unique(model.plants.map((plant) => plant.ownerId));
    const capacity = model.kind === 'method' && model.route
      ? capacityFor(review, model.plants, model.route.field)
      : capacityFor(review, model.plants);

    if (model.kind === 'site') {
      metric(metrics, formatCapacity(capacity), 'Known operating crude-steel capacity');
      metric(metrics, plantStatuses(model.plant).map(sentenceCase).join(' · ') || 'Not stated', 'GIST capacity status');
      metric(metrics, model.plant.owner || 'Not stated', 'Immediate owner / operator');
    } else {
      metric(metrics, model.plants.length.toLocaleString('en-GB'), model.plants.length === 1 ? 'Site' : 'Sites');
      if (model.kind !== 'company') metric(metrics, companies.length.toLocaleString('en-GB'), companies.length === 1 ? 'Company' : 'Companies');
      metric(metrics, countries.length.toLocaleString('en-GB'), countries.length === 1 ? 'Country / area' : 'Countries / areas');
      metric(metrics, formatCapacity(capacity), model.kind === 'method' ? 'Known operating method capacity' : 'Known operating crude-steel capacity');
    }
    root.append(metrics);
  }

  function siteRow(plant, showOwner = false) {
    const row = document.createElement('article');
    row.className = 'selection-profile-site';
    const top = document.createElement('div');
    top.className = 'selection-profile-site-top';
    const left = document.createElement('div');
    addText(left, 'strong', 'selection-profile-site-name', plant.name);
    const place = [plant.city && plant.city !== 'unknown' ? plant.city : '', plant.country].filter(Boolean).join(' · ');
    if (place) addText(left, 'span', 'selection-profile-site-place', place);
    top.append(left);

    const statuses = plantStatuses(plant);
    if (statuses.length) {
      const statusWrap = document.createElement('div');
      statusWrap.className = 'selection-profile-statuses';
      for (const status of statuses) addText(statusWrap, 'span', 'selection-profile-status', sentenceCase(status));
      top.append(statusWrap);
    }
    row.append(top);

    if (showOwner && plant.owner) addText(row, 'p', 'selection-profile-owner', `GEM owner / operator: ${plant.owner}`);

    const products = unique(plant.products?.values ?? []).map(sentenceCase).sort((a, b) => a.localeCompare(b, 'en'));
    if (products.length) {
      const productWrap = document.createElement('div');
      productWrap.className = 'selection-profile-products';
      addText(productWrap, 'span', 'selection-profile-inline-label', 'GIST-listed products');
      const chips = document.createElement('div');
      chips.className = 'selection-profile-chips';
      for (const product of products) addText(chips, 'span', 'selection-profile-chip', product);
      productWrap.append(chips);
      row.append(productWrap);
    }
    return row;
  }

  function renderSites(root, model) {
    const sites = section(root, model.kind === 'site' ? 'SITE & PRODUCTS' : 'SITES & PRODUCTS');
    const list = document.createElement('div');
    list.className = 'selection-profile-site-list';
    const showOwner = model.kind !== 'company' && model.kind !== 'site';
    model.plants.forEach((plant, index) => {
      const row = siteRow(plant, showOwner);
      if (index >= SITE_LIMIT) row.hidden = true;
      list.append(row);
    });
    sites.append(list);

    if (model.plants.length > SITE_LIMIT) {
      const remaining = model.plants.length - SITE_LIMIT;
      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'selection-profile-more';
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = `Show ${remaining} more sites ↓`;
      toggle.addEventListener('click', () => {
        const expanded = toggle.getAttribute('aria-expanded') === 'true';
        [...list.children].forEach((row, index) => { if (index >= SITE_LIMIT) row.hidden = expanded; });
        toggle.setAttribute('aria-expanded', String(!expanded));
        toggle.textContent = expanded ? `Show ${remaining} more sites ↓` : 'Show fewer sites ↑';
      });
      sites.append(toggle);
    }
  }

  function routeRows(review, plants) {
    return ROUTES.map((route) => {
      const members = plants.filter((plant) => review.model?.hasRoute?.(plant, route.id));
      if (!members.length) return null;
      return {...route, members, capacity: capacityFor(review, plants, route.field)};
    }).filter(Boolean);
  }

  function renderProduction(root, model, review) {
    const routes = routeRows(review, model.plants);
    if (!routes.length) return;
    const production = section(root, 'PRODUCTION');
    const rows = document.createElement('div');
    rows.className = 'selection-profile-fact-list';
    for (const route of routes) {
      const row = document.createElement('div');
      row.className = 'selection-profile-fact';
      addText(row, 'strong', '', route.name);
      addText(row, 'span', '', `${formatCapacity(route.capacity)} known operating capacity · ${route.members.length} ${route.members.length === 1 ? 'site' : 'sites'}`);
      rows.append(row);
    }
    production.append(rows);
  }

  function statusFor(payload, ownerId) {
    return payload?.statuses?.find?.((item) => item.company_id === ownerId) ?? null;
  }

  function formatDate(value) {
    const text = String(value ?? '');
    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
      const [year, month, day] = text.split('-').map(Number);
      return new Intl.DateTimeFormat('en-GB', {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'})
        .format(new Date(Date.UTC(year, month - 1, day)));
    }
    return text;
  }

  function renderSanctionFinding(parent, ownerNameValue, label, status, kind) {
    const card = document.createElement('div');
    card.className = 'selection-profile-regulatory-item';
    const top = document.createElement('div');
    top.className = 'selection-profile-regulatory-top';
    addText(top, 'span', 'selection-profile-regulatory-label', label);
    addText(top, 'span', 'selection-profile-regulatory-state', status.state === 'direct_list_match' ? 'Listed' : 'Unresolved match');
    card.append(top);
    addText(card, 'strong', '', ownerNameValue);

    const matches = Array.isArray(status.reviewed_matches) ? status.reviewed_matches : [];
    if (kind === 'ofac' && status.state === 'direct_list_match') {
      const listed = unique(matches.map((item) => item.listed_since).filter(Boolean)).map(formatDate);
      const context = unique(matches.map((item) => item.designation_summary).filter(Boolean));
      const programs = unique(matches.flatMap((item) => Array.isArray(item.programmes) ? item.programmes : []));
      const parts = [
        listed.length ? `Listed since ${listed.join(', ')}` : '',
        context.join(' · '),
        programs.length ? `Program: ${programs.join(', ')}` : '',
      ].filter(Boolean);
      if (parts.length) addText(card, 'p', '', parts.join(' · '));
      const urls = unique(matches.map((item) => item.designation_source_url).filter(Boolean));
      if (urls.length === 1) addLink(card, 'OFAC designation ↗', urls[0]);
    } else if (kind === 'eu' && status.state === 'direct_list_match') {
      const refs = unique(matches.map((item) => item.eu_reference).filter(Boolean));
      if (refs.length) addText(card, 'p', '', `EU reference: ${refs.join(', ')}`);
    }
    parent.append(card);
  }

  function renderRegulatory(root, model, review, payloads, tradePayload) {
    const ownerIds = unique(model.ownerIds);
    const findings = [];
    for (const ownerId of ownerIds) {
      const name = ownerName(review, ownerId);
      const eu = statusFor(payloads.eu, ownerId);
      const ofac = statusFor(payloads.ofac, ownerId);
      if (eu && ['direct_list_match', 'review_required'].includes(eu.state)) findings.push({name, label: 'EU sanctions list', status: eu, kind: 'eu'});
      if (ofac && ['direct_list_match', 'review_required'].includes(ofac.state)) findings.push({name, label: 'U.S. sanctions list', status: ofac, kind: 'ofac'});
    }

    const siteIds = new Set(model.plants.map((plant) => plant.id));
    const tradeRows = Array.isArray(tradePayload?.plants)
      ? tradePayload.plants.filter((row) => siteIds.has(row.plant_id))
      : [];

    if (!findings.length && !tradeRows.length) return;
    const regulatory = section(root, 'SANCTIONS & TRADE');
    const list = document.createElement('div');
    list.className = 'selection-profile-regulatory-list';
    for (const finding of findings) renderSanctionFinding(list, finding.name, finding.label, finding.status, finding.kind);

    if (tradeRows.length) {
      const card = document.createElement('div');
      card.className = 'selection-profile-regulatory-item selection-profile-trade';
      const top = document.createElement('div');
      top.className = 'selection-profile-regulatory-top';
      addText(top, 'span', 'selection-profile-regulatory-label', 'EU steel import measure');
      addText(top, 'span', 'selection-profile-regulatory-state', `${tradeRows.length} ${tradeRows.length === 1 ? 'site' : 'sites'}`);
      card.append(top);
      addText(card, 'strong', '', 'EU tariff-quota framework in force');
      addText(card, 'p', '', 'Regulation (EU) 2026/1384 · annual quota period 1 Jul–30 Jun. Current Commission allocation under Implementing Regulation (EU) 2026/1457 applies 1 Jul–31 Dec 2026.');
      addText(card, 'p', 'selection-profile-impact', '50% out-of-quota duty after applicable quota exhaustion.');
      const links = document.createElement('div');
      links.className = 'selection-profile-links';
      addLink(links, 'Regulation 2026/1384 ↗', 'https://eur-lex.europa.eu/eli/reg/2026/1384/oj/eng');
      addLink(links, 'Implementing Regulation 2026/1457 ↗', 'https://eur-lex.europa.eu/eli/reg_impl/2026/1457/oj/eng');
      if (tradeRows.some((row) => row.legal_route === 'bilateral_safeguard_2026_1930')) {
        addLink(links, 'Implementing Regulation 2026/1930 ↗', 'https://eur-lex.europa.eu/eli/reg_impl/2026/1930/oj/eng');
      }
      card.append(links);
      list.append(card);
    }
    regulatory.append(list);
  }

  function renderEvidence(root, model) {
    const evidence = section(root, 'EVIDENCE & SOURCES');
    const line = document.createElement('div');
    line.className = 'selection-profile-source-line';
    addText(line, 'span', '', 'Global Energy Monitor · Global Iron and Steel Tracker · June 2026 (V1)');
    evidence.append(line);

    const links = document.createElement('div');
    links.className = 'selection-profile-links';
    if (model.kind === 'site' && model.plant?.source_url) addLink(links, 'GIST plant source ↗', model.plant.source_url);
    const sources = document.createElement('button');
    sources.type = 'button';
    sources.className = 'selection-profile-source-button';
    sources.textContent = 'Sources & interpretation ↗';
    sources.addEventListener('click', () => document.querySelector('#footer-sources')?.click());
    links.append(sources);
    evidence.append(links);
  }

  function renderProfile(review, payloads, tradePayload) {
    const area = document.querySelector('.reading-area');
    const root = document.querySelector('#selection-profile');
    if (!area || !root) return;
    const model = selectionModel(review);
    if (!model || !model.plants.length) {
      root.replaceChildren();
      area.hidden = true;
      return;
    }

    area.hidden = false;
    root.replaceChildren();
    root.dataset.profileKind = model.kind;

    const header = document.createElement('header');
    header.className = 'selection-profile-header';
    addText(header, 'span', 'selection-profile-eyebrow', model.eyebrow);
    addText(header, 'h2', 'selection-profile-title', model.title);
    if (model.subtitle) addText(header, 'p', 'selection-profile-subtitle', model.subtitle);
    root.append(header);

    renderMetrics(root, model, review);
    const body = document.createElement('div');
    body.className = 'selection-profile-body';
    renderSites(body, model);
    renderProduction(body, model, review);
    renderRegulatory(body, model, review, payloads, tradePayload);
    renderEvidence(body, model);
    root.append(body);
  }

  async function init() {
    const [payloads, tradePayload] = await Promise.all([
      globalThis.__ATLAS_SANCTIONS_PROMISE__ ?? Promise.resolve({eu: null, ofac: null}),
      globalThis.__ATLAS_TRADE_PROMISE__ ?? Promise.resolve(null),
    ]);

    const wait = () => {
      const review = reviewApi();
      const path = document.querySelector('#selection-path');
      const region = document.querySelector('#region-title');
      if (!review?.snapshot || !path || !region) {
        requestAnimationFrame(wait);
        return;
      }
      const reconcile = () => renderProfile(review, payloads ?? {eu: null, ofac: null}, tradePayload);
      new MutationObserver(reconcile).observe(path, {childList: true, subtree: true});
      new MutationObserver(reconcile).observe(region, {childList: true, subtree: true, characterData: true});
      reconcile();
    };
    wait();
  }

  init();
})();
