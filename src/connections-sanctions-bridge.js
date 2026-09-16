(() => {
  const userStateLabels = {
    direct_list_match: 'Listed',
    review_required: 'Unresolved match',
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
    addText(top, 'span', 'sanctions-state', userStateLabels[status.state] ?? status.state);
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

  function renderEuContext(payload, status) {
    const section = baseSection(status, 'EU SANCTIONS', 'EU sanctions context', 'sanctions-source-eu');

    if (status.state === 'direct_list_match') {
      addText(section, 'h3', 'sanctions-title', 'Company identity listed by the EU');
      addText(section, 'p', 'sanctions-list-name', 'EU financial sanctions list');
      const matches = Array.isArray(status.reviewed_matches) ? status.reviewed_matches : [];
      const references = [...new Set(matches.map((item) => item.eu_reference).filter(Boolean))];
      addFacts(section, [['EU reference', references.join(', ')]]);
      addText(
        section,
        'p',
        'sanctions-note',
        'The reviewed GIST company identity is linked to an entity in the pinned European Commission sanctions-list snapshot.'
      );
    } else if (status.state === 'review_required') {
      addText(section, 'h3', 'sanctions-title', 'Candidate EU sanctions-list identity');
      addText(section, 'p', 'sanctions-note', 'The deterministic identity screen found relevant evidence, but the reviewed identity link remains unresolved.');
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

      addText(section, 'h3', 'sanctions-title', 'Company identity listed by OFAC');
      addText(section, 'p', 'sanctions-list-name', sourceListName(sourceLists));
      addFacts(section, [
        ['Listed since', listedDates.map(formatDate).join(', ')],
        ['Designation context', summaries.join(', ')],
        ['Program', programmes.join(', ')],
        ['OFAC UID', uids.join(', ')],
      ]);
      if (actions.length) addText(section, 'p', 'sanctions-action', actions.join(' · '));
      if (actionUrls.length === 1) addLink(section, 'sanctions-action-link', 'OFAC designation action ↗', actionUrls[0]);

      addText(
        section,
        'p',
        'sanctions-note',
        sourceLists.includes('SDN')
          ? 'The reviewed GIST company identity is listed on OFAC’s SDN List. The source list, program and designation context are preserved here as evidence.'
          : 'The reviewed GIST company identity is listed by OFAC. The source list and program remain visible because Non-SDN and SDN list types are distinct.'
      );
    } else if (status.state === 'review_required') {
      addText(section, 'h3', 'sanctions-title', 'Candidate U.S. sanctions-list identity');
      addText(section, 'p', 'sanctions-note', 'The deterministic OFAC identity screen found relevant evidence, but the reviewed identity link remains unresolved.');
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
      else if (euStatus?.state === 'review_required') flags.push('EU sanctions identity match');
      if (ofacStatus?.state === 'direct_list_match') flags.push('U.S. sanctions list');
      else if (ofacStatus?.state === 'review_required') flags.push('U.S. sanctions identity match');
      if (!flags.length) continue;

      row.classList.add('has-sanctions-listing');
      const wrap = document.createElement('span');
      wrap.className = 'company-sanctions-flags';
      for (const value of flags) addText(wrap, 'span', 'company-sanctions-flag', value);
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

    if (euStatus?.state === 'direct_list_match' || euStatus?.state === 'review_required') {
      readingDetail.append(renderEuContext(payloads.eu, euStatus));
    }
    if (ofacStatus?.state === 'direct_list_match' || ofacStatus?.state === 'review_required') {
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

  function reconcileSourcesDialog(payloads, tradePayload) {
    const sourceContent = document.querySelector('#source-content');
    if (!sourceContent || !sourceContent.children.length) return;

    const cartographySection = [...sourceContent.querySelectorAll('.source-section')].find(
      (section) => section.querySelector('h3')?.textContent === 'Cartography and local review'
    );
    const scopeParagraph = cartographySection?.querySelector('p:last-child');
    if (scopeParagraph) {
      scopeParagraph.textContent = 'Water-stress, emissions and buyer-supplier layers are not present. EU and U.S. sanctions context and the EU steel-import scenario are separate reviewed layers built from pinned source snapshots. The integration remains pre-publication until the repository release checklist is completed.';
    }

    if (payloads.eu && !sourceContent.querySelector('.sanctions-source-section-eu')) {
      const generationDates = payloads.eu.meta?.source_file_generation_dates;
      const suffix = Array.isArray(generationDates) && generationDates.length
        ? ` Source file date: ${generationDates.join(', ')}.`
        : '';
      sourceContent.append(sourceSection(
        'EU sanctions screening',
        [
          'Usable GIST company identities are screened against the pinned European Commission financial-sanctions snapshot. Confirmed identity matches are shown as listed; unresolved candidates retain their unresolved state. A negative screen is not sanctions clearance.',
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
          'Usable GIST company identities are screened against pinned OFAC Entity records. The full source-list name, program and designation date remain visible for confirmed matches; SDN and Non-SDN list types remain distinct.',
          'A negative direct-list result is not sanctions clearance and does not evaluate OFAC ownership/control rules for unnamed entities.',
          `OFAC snapshots · SDN ${dates.SDN ?? 'date unavailable'} · SHA-256 ${hashes.SDN ?? 'not available'} · Consolidated Non-SDN ${dates['Consolidated Non-SDN'] ?? 'date unavailable'} · SHA-256 ${hashes['Consolidated Non-SDN'] ?? 'not available'}`,
        ],
        'sanctions-source-section-ofac'
      ));
    }

    if (tradePayload && !sourceContent.querySelector('.trade-source-section-eu-steel')) {
      const meta = tradePayload.meta ?? {};
      const measureSha = meta.sources?.commission_implementing_regulation_2026_1457?.sha256 ?? 'not available';
      const bilateralSha = meta.sources?.commission_implementing_regulation_2026_1930?.sha256 ?? 'not available';
      sourceContent.append(sourceSection(
        'EU steel import scenario',
        [
          'Plant origin and GIST product-family evidence are mapped to the current EU steel import measure for a hypothetical import into the EU. The scenario does not assert that a plant exports to the EU.',
          `Pinned EUR-Lex source hashes · Regulation 2026/1457: ${measureSha} · Regulation 2026/1930: ${bilateralSha}`,
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
