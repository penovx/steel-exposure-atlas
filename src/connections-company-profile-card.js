(() => {
  let queued = false;

  function reviewApi() {
    try { return globalThis.__atlasReview ?? null; } catch { return null; }
  }

  function closeCompanySelection() {
    const review = reviewApi();
    const ownerId = review?.snapshot?.()?.state?.filters?.owner;
    if (ownerId) review.choose?.('owner', ownerId);
  }

  function reconcile() {
    queued = false;
    const review = reviewApi();
    const card = document.querySelector('#company-profile-card');
    const root = document.querySelector('#selection-profile');
    const area = document.querySelector('.reading-area');
    if (!review?.snapshot || !card || !root || !area) return;

    const state = review.snapshot()?.state;
    const ownerId = state?.filters?.owner ?? null;
    const companyProfileReady = ownerId && root.dataset.profileKind === 'company';

    if (!companyProfileReady) {
      card.hidden = true;
      card.replaceChildren();
      return;
    }

    if (root.childNodes.length) {
      const close = document.createElement('button');
      close.type = 'button';
      close.className = 'company-profile-card-close';
      close.setAttribute('aria-label', 'Close company profile');
      close.textContent = '×';
      close.addEventListener('click', closeCompanySelection);

      const inner = document.createElement('div');
      inner.className = 'company-profile-card-inner';
      while (root.firstChild) inner.append(root.firstChild);
      card.replaceChildren(close, inner);
    }

    if (card.childNodes.length) {
      card.hidden = false;
      area.hidden = true;
    }
  }

  function queue() {
    if (queued) return;
    queued = true;
    queueMicrotask(reconcile);
  }

  function install() {
    const root = document.querySelector('#selection-profile');
    const path = document.querySelector('#selection-path');
    const card = document.querySelector('#company-profile-card');
    if (!root || !path || !card || !reviewApi()?.snapshot) {
      requestAnimationFrame(install);
      return;
    }
    if (card.dataset.companyProfileInstalled === 'true') return;
    card.dataset.companyProfileInstalled = 'true';

    new MutationObserver(queue).observe(root, {childList: true});
    new MutationObserver(queue).observe(path, {childList: true, subtree: true});
    queue();
  }

  install();
})();
