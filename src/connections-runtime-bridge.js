// Runtime bridge for the relational homepage.
// It keeps the stable interaction core unchanged while supplying UI semantics that
// are easier to read in the connected view.

function reviewState() {
  try {
    return globalThis.__atlasReview?.snapshot?.().state ?? null;
  } catch {
    return null;
  }
}

function hasRelationalFocus(state) {
  if (!state) return false;
  const products = state.filters?.products ?? [];
  return Boolean(
    state.site ||
    state.filters?.country ||
    state.filters?.owner ||
    state.filters?.route ||
    products.length
  );
}

// The old prototype explorer remains reachable by its direct route for internal
// reference, but it is not part of the public-facing homepage navigation.
document.querySelector('a[href="./prototype/evidence.html"]')?.remove();

// connections-core.js reads this global binding when deciding which product edges
// to draw. No selection keeps the global overview sparse. Once any dimension is
// selected, every product listed by the connected plants can receive an edge. This
// includes product-led selections: selecting "bar", for example, can reveal which
// other product descriptions occur at those same connected plants instead of
// forcing every product edge into the selected "bar" port.
var selectedProducts = {
  get size() {
    return hasRelationalFocus(reviewState()) ? 1 : 0;
  },
  has() {
    return hasRelationalFocus(reviewState());
  },
};

function decorateProductLabels() {
  const state = reviewState();
  if (!state) return;
  const focused = hasRelationalFocus(state);

  for (const node of document.querySelectorAll('#product-nodes .product-node')) {
    const count = node.querySelector(':scope > span');
    if (!count) continue;

    if (!count.dataset.countValue) {
      count.dataset.countValue = count.textContent.trim();
    }
    const value = count.dataset.countValue;
    count.textContent = focused ? `${value} connected` : `${value} sites`;
  }
}

function installProductLabelObserver() {
  const productNodes = document.querySelector('#product-nodes');
  if (!productNodes || productNodes.dataset.labelObserver === 'true') return;
  productNodes.dataset.labelObserver = 'true';
  const observer = new MutationObserver(decorateProductLabels);
  observer.observe(productNodes, {childList: true});
  decorateProductLabels();
}

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

  installProductLabelObserver();
  decorateProductLabels();
}

applyWorldEntry();
