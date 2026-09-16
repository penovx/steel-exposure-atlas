(() => {
  let queued = false;

  function reviewApi() {
    try {
      return globalThis.__atlasReview ?? null;
    } catch {
      return null;
    }
  }

  function selectedOwnerId(review) {
    const state = review?.snapshot?.()?.state;
    if (!state) return null;
    if (state.filters?.owner) return state.filters.owner;
    if (!state.site) return null;
    return review.all?.find?.((plant) => plant.id === state.site)?.ownerId ?? null;
  }

  function connectedPlants(review, ownerId) {
    const selected = new Set(review?.snapshot?.()?.selectedIds ?? []);
    return (review?.all ?? []).filter(
      (plant) => plant.ownerId === ownerId && selected.has(plant.id),
    );
  }

  function cardIsOpen(ownerId) {
    const card = document.querySelector('#company-context-card');
    return Boolean(card && !card.hidden && card.dataset.owner === ownerId);
  }

  function ensureFirstClickOffer() {
    const review = reviewApi();
    const selected = selectedOwnerId(review);

    for (const row of document.querySelectorAll('#company-nodes .company-node[data-owner]')) {
      const existing = row.querySelector('.company-brief-offer');
      if (!selected || row.dataset.owner !== selected) {
        existing?.remove();
        row.classList.remove('has-company-brief-offer');
        continue;
      }

      let offer = existing;
      if (!offer) {
        offer = document.createElement('span');
        offer.className = 'company-brief-offer';
        offer.setAttribute('aria-hidden', 'true');
        row.append(offer);
      }

      const open = cardIsOpen(selected);
      const copy = open ? 'Company brief open ↑' : 'Open company brief →';
      if (offer.textContent !== copy) offer.textContent = copy;
      row.classList.add('has-company-brief-offer');

      const name = row.querySelector('.company-name')?.textContent?.trim() ?? 'Company';
      const aria = `${name}, selected. Click again to ${open ? 'close' : 'open'} company brief.`;
      if (row.getAttribute('aria-label') !== aria) row.setAttribute('aria-label', aria);
    }
  }

  function formatCountrySummary(plants) {
    const counts = new Map();
    for (const plant of plants) {
      if (!plant.country) continue;
      counts.set(plant.country, (counts.get(plant.country) ?? 0) + 1);
    }
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'en'))
      .map(([country, count]) => `${count} ${count === 1 ? 'site' : 'sites'} in ${country}`)
      .join(' · ');
  }

  function sectionByLabel(label) {
    return [...document.querySelectorAll('#company-context-card .company-brief-section')]
      .find((section) => section.querySelector('.company-brief-section-label')?.textContent?.trim() === label) ?? null;
  }

  function patchSitesAndCountries(review, ownerId) {
    const section = sectionByLabel('FOOTPRINT') ?? sectionByLabel('SITES & COUNTRIES');
    if (!section) return;

    const label = section.querySelector('.company-brief-section-label');
    if (label?.textContent !== 'SITES & COUNTRIES') label.textContent = 'SITES & COUNTRIES';

    let title = section.querySelector('.company-brief-section-title');
    if (!title) {
      title = document.createElement('h4');
      title.className = 'company-brief-section-title';
      label?.after(title);
    }
    const titleCopy = 'Where the connected plants are located';
    if (title.textContent !== titleCopy) title.textContent = titleCopy;

    const plants = connectedPlants(review, ownerId);
    const summary = section.querySelector('.company-brief-footprint-line');
    const countryCopy = formatCountrySummary(plants);
    if (summary && summary.textContent !== countryCopy) summary.textContent = countryCopy;

    for (const country of section.querySelectorAll('.company-brief-site-country')) {
      const plain = country.textContent.replace(/^·\s*/, '').trim();
      const copy = plain ? `· ${plain}` : '';
      if (country.textContent !== copy) country.textContent = copy;
    }
  }

  function patchProductCoverage() {
    const section = sectionByLabel('PRODUCTS');
    if (!section) return;

    const title = section.querySelector('.company-brief-section-title');
    if (title) {
      const match = title.textContent.match(/^(\d+)\s+listed product types$/i);
      if (match) title.textContent = `${match[1]} product types listed across connected sites`;
    }

    for (const value of section.querySelectorAll('.company-brief-ranked-value')) {
      const match = value.textContent.trim().match(/^(\d+)\/(\d+)\s+sites$/i);
      if (!match) continue;
      const listed = Number(match[1]);
      const total = Number(match[2]);
      const copy = `Listed at ${listed} of ${total} connected ${total === 1 ? 'site' : 'sites'}`;
      if (value.textContent !== copy) value.textContent = copy;
    }
  }

  function patchTradeCoverage() {
    const detail = document.querySelector(
      '#company-context-card .company-context-signal-trade .company-context-signal-detail',
    );
    if (!detail) return;
    const copy = detail.textContent.replace(
      /(\d+)\/(\d+) connected sites/i,
      'trade context at $1 of $2 connected sites',
    );
    if (detail.textContent !== copy) detail.textContent = copy;
  }

  function patchOpenBrief() {
    const review = reviewApi();
    const ownerId = selectedOwnerId(review);
    const card = document.querySelector('#company-context-card');
    if (!review || !ownerId || !card || card.hidden) return;
    patchSitesAndCountries(review, ownerId);
    patchProductCoverage();
    patchTradeCoverage();
  }

  function sync() {
    ensureFirstClickOffer();
    patchOpenBrief();
  }

  function queueSync() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      sync();
      // Core and rail polish both rebuild company rows synchronously/next-frame.
      // One extra frame ensures the first-click affordance survives that rebuild.
      requestAnimationFrame(sync);
    });
  }

  function install() {
    const companyNodes = document.querySelector('#company-nodes');
    const selectionPath = document.querySelector('#selection-path');
    if (!companyNodes || !selectionPath || !reviewApi()?.snapshot) {
      requestAnimationFrame(install);
      return;
    }

    document.addEventListener('click', (event) => {
      if (
        event.target.closest?.('#company-nodes .company-node[data-owner]') ||
        event.target.closest?.('.company-context-close')
      ) queueSync();
    }, true);

    new MutationObserver(queueSync).observe(companyNodes, {childList: true});
    new MutationObserver(queueSync).observe(selectionPath, {childList: true, subtree: true});
    queueSync();
  }

  install();
})();
