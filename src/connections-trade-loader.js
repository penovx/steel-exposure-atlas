(() => {
  const EXPECTED_SCHEMA = 'steel-exposure-atlas/eu-steel-trade-context-v1.0';
  const EXPECTED_MEASURE_SHA = 'B869A4BB8C4E4F7AE320B4CE4A117A33B05CADEEDF1C9DF106845EBCA9D9B21B';
  const EXPECTED_BILATERAL_SHA = '5F0214CD0FC9FC85A114B9EC485E2D6887F3F2137BD177EE357CC00FE2BB32BE';
  const URL = './public/data/eu-steel-trade-context.v1.json';

  async function load() {
    let response;
    try {
      response = await fetch(URL, {cache: 'no-store'});
    } catch {
      return null;
    }
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`EU steel trade context returned HTTP ${response.status}.`);

    const payload = await response.json();
    const meta = payload?.meta;
    if (!meta || meta.schema !== EXPECTED_SCHEMA) {
      throw new Error('Unexpected EU steel trade context schema.');
    }
    if (meta.measure_snapshot_sha256 !== EXPECTED_MEASURE_SHA) {
      throw new Error('EU steel trade context uses an unexpected Regulation 2026/1457 snapshot.');
    }
    if (meta.bilateral_snapshot_sha256 !== EXPECTED_BILATERAL_SHA) {
      throw new Error('EU steel trade context uses an unexpected Regulation 2026/1930 snapshot.');
    }
    if (!Array.isArray(payload.plants)) {
      throw new Error('EU steel trade context has no plants list.');
    }
    return payload;
  }

  globalThis.__ATLAS_TRADE_PROMISE__ = load();
})();
