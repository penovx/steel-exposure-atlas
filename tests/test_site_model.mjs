import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { processBranches, productionSeries, matchingProductPlants, siteContribution } from '../prototype/site-model.mjs';
import { CAPACITY_FIELDS } from '../prototype/gist-adapter.mjs';

// Original, wholly fictional examples. No third-party extract is needed for
// these semantic tests, and no real plant data is copied into a fixture.
const cell = (state, value_ttpa = null) => ({state, value_ttpa});
const tranche = (status, total, overrides = {}) => ({
  ...Object.fromEntries(Object.keys(CAPACITY_FIELDS).map(field => [field, cell('N/A')])),
  status, crude_steel_capacity_ttpa: total, equipment: {state: 'unknown', values: []}, ...overrides,
});
const fictionalPlant = (id, tranches, overrides = {}) => ({
  plant_id: id, plant_name: `Fictional Forge ${id}`, country_area: 'Exampleland', region: 'Example region',
  capacity: {tranches}, steel_products: {state: 'unknown', values: []}, ...overrides,
});

test('process branches retain their source status and cannot borrow plant-level equipment', () => {
  const record = fictionalPlant('Alpha', [
    tranche('cancelled', cell('numeric', 600), {dri_iron_capacity_ttpa: cell('numeric', 700), eaf_steel_capacity_ttpa: cell('numeric', 600)}),
    tranche('operating', cell('numeric', 2000), {bf_iron_capacity_ttpa: cell('numeric', 1500), bof_steel_capacity_ttpa: cell('numeric', 2000), eaf_steel_capacity_ttpa: cell('unknown')}),
  ], {main_production_equipment: {state: 'text', values: ['BF', 'BOF', 'DRI', 'EAF', 'IF']}});
  const before = structuredClone(record), branches = processBranches(record);
  assert.deepEqual(branches.map(b => [b.status, b.nodes.map(n => n.code)]), [['operating', ['BF', 'BOF']], ['cancelled', ['DRI', 'EAF']]]);
  assert.equal(branches[0].nodes[0].cell.value_ttpa, 1500);
  assert.equal(branches[0].nodes[1].cell.value_ttpa, 2000);
  assert.equal(branches[1].nodes[0].cell.value_ttpa, 700);
  assert.equal(branches[1].nodes[1].cell.value_ttpa, 600);
  assert.deepEqual(record, before, 'Inspection must not reorder or rewrite source tranches');
});

test('status-specific equipment and unquantified positive route capacity retain their source states', () => {
  const record = fictionalPlant('Unquantified', [tranche('operating', cell('unknown'), {
    eaf_steel_capacity_ttpa: cell('>0'), if_steel_capacity_ttpa: cell('unknown'),
    equipment: {state: 'text', values: ['IF']},
  })]);
  const nodes = processBranches(record)[0].nodes;
  assert.deepEqual(nodes.map(node => [node.code, node.cell.state, node.cell.value_ttpa]), [['EAF', '>0', null], ['IF', 'unknown', null]]);
  assert.equal(processBranches(fictionalPlant('No operating route', [tranche('operating', cell('N/A'))]))[0].nodes.length, 0);
});

test('production missingness and nonnumeric states remain gaps while reported zero is numeric', () => {
  const record = fictionalPlant('History', [], {production: {crude_steel_ttpa: {
    '2019': cell('numeric', 1200), '2021': cell('numeric', 0), '2022': cell('unknown'),
    '2023': cell('N/A'), '2024': cell('>0'), '2025': cell('numeric', 8888),
  }}});
  const series = productionSeries(record);
  assert.deepEqual(series.map(point => point.year), ['2019', '2020', '2021', '2022', '2023', '2024']);
  assert.deepEqual(series.map(point => point.mt), [1.2, null, 0, null, null, null]);
  assert.deepEqual(series.map(point => point.state), ['numeric', 'not provided', 'numeric', 'unknown', 'N/A', '>0']);
  assert.ok(productionSeries(fictionalPlant('No production', [])).every(point => point.mt === null && point.state === 'not provided'));
  const blank = fictionalPlant('Blank production', [], {production: {crude_steel_ttpa: {'2019': cell('blank')}}});
  assert.deepEqual(productionSeries(blank)[0], {year: '2019', state: 'blank', mt: null});
});

test('contribution denominator excludes other statuses, route breakdowns and iron capacity', () => {
  const alpha = fictionalPlant('Alpha', [
    tranche('operating', cell('numeric', 1000), {eaf_steel_capacity_ttpa: cell('numeric', 1000), iron_capacity_ttpa: cell('numeric', 9000)}),
    tranche('construction', cell('numeric', 7000)), tranche('cancelled', cell('numeric', 8000)),
  ]);
  const beta = fictionalPlant('Beta', [tranche('operating pre-retirement', cell('numeric', 3000)), tranche('retired', cell('numeric', 6000))]);
  const unknown = fictionalPlant('Unknown', [tranche('operating', cell('unknown'))]);
  const positive = fictionalPlant('Unquantified positive', [tranche('operating', cell('>0'))]);
  const scope = [alpha, beta, unknown, positive];
  assert.deepEqual(siteContribution(alpha, scope), {own: 1, total: 4, share: .25});
  assert.deepEqual(siteContribution(beta, scope), {own: 3, total: 4, share: .75});
  assert.equal(siteContribution(unknown, scope).own, null); assert.equal(siteContribution(unknown, scope).share, null);
  assert.equal(siteContribution(positive, scope).own, null); assert.equal(siteContribution(positive, scope).share, null);
  assert.equal(siteContribution(unknown, [unknown, positive]).share, null);
});

test('exact product matching preserves the supplied scope and whole-scope capacity contributions', () => {
  const productPlant = (id, value, token, state = 'text') => fictionalPlant(id, [tranche('operating', cell('numeric', value))], {steel_products: {state, values: [token]}});
  const alpha = productPlant('Alpha', 1000, 'galvanized'), beta = productPlant('Beta', 3000, 'galvanised');
  const caseVariant = productPlant('Gamma', 2000, 'Galvanized'), unknown = productPlant('Delta', 4000, 'galvanized', 'unknown');
  const scope = [alpha, beta, caseVariant, unknown];
  const results = matchingProductPlants(scope, 'galvanized');
  assert.deepEqual(results.map(row => row.plant.plant_id), ['Alpha']);
  assert.equal(results[0].share, .1, 'Product highlighting must not shrink the capacity denominator to its matches');
  assert.deepEqual(matchingProductPlants(scope, 'galvanised').map(row => row.plant.plant_id), ['Beta']);
  assert.equal(matchingProductPlants(scope, 'galvan').length, 0);
  assert.equal(matchingProductPlants(scope, ' galvanized').length, 0);
  assert.equal(matchingProductPlants(scope, '').length, 0);
  assert.equal(matchingProductPlants([beta, caseVariant, unknown], 'galvanized').length, 0);
});

test('no numeric scope total stays null while a reported zero remains numeric', () => {
  const unknown = fictionalPlant('Unknown denominator', [tranche('operating', cell('unknown'))]);
  const positive = fictionalPlant('Positive denominator', [tranche('operating', cell('>0'))]);
  const zero = fictionalPlant('Reported zero', [tranche('operating', cell('numeric', 0))]);
  assert.deepEqual(siteContribution(unknown, [unknown, positive]), {own: null, total: null, share: null});
  assert.deepEqual(siteContribution(zero, [zero, unknown]), {own: 0, total: 0, share: null});
  assert.deepEqual(siteContribution(unknown, []), {own: null, total: null, share: null});
});

test('a site outside the supplied population cannot receive a share of that population', () => {
  const selected = fictionalPlant('Outside scope', [tranche('operating', cell('numeric', 5000))]);
  const included = fictionalPlant('Inside scope', [tranche('operating', cell('numeric', 1000))]);
  assert.deepEqual(siteContribution(selected, [included]), {own: 5, total: 1, share: null});
});

// These release readbacks add evidence when the reviewed local file is present.
// Missing local data is expected in CI; malformed or unreadable supplied files
// still fail instead of being silently classified as absent.
let plants;
try {
  plants = JSON.parse(readFileSync(new URL('../public/data/gist-plants.v1.json', import.meta.url), 'utf8')).plants;
  assert.ok(Array.isArray(plants), 'A supplied GIST artifact must contain a plants array');
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}
const localOnly = {skip: !plants && 'Reviewed local GIST artifact is intentionally not bundled.'};
const bremen = plants?.find(p => p.plant_id === 'P100000120426');
const germany = plants?.filter(p => p.country_area === 'Germany');

test('local Bremen operating and cancelled process branches match the reviewed extract', localOnly, () => {
  const branches = processBranches(bremen);
  assert.deepEqual(branches.map(b => [b.status, b.nodes.map(n => n.code)]), [['operating', ['BF', 'BOF']], ['cancelled', ['DRI', 'EAF']]]);
  assert.deepEqual(branches.map(b => b.nodes.map(n => n.cell.value_ttpa)), [[3900, 3960], [2000, 1400]]);
});
test('local Bremen production is the reviewed 2019–2024 series', localOnly, () => {
  assert.deepEqual(productionSeries(bremen).map(p => p.mt), [3.1, 2.8, 3.3, 3.1, 2.9, 3.1]);
});
test('local Bremen contribution uses the known German operating crude-steel component', localOnly, () => {
  const c = siteContribution(bremen, germany);
  assert.equal(c.own, 3.96); assert.ok(Math.abs(c.total - 44.72) < 1e-10); assert.ok(Math.abs(c.share - 3960 / 44720) < 1e-10);
});
