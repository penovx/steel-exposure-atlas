(() => {
  function companyName(node) {
    return node.querySelector('.company-name')?.textContent?.trim() ?? '';
  }

  function syncCompanyEdges(visibleOwnerIds, hasQuery) {
    const review = globalThis.__atlasReview;
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

  function install() {
    const input = document.querySelector('#company-search-input');
    const container = document.querySelector('#company-nodes');
    if (!input || !container) {
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
    filterCompanies();
  }

  install();
})();
