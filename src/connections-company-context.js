(() => {
  let contextOpenOwnerId = null;
  let loadedPayloads = {eu: null, ofac: null};
  let loadedTradePayload = null;

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

  function connectedPlants(review, ownerId) {
    const snapshot = review?.snapshot?.();
    const selected = new Set(Array.isArray(snapshot?.selectedIds) ? snapshot.selectedIds : []);
    return review.all.filter((plant) => plant.ownerId === ownerId && selected.has(plant.id));
  }

  function connectedSiteIds(review, ownerId) {
    return connectedPlants(review, ownerId).map((plant) => plant.id);
  }

  function companyScopeSummary(review, ownerId) {
    const plants = connectedPlants(review, ownerId);
    const countries = new Set(plants.map((plant) => plant.country).filter(Boolean));
    let capacity = null;
    try {
      capacity = review.model?.total?.(plants) ?? null;
    } catch {
      capacity = null;
    }
    let capacityText = '—';
    if (capacity?.known !== null && capacity?.known !== undefined) {
      const value = capacity.known / 1000;
      capacityText = `${value.toLocaleString('en-GB', {maximumFractionDigits: value < 10 ? 2 : 1})}${capacity.positive ? '+' : ''} Mtpa`;
    }
    return {
      plants,
      siteCount: plants.length,
      countryCount: countries.size,
      capacityText,
    };
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
    card.setAttribute('aria-label', 'Company context');
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
    const listed = matches.map((item) => item.listed_since).filter(Boolean);
    const contexts = [...new Set(matches.map((item) => item.designation_summary).filter(Boolean))];
    const since = listed.length ? ` since ${listed.map(formatDate).join(', ')}` : '';
    return {
      title: `Listed by OFAC${since}`,
      detail: contexts.join(' · '),
    };
  }

  function listSummary(values, limit = 3) {
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
    const routes = new Set(rows.map((row) => row.quota_route).filter(Boolean));
    const needsProductConfirmation = rows.some((row) => row.product_family_state === 'family_requires_confirmation');
    const routeLabel = routes.size > 1
      ? 'Multiple quota routes'
      : routes.has('origin_specific') ? 'Origin-specific quota' : 'Pooled / residual quota';
    const followUp = needsProductConfirmation || routes.has('pooled_or_residual')
      ? 'For EU import, confirm the customs code and applicable quota route before contracting or ordering.'
      : 'For EU import, confirm the customs code and current quota position before contracting or ordering.';
    return {
      origins: listSummary(origins),
      families: listSummary(families),
      routeLabel,
      state: needsProductConfirmation ? 'Product check' : 'Quota context',
      followUp,
    };
  }

  function addAction(body, paragraphs) {
    if (!paragraphs.length) return;
    const action = document.createElement('div');
    action.className = 'company-context-action';
    text(action, 'strong', '', 'Procurement follow-up');
    for (const paragraph of paragraphs) text(action, 'p', '', paragraph);
    body.append(action);
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
    text(top, 'span', 'trade-context-state', `${rows.length} ${rows.length === 1 ? 'site' : 'sites'}`);
    section.append(top);
    text(section, 'h3', 'trade-context-title', 'If imported into the EU');
    text(section, 'p', 'trade-context-intro', 'The connected site and product-family evidence points to the current EU steel import measure.');

    const facts = document.createElement('dl');
    facts.className = 'trade-context-facts';
    for (const [label, value] of [
      ['Origin', summary.origins],
      ['Product family', summary.families],
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

    const action = document.createElement('div');
    action.className = 'trade-context-action';
    text(action, 'strong', '', 'Procurement follow-up');
    text(action, 'p', '', summary.followUp);
    section.append(action);

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

  function renderCard(payloads = loadedPayloads, tradePayload = loadedTradePayload) {
    const review = reviewApi();
    const stage = document.querySelector('#connections-stage');
    if (!review?.snapshot || !stage) return null;

    const card = ensureCard(stage);
    const ownerId = selectedOwnerId(review);
    if (!ownerId) {
      card.hidden = true;
      card.removeAttribute('data-owner');
      return null;
    }

    const scope = companyScopeSummary(review, ownerId);
    const siteIds = scope.plants.map((plant) => plant.id);
    const tradeRows = tradeRowsFor(tradePayload, siteIds);
    const trade = tradeSummary(tradeRows);

    card.replaceChildren();
    card.dataset.owner = ownerId;
    card.hidden = contextOpenOwnerId !== ownerId;

    const header = document.createElement('div');
    header.className = 'company-context-header';
    const heading = document.createElement('div');
    text(heading, 'span', 'company-context-eyebrow', 'COMPANY CONTEXT');
    text(heading, 'h3', 'company-context-title', ownerName(review, ownerId));
    text(heading, 'p', 'company-context-role', 'Immediate owner or operator named by GEM');
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'company-context-close';
    close.setAttribute('aria-label', 'Close company context');
    close.textContent = '×';
    close.addEventListener('click', () => {
      contextOpenOwnerId = null;
      card.hidden = true;
    });
    header.append(heading, close);
    card.append(header);

    const metrics = document.createElement('div');
    metrics.className = 'company-context-metrics';
    addMetric(metrics, scope.siteCount.toLocaleString('en-GB'), 'Connected sites');
    addMetric(metrics, scope.countryCount.toLocaleString('en-GB'), 'Countries');
    addMetric(metrics, scope.capacityText, 'Known operating capacity');
    card.append(metrics);

    const euStatus = statusFor(payloads.eu, ownerId);
    const ofacStatus = statusFor(payloads.ofac, ownerId);
    const hasScreeningResult = Boolean(euStatus || ofacStatus);
    const hasEuFinding = ['direct_list_match', 'review_required'].includes(euStatus?.state);
    const hasOfacFinding = ['direct_list_match', 'review_required'].includes(ofacStatus?.state);

    const body = document.createElement('div');
    body.className = 'company-context-body';

    if (euStatus?.state === 'direct_list_match') {
      signal(body, {label: 'EU sanctions list', state: 'Listed', title: 'Listed by the EU', detail: 'Financial sanctions list', kind: 'sanctions'});
    } else if (euStatus?.state === 'review_required') {
      signal(body, {label: 'EU sanctions', state: 'Needs review', title: 'Possible sanctions-list identity', detail: 'Company identity requires review', kind: 'sanctions'});
    }

    if (ofacStatus?.state === 'direct_list_match') {
      const summary = ofacSummary(ofacStatus);
      signal(body, {label: 'U.S. sanctions list', state: 'Listed', title: summary.title, detail: summary.detail, kind: 'sanctions'});
    } else if (ofacStatus?.state === 'review_required') {
      signal(body, {label: 'U.S. sanctions', state: 'Needs review', title: 'Possible sanctions-list identity', detail: 'Company identity requires review', kind: 'sanctions'});
    }

    const hasFinding = hasEuFinding || hasOfacFinding;
    if (hasScreeningResult && !hasFinding) {
      signal(body, {label: 'Sanctions screening', state: 'No direct listing', title: 'No direct EU or U.S. listing found', detail: 'This is not sanctions clearance.', kind: 'sanctions-negative'});
    }

    if (trade) {
      const detail = ['If imported into the EU', `${tradeRows.length} connected ${tradeRows.length === 1 ? 'site' : 'sites'}`, trade.origins, trade.families].filter(Boolean).join(' · ');
      signal(body, {
        label: 'EU steel import measure',
        state: trade.state,
        title: trade.routeLabel,
        detail,
        consequence: '50% additional duty after the applicable quota is exhausted.',
        kind: 'trade',
      });
    }

    const followUps = [];
    if (hasFinding) {
      followUps.push(
        euStatus?.state === 'review_required' || ofacStatus?.state === 'review_required'
          ? 'Resolve the company identity and route it for sanctions/compliance review before proceeding.'
          : 'Sanctions/compliance review before contracting, ordering or payment.'
      );
    }
    if (trade) followUps.push(trade.followUp);
    addAction(body, followUps);
    if (body.children.length) card.append(body);

    if (hasScreeningResult || trade) {
      const evidence = document.createElement('button');
      evidence.type = 'button';
      evidence.className = 'company-context-evidence';
      evidence.textContent = 'View evidence ↓';
      evidence.addEventListener('click', () => {
        const target = document.querySelector('#reading-detail .sanctions-context, #reading-detail .trade-context, #reading-detail .sanctions-secondary-result');
        target?.scrollIntoView({behavior: 'smooth', block: 'start'});
      });
      card.append(evidence);
    }
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
      if (!review?.snapshot || !selectionPath || !stage) {
        requestAnimationFrame(wait);
        return;
      }

      const reconcile = () => {
        const ownerId = selectedOwnerId(review);
        if (ownerId !== lastOwnerId) contextOpenOwnerId = null;
        lastOwnerId = ownerId;
        const siteIds = ownerId ? connectedSiteIds(review, ownerId) : [];
        renderTradeEvidence(loadedTradePayload, tradeRowsFor(loadedTradePayload, siteIds));
        renderCard();
      };

      new MutationObserver(reconcile).observe(selectionPath, {childList: true, subtree: true});
      reconcile();
    };

    wait();
  }

  init();
})();
