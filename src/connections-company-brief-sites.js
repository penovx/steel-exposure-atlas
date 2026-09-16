(() => {
  const INITIAL_SITE_LIMIT = 4;
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

  function selectedOwnerId(review) {
    const state = review?.snapshot?.()?.state;
    if (!state) return null;
    if (state.filters?.owner) return state.filters.owner;
    if (!state.site) return null;
    return review.all?.find?.((plant) => plant.id === state.site)?.ownerId ?? null;
  }

  // A company brief describes the selected company inside the chosen geography.
  // Product/method cross-filters must not turn the company brief into an empty intersection.
  function plantsAttributedToOwnerInGeography(review, ownerId) {
    const region = review?.snapshot?.()?.state?.region ?? 'World';
    return (review?.all ?? [])
      .filter((plant) =>
        plant.ownerId === ownerId && (region === 'World' || plant.region === region)
      )
      .sort((a, b) =>
        String(a.country ?? '').localeCompare(String(b.country ?? ''), 'en') ||
        placeName(a).localeCompare(placeName(b), 'en')
      );
  }

  function placeName(plant) {
    if (plant.city && plant.city !== 'unknown') return plant.city;
    return String(plant.name ?? '').replace(/\s+steel plant$/i, '') || plant.id;
  }

  function placeLabel(plant) {
    return `${placeName(plant)} · ${plant.country ?? ''}`;
  }

  function productLabel(value) {
    const label = String(value ?? '').trim();
    return label ? label.charAt(0).toUpperCase() + label.slice(1) : '';
  }

  function formatCapacity(result) {
    if (!result) return 'Not quantified';
    if (result.known !== null && result.known !== undefined) {
      const value = result.known / 1000;
      return `${value.toLocaleString('en-GB', {
        maximumFractionDigits: value < 10 ? 2 : 1,
      })}${result.positive ? '+' : ''} Mtpa`;
    }
    if (result.positive) return '>0 Mtpa · not numerically quantified';
    return 'Not quantified';
  }

  function capacityFor(review, plants, field = 'crude_steel_capacity_ttpa') {
    try {
      return review.model?.total?.(plants, field) ?? null;
    } catch {
      return null;
    }
  }

  function sectionByLabel(card, label) {
    return [...card.querySelectorAll('.company-brief-section')]
      .find((section) => section.querySelector('.company-brief-section-label')?.textContent?.trim() === label) ?? null;
  }

  function keepCapacityMetricOnly(card, review, plants) {
    const metrics = card.querySelector('.company-context-metrics');
    if (!metrics) return;

    let capacity = [...metrics.querySelectorAll('.company-context-metric')]
      .find((item) => item.querySelector('span')?.textContent?.includes('Known operating crude-steel capacity'));

    if (!capacity) {
      capacity = document.createElement('div');
      capacity.className = 'company-context-metric';
      const value = document.createElement('strong');
      const label = document.createElement('span');
      label.textContent = 'Known operating crude-steel capacity';
      capacity.append(value, label);
    }

    const value = capacity.querySelector('strong');
    if (value) value.textContent = formatCapacity(capacityFor(review, plants));

    metrics.replaceChildren(capacity);
    metrics.dataset.siteProductView = 'true';
    metrics.classList.add('company-context-metrics-capacity-only');
    metrics.hidden = false;
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

  function renderSitesAndProducts(card, plants) {
    const sitesSection = sectionByLabel(card, 'SITES & COUNTRIES') ?? sectionByLabel(card, 'SITES & PRODUCTS');
    if (!sitesSection) return;

    const productSection = sectionByLabel(card, 'PRODUCT-TO-SITE RELATION');
    productSection?.remove();

    const overview = sitesSection.closest('.company-brief-overview');
    overview?.classList.add('company-brief-overview-site-products');

    const sectionLabel = sitesSection.querySelector('.company-brief-section-label');
    if (sectionLabel) sectionLabel.textContent = 'SITES & PRODUCTS';

    for (const node of sitesSection.querySelectorAll(
      '.company-brief-interpretation,.company-brief-footprint-line,.company-brief-site-list,.company-brief-section-title,.company-brief-site-product-list,.company-brief-site-toggle'
    )) node.remove();

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
        [...list.children].forEach((site, index) => {
          if (index >= INITIAL_SITE_LIMIT) site.hidden = expanded;
        });
        toggle.setAttribute('aria-expanded', String(!expanded));
        toggle.textContent = expanded ? `Show ${remaining} more sites ↓` : 'Show fewer sites ↑';
      });
      sitesSection.append(toggle);
    }

    sitesSection.dataset.siteProductView = 'true';
  }

  function routeRows(review, plants) {
    return ROUTES.map((route) => {
      const routePlants = plants.filter((plant) => review.model?.hasRoute?.(plant, route.id));
      if (!routePlants.length) return null;
      return {
        ...route,
        plants: routePlants,
        capacity: capacityFor(review, plants, route.field),
      };
    }).filter(Boolean);
  }

  function summarizedPlaces(plants, limit = 4) {
    const labels = plants.map(placeLabel);
    if (labels.length <= limit) return labels.join('; ');
    return `${labels.slice(0, limit).join('; ')}; +${labels.length - limit} more sites`;
  }

  function patchProductionProfile(card, review, plants) {
    const section = sectionByLabel(card, 'PRODUCTION PROFILE');
    if (!section) return;

    const routes = routeRows(review, plants);
    let title = section.querySelector('.company-brief-section-title');
    if (!title) {
      title = document.createElement('h4');
      title.className = 'company-brief-section-title';
      section.querySelector('.company-brief-section-label')?.after(title);
    }
    title.textContent = `${routes.length} production ${routes.length === 1 ? 'method' : 'methods'} represented across these sites`;

    let list = section.querySelector('.company-brief-ranked-list');
    if (!list) {
      list = document.createElement('div');
      list.className = 'company-brief-ranked-list';
      section.append(list);
    }
    list.replaceChildren();

    for (const route of routes) {
      const row = document.createElement('div');
      row.className = 'company-brief-ranked-row';

      const name = document.createElement('span');
      name.className = 'company-brief-ranked-name';
      name.textContent = route.name;

      const value = document.createElement('span');
      value.className = 'company-brief-ranked-value';
      const capacity = formatCapacity(route.capacity);
      value.textContent = `${capacity} known operating capacity · ${summarizedPlaces(route.plants)}`;
      row.append(name, value);
      list.append(row);
    }
  }

  // Derivation details stay in View evidence. The company brief first explains the
  // legal quota mechanism, then the consequence of quota exhaustion.
  function patchTradeSignal(card) {
    const signal = card.querySelector('.company-context-signal-trade');
    if (!signal) return;

    const title = signal.querySelector('.company-context-signal-title');
    const detail = signal.querySelector('.company-context-signal-detail');
    const consequence = signal.querySelector('.company-context-signal-consequence');

    if (title) title.textContent = 'EU tariff-quota framework in force';
    if (detail) {
      detail.textContent = 'European Parliament and Council: Regulation (EU) 2026/1384 · annual quota period 1 Jul–30 Jun. European Commission: current allocation under Implementing Regulation (EU) 2026/1457 applies 1 Jul–31 Dec 2026. Purpose: address trade-related effects of global steel overcapacity.';
    }
    if (consequence) {
      consequence.textContent = '50% out-of-quota duty after quota exhaustion. If covered steel is imported into the EU, the 50% duty applies once the applicable quota is exhausted.';
    }
  }

  function patchRole(card) {
    const role = card.querySelector('.company-context-role');
    if (role) {
      role.textContent = 'GEM names this company as the immediate owner or operator of the sites in the current geographic scope.';
    }
  }

  function patchOpenCard() {
    const review = reviewApi();
    const ownerId = selectedOwnerId(review);
    const card = document.querySelector('#company-context-card');
    if (!review || !ownerId || !card || card.hidden || card.dataset.owner !== ownerId) return;

    const plants = plantsAttributedToOwnerInGeography(review, ownerId);
    patchRole(card);
    keepCapacityMetricOnly(card, review, plants);
    renderSitesAndProducts(card, plants);
    patchProductionProfile(card, review, plants);
    patchTradeSignal(card);
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