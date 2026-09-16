(() => {
  let queued = false;
  let openOwnerId = null;

  function reviewApi() {
    try { return globalThis.__atlasReview ?? null; } catch { return null; }
  }

  function currentOwnerId() {
    return reviewApi()?.snapshot?.()?.state?.filters?.owner ?? null;
  }

  function returnCardContentToRoot() {
    const card = document.querySelector('#company-profile-card');
    const root = document.querySelector('#selection-profile');
    const inner = card?.querySelector('.company-profile-card-inner');
    if (!card || !root || !inner) return;
    const fragment = document.createDocumentFragment();
    while (inner.firstChild) fragment.append(inner.firstChild);
    root.replaceChildren(fragment);
    card.replaceChildren();
    delete card.dataset.ownerId;
  }

  function closeProfileOnly() {
    openOwnerId = null;
    returnCardContentToRoot();
    const card = document.querySelector('#company-profile-card');
    if (card) card.hidden = true;
  }

  function reconcile() {
    queued = false;
    const review = reviewApi();
    const card = document.querySelector('#company-profile-card');
    const root = document.querySelector('#selection-profile');
    const area = document.querySelector('.reading-area');
    if (!review?.snapshot || !card || !root || !area) return;

    const ownerId = currentOwnerId();
    const companyProfileReady = ownerId && root.dataset.profileKind === 'company';

    if (!ownerId) {
      openOwnerId = null;
      card.hidden = true;
      card.replaceChildren();
      delete card.dataset.ownerId;
      return;
    }

    // Company selection itself only marks the company and exposes the explicit
    // "Open company profile" action in the rail. The lower profile stays hidden.
    area.hidden = true;

    if (openOwnerId !== ownerId) {
      if (card.dataset.ownerId && card.dataset.ownerId !== ownerId) {
        card.replaceChildren();
        delete card.dataset.ownerId;
      }
      card.hidden = true;
      return;
    }

    if (!companyProfileReady) return;
    if (card.dataset.ownerId === ownerId && card.childNodes.length) {
      card.hidden = false;
      return;
    }
    if (!root.childNodes.length) return;

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'company-profile-card-close';
    close.setAttribute('aria-label', 'Close company profile');
    close.textContent = '×';
    close.addEventListener('click', closeProfileOnly);

    const inner = document.createElement('div');
    inner.className = 'company-profile-card-inner';
    while (root.firstChild) inner.append(root.firstChild);
    card.replaceChildren(close, inner);
    card.dataset.ownerId = ownerId;
    card.hidden = false;
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

    window.addEventListener('atlas-open-company-profile', (event) => {
      const ownerId = String(event.detail?.ownerId ?? '');
      if (!ownerId || currentOwnerId() !== ownerId) return;
      openOwnerId = ownerId;
      queue();
    });

    new MutationObserver(queue).observe(root, {childList: true});
    new MutationObserver(queue).observe(path, {childList: true, subtree: true});
    queue();
  }

  install();
})();
