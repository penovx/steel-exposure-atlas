(() => {
  'use strict';

  const SOURCE_BUTTON_IDS = ['open-sources', 'map-basis', 'footer-sources'];

  function reviewApi() {
    try { return globalThis.__atlasReview ?? null; } catch { return null; }
  }

  function addText(parent, tag, text) {
    const node = document.createElement(tag);
    node.textContent = text;
    parent.append(node);
    return node;
  }

  function addLink(parent, label, href) {
    const link = document.createElement('a');
    link.href = href;
    link.target = '_blank';
    link.rel = 'noreferrer';
    link.textContent = label;
    parent.append(link);
    return link;
  }

  function section(root, title, paragraphs = []) {
    const node = document.createElement('section');
    node.className = 'source-section';
    addText(node, 'h3', title);
    for (const paragraph of paragraphs) addText(node, 'p', paragraph);
    root.append(node);
    return node;
  }

  function currentPlant(review) {
    const siteId = review.snapshot?.()?.state?.site;
    return siteId ? review.all?.find?.((plant) => plant.id === siteId) ?? null : null;
  }

  function renderPlantSource(root, plant) {
    if (!plant) return;
    const node = section(root, plant.name, [
      `${plant.country} · location accuracy: ${plant.accuracy}`,
      `Immediate owner/operator: ${plant.owner} · GEM plant ID: ${plant.id} · GEM entity ID: ${plant.ownerId}`,
    ]);
    const links = document.createElement('p');
    const href = /^https:\/\/(www\.)?gem\.wiki\//.test(plant.source_url ?? '')
      ? plant.source_url
      : 'https://globalenergymonitor.org/projects/global-iron-steel-tracker/';
    addLink(links, 'Plant source page ↗', href);
    node.append(links);
  }

  function renderSources() {
    const review = reviewApi();
    const dialog = document.querySelector('#sources-dialog');
    const root = document.querySelector('#source-content');
    if (!review?.snapshot || !dialog || !root) return;

    root.replaceChildren();
    renderPlantSource(root, currentPlant(review));

    section(root, 'How the connections work', [
      'Company means the immediate owner or operator recorded by GEM. It is not a claim about ultimate parentage or independent control. A product connection means the plant lists that product description. A production-method connection requires positive operating capacity for that method.',
      'Lines show relationships inside the reviewed data model. They do not show shipments, buyer-supplier relationships, contractual supply, corporate headquarters or available volume.',
    ]);

    section(root, 'Reading the atlas', [
      'The Company rail exposes the eligible company population for the selected geography through a virtualized list and search. Selecting a company keeps the full map visible and highlights its sites; the company profile opens only through the explicit profile action.',
      'Products are multi-select. Production methods are single-select. A site selection can start a new path and clears incompatible filters. Map zoom and pan never change the underlying population.',
    ]);

    section(root, 'Capacity and products', [
      'Operating capacity includes only source tranches with status “operating” or “operating pre-retirement”. Unknown, blank, N/A and positive-but-unquantified values remain distinct. A plus sign indicates additional positive capacity that is not numerically quantified.',
      'Plant product labels are descriptive source fields. They do not establish product-specific capacity, grade availability, commercial suitability or available supply. Operating capacity must not be read as supply available to a buyer.',
    ]);

    section(root, 'Sanctions and EU steel trade context', [
      'Company profiles can display categorical sanctions evidence from the pinned OFAC and EU source artifacts. Direct-list evidence is shown as a finding; absence of a direct match is not promoted as clearance and no sanctions probability or composite risk score is calculated.',
      'EU steel trade context is a hypothetical import-into-the-EU relationship derived from plant origin and plant-level product descriptions. Product-family mappings remain candidate mappings where the source data does not establish a customs classification.',
    ]);

    const gem = section(root, 'Primary industrial data', [
      'Global Energy Monitor · Global Iron and Steel Tracker · June 2026 (V1). Retrieved 2026-09-14. This project uses a transformed extract with derived calculations and presentation; Global Energy Monitor does not endorse Steel Exposure Atlas.',
      'The 1,293 tracked plants are not all operating steel suppliers. Regional names are preserved from GEM. Multiple or unresolved company identities are not forced into one company.',
    ]);
    const licence = document.createElement('p');
    addLink(licence, 'GEM / GIST source ↗', 'https://globalenergymonitor.org/projects/global-iron-steel-tracker/');
    licence.append(document.createTextNode(' · '));
    addLink(licence, 'CC BY 4.0 ↗', 'https://creativecommons.org/licenses/by/4.0/');
    gem.append(licence);

    const provenance = section(root, 'Cartography and provenance', [
      'Natural Earth 1:110m Admin 0 Countries v5.1.1 provides cartographic context. Country membership comes from the GIST records, not from spatial inference against the map geometry.',
      'The runtime reads reviewed local artifacts only. Sanctions and trade evidence is kept separate from the GIST industrial source and linked through explicit company, plant, origin and product relationships.',
      'Steel Exposure Atlas remains pre-publication until the repository release checklist is complete.',
    ]);
    const hash = globalThis.__ATLAS_DATA__?.json_sha256;
    if (hash) {
      const line = document.createElement('p');
      line.append(document.createTextNode('Reviewed GIST runtime SHA-256: '));
      const code = document.createElement('code');
      code.textContent = hash;
      line.append(code);
      provenance.append(line);
    }

    if (!dialog.open) dialog.showModal();
  }

  function install() {
    const review = reviewApi();
    const ready = SOURCE_BUTTON_IDS.every((id) => document.getElementById(id));
    if (!review?.snapshot || !ready) {
      requestAnimationFrame(install);
      return;
    }
    if (document.documentElement.dataset.sourcesDialogInstalled === 'true') return;
    document.documentElement.dataset.sourcesDialogInstalled = 'true';
    for (const id of SOURCE_BUTTON_IDS) document.getElementById(id).onclick = renderSources;
  }

  install();
})();
