(() => {
  function currentReview() {
    try {
      return globalThis.__atlasReview ?? null;
    } catch {
      return null;
    }
  }

  function companyIsEligible(ownerId) {
    const eligibility = globalThis.__ATLAS_COMPANY_ELIGIBILITY__;
    return !eligibility?.ready || eligibility.isVisible(ownerId);
  }

  function syncCompanyEdges(visibleOwnerIds) {
    const review = currentReview();
    if (!review?.all) return;
    const ownerBySite = new Map(review.all.map((plant) => [plant.id, plant.ownerId]));
    for (const edge of document.querySelectorAll('#edge-layer .connection-edge.company')) {
      const ownerId = ownerBySite.get(edge.dataset.site);
      edge.hidden = !companyIsEligible(ownerId) || !visibleOwnerIds.has(ownerId);
    }
  }

  function filterCompanies() {
    const container = document.querySelector('#company-nodes');
    const empty = document.querySelector('#company-search-empty');
    if (!container) return [];

    const visible = [];
    const visibleOwnerIds = new Set();
    for (const node of container.querySelectorAll('.company-node[data-owner]')) {
      const eligible = companyIsEligible(node.dataset.owner);
      node.hidden = !eligible;
      if (eligible) {
        visible.push(node);
        visibleOwnerIds.add(node.dataset.owner);
      }
    }
    if (empty) empty.hidden = true;
    syncCompanyEdges(visibleOwnerIds);
    return visible;
  }

  function openCompanyPicker() {
    const trigger = document.querySelector('[data-open-facet="owner"]');
    if (!trigger) return;
    trigger.click();
    requestAnimationFrame(() => document.querySelector('#browse-query')?.focus());
  }

  function ownerDisplayName(review, ownerId) {
    return review?.all?.find?.((plant) => plant.ownerId === ownerId)?.owner ?? ownerId;
  }

  function syncReadingCopy() {
    const review = currentReview();
    const description = document.querySelector('#reading-description');
    const caption = document.querySelector('#connection-caption');
    if (!review?.snapshot || !description || !caption) return;

    const snapshot = review.snapshot();
    const state = snapshot?.state;
    if (!state) return;
    const filters = state.filters ?? {};
    const products = Array.isArray(filters.products) ? filters.products : [];
    const selectedCount = Array.isArray(snapshot.selectedIds) ? snapshot.selectedIds.length : 0;
    const focused = Boolean(state.site || filters.owner || filters.route || filters.country || products.length);

    if (state.site) {
      const plant = review.all?.find?.((item) => item.id === state.site);
      const owner = plant?.owner ? `GEM names ${plant.owner} as its immediate owner or operator. ` : '';
      description.textContent = `${owner}The plant record also carries its listed products and production-method data for comparison with other sites in the same geographic scope.`;
    } else if (filters.owner) {
      const owner = ownerDisplayName(review, filters.owner);
      description.textContent = `GEM names ${owner} as the immediate owner or operator of the sites in this view. The atlas compares their geography, listed products, production methods and reviewed regulatory context.`;
    } else if (products.length) {
      const productPhrase = products.length > 1
        ? (filters.productMode === 'all' ? 'all selected products' : 'at least one selected product')
        : 'the selected product';
      description.textContent = `These site records list ${productPhrase}. Compare their locations, the companies GEM names as owner or operator, and their recorded production methods. Product labels do not indicate available supply or product-specific capacity.`;
    } else if (filters.route) {
      description.textContent = 'These sites record the selected production method in the June 2026 operating-capacity snapshot. A site can use more than one production method.';
    } else if (filters.country) {
      description.textContent = 'These are the site records in this place. Compare the companies GEM names as owner or operator, their listed products and recorded production methods.';
    } else {
      description.textContent = 'The same site records are compared across geography, company attribution, listed products and production methods.';
    }

    caption.textContent = focused
      ? `${selectedCount} sites in the current selection within ${state.region}. Product and production-method lines refer to those same site records, not material flows.`
      : 'The same site records are viewed through geography, company attribution, listed products and production methods.';
  }

  function install() {
    const input = document.querySelector('#company-search-input');
    const container = document.querySelector('#company-nodes');
    const selectionPath = document.querySelector('#selection-path');
    if (!input || !container || !selectionPath) {
      requestAnimationFrame(install);
      return;
    }
    if (input.dataset.searchInstalled === 'true') return;
    input.dataset.searchInstalled = 'true';

    // The rail is intentionally bounded for immediate map rendering. Search opens
    // the complete company picker instead of silently expanding hundreds of rows.
    input.readOnly = true;
    input.placeholder = 'Search all companies';
    input.setAttribute('aria-haspopup', 'dialog');
    input.addEventListener('click', openCompanyPicker);
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openCompanyPicker();
      }
    });

    new MutationObserver(filterCompanies).observe(container, {childList: true});
    new MutationObserver(() => {
      syncReadingCopy();
      filterCompanies();
    }).observe(selectionPath, {childList: true, subtree: true});
    window.addEventListener('atlas-company-eligibility-ready', filterCompanies);

    filterCompanies();
    syncReadingCopy();
  }

  install();
})();