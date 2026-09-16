(() => {
  const ROW_STEP = 72;
  const PROFILE_ACTION_HEIGHT = 28;
  const BUFFER_ROWS = 6;
  const FALLBACK_VISIBLE_ROWS = 7;

  let review = null;
  let container = null;
  let input = null;
  let empty = null;
  let query = '';
  let logicalGroups = [];
  let filteredGroups = [];
  let modelKey = '';
  let lastRegion = null;
  let lastScrollTop = 0;
  let eligibilityEpoch = 0;
  let renderQueued = 0;
  let renderSignature = '';
  let suppressScroll = false;

  function reviewApi() {
    try { return globalThis.__atlasReview ?? null; } catch { return null; }
  }

  function eligibilityApi() {
    try { return globalThis.__ATLAS_COMPANY_ELIGIBILITY__ ?? null; } catch { return null; }
  }

  function isFocused(state) {
    const products = state?.filters?.products ?? [];
    return Boolean(
      state?.site || state?.filters?.country || state?.filters?.owner ||
      state?.filters?.route || products.length
    );
  }

  function selectedOwnerFromState(state) {
    if (state?.filters?.owner) return state.filters.owner;
    if (!state?.site) return '';
    return review?.all?.find?.((plant) => plant.id === state.site)?.ownerId ?? '';
  }

  function rebuildLogicalGroups(snapshot) {
    const state = snapshot?.state;
    if (!state) return;
    const region = state.region ?? 'World';
    const eligibility = eligibilityApi();
    const selectedOwner = selectedOwnerFromState(state);
    const nextKey = [region, eligibilityEpoch, Boolean(eligibility?.ready), selectedOwner].join('|');
    if (nextKey === modelKey) return;

    const scoped = region === 'World'
      ? review.all
      : review.all.filter((plant) => plant.region === region);
    let groups = review.model.owners(scoped);
    if (eligibility?.ready) groups = groups.filter((group) => eligibility.isVisible(group.id));

    logicalGroups = groups;
    modelKey = nextKey;
    if (lastRegion !== null && lastRegion !== region) {
      query = '';
      lastScrollTop = 0;
      if (input) input.value = '';
    }
    lastRegion = region;
    applyQuery();
  }

  function applyQuery() {
    const needle = query.trim().toLocaleLowerCase('en');
    filteredGroups = needle
      ? logicalGroups.filter((group) => group.name.toLocaleLowerCase('en').includes(needle))
      : logicalGroups;
    const total = document.querySelector('#company-total');
    if (total) total.textContent = logicalGroups.length.toLocaleString('en-GB');
    if (empty) empty.hidden = !needle || filteredGroups.length > 0;
  }

  function spacer(kind, height) {
    const node = document.createElement('div');
    node.className = 'company-virtual-spacer';
    node.dataset.virtualSpacer = kind;
    node.setAttribute('aria-hidden', 'true');
    node.style.height = `${Math.max(0, height)}px`;
    return node;
  }

  function selectedIndex(snapshot) {
    const ownerId = snapshot?.state?.filters?.owner;
    if (!ownerId) return -1;
    return filteredGroups.findIndex((group) => group.id === ownerId);
  }

  function rowOffset(index, selectedPosition) {
    return index * ROW_STEP + (selectedPosition >= 0 && index > selectedPosition ? PROFILE_ACTION_HEIGHT : 0);
  }

  function totalVirtualHeight(selectedPosition) {
    return filteredGroups.length * ROW_STEP + (selectedPosition >= 0 ? PROFILE_ACTION_HEIGHT : 0);
  }

  function firstVisibleIndex(scrollTop, selectedPosition) {
    if (!filteredGroups.length) return 0;
    if (selectedPosition < 0) return Math.min(filteredGroups.length - 1, Math.floor(scrollTop / ROW_STEP));
    const selectedStart = selectedPosition * ROW_STEP;
    const selectedEnd = selectedStart + ROW_STEP + PROFILE_ACTION_HEIGHT;
    if (scrollTop < selectedStart) return Math.floor(scrollTop / ROW_STEP);
    if (scrollTop < selectedEnd) return selectedPosition;
    return Math.min(
      filteredGroups.length - 1,
      selectedPosition + 1 + Math.floor((scrollTop - selectedEnd) / ROW_STEP),
    );
  }

  function companyRow(group, position, total, snapshot) {
    const state = snapshot.state;
    const selectedIds = new Set(snapshot.selectedIds ?? []);
    const related = group.members.reduce(
      (count, plant) => count + (selectedIds.has(plant.id) ? 1 : 0),
      0,
    );
    const selected = state.filters?.owner === group.id;
    const dim = isFocused(state) && related === 0;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = `company-node${selected ? ' is-selected' : ''}${dim ? ' dim' : ''}`;
    button.dataset.owner = group.id;
    button.dataset.virtualOwner = group.id;
    button.dataset.port = `owner:${group.id}`;
    button.setAttribute('aria-pressed', String(selected));
    button.setAttribute('aria-posinset', String(position + 1));
    button.setAttribute('aria-setsize', String(total));
    button.setAttribute('aria-label', `${group.name}, ${group.members.length} sites in ${state.region}`);

    const name = document.createElement('span');
    name.className = 'company-name';
    name.textContent = group.name;
    const count = document.createElement('span');
    count.className = 'company-count';
    count.textContent = String(group.members.length);
    const sub = document.createElement('span');
    sub.className = 'company-sub';
    sub.textContent = `${isFocused(state) ? `${related} connected · ` : ''}${group.members.length} sites in scope`;
    button.append(name, count, sub);
    return button;
  }

  function profileAction(ownerId) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'company-profile-open';
    button.dataset.companyProfileOwner = ownerId;
    button.textContent = 'Open company profile →';
    return button;
  }

  function renderVirtualRail(force = false) {
    renderQueued = 0;
    if (!review?.snapshot || !container) return;
    const snapshot = review.snapshot();
    rebuildLogicalGroups(snapshot);

    const selectedPosition = selectedIndex(snapshot);
    const viewportHeight = container.clientHeight || ROW_STEP * FALLBACK_VISIBLE_ROWS;
    const maxScroll = Math.max(0, totalVirtualHeight(selectedPosition) - viewportHeight);
    lastScrollTop = Math.max(0, Math.min(lastScrollTop, maxScroll));

    const firstVisible = firstVisibleIndex(lastScrollTop, selectedPosition);
    const start = Math.max(0, firstVisible - BUFFER_ROWS);
    const visibleRows = Math.max(FALLBACK_VISIBLE_ROWS, Math.ceil(viewportHeight / ROW_STEP));
    const end = Math.min(filteredGroups.length, start + visibleRows + BUFFER_ROWS * 2);
    const owned = Boolean(container.querySelector('[data-virtual-spacer="top"]'));
    const signature = [
      snapshot.renderCount,
      eligibilityEpoch,
      query,
      start,
      end,
      filteredGroups.length,
      snapshot.state?.filters?.owner ?? '',
      snapshot.state?.site ?? '',
    ].join('|');
    if (!force && owned && signature === renderSignature) return;

    const fragment = document.createDocumentFragment();
    fragment.append(spacer('top', rowOffset(start, selectedPosition)));
    for (let index = start; index < end; index += 1) {
      const group = filteredGroups[index];
      fragment.append(companyRow(group, index, filteredGroups.length, snapshot));
      if (index === selectedPosition) fragment.append(profileAction(group.id));
    }
    fragment.append(spacer('bottom', totalVirtualHeight(selectedPosition) - rowOffset(end, selectedPosition)));

    suppressScroll = true;
    container.replaceChildren(fragment);
    container.classList.add('is-virtualized');
    container.dataset.virtualRail = 'true';
    container.scrollTop = lastScrollTop;
    suppressScroll = false;
    renderSignature = signature;
  }

  function queueRender(force = false) {
    if (force) renderSignature = '';
    if (renderQueued) return;
    renderQueued = requestAnimationFrame(() => renderVirtualRail(force));
  }

  function bindContainer() {
    container.addEventListener('scroll', () => {
      if (suppressScroll) return;
      lastScrollTop = container.scrollTop;
      queueRender();
    }, {passive: true});

    container.addEventListener('click', (event) => {
      const profileButton = event.target.closest?.('.company-profile-open[data-company-profile-owner]');
      if (profileButton && container.contains(profileButton)) {
        window.dispatchEvent(new CustomEvent('atlas-open-company-profile', {
          detail: {ownerId: profileButton.dataset.companyProfileOwner},
        }));
        return;
      }

      const button = event.target.closest?.('.company-node[data-virtual-owner]');
      if (!button || !container.contains(button)) return;
      const pageX = window.scrollX;
      const pageY = window.scrollY;
      lastScrollTop = container.scrollTop;
      review.choose('owner', button.dataset.virtualOwner);
      queueRender(true);
      requestAnimationFrame(() => requestAnimationFrame(() => {
        window.scrollTo({left: pageX, top: pageY, behavior: 'auto'});
      }));
    });

    new MutationObserver(() => queueRender()).observe(container, {childList: true});
    new ResizeObserver(() => queueRender(true)).observe(container);
  }

  function bindSearch(field) {
    input = field;
    input.readOnly = false;
    input.placeholder = 'Search companies';
    input.removeAttribute('aria-haspopup');
    input.dataset.virtualSearch = 'true';
    input.value = query;

    input.addEventListener('input', () => {
      query = input.value;
      lastScrollTop = 0;
      applyQuery();
      queueRender(true);
    });
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && input.value) {
        input.value = '';
        query = '';
        lastScrollTop = 0;
        applyQuery();
        queueRender(true);
        event.preventDefault();
        return;
      }
      if (event.key === 'Enter' && filteredGroups.length === 1) {
        lastScrollTop = 0;
        review.choose('owner', filteredGroups[0].id);
        queueRender(true);
        event.preventDefault();
      }
    });
  }

  function takeOverSearch(attempt = 0) {
    const current = document.querySelector('#company-search-input');
    if (!current) {
      requestAnimationFrame(() => takeOverSearch(attempt + 1));
      return;
    }
    if (current.dataset.virtualSearch === 'true') {
      input = current;
      return;
    }
    if (current.dataset.searchInstalled !== 'true' && attempt < 120) {
      requestAnimationFrame(() => takeOverSearch(attempt + 1));
      return;
    }

    const replacement = current.cloneNode(true);
    replacement.removeAttribute('readonly');
    current.replaceWith(replacement);
    bindSearch(replacement);
    queueRender(true);
  }

  function install() {
    review = reviewApi();
    container = document.querySelector('#company-nodes');
    empty = document.querySelector('#company-search-empty');
    const path = document.querySelector('#selection-path');
    const region = document.querySelector('#region-title');
    if (!review?.snapshot || !review?.model?.owners || !container || !path || !region) {
      requestAnimationFrame(install);
      return;
    }
    if (container.dataset.virtualRailInstalled === 'true') return;
    container.dataset.virtualRailInstalled = 'true';
    container.dataset.viewportGuard = 'true';

    bindContainer();
    new MutationObserver(() => queueRender(true)).observe(path, {childList: true, subtree: true});
    new MutationObserver(() => queueRender(true)).observe(region, {childList: true, subtree: true, characterData: true});
    window.addEventListener('atlas-company-eligibility-ready', () => {
      eligibilityEpoch += 1;
      modelKey = '';
      queueRender(true);
    });
    window.addEventListener('resize', () => queueRender(true), {passive: true});

    renderVirtualRail(true);
    requestAnimationFrame(() => takeOverSearch());
  }

  install();
})();
