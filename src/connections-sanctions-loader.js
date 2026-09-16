(() => {
  const eu = {
    key: 'eu',
    label: 'EU sanctions context',
    url: new URL('../public/data/eu-sanctions-owner-status.v1.json', document.currentScript.src),
    schema: 'steel-exposure-atlas/eu-sanctions-owner-status-v1.0',
    validateSnapshot(payload) {
      return payload?.meta?.source_snapshot_sha256 === '049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015';
    },
  };

  const ofac = {
    key: 'ofac',
    label: 'OFAC sanctions context',
    url: new URL('../public/data/ofac-sanctions-owner-status.v1.json', document.currentScript.src),
    schema: 'steel-exposure-atlas/ofac-sanctions-owner-status-v1.0',
    validateSnapshot(payload) {
      const hashes = payload?.meta?.source_snapshot_sha256;
      return hashes?.SDN === '3D594ED7CDB5E0FD13F126A3815255146D730F791DCF672665C67416D03A7C1F'
        && hashes?.['Consolidated Non-SDN'] === 'C59772F3EDD625812AC43C4AEC57513D08CDD180135A3B6368DBC086AB81DF7D';
    },
  };

  async function loadOne(spec) {
    const response = await fetch(spec.url, {
      credentials: 'same-origin',
      cache: 'no-store',
    });

    // Procurement-context layers are optional during local build steps.
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`${spec.label} is unavailable (${response.status}).`);

    const payload = await response.json();
    if (payload?.meta?.schema !== spec.schema) {
      throw new Error(`Unexpected ${spec.label} schema: ${payload?.meta?.schema ?? 'missing'}`);
    }
    if (!spec.validateSnapshot(payload)) {
      throw new Error(`${spec.label} does not match the pinned source snapshot.`);
    }
    if (!Array.isArray(payload.statuses)) {
      throw new Error(`${spec.label} has no statuses array.`);
    }
    return payload;
  }

  async function safeLoad(spec) {
    try {
      return await loadOne(spec);
    } catch (error) {
      console.error(error);
      globalThis.__ATLAS_SANCTIONS_ERRORS__ ??= {};
      globalThis.__ATLAS_SANCTIONS_ERRORS__[spec.key] = String(error?.message ?? error);
      return null;
    }
  }

  globalThis.__ATLAS_SANCTIONS_PROMISE__ = Promise.all([
    safeLoad(eu),
    safeLoad(ofac),
  ]).then(([euPayload, ofacPayload]) => ({
    eu: euPayload,
    ofac: ofacPayload,
  }));
})();
