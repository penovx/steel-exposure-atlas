(() => {
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

  function ownerSiteCount(review, ownerId) {
    const state = review?.snapshot?.()?.state;
    if (!state) return 0;
    return review.all.filter((plant) => (
      plant.ownerId === ownerId && (state.region === 'World' || plant.region === state.region)
    )).length;
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

  function ensureCard(stage) {
    let card = stage.querySelector('#company-context-card');
    if (card) return card;

    card = document.createElement('aside');
    card.id = 'company-context-card';
    card.className = 'company-context-card';
    card.setAttribute('aria-live', 'polite');
    card.hidden = true;
    stage.append(card);
    return card;
  }

  function signal(parent, label, state, title, detail) {
    const row = document.createElement('div');
    row.className = 'company-context-signal';
    const top = document.createElement('div');
    top.className = 'company-context-signal-top';
    text(top, 'span', 'company-context-signal-label', label);
    text(top, 'span', 'company-context-signal-state', state);
    row.append(top);
    text(row, 'strong', 'company-context-signal-title', title);
    if (detail) text(row, 'p', 'company-context-signal-detail', detail);
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

  function renderCard(payloads, dismissed) {
    const review = reviewApi();
    const stage = document.querySelector('#connections-stage');
    if (!review?.snapshot || !stage) return null;

    const card = ensureCard(stage);
    const ownerId = selectedOwnerId(review);
    if (!ownerId || dismissed.value === ownerId) {
      card.hidden = true;
      return ownerId;
    }

    card.replaceChildren();
    card.hidden = false;
    card.dataset.owner = ownerId;

    const header = document.createElement('div');
    header.className = 'company-context-header';
    const heading = document.createElement('div');
    text(heading, 'span', 'company-context-eyebrow', 'COMPANY CONTEXT');
    text(heading, 'h3', 'company-context-title', ownerName(review, ownerId));
    const siteCount = ownerSiteCount(review, ownerId);
    text(heading, 'p', 'company-context-sites', `${siteCount.toLocaleString('en-GB')} connected ${siteCount === 1 ? 'site' : 'sites'}`);
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'company-context-close';
    close.setAttribute('aria-label', 'Close company context');
    close.textContent = '×';
    close.addEventListener('click', () => {
      dismissed.value = ownerId;
      card.hidden = true;
    });
    header.append(heading, close);
    card.append(header);

    const euStatus = statusFor(payloads.eu, ownerId);
    const ofacStatus = statusFor(payloads.ofac, ownerId);
    const hasEuFinding = ['direct_list_match', 'review_required'].includes(euStatus?.state);
    const hasOfacFinding = ['direct_list_match', 'review_required'].includes(ofacStatus?.state);

    const body = document.createElement('div');
    body.className = 'company-context-body';

    if (euStatus?.state === 'direct_list_match') {
      signal(body, 'EU sanctions list', 'Listed', 'Listed by the EU', 'Financial sanctions list');
    } else if (euStatus?.state === 'review_required') {
      signal(body, 'EU sanctions', 'Needs review', 'Possible sanctions-list identity', 'Company identity requires review');
    }

    if (ofacStatus?.state === 'direct_list_match') {
      const summary = ofacSummary(ofacStatus);
      signal(body, 'U.S. sanctions list', 'Listed', summary.title, summary.detail);
    } else if (ofacStatus?.state === 'review_required') {
      signal(body, 'U.S. sanctions', 'Needs review', 'Possible sanctions-list identity', 'Company identity requires review');
    }

    const hasFinding = hasEuFinding || hasOfacFinding;
    if (!hasFinding) {
      signal(body, 'Sanctions screening', 'No direct listing', 'No direct EU or U.S. listing found', 'This is not sanctions clearance.');
    }

    if (hasFinding) {
      const action = document.createElement('div');
      action.className = 'company-context-action';
      text(action, 'strong', '', 'Procurement follow-up');
      text(
        action,
        'p',
        '',
        euStatus?.state === 'review_required' || ofacStatus?.state === 'review_required'
          ? 'Resolve the company identity and route it for sanctions/compliance review before proceeding.'
          : 'Sanctions/compliance review before contracting, ordering or payment.'
      );
      body.append(action);
    }

    card.append(body);

    const evidence = document.createElement('button');
    evidence.type = 'button';
    evidence.className = 'company-context-evidence';
    evidence.textContent = 'View evidence ↓';
    evidence.addEventListener('click', () => {
      const target = document.querySelector('#reading-detail .sanctions-context, #reading-detail .sanctions-secondary-result');
      target?.scrollIntoView({behavior: 'smooth', block: 'start'});
    });
    card.append(evidence);
    return ownerId;
  }

  async function init() {
    const payloads = await (globalThis.__ATLAS_SANCTIONS_PROMISE__ ?? Promise.resolve({eu: null, ofac: null}));
    const dismissed = {value: null};
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
        if (ownerId !== lastOwnerId) dismissed.value = null;
        lastOwnerId = ownerId;
        renderCard(payloads, dismissed);
      };

      new MutationObserver(reconcile).observe(selectionPath, {childList: true, subtree: true});
      reconcile();
    };

    wait();
  }

  init();
})();
