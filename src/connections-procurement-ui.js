(() => {
  function currentReview() {
    try {
      return globalThis.__atlasReview ?? null;
    } catch {
      return null;
    }
  }

  function companyName(node) {
    return node.querySelector('.company-name')?.textContent?.trim() ?? '';
  }

  function syncCompanyEdges(visibleOwnerIds, hasQuery) {
    const review = currentReview();
    if (!review?.all) return;
    const ownerBySite = new Map(review.all.map((plant) => [plant.id, plant.ownerId]));
    for (const edge of document.querySelectorAll('#edge-layer .connection-edge.company')) {
      if (!hasQuery) {
        edge.hidden = false;
        continue;
      }
      const ownerId = ownerBySite.get(edge.dataset.site);
      edge.hidden = !visibleOwnerIds.has(ownerId);
    }
  }

  function filterCompanies() {
    const input = document.querySelector('#company-search-input');
    const container = document.querySelector('#company-nodes');
    const empty = document.querySelector('#company-search-empty');
    if (!input || !container || !empty) return [];

    const query = input.value.trim().toLocaleLowerCase('en');
    const visible = [];
    const visibleOwnerIds = new Set();
    for (const node of container.querySelectorAll('.company-node[data-owner]')) {
      const matches = !query || companyName(node).toLocaleLowerCase('en').includes(query);
      node.hidden = !matches;
      if (matches) {
        visible.push(node);
        visibleOwnerIds.add(node.dataset.owner);
      }
    }
    empty.hidden = !query || visible.length > 0;
    syncCompanyEdges(visibleOwnerIds, Boolean(query));
    return visible;
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
      description.textContent = 'This plant connects to its company, listed products and production methods. Follow those links to compare it with other sites in the same geographic scope.';
    } else if (filters.owner) {
      description.textContent = 'These sites are linked to the same company. Use this view to see where it operates, which products its sites list, which production methods they use, and whether sanctions evidence is attached to the company.';
    } else if (products.length) {
      const productPhrase = products.length > 1
        ? (filters.productMode === 'all' ? 'all selected products' : 'at least one selected product')
        : 'the selected product';
      description.textContent = `These sites list ${productPhrase}. Compare where those sites are, which companies they connect to and which production methods they use. Product labels do not indicate available supply or product-specific capacity.`;
    } else if (filters.route) {
      description.textContent = 'These sites use the selected production method in the June 2026 operating-capacity snapshot. A site can use more than one production method, so other methods may coexist at the same location.';
    } else if (filters.country) {
      description.textContent = 'See which companies operate sites here, which products those sites list and which production methods are present.';
    } else {
      description.textContent = 'Companies, products and production methods are linked to the same sites. Select any dimension to see how the industrial footprint changes.';
    }

    caption.textContent = focused
      ? `${selectedCount} connected sites in ${state.region}. Product and production-method links describe the same sites, not material flows.`
      : 'The same sites connect geography, companies, products and production methods.';
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

    input.addEventListener('input', () => {
      container.scrollTop = 0;
      filterCompanies();
    });
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && input.value) {
        input.value = '';
        container.scrollTop = 0;
        filterCompanies();
        event.preventDefault();
        return;
      }
      if (event.key === 'Enter') {
        const visible = filterCompanies();
        if (visible.length === 1) {
          visible[0].click();
          event.preventDefault();
        }
      }
    });

    new MutationObserver(filterCompanies).observe(container, {childList: true});
    const edges = document.querySelector('#edge-layer');
    if (edges) new MutationObserver(filterCompanies).observe(edges, {childList: true});
    new MutationObserver(syncReadingCopy).observe(selectionPath, {childList: true, subtree: true});

    filterCompanies();
    syncReadingCopy();
  }

  install();
})();
