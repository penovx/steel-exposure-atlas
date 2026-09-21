import { rankCapacityPlants, formatCapacity, CAPACITY_FIELDS } from './gist-adapter.mjs';
import { processBranches, productionSeries, documentedProducts, matchingProductPlants, siteContribution } from './site-model.mjs';

const node = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
const fmt = (value, digits = 2) => value.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
const pct = share => `${fmt(share * 100, 1)}%`;
const mtpa = cell => cell?.state === 'numeric' ? `${fmt(cell.value_ttpa / 1000)} Mtpa` : formatCapacity(cell);
const btn = (text, key, action, cls) => { const n = node('button', text, cls); n.type = 'button'; n.dataset.focusKey = key; n.addEventListener('click', action); return n; };
const svgNode = (tag, attrs, text) => { const n = document.createElementNS('http://www.w3.org/2000/svg', tag); Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, String(v))); if (text !== undefined) n.textContent = text; return n; };
const sourceName = 'GIST · June 2026 (V1) · reviewed local extract';

export function renderSiteExplorer({ plant, records, scopeName, state, onSelect, onHover, onProduct, onProcess, onYear, onClose, sourceDetails, onRoute = () => {}, onPin = () => {}, onSiteView = () => {} }) {
  const view = state.siteView || 'process';
  const root = node('article', undefined, `site-explorer-body map-site-model${state.route ? ' route-focused' : ''}`);
  if (plant.coordinate_accuracy === 'approximate') root.classList.add('approximate-location');
  root.dataset.view = view;
  const header = node('header', undefined, 'site-explorer-heading');
  const actions = node('div', undefined, 'site-actions');
  actions.append(btn('Close site', 'site-close', onClose, 'site-back'));
  const pinned = state.pins?.includes(plant.plant_id);
  const pin = btn(pinned ? 'Unpin site' : 'Pin for comparison', 'site-pin', () => onPin(plant.plant_id), 'site-pin');
  pin.disabled = !pinned && state.pins?.length === 2; pin.setAttribute('aria-pressed', String(Boolean(pinned))); actions.append(pin);
  header.append(node('p', `${plant.municipality || plant.country_area} · ${plant.country_area} · ${plant.coordinate_accuracy} location`, 'site-location'));
  header.append(node('h2', plant.plant_name.replace(/ steel plant$/i, '')));
  const contribution = siteContribution(plant, records);
  const scale = node('div', undefined, 'site-contribution-heading');
  scale.append(node('strong', contribution.own === null ? 'Not quantified' : `${fmt(contribution.own)} Mtpa`));
  scale.append(node('span', 'known operating crude-steel capacity'));
  if (contribution.share !== null) scale.append(node('b', `${pct(contribution.share)} of ${scopeName}`));
  header.append(scale); const persistent = node('div', undefined, 'site-persistent-heading'); persistent.append(actions,header); root.append(persistent);

  const context = node('section', undefined, 'site-scope-context');
  context.setAttribute('aria-label', 'Contribution to known operating capacity');
  const bar = node('div', undefined, 'site-contribution-bar');
  const ranked = rankCapacityPlants(records), quantified = ranked.filter(row => row.operating.knownMtpa > 0);
  for (const row of quantified) {
    const segment = btn('', `segment-${row.plant.plant_id}`, () => onSelect(row.plant.plant_id), `site-segment${row.plant.plant_id === plant.plant_id ? ' selected' : ''}`);
    segment.style.flexGrow = row.operating.knownMtpa;
    segment.setAttribute('aria-label', `${row.plant.plant_name}: ${fmt(row.operating.knownMtpa)} Mtpa, ${pct(row.share)} of known ${scopeName} operating capacity`);
    segment.title = segment.getAttribute('aria-label'); segment.dataset.plantId = row.plant.plant_id;
    segment.addEventListener('pointerenter', () => onHover([row.plant])); segment.addEventListener('pointerleave', () => onHover([]));
    segment.addEventListener('focus', () => onHover([row.plant])); segment.addEventListener('blur', () => onHover([]));
    bar.append(segment);
  }
  context.append(bar, node('p', contribution.total === null ? `${scopeName} · operating capacity is not quantified in this extract.` : `${scopeName} · ${fmt(contribution.total)} Mtpa known operating. Select a site segment; unquantified values are excluded.`, 'site-note'));
  root.append(context);
  const navigation = node('nav', undefined, 'site-views'); navigation.setAttribute('aria-label', 'Site investigation');
  for (const [value, label] of [['process', 'Production system'], ['projects', 'Project changes'], ['products', 'Products'], ['production', 'Production history'], ['source', 'Source details']]) {
    if (value === 'projects' && !plant.capacity.tranches.some(t => !t.status.startsWith('operating'))) continue;
    const button = btn(label, `view-${value}`, () => onSiteView(value)); button.setAttribute('aria-pressed', String(view === value)); navigation.append(button);
  }
  root.append(navigation);

  const system = node('section', undefined, 'site-system');
  const systemHead = node('div', undefined, 'site-section-heading');
  systemHead.append(node('h3', view === 'projects' ? 'Recorded project changes' : 'Operating process schematic'), node('span', 'Capacity snapshot · June 2026'));
  system.append(systemHead);
  const allBranches = processBranches(plant);
  const branches = view === 'projects' ? allBranches.filter(branch => !branch.status.startsWith('operating')) : allBranches.filter(branch => branch.status.startsWith('operating'));
  for (const branch of branches) {
    const row = node('div', undefined, `process-branch ${branch.status === 'cancelled' ? 'cancelled' : branch.status.startsWith('operating') ? 'operating' : 'other-status'}`);
    const status = node('div', undefined, 'process-status');
    status.append(node('strong', branch.status === 'cancelled' ? 'Cancelled project' : branch.status === 'operating' ? 'Operating' : branch.status), node('span', branch.status === 'cancelled' ? 'Separate from operating capacity' : 'Source status'));
    row.append(status);
    const track = node('div', undefined, `process-track${branch.paired ? ' paired' : ''}`);
    if (!branch.nodes.length) track.append(node('p', 'No usable route information for this source status.', 'site-note'));
    branch.nodes.forEach((stage, i) => {
      if (i && branch.paired) { const link = node('div', undefined, 'process-connection'); link.append(node('span', branch.nodes[i - 1].output), node('span', '→')); link.setAttribute('aria-label', 'Illustrative process connection, not a measured flow'); track.append(link); }
      const selected = state.processStage?.status === branch.status && state.processStage?.field === stage.field;
      const module = btn('', `process-${branch.status}-${stage.field}`, () => onProcess(selected ? null : { status: branch.status, field: stage.field }), `process-module${selected ? ' selected' : ''}`);
      module.setAttribute('aria-pressed', String(selected));
      module.append(node('span', `${stage.label} · ${stage.code}`, 'process-name'), node('strong', mtpa(stage.cell)), node('span', `${stage.material === 'iron' ? 'Ironmaking' : 'Crude-steel'} capacity`, 'process-output'));
      track.append(module);
    });
    row.append(track); system.append(row);
  }
  system.append(node('p', 'Schematic connection, not a measured flow. Iron and steel capacities are separate.', 'site-note'));
  if (state.processStage) {
    const branch = processBranches(plant).find(b => b.status === state.processStage.status);
    const stage = branch?.nodes.find(n => n.field === state.processStage.field);
    if (stage) {
      const detail = node('details', undefined, 'process-readout'); detail.append(node('summary', 'Inspect the selected stage'));
      detail.append(node('strong', `${stage.label} · ${branch.status}`), node('p', `${CAPACITY_FIELDS[stage.field]}: ${formatCapacity(stage.cell)}. ${sourceName}.`));
      if (stage.material === 'steel' && branch.status.startsWith('operating') && (stage.cell?.value_ttpa > 0 || stage.cell?.state === '>0')) {
        systemHead.append(btn('Show sites using this route', `show-route-${stage.field}`, () => onRoute(stage.field), 'route-action'));
      }
      detail.append(node('p', 'Status-specific capacity; individual furnace counts are not in this extract.'));
      if (branch.status === 'cancelled') detail.append(node('p', 'The cancellation date is not included in this extract. This status describes this recorded project; it does not rule out a future project.'));
      system.append(detail);
    }
  }
  if (view === 'process' || view === 'projects') {
    if (!branches.length) system.append(node('p', 'No operating route is documented in this extract. Use Project changes or Source details to inspect other source statuses.', 'site-note'));
    root.append(system);
    if (state.route) root.append(node('p', 'Matching operating routes are highlighted on the map. Select another site, or pin this site and a second one to compare.', 'site-route-context'));
  }

  const lower = node('div', undefined, 'site-temporal-products');
  const history = node('section', undefined, 'site-production');
  history.append(node('h3', 'What has this site actually produced?'), node('p', 'Reported crude-steel production · million tonnes', 'site-note'));
  const series = productionSeries(plant), max = Math.max(4, ...series.map(p => p.mt ?? 0));
  const chart = svgNode('svg', { viewBox: '0 0 550 130', role: 'img', 'aria-label': series.map(p => `${p.year}: ${p.mt === null ? p.state : fmt(p.mt, 1) + ' million tonnes'}`).join('; '), class: 'production-chart' });
  chart.append(svgNode('line', { x1: 22, y1: 110, x2: 528, y2: 110, class: 'production-baseline' }));
  chart.append(svgNode('text', { x: 5, y: 114, class: 'production-axis' }, '0'));
  const coords = series.map((p, i) => ({ ...p, x: 28 + i * 98, y: p.mt === null ? null : 110 - p.mt / max * 86 }));
  let previous = null;
  for (const point of coords) {
    if (point.mt === null) { chart.append(svgNode('text', { x: point.x, y: 89, 'text-anchor': 'middle', class: 'production-value' }, '—')); previous = null; continue; }
    if (previous) chart.append(svgNode('line', { x1: previous.x, y1: previous.y, x2: point.x, y2: point.y, class: 'production-line' }));
    chart.append(svgNode('circle', { cx: point.x, cy: point.y, r: state.productionYear === point.year ? 6 : 4, class: 'production-point' }));
    chart.append(svgNode('text', { x: point.x, y: point.y - 12, 'text-anchor': 'middle', class: 'production-value' }, fmt(point.mt, 1))); previous = point;
  }
  history.append(chart);
  const years = node('div', undefined, 'production-years');
  for (const point of series) { const year = btn(point.year, `year-${point.year}`, () => onYear(point.year)); year.setAttribute('aria-label', `${point.year}, ${point.mt === null ? point.state : fmt(point.mt, 1) + ' million tonnes'}. Inspect source value`); year.setAttribute('aria-pressed', String(state.productionYear === point.year)); years.append(year); }
  history.append(years);
  const point = series.find(p => p.year === state.productionYear);
  const readout = node('p', point ? `${point.year}: ${point.mt === null ? point.state : fmt(point.mt, 1) + ' million tonnes'}. ${sourceName}.` : 'Select a year for its value and source. Missing years remain gaps. Capacity for those historical years is not established.', 'site-note production-readout');
  readout.setAttribute('role', 'status'); history.append(readout); lower.append(history);

  const products = node('section', undefined, 'site-products'); products.append(node('h3', 'What products are documented?'));
  const categories = plant.product_category?.state === 'text' ? plant.product_category.values.join(' · ') : 'Product category not provided';
  products.append(node('p', `${categories} · source labels`, 'site-note'));
  const values = documentedProducts(plant);
  const groups = [ ['Rolling', ['hot rolled', 'cold rolled']], ['Coating', ['coated', 'galvanized']], ['Form / other', values.filter(p => !['hot rolled', 'cold rolled', 'coated', 'galvanized'].includes(p))] ];
  for (const [name, terms] of groups) {
    const present = terms.filter(term => values.includes(term)); if (!present.length) continue;
    const group = node('div', undefined, 'product-group'); group.append(node('span', name));
    for (const term of present) { const button = btn(term, `product-${term}`, () => onProduct(state.product === term ? null : term)); button.setAttribute('aria-pressed', String(state.product === term)); group.append(button); }
    products.append(group);
  }
  if (!values.length) products.append(node('p', `Products: ${plant.steel_products?.state ?? 'not provided'}.`, 'site-note'));
  products.append(node('p', 'Select a product to highlight sites with that exact source label in the same geographic scope.', 'site-note'));
  const sectors = plant.end_user_sectors;
  if (sectors?.state === 'text') { const details = node('details', undefined, 'site-sectors'); details.append(node('summary', `Documented end-use sectors (${sectors.values.length})`), node('p', sectors.values.join(' · '), 'site-note')); products.append(details); }
  lower.append(products);
  if (view === 'production') root.append(history);
  if (view === 'products') root.append(products);
  if (view === 'products' && state.product) {
    const matches = matchingProductPlants(records, state.product), related = node('section', undefined, 'product-matches');
    related.append(node('h3', `${matches.length} sites document “${state.product}”`), node('p', `${scopeName} · same capacity scope. Product documentation does not establish grades, qualification or delivery capability.`, 'site-note'));
    const list = node('div', undefined, 'product-match-list');
    for (const row of matches) { const b = btn(`${row.plant.plant_name} · ${row.operating.knownMtpa === null ? 'capacity unquantified' : fmt(row.operating.knownMtpa) + ' Mtpa'}`, `product-site-${row.plant.plant_id}`, () => onSelect(row.plant.plant_id)); b.setAttribute('aria-pressed', String(row.plant.plant_id === plant.plant_id)); b.addEventListener('pointerenter', () => onHover([row.plant])); b.addEventListener('pointerleave', () => onHover([])); b.addEventListener('focus', () => onHover([row.plant])); b.addEventListener('blur', () => onHover([])); list.append(b); }
    related.append(list); root.append(related);
  }
  if (view === 'projects') root.append(node('p', 'Next check: which route and implementation status support the offering being investigated?', 'site-next-check'));
  if (sourceDetails && view === 'source') { const source = node('section', undefined, 'site-source-details'); source.append(node('h3', 'Source details'), sourceDetails); root.append(source); }
  if (view === 'source') root.append(node('p', `${sourceName}. Source product labels do not identify customers or suppliers.`, 'site-note site-source-credit'));
  return root;
}

export function renderSiteComparison({ records, state, onSelect, onUnpin, onHover, onClose }) {
  const root = node('section', undefined, 'map-site-comparison');
  const rows = rankCapacityPlants(records).filter(row => state.pins.includes(row.plant.plant_id));
  const heading = node('div', undefined, 'site-comparison-heading');
  heading.append(node('h2', 'Two sites. One capacity scale.'), btn('Clear comparison', 'comparison-close', onClose)); root.append(heading);
  root.append(node('p', 'Known operating crude-steel capacity · Mtpa · June 2026', 'site-note'));
  const max = Math.max(1, ...rows.map(row => row.operating.knownMtpa ?? 0));
  const axis = node('div', undefined, 'site-compare-axis'); axis.append(node('span', '0'), node('span', `${fmt(max)} Mtpa`)); root.append(axis);
  for (const row of rows) {
    const item = node('div', undefined, 'site-compare-item'); item.dataset.plantId = row.plant.plant_id;
    const label = btn(`${String.fromCharCode(65+state.pins.indexOf(row.plant.plant_id))} · ${row.plant.plant_name}`, `compare-select-${row.plant.plant_id}`, () => onSelect(row.plant.plant_id), 'compare-site-name');
    label.addEventListener('pointerenter', () => onHover([row.plant])); label.addEventListener('pointerleave', () => onHover([])); label.addEventListener('focus', () => onHover([row.plant])); label.addEventListener('blur', () => onHover([]));
    const value = node('strong', row.operating.knownMtpa === null ? 'Not quantified' : `${fmt(row.operating.knownMtpa)} Mtpa`);
    const labels = node('div', undefined, 'site-compare-labels'); labels.append(label, value);
    const bar = node('div', undefined, 'site-compare-track'); const fill = node('span'); fill.style.width = `${(row.operating.knownMtpa ?? 0) / max * 100}%`; bar.append(fill);
    const nonnumeric = row.operating.contributing_rows - row.operating.numeric_rows;
    item.append(labels, bar, node('p', `${row.share === null ? 'Share unavailable' : pct(row.share) + ' of the scope’s known operating component'}${nonnumeric ? ` · ${nonnumeric} non-numeric source value(s)` : ''}`, 'site-note'));
    item.append(btn('Unpin', `compare-unpin-${row.plant.plant_id}`, () => onUnpin(row.plant.plant_id), 'compare-unpin')); root.append(item);
  }
  root.append(node('p', 'Capacity is not production, availability or a supplier qualification. Both sites remain marked on the map.', 'site-note'));
  return root;
}
