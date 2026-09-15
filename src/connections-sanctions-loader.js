(() => {
  const sourceUrl = new URL('../public/data/eu-sanctions-owner-status.v1.json', document.currentScript.src);
  const expectedSchema = 'steel-exposure-atlas/eu-sanctions-owner-status-v1.0';
  const expectedSourceHash = '049CB95CF55CD9A77DFB8D3FED21EB61A541E4C46F80D1F1B581F2E537E0F015';

  async function load() {
    const response = await fetch(sourceUrl, {
      credentials: 'same-origin',
      cache: 'no-store',
    });

    // The base atlas remains usable while the optional procurement-context layer
    // is still being built locally. Any non-404 failure is surfaced.
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`EU sanctions context is unavailable (${response.status}).`);

    const payload = await response.json();
    if (payload?.meta?.schema !== expectedSchema) {
      throw new Error(`Unexpected EU sanctions context schema: ${payload?.meta?.schema ?? 'missing'}`);
    }
    if (payload?.meta?.source_snapshot_sha256 !== expectedSourceHash) {
      throw new Error('EU sanctions context does not match the pinned source snapshot.');
    }
    if (!Array.isArray(payload.statuses)) {
      throw new Error('EU sanctions context has no statuses array.');
    }
    return payload;
  }

  globalThis.__ATLAS_SANCTIONS_PROMISE__ = load().catch((error) => {
    console.error(error);
    globalThis.__ATLAS_SANCTIONS_ERROR__ = String(error?.message ?? error);
    return null;
  });
})();
