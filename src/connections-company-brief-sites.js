(() => {
  const INITIAL_SITE_LIMIT = 4;

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

  function plantsAttributedToOwnerInView(review, ownerId) {
    const selected = new Set(review?.snapshot?.()?.selectedIds ?? []);
    return (review?.all ?? [])
      .filter((plant) => plant.ownerId === ownerId && selected.has(plant.id))
      .sort((a, b) =>
        String(a.country ?? '').localeCompare(String(b.country ?? ''), 'en') ||
        placeName(a).localeCompare(placeName(b), 'en')
      );
  }

  function placeName(plant) {
    if (plant.city && plant.city !== 'unknown') return plant.city;
    return String(plant.name ?? '').replace(/\s+steel plant$/i, '') || plant.id;
  }

  function productLabel(value) {
    const label = String(value ?? '').trim();
    return label ? label.charAt(0).toUpperCase() + label.slice(1) : '';
  }

  function sectionByLabel(card, label) {
    return [...card.querySelectorAll('.company-brief-section')]
      .find((section) => section.querySelector('.company-brief-section-label')?.textContent?.trim() === label) ?? null;
  }

  function keepCapacityMetricOnly(card) {
    const metrics = card.querySelector('.company-context-metrics');
    if (!metrics || metrics.dataset.siteProductView === 'true') return;

    const capacity = [...metrics.querySelectorAll('.company-context-metric')]
      .find((item) => item.querySelector('span')?.textContent?.includes('Known operating crude-steel capacity'));

    metrics.replaceChildren();
    if (capacity) metrics.append(capacity);
    metrics.dataset.siteProductView = 'true';
    metrics.classList.add('company-context-metrics-capacity-only');
    if (!capacity) metrics.hidden = true;
  }

  function siteRow(plant, hidden) {
    const row = document.createElement('article');
    row.className = 'company-brief-site-product-row';
    row.hidden = hidden;

    const head = document.createElement('div');
    head.className = 'company-brief-site-product-head';

    const name = document.createElement('strong');
    name.className = 'company-brief-site-product-name';
    name.textContent = placeName(plant);

    const country = document.createElement('span');
    country.className = 'company-brief-site-product-country';
    country.textContent = plant.country ?? '';
    head.append(name, country);
    row.append(head);

    const products = [...new Set((plant.products?.values ?? []).map(productLabel).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, 'en'));
    if (products.length) {
      const productBlock = document.createElement('div');
      productBlock.className = 'company-brief-site-products';

      const label = document.createElement('span');
      label.className = 'company-brief-site-products-label';
      label.textContent = 'GIST-listed products';

      const values = document.createElement('div');
      values.className = 'company-brief-site-product-values';
      for (const product of products) {
        const chip = document.createElement('span');
        chip.className = 'company-brief-site-product';
        chip.textContent = product;
        values.append(chip);
      }
      productBlock.append(label, values);
      row.append(productBlock);
    }

    return row;
  }

  function renderSitesAndProducts(card, review, ownerId) {
    const sitesSection = sectionByLabel(card, 'SITES & COUNTRIES') ?? sectionByLabel(card, 'SITES & PRODUCTS');
    if (!sitesSection || sitesSection.dataset.siteProductView === 'true') return;

    const productSection = sectionByLabel(card, 'PRODUCT-TO-SITE RELATION');
    productSection?.remove();

    const overview = sitesSection.closest('.company-brief-overview');
    overview?.classList.add('company-brief-overview-site-products');

    const sectionLabel = sitesSection.querySelector('.company-brief-section-label');
    if (sectionLabel) sectionLabel.textContent = 'SITES & PRODUCTS';

    for (const node of sitesSection.querySelectorAll(
      '.company-brief-interpretation,.company-brief-footprint-line,.company-brief-site-list,.company-brief-section-title'
    )) node.remove();

    const plants = plantsAttributedToOwnerInView(review, ownerId);
    const list = document.createElement('div');
    list.className = 'company-brief-site-product-list';
    plants.forEach((plant, index) => list.append(siteRow(plant, index >= INITIAL_SITE_LIMIT)));
    sitesSection.append(list);

    if (plants.length > INITIAL_SITE_LIMIT) {
      const remaining = plants.length - INITIAL_SITE_LIMIT;
      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'company-brief-site-toggle';
      toggle.setAttribute('aria-expanded', 'false');
      toggle.textContent = `Show ${remaining} more sites ↓`;
      toggle.addEventListener('click', () => {
        const expanded = toggle.getAttribute('aria-expanded') === 'true';
        for (const row of list.querySelectorAll('.company-brief-site-product-row')) {
          if (row.dataset.initial === 'true') continue;
        }
        [...list.children].forEach((row, index) => {
          if (index >= INITIAL_SITE_LIMIT) row.hidden = expanded;
        });
        toggle.setAttribute('aria-expanded', String(!expanded));
        toggle.textContent = expanded ? `Show ${remaining} more sites ↓` : 'Show fewer sites ↑';
      });
      sitesSection.append(toggle);
    }

    sitesSection.dataset.siteProductView = 'true';
  }

  function patchOpenCard() {
    const review = reviewApi();
    const ownerId = selectedOwnerId(review);
    const card = document.querySelector('#company-context-card');
    if (!review || !ownerId || !card || card.hidden || card.dataset.owner !== ownerId) return;

    keepCapacityMetricOnly(card);
    renderSitesAndProducts(card, review, ownerId);
  }

  function queuePatch() {
    requestAnimationFrame(patchOpenCard);
  }

  function install() {
    const stage = document.querySelector('#connections-stage');
    if (!stage || !reviewApi()?.snapshot) {
      requestAnimationFrame(install);
      return;
    }

    const observer = new MutationObserver(queuePatch);
    observer.observe(stage, {childList: true, subtree: true, attributes: true, attributeFilter: ['hidden', 'data-owner']});
    document.addEventListener('click', (event) => {
      if (event.target.closest?.('#company-nodes .company-node[data-owner],#company-context-card')) queuePatch();
    }, true);
    queuePatch();
  }

  install();
})();
