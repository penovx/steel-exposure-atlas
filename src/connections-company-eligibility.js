(() => {
  const ROUTES = ['BOF', 'EAF', 'IF', 'Other'];
  const productionEligibleOwners = new Set();
  const directListedOwners = new Set();

  function reviewApi() {
    try {
      return globalThis.__atlasReview ?? null;
    } catch {
      return null;
    }
  }

  function selectedOwnerId(review = reviewApi()) {
    const state = review?.snapshot?.()?.state;
    if (!state) return null;
    if (state.filters?.owner) return state.filters.owner;
    if (!state.site) return null;
    return review.all?.find?.((plant) => plant.id === state.site)?.ownerId ?? null;
  }

  function hasPositiveOperatingSteel(review, plant) {
    if (ROUTES.some((route) => review.model?.hasRoute?.(plant, route))) return true;
    try {
      const total = review.model?.total?.([plant]);
      const known = Number(total?.known);
      return (Number.isFinite(known) && known > 0) || Boolean(total?.positive);
    } catch {
      return false;
    }
  }

  function buildProductionEligibility(review) {
    productionEligibleOwners.clear();
    for (const plant of review?.all ?? []) {
      const ownerId = String(plant.ownerId ?? '').trim();
      if (!ownerId || !hasPositiveOperatingSteel(review, plant)) continue;
      productionEligibleOwners.add(ownerId);
    }
  }

  function addDirectListings(payload) {
    for (const status of payload?.statuses ?? []) {
      if (status?.state !== 'direct_list_match') continue;
      const ownerId = String(status.company_id ?? '').trim();
      if (ownerId) directListedOwners.add(ownerId);
    }
  }

  function buildSanctionsOverride(payloads) {
    directListedOwners.clear();
    addDirectListings(payloads?.eu);
    addDirectListings(payloads?.ofac);
  }

  function isVisible(ownerId) {
    const id = String(ownerId ?? '').trim();
    if (!id) return false;
    if (!eligibility.ready) return true;
    return productionEligibleOwners.has(id)
      || directListedOwners.has(id)
      || selectedOwnerId() === id;
  }

  function applyOwnerPickerEligibility() {
    if (!eligibility.ready) return;
    const result = document.querySelector('#browse-result');
    if (!result) return;
    const items = [...result.querySelectorAll('.browse-item[data-browse-kind="owner"]')];
    if (!items.length) {
      result.querySelector('.company-eligibility-empty')?.remove();
      return;
    }

    let visibleCount = 0;
    for (const item of items) {
      const visible = isVisible(item.dataset.browseId);
      item.hidden = !visible;
      if (visible) visibleCount += 1;
    }

    const count = document.querySelector('#browse-count');
    if (count) count.textContent = `${visibleCount} results`;

    let empty = result.querySelector('.company-eligibility-empty');
    if (visibleCount === 0) {
      if (!empty) {
        empty = document.createElement('p');
        empty.className = 'empty company-eligibility-empty';
        empty.textContent = 'No matching production-relevant companies.';
        result.append(empty);
      }
    } else {
      empty?.remove();
    }
  }

  const eligibility = {
    ready: false,
    isVisible,
    isProductionEligible: (ownerId) => productionEligibleOwners.has(String(ownerId ?? '').trim()),
    isDirectListed: (ownerId) => directListedOwners.has(String(ownerId ?? '').trim()),
    counts: () => ({
      productionEligibleOwners: productionEligibleOwners.size,
      directListedOwners: directListedOwners.size,
    }),
  };
  globalThis.__ATLAS_COMPANY_ELIGIBILITY__ = eligibility;

  async function init() {
    const payloadPromise = globalThis.__ATLAS_SANCTIONS_PROMISE__ ?? Promise.resolve({eu: null, ofac: null});

    const waitForReview = () => new Promise((resolve) => {
      const tick = () => {
        const review = reviewApi();
        if (review?.all && review?.model?.total && review?.model?.hasRoute) {
          resolve(review);
          return;
        }
        requestAnimationFrame(tick);
      };
      tick();
    });

    const [review, payloads] = await Promise.all([waitForReview(), payloadPromise]);
    buildProductionEligibility(review);
    buildSanctionsOverride(payloads ?? {});
    eligibility.ready = true;

    window.dispatchEvent(new CustomEvent('atlas-company-eligibility-ready'));
    applyOwnerPickerEligibility();

    const browseResult = document.querySelector('#browse-result');
    if (browseResult) {
      new MutationObserver(applyOwnerPickerEligibility).observe(browseResult, {
        childList: true,
        subtree: true,
      });
    }

    const selectionPath = document.querySelector('#selection-path');
    if (selectionPath) {
      new MutationObserver(applyOwnerPickerEligibility).observe(selectionPath, {
        childList: true,
        subtree: true,
      });
    }
  }

  init();
})();
