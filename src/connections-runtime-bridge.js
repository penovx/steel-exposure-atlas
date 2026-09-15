// Runtime bridge for the relational homepage.
// It keeps the stable interaction core unchanged while supplying two UI semantics:
// a neutral World entry scope and symmetric product edges for non-product selections.

function reviewState() {
  try {
    return globalThis.__atlasReview?.snapshot?.().state ?? null;
  } catch {
    return null;
  }
}

// connections-core.js reads this global binding when deciding which product edges
// to draw. No selection keeps the overview sparse. A product selection draws only
// those selected products. Place/company/method/site selections draw every product
// listed by their connected plants so all entry dimensions respond symmetrically.
var selectedProducts = {
  get size() {
    const state = reviewState();
    if (!state) return 0;
    const products = state.filters?.products ?? [];
    if (products.length) return products.length;
    return state.site || state.filters?.country || state.filters?.owner || state.filters?.route ? 1 : 0;
  },
  has(productId) {
    const state = reviewState();
    if (!state) return false;
    const products = state.filters?.products ?? [];
    if (products.length) return products.includes(productId);
    return Boolean(state.site || state.filters?.country || state.filters?.owner || state.filters?.route);
  },
};

function applyWorldEntry() {
  const review = globalThis.__atlasReview;
  if (!review?.setRegion || !review?.snapshot) {
    requestAnimationFrame(applyWorldEntry);
    return;
  }

  if (review.snapshot().state.region !== 'World') review.setRegion('World');

  const brand = document.querySelector('#brand-home');
  if (brand) {
    brand.onclick = (event) => {
      event.preventDefault();
      review.setRegion('World');
      window.scrollTo({top: 0, behavior: 'smooth'});
    };
  }
}

applyWorldEntry();
