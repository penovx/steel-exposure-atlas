(() => {
  const stateLabels = {
    direct_list_match: 'Direct list match',
    review_required: 'Review required',
    no_direct_list_match_in_snapshot: 'No direct list match in this snapshot',
  };

  function currentReview() {
    try {
      return globalThis.__atlasReview ?? null;
    } catch {
      return null;
    }
  }

  function selectedOwnerId(review) {
    const snapshot = review.snapshot();
    const state = snapshot?.state;
    if (!state) return null;
    if (state.filters?.owner) return state.filters.owner;
    if (!state.site) return null;
    const plant = review.all?.find?.((item) => item.id === state.site);
    return plant?.ownerId ?? null;
  }

  function addText(parent, tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = text;
    parent.append(node);
    return node;
  }

  function renderContext(payload) {
    document.querySelector('.sanctions-context')?.remove();

    const review = currentReview();
    const readingDetail = document.querySelector('#reading-detail');
    if (!review?.snapshot || !readingDetail || !payload) return;

    const ownerId = selectedOwnerId(review);
    if (!ownerId) return;

    const status = payload.statuses.find((item) => item.company_id === ownerId);
    if (!status || !stateLabels[status.state]) return;

    const section = document.createElement('section');
    section.className = `sanctions-context sanctions-${status.state}`;
    section.setAttribute('aria-label', 'EU sanctions context');

    const top = document.createElement('div');
    top.className = 'sanctions-context-top';
    addText(top, 'span', 'sanctions-eyebrow', 'EU SANCTIONS CONTEXT');
    addText(top, 'span', 'sanctions-state', stateLabels[status.state]);
    section.append(top);

    if (status.state === 'direct_list_match') {
      addText(section, 'h3', 'sanctions-title', 'Identity resolution: Confirmed');
      const matches = Array.isArray(status.reviewed_matches) ? status.reviewed_matches : [];
      const references = matches.map((item) => item.eu_reference).filter(Boolean);
      const reviewedDates = matches.map((item) => item.reviewed_at).filter(Boolean);
      const meta = [
        references.length ? `EU reference ${references.join(', ')}` : null,
        reviewedDates.length ? `identity reviewed ${reviewedDates.join(', ')}` : null,
      ].filter(Boolean).join(' · ');
      if (meta) addText(section, 'p', 'sanctions-meta', meta);
      addText(
        section,
        'p',
        'sanctions-note',
        'A reviewed cross-source identity resolution links this GIST company identity to an entity in the pinned EU sanctions-list snapshot. This is company-level evidence, not a separate finding about the plant, subsidiaries or related parties.'
      );
    } else if (status.state === 'review_required') {
      addText(section, 'h3', 'sanctions-title', 'Identity resolution: Review required');
      addText(
        section,
        'p',
        'sanctions-note',
        'The deterministic screen found relevant identity evidence, but it has not been resolved strongly enough for a direct-list-match finding.'
      );
    } else {
      addText(section, 'h3', 'sanctions-title', 'Deterministic entity screen');
      addText(
        section,
        'p',
        'sanctions-note',
        'No direct deterministic list match was found for this screened GIST owner identity in the pinned EU snapshot. This is not sanctions clearance and does not address ownership, control or related-party effects.'
      );
    }

    const generationDates = payload.meta?.source_file_generation_dates;
    if (Array.isArray(generationDates) && generationDates.length) {
      addText(
        section,
        'p',
        'sanctions-source',
        `European Commission · Consolidated Financial Sanctions File 1.1 · source file date ${generationDates.join(', ')}`
      );
    }

    readingDetail.append(section);
  }

  function reconcileSourcesDialog(payload) {
    const sourceContent = document.querySelector('#source-content');
    if (!sourceContent || !sourceContent.children.length) return;

    for (const paragraph of sourceContent.querySelectorAll('p')) {
      if (!paragraph.textContent?.includes('This visual connects fields within GIST; it is not yet a multi-publisher finding.')) continue;
      paragraph.textContent = 'No water-stress, trade, emissions or buyer-supplier layer is present. EU sanctions context is a separate reviewed company-level layer loaded from a pinned local derived artifact. The integration remains pre-publication until the repository release checklist is completed.';
    }

    if (sourceContent.querySelector('.sanctions-source-section')) return;
    const section = document.createElement('section');
    section.className = 'source-section sanctions-source-section';
    addText(section, 'h3', '', 'EU sanctions context');
    addText(
      section,
      'p',
      '',
      'The sanctions layer screens usable GIST owner identities against the pinned European Commission Consolidated Financial Sanctions File 1.1 enterprise snapshot. It uses categorical states only: Direct list match, Review required, or No direct list match in this snapshot. No sanctions percentage or risk score is defined.'
    );
    addText(
      section,
      'p',
      '',
      'A direct list match can be published only after the company identity is sufficiently resolved. A negative result is not sanctions clearance. Ownership, control, subsidiaries and related-party effects remain separate questions.'
    );
    const generationDates = payload.meta?.source_file_generation_dates;
    const suffix = Array.isArray(generationDates) && generationDates.length
      ? ` Source file date: ${generationDates.join(', ')}.`
      : '';
    addText(
      section,
      'p',
      '',
      `European Commission source snapshot SHA-256: ${payload.meta?.source_snapshot_sha256 ?? 'not available'}.${suffix}`
    );
    sourceContent.append(section);
  }

  async function init() {
    const payload = await (globalThis.__ATLAS_SANCTIONS_PROMISE__ ?? Promise.resolve(null));
    if (!payload) return;

    const sourceContent = document.querySelector('#source-content');
    if (sourceContent) {
      const sourceObserver = new MutationObserver(() => reconcileSourcesDialog(payload));
      sourceObserver.observe(sourceContent, {childList: true});
    }

    const waitForCore = () => {
      const review = currentReview();
      const selectionPath = document.querySelector('#selection-path');
      if (!review?.snapshot || !selectionPath) {
        requestAnimationFrame(waitForCore);
        return;
      }

      const observer = new MutationObserver(() => renderContext(payload));
      observer.observe(selectionPath, {childList: true, subtree: true});
      renderContext(payload);
      reconcileSourcesDialog(payload);
    };

    waitForCore();
  }

  init();
})();
