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

  function statusFor(payload, ownerId) {
    return payload?.statuses?.find?.((item) => item.company_id === ownerId) ?? null;
  }

  function baseSection(status, eyebrow, ariaLabel, sourceClass) {
    const section = document.createElement('section');
    section.className = `sanctions-context sanctions-${status.state} ${sourceClass}`;
    section.setAttribute('aria-label', ariaLabel);

    const top = document.createElement('div');
    top.className = 'sanctions-context-top';
    addText(top, 'span', 'sanctions-eyebrow', eyebrow);
    addText(top, 'span', 'sanctions-state', stateLabels[status.state]);
    section.append(top);
    return section;
  }

  function renderEuContext(payload, status) {
    const section = baseSection(status, 'EU SANCTIONS CONTEXT', 'EU sanctions context', 'sanctions-source-eu');

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
        'The deterministic EU screen found relevant identity evidence, but it has not been resolved strongly enough for a direct-list-match finding.'
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
    return section;
  }

  function renderOfacContext(payload, status) {
    const section = baseSection(status, 'U.S. / OFAC SANCTIONS CONTEXT', 'U.S. OFAC sanctions context', 'sanctions-source-ofac');

    if (status.state === 'direct_list_match') {
      addText(section, 'h3', 'sanctions-title', 'Identity resolution: Confirmed');
      const matches = Array.isArray(status.reviewed_matches) ? status.reviewed_matches : [];
      const sourceLists = [...new Set(matches.map((item) => item.source_list).filter(Boolean))];
      const uids = matches.map((item) => item.ofac_uid).filter(Boolean);
      const programmes = [...new Set(matches.flatMap((item) => Array.isArray(item.programmes) ? item.programmes : []))];
      const reviewedDates = [...new Set(matches.map((item) => item.reviewed_at).filter(Boolean))];
      const meta = [
        sourceLists.length ? sourceLists.join(', ') : null,
        uids.length ? `OFAC UID ${uids.join(', ')}` : null,
        programmes.length ? programmes.join(', ') : null,
        reviewedDates.length ? `identity reviewed ${reviewedDates.join(', ')}` : null,
      ].filter(Boolean).join(' · ');
      if (meta) addText(section, 'p', 'sanctions-meta', meta);
      addText(
        section,
        'p',
        'sanctions-note',
        'A reviewed cross-source identity resolution links this GIST company identity to an entry in the pinned OFAC sanctions-list snapshot. The source list and program context are retained. This is company-level direct-list evidence, not a separate plant-level finding.'
      );
    } else if (status.state === 'review_required') {
      addText(section, 'h3', 'sanctions-title', 'Identity resolution: Review required');
      addText(
        section,
        'p',
        'sanctions-note',
        'The deterministic OFAC screen found relevant identity evidence, but it has not been resolved strongly enough for a direct-list-match finding.'
      );
    } else {
      addText(section, 'h3', 'sanctions-title', 'Deterministic entity screen');
      addText(
        section,
        'p',
        'sanctions-note',
        'No direct deterministic OFAC list match was found for this screened GIST owner identity in the pinned snapshots. This is not sanctions clearance and does not address ownership or control rules, including entities that may be affected without being separately named on a list.'
      );
    }

    const dates = payload.meta?.source_publish_dates;
    if (dates && typeof dates === 'object') {
      const parts = [
        dates.SDN ? `SDN ${dates.SDN}` : null,
        dates['Consolidated Non-SDN'] ? `Consolidated Non-SDN ${dates['Consolidated Non-SDN']}` : null,
      ].filter(Boolean);
      addText(
        section,
        'p',
        'sanctions-source',
        `U.S. Department of the Treasury · OFAC${parts.length ? ` · source publish dates ${parts.join(' · ')}` : ''}`
      );
    }
    return section;
  }

  function renderContexts(payloads) {
    for (const node of document.querySelectorAll('.sanctions-context')) node.remove();

    const review = currentReview();
    const readingDetail = document.querySelector('#reading-detail');
    if (!review?.snapshot || !readingDetail || !payloads) return;

    const ownerId = selectedOwnerId(review);
    if (!ownerId) return;

    const euStatus = statusFor(payloads.eu, ownerId);
    if (euStatus && stateLabels[euStatus.state]) {
      readingDetail.append(renderEuContext(payloads.eu, euStatus));
    }

    const ofacStatus = statusFor(payloads.ofac, ownerId);
    if (ofacStatus && stateLabels[ofacStatus.state]) {
      readingDetail.append(renderOfacContext(payloads.ofac, ofacStatus));
    }
  }

  function sourceSection(title, paragraphs, className) {
    const section = document.createElement('section');
    section.className = `source-section sanctions-source-section ${className}`;
    addText(section, 'h3', '', title);
    for (const paragraph of paragraphs) addText(section, 'p', '', paragraph);
    return section;
  }

  function reconcileSourcesDialog(payloads) {
    const sourceContent = document.querySelector('#source-content');
    if (!sourceContent || !sourceContent.children.length) return;

    for (const paragraph of sourceContent.querySelectorAll('p')) {
      if (!paragraph.textContent?.includes('No water-stress, trade, emissions or buyer-supplier layer is present.')) continue;
      paragraph.textContent = 'No water-stress, trade, emissions or buyer-supplier layer is present. EU and U.S. OFAC sanctions context are separate reviewed company-level layers loaded from pinned local derived artifacts. The integration remains pre-publication until the repository release checklist is completed.';
    }

    if (payloads.eu && !sourceContent.querySelector('.sanctions-source-section-eu')) {
      const generationDates = payloads.eu.meta?.source_file_generation_dates;
      const suffix = Array.isArray(generationDates) && generationDates.length
        ? ` Source file date: ${generationDates.join(', ')}.`
        : '';
      sourceContent.append(sourceSection(
        'EU sanctions context',
        [
          'The EU layer screens usable GIST owner identities against the pinned European Commission Consolidated Financial Sanctions File 1.1 enterprise snapshot. It uses categorical states only: Direct list match, Review required, or No direct list match in this snapshot. No sanctions percentage or risk score is defined.',
          'A direct list match can be published only after the company identity is sufficiently resolved. A negative result is not sanctions clearance. Ownership, control, subsidiaries and related-party effects remain separate questions.',
          `European Commission source snapshot SHA-256: ${payloads.eu.meta?.source_snapshot_sha256 ?? 'not available'}.${suffix}`,
        ],
        'sanctions-source-section-eu'
      ));
    }

    if (payloads.ofac && !sourceContent.querySelector('.sanctions-source-section-ofac')) {
      const hashes = payloads.ofac.meta?.source_snapshot_sha256 ?? {};
      const dates = payloads.ofac.meta?.source_publish_dates ?? {};
      sourceContent.append(sourceSection(
        'U.S. / OFAC sanctions context',
        [
          'The OFAC layer screens usable GIST owner identities against pinned Entity records from the Specially Designated Nationals and Blocked Persons List and the Consolidated Non-SDN Sanctions List. SDN and Non-SDN source-list/program context are retained rather than collapsed into one legal-effect flag.',
          'A direct list match can be published only after the company identity is sufficiently resolved. A negative direct-list result is not sanctions clearance and does not evaluate OFAC ownership/control rules for unnamed entities.',
          `OFAC source snapshots · SDN ${dates.SDN ?? 'date unavailable'} · SHA-256 ${hashes.SDN ?? 'not available'} · Consolidated Non-SDN ${dates['Consolidated Non-SDN'] ?? 'date unavailable'} · SHA-256 ${hashes['Consolidated Non-SDN'] ?? 'not available'}`,
        ],
        'sanctions-source-section-ofac'
      ));
    }
  }

  async function init() {
    const payloads = await (globalThis.__ATLAS_SANCTIONS_PROMISE__ ?? Promise.resolve({eu: null, ofac: null}));
    if (!payloads?.eu && !payloads?.ofac) return;

    const sourceContent = document.querySelector('#source-content');
    if (sourceContent) {
      const sourceObserver = new MutationObserver(() => reconcileSourcesDialog(payloads));
      sourceObserver.observe(sourceContent, {childList: true});
    }

    const waitForCore = () => {
      const review = currentReview();
      const selectionPath = document.querySelector('#selection-path');
      if (!review?.snapshot || !selectionPath) {
        requestAnimationFrame(waitForCore);
        return;
      }

      const observer = new MutationObserver(() => renderContexts(payloads));
      observer.observe(selectionPath, {childList: true, subtree: true});
      renderContexts(payloads);
      reconcileSourcesDialog(payloads);
    };

    waitForCore();
  }

  init();
})();
