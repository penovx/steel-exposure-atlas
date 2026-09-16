(() => {
  const userStateLabels = {
    direct_list_match: 'Listed',
    review_required: 'Needs review',
    no_direct_list_match_in_snapshot: 'No direct listing found',
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

  function addLink(parent, className, text, href) {
    const node = document.createElement('a');
    if (className) node.className = className;
    node.textContent = text;
    node.href = href;
    node.target = '_blank';
    node.rel = 'noreferrer';
    parent.append(node);
    return node;
  }

  function statusFor(payload, ownerId) {
    return payload?.statuses?.find?.((item) => item.company_id === ownerId) ?? null;
  }

  function formatDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value ?? ''))) return String(value ?? '');
    const [year, month, day] = value.split('-').map(Number);
    return new Intl.DateTimeFormat('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC',
    }).format(new Date(Date.UTC(year, month - 1, day)));
  }

  function baseSection(status, eyebrow, ariaLabel, sourceClass) {
    const section = document.createElement('section');
    section.className = `sanctions-context sanctions-${status.state} ${sourceClass}`;
    section.setAttribute('aria-label', ariaLabel);

    const top = document.createElement('div');
    top.className = 'sanctions-context-top';
    addText(top, 'span', 'sanctions-eyebrow', eyebrow);
    addText(top, 'span', 'sanctions-state', userStateLabels[status.state]);
    section.append(top);
    return section;
  }

  function addFacts(section, facts) {
    const list = document.createElement('dl');
    list.className = 'sanctions-facts';
    for (const [label, value] of facts) {
      if (!value) continue;
      const row = document.createElement('div');
      row.className = 'sanctions-fact';
      addText(row, 'dt', '', label);
      addText(row, 'dd', '', value);
      list.append(row);
    }
    if (list.children.length) section.append(list);
  }

  function addProcurementImplication(section, text) {
    const box = document.createElement('div');
    box.className = 'sanctions-impact';
    addText(box, 'strong', '', 'Procurement implication');
    addText(box, 'p', '', text);
    section.append(box);
  }

  function renderEuContext(payload, status) {
    const section = baseSection(status, 'EU SANCTIONS', 'EU sanctions context', 'sanctions-source-eu');

    if (status.state === 'direct_list_match') {
      addText(section, 'h3', 'sanctions-title', 'Listed by the EU');
      addText(section, 'p', 'sanctions-list-name', 'EU financial sanctions list');
      const matches = Array.isArray(status.reviewed_matches) ? status.reviewed_matches : [];
      const references = [...new Set(matches.map((item) => item.eu_reference).filter(Boolean))];
      addFacts(section, [
        ['EU reference', references.join(', ')],
      ]);
      addProcurementImplication(
        section,
        'Route this company for sanctions/compliance review before contracting, ordering or payment.'
      );
      addText(
        section,
        'p',
        'sanctions-note',
        'The company identity was reviewed across sources and linked to an entity in the pinned EU sanctions-list snapshot. Applicable restrictions depend on the relevant EU measures and transaction.'
      );
    } else if (status.state === 'review_required') {
      addText(section, 'h3', 'sanctions-title', 'Possible EU sanctions-list identity');
      addProcurementImplication(section, 'Resolve the company identity before proceeding with sourcing or payment decisions.');
      addText(section, 'p', 'sanctions-note', 'The deterministic screen found relevant identity evidence, but the match is not confirmed.');
    }

    const generationDates = payload.meta?.source_file_generation_dates;
    if (Array.isArray(generationDates) && generationDates.length) {
      addText(section, 'p', 'sanctions-source', `European Commission · source file date ${generationDates.join(', ')}`);
    }
    return section;
  }

  function sourceListName(sourceLists) {
    if (sourceLists.length === 1 && sourceLists[0] === 'SDN') {
      return 'Specially Designated Nationals and Blocked Persons (SDN) List';
    }
    if (sourceLists.length === 1 && sourceLists[0] === 'Consolidated Non-SDN') {
      return 'Consolidated Non-SDN Sanctions List';
    }
    return sourceLists.join(' + ');
  }

  function renderOfacContext(payload, status) {
    const section = baseSection(status, 'U.S. SANCTIONS', 'U.S. sanctions context', 'sanctions-source-ofac');

    if (status.state === 'direct_list_match') {
      const matches = Array.isArray(status.reviewed_matches) ? status.reviewed_matches : [];
      const sourceLists = [...new Set(matches.map((item) => item.source_list).filter(Boolean))];
      const uids = [...new Set(matches.map((item) => item.ofac_uid).filter(Boolean))];
      const programmes = [...new Set(matches.flatMap((item) => Array.isArray(item.programmes) ? item.programmes : []))];
      const listedDates = [...new Set(matches.map((item) => item.listed_since).filter(Boolean))];
      const summaries = [...new Set(matches.map((item) => item.designation_summary).filter(Boolean))];
      const actions = [...new Set(matches.map((item) => item.designation_action).filter(Boolean))];
      const actionUrls = [...new Set(matches.map((item) => item.designation_source_url).filter(Boolean))];

      addText(section, 'h3', 'sanctions-title', 'Listed by OFAC');
      addText(section, 'p', 'sanctions-list-name', sourceListName(sourceLists));
      addFacts(section, [
        ['Listed since', listedDates.map(formatDate).join(', ')],
        ['Designation context', summaries.join(', ')],
        ['Program', programmes.join(', ')],
        ['OFAC UID', uids.join(', ')],
      ]);
      if (actions.length) addText(section, 'p', 'sanctions-action', actions.join(' · '));
      if (actionUrls.length === 1) addLink(section, 'sanctions-action-link', 'OFAC designation action ↗', actionUrls[0]);

      const isSdn = sourceLists.includes('SDN');
      addProcurementImplication(
        section,
        isSdn
          ? 'Route this company for sanctions/compliance review before contracting, ordering or payment.'
          : 'Review the applicable OFAC restrictions before contracting, ordering or payment.'
      );
      addText(
        section,
        'p',
        'sanctions-note',
        isSdn
          ? 'The reviewed company identity is listed on OFAC’s SDN List. Restrictions can affect transactions involving U.S. persons or U.S. jurisdiction; the exact effect depends on the applicable sanctions authority and transaction.'
          : 'The reviewed company identity is listed by OFAC. Non-SDN programs can impose restrictions that differ from SDN blocking, so the source list and program remain visible.'
      );
    } else if (status.state === 'review_required') {
      addText(section, 'h3', 'sanctions-title', 'Possible U.S. sanctions-list identity');
      addProcurementImplication(section, 'Resolve the company identity before proceeding with sourcing or payment decisions.');
      addText(section, 'p', 'sanctions-note', 'The deterministic OFAC screen found relevant identity evidence, but the match is not confirmed.');
    }

    const dates = payload.meta?.source_publish_dates;
    if (dates && typeof dates === 'object') {
      const parts = [
        dates.SDN ? `SDN ${dates.SDN}` : null,
        dates['Consolidated Non-SDN'] ? `Consolidated Non-SDN ${dates['Consolidated Non-SDN']}` : null,
      ].filter(Boolean);
      addText(section, 'p', 'sanctions-source', `U.S. Department of the Treasury · OFAC${parts.length ? ` · snapshot ${parts.join(' · ')}` : ''}`);
    }
    return section;
  }

  function appendCompactNegative(readingDetail, negatives, hasFinding) {
    if (!negatives.length) return;
    if (hasFinding) {
      const line = document.createElement('p');
      line.className = 'sanctions-secondary-result';
      line.textContent = `${negatives.join(' and ')} screen${negatives.length > 1 ? 's' : ''}: no direct listing found in the pinned snapshot${negatives.length > 1 ? 's' : ''}.`;
      readingDetail.append(line);
      return;
    }

    const section = document.createElement('section');
    section.className = 'sanctions-context sanctions-negative-summary';
    const top = document.createElement('div');
    top.className = 'sanctions-context-top';
    addText(top, 'span', 'sanctions-eyebrow', 'SANCTIONS SCREENING');
    addText(top, 'span', 'sanctions-state', 'No direct listings found');
    section.append(top);
    addText(section, 'h3', 'sanctions-title', 'No direct EU or U.S. listing found');
    addText(section, 'p', 'sanctions-note', 'No direct listing was found for this company identity in the pinned sanctions snapshots. This does not mean sanctions-cleared; ownership, control and other restrictions may still apply.');
    readingDetail.append(section);
  }

  function renderCompanyIndicators(payloads) {
    const rows = document.querySelectorAll('#company-nodes .company-node[data-owner]');
    for (const row of rows) {
      row.querySelector('.company-sanctions-flags')?.remove();
      row.classList.remove('has-sanctions-listing');
      const ownerId = row.dataset.owner;
      const flags = [];
      const euStatus = statusFor(payloads.eu, ownerId);
      const ofacStatus = statusFor(payloads.ofac, ownerId);
      if (euStatus?.state === 'direct_list_match') flags.push('EU sanctions list');
      else if (euStatus?.state === 'review_required') flags.push('EU sanctions review');
      if (ofacStatus?.state === 'direct_list_match') flags.push('U.S. sanctions list');
      else if (ofacStatus?.state === 'review_required') flags.push('U.S. sanctions review');
      if (!flags.length) continue;

      row.classList.add('has-sanctions-listing');
      const wrap = document.createElement('span');
      wrap.className = 'company-sanctions-flags';
      for (const text of flags) addText(wrap, 'span', 'company-sanctions-flag', text);
      row.append(wrap);
    }
  }

  function renderContexts(payloads) {
    for (const node of document.querySelectorAll('.sanctions-context,.sanctions-secondary-result')) node.remove();

    const review = currentReview();
    const readingDetail = document.querySelector('#reading-detail');
    if (!review?.snapshot || !readingDetail || !payloads) return;

    const ownerId = selectedOwnerId(review);
    if (!ownerId) return;

    const euStatus = statusFor(payloads.eu, ownerId);
    const ofacStatus = statusFor(payloads.ofac, ownerId);
    let hasFinding = false;
    const negatives = [];

    if (euStatus?.state === 'direct_list_match' || euStatus?.state === 'review_required') {
      readingDetail.append(renderEuContext(payloads.eu, euStatus));
      hasFinding = true;
    } else if (euStatus?.state === 'no_direct_list_match_in_snapshot') {
      negatives.push('EU');
    }

    if (ofacStatus?.state === 'direct_list_match' || ofacStatus?.state === 'review_required') {
      readingDetail.append(renderOfacContext(payloads.ofac, ofacStatus));
      hasFinding = true;
    } else if (ofacStatus?.state === 'no_direct_list_match_in_snapshot') {
      negatives.push('U.S. / OFAC');
    }

    appendCompactNegative(readingDetail, negatives, hasFinding);
  }

  function sourceSection(title, paragraphs, className) {
    const section = document.createElement('section');
    section.className = `source-section sanctions-source-section ${className}`;
    addText(section, 'h3', '', title);
    for (const paragraph of paragraphs) addText(section, 'p', '', paragraph);
    return section;
  }

  function reconcileSourcesDialog(payloads, tradePayload) {
    const sourceContent = document.querySelector('#source-content');
    if (!sourceContent || !sourceContent.children.length) return;

    for (const paragraph of sourceContent.querySelectorAll('p')) {
      if (!paragraph.textContent?.includes('No water-stress, trade, emissions or buyer-supplier layer is present.')) continue;
      paragraph.textContent = 'Water-stress, emissions and buyer-supplier layers are not present. EU and U.S. sanctions context and the EU steel-import scenario are separate reviewed layers built from pinned source snapshots. The integration remains pre-publication until the repository release checklist is completed.';
    }

    if (payloads.eu && !sourceContent.querySelector('.sanctions-source-section-eu')) {
      const generationDates = payloads.eu.meta?.source_file_generation_dates;
      const suffix = Array.isArray(generationDates) && generationDates.length
        ? ` Source file date: ${generationDates.join(', ')}.`
        : '';
      sourceContent.append(sourceSection(
        'EU sanctions screening',
        [
          'Usable GIST company identities are screened against the pinned European Commission financial-sanctions snapshot. Confirmed identity matches are shown as listed; unresolved candidates remain review items. A negative screen is not sanctions clearance.',
          `European Commission source snapshot SHA-256: ${payloads.eu.meta?.source_snapshot_sha256 ?? 'not available'}.${suffix}`,
        ],
        'sanctions-source-section-eu'
      ));
    }

    if (payloads.ofac && !sourceContent.querySelector('.sanctions-source-section-ofac')) {
      const hashes = payloads.ofac.meta?.source_snapshot_sha256 ?? {};
      const dates = payloads.ofac.meta?.source_publish_dates ?? {};
      sourceContent.append(sourceSection(
        'U.S. / OFAC sanctions screening',
        [
          'Usable GIST company identities are screened against pinned OFAC Entity records. The full source-list name, program and designation date remain visible for confirmed matches; SDN and Non-SDN restrictions are not treated as equivalent.',
          'A negative direct-list result is not sanctions clearance and does not evaluate OFAC ownership/control rules for unnamed entities.',
          `OFAC snapshots · SDN ${dates.SDN ?? 'date unavailable'} · SHA-256 ${hashes.SDN ?? 'not available'} · Consolidated Non-SDN ${dates['Consolidated Non-SDN'] ?? 'date unavailable'} · SHA-256 ${hashes['Consolidated Non-SDN'] ?? 'not available'}`,
        ],
        'sanctions-source-section-ofac'
      ));
    }

    if (tradePayload && !sourceContent.querySelector('.trade-source-section-eu-steel')) {
      const meta = tradePayload.meta ?? {};
      sourceContent.append(sourceSection(
        'EU steel import scenario',
        [
          'Plant origin and GIST product-family evidence are connected to the current EU steel import measure to create a procurement follow-up for a hypothetical import into the EU. The scenario does not assert that a plant exports to the EU.',
          `Pinned EUR-Lex source hashes · Regulation 2026/1457: ${meta.measure_snapshot_sha256 ?? 'not available'} · Regulation 2026/1930: ${meta.bilateral_snapshot_sha256 ?? 'not available'}`,
        ],
        'trade-source-section-eu-steel'
      ));
    }
  }

  async function init() {
    const [payloads, tradePayload] = await Promise.all([
      globalThis.__ATLAS_SANCTIONS_PROMISE__ ?? Promise.resolve({eu: null, ofac: null}),
      globalThis.__ATLAS_TRADE_PROMISE__ ?? Promise.resolve(null),
    ]);
    if (!payloads?.eu && !payloads?.ofac && !tradePayload) return;

    const sourceContent = document.querySelector('#source-content');
    if (sourceContent) {
      const sourceObserver = new MutationObserver(() => reconcileSourcesDialog(payloads, tradePayload));
      sourceObserver.observe(sourceContent, {childList: true});
    }

    const waitForCore = () => {
      const review = currentReview();
      const selectionPath = document.querySelector('#selection-path');
      const companyNodes = document.querySelector('#company-nodes');
      if (!review?.snapshot || !selectionPath || !companyNodes) {
        requestAnimationFrame(waitForCore);
        return;
      }

      const selectionObserver = new MutationObserver(() => renderContexts(payloads));
      selectionObserver.observe(selectionPath, {childList: true, subtree: true});
      const companyObserver = new MutationObserver(() => renderCompanyIndicators(payloads));
      companyObserver.observe(companyNodes, {childList: true});

      renderCompanyIndicators(payloads);
      renderContexts(payloads);
      reconcileSourcesDialog(payloads, tradePayload);
    };

    waitForCore();
  }

  init();
})();
