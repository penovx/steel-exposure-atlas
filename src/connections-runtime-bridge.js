// Runtime bridge for relationship-line semantics and neutral world entry.
// This file is intentionally tiny: the main atlas model stays in connections-core.js.
// It supplies the product-link selector consumed by the stable core without changing
// plant evidence, filtering, or capacity calculations.

function reviewState() {
  try {
    return globalThis.__atlasReview?.snapshot?.().state ?? null;
  } catch {
    return null;
  }
}

// connections-core.js reads this binding when deciding which product edges to draw.
// - No analytical selection: keep overview density low (one product edge per plant).
// - Product selection: draw only selected products.
// - Place/company/method/site selection without a product filter: draw all related
//   products so every entry dimension responds symmetrically.
globalThis.selectedProducts = {
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
