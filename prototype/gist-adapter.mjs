// Bounded read adapter for the reviewed June 2026 (V1) extract.
export const GIST_SHA256 = '6D9C2CBAC1DBC25068AF5DD69736FF7E44D6074E220BDB5880054487F28A3EC3';
export const SOURCE_SHA256 = 'A5768B59CD7E6CEC217692AE45EDA80EA70AAB1666AEF74332CC1B41DD5338EB';
export const STATUS_BUCKETS = Object.freeze({
  operating: ['operating', 'operating pre-retirement'],
  development: ['announced', 'construction'],
  mothballed: ['mothballed', 'mothballed pre-retirement'],
  closed_or_cancelled: ['retired', 'cancelled'],
});
export const CAPACITY_FIELDS = Object.freeze({
  crude_steel_capacity_ttpa: 'Crude steel total', iron_capacity_ttpa: 'Iron total',
  bof_steel_capacity_ttpa: 'BOF steel', eaf_steel_capacity_ttpa: 'EAF steel',
  if_steel_capacity_ttpa: 'IF steel', other_steel_capacity_ttpa: 'Other steel',
  bf_iron_capacity_ttpa: 'BF iron', dri_iron_capacity_ttpa: 'DRI iron', other_iron_capacity_ttpa: 'Other iron',
});
const STEEL_ROUTES = Object.freeze([
  {field: 'bof_steel_capacity_ttpa', label: 'BOF', equipment: 'BOF'},
  {field: 'eaf_steel_capacity_ttpa', label: 'EAF', equipment: 'EAF'},
  {field: 'if_steel_capacity_ttpa', label: 'IF', equipment: 'IF'},
  {field: 'other_steel_capacity_ttpa', label: 'Other / unspecified', equipment: 'Steel other/unspecified'},
]);
const STATES = ['numeric', 'unknown', 'N/A', '>0', 'blank'];
const EMPTY_SITE_DEPTH = Object.freeze({product: null, processStage: null, productionYear: null, siteView: 'process'});
const SITE_VIEWS = Object.freeze(['process', 'projects', 'products', 'production', 'source']);
export function validatePinnedPayload(payload, digest) {
  if (String(digest).toUpperCase() !== GIST_SHA256) throw new Error('The local GIST file does not match the reviewed extract SHA-256.');
  if (payload?.meta?.schema !== 'steel-exposure-atlas/gist-plant-v1.0') throw new Error('Unexpected GIST schema.');
  if (payload.meta.source_sha256 !== SOURCE_SHA256 || payload.meta.source_release !== 'June 2026 (V1)' || payload.meta.licence !== 'CC BY 4.0') throw new Error('Unexpected source identity or licence.');
  if (JSON.stringify(payload.meta.production_years) !== JSON.stringify(['2019', '2020', '2021', '2022', '2023', '2024'])) throw new Error('Unexpected production years.');
  if (!Array.isArray(payload.plants) || payload.plants.length !== 1293) throw new Error('Expected 1,293 plants in this pinned release.');
  const ids = new Set(); let rows = 0; let exact = 0; let approximate = 0;
  for (const plant of payload.plants) {
    if (!plant.plant_id || ids.has(plant.plant_id)) throw new Error('Missing or duplicate plant identity.');
    ids.add(plant.plant_id);
    if (!Number.isFinite(plant.latitude) || !Number.isFinite(plant.longitude) || Math.abs(plant.latitude) > 90 || Math.abs(plant.longitude) > 180) throw new Error('Invalid plant coordinates.');
    if (plant.coordinate_accuracy === 'exact') exact++;
    else if (plant.coordinate_accuracy === 'approximate') approximate++;
    else throw new Error('Missing coordinate accuracy.');
    if (!Array.isArray(plant.capacity?.tranches)) throw new Error('Missing source tranches.');
    const statuses = new Set();
    for (const tranche of plant.capacity.tranches) {
      if (!Object.values(STATUS_BUCKETS).flat().includes(tranche.status) || statuses.has(tranche.status)) throw new Error('Unknown or repeated source status.');
      statuses.add(tranche.status); rows++;
      for (const key of Object.keys(CAPACITY_FIELDS)) {
        const value = tranche[key];
        if (!value || !STATES.includes(value.state)) throw new Error('Unrecognised capacity state.');
        if (value.state === 'numeric' ? !Number.isFinite(value.value_ttpa) || value.value_ttpa < 0 : value.value_ttpa !== null) throw new Error('Capacity value and state disagree.');
      }
    }
  }
  if (rows !== 1845 || exact !== 1141 || approximate !== 152) throw new Error('Release-specific counts do not match.');
  return payload;
}
export function scopePlants(plants, scope) {
  return plants.filter(p => (!scope.region || p.region === scope.region) && (!scope.country || p.country_area === scope.country));
}
export function searchPlants(plants, query) {
  const term = query.trim().toLocaleLowerCase('en');
  return plants.filter(p => !term || [p.plant_name, p.plant_id, p.municipality].some(v => String(v ?? '').toLocaleLowerCase('en').includes(term)));
}
export function valuesFor(plants, field) {
  return [...new Set(plants.map(p => p[field]).filter(v => typeof v === 'string' && v.trim()))].sort((a, b) => a.localeCompare(b, 'en'));
}
export function aggregateCapacity(plants, bucket, field = 'crude_steel_capacity_ttpa') {
  if (!STATUS_BUCKETS[bucket] || !Object.hasOwn(CAPACITY_FIELDS, field)) throw new Error('An explicit reviewed status bucket and capacity field are required.');
  const result = { known_numeric_sum_ttpa: 0, contributing_rows: 0, numeric_rows: 0, has_unquantified_positive: false, states: Object.fromEntries(STATES.map(s => [s, 0])) };
  for (const plant of plants) for (const tranche of plant.capacity.tranches) {
    if (!STATUS_BUCKETS[bucket].includes(tranche.status)) continue;
    const cell = tranche[field];
    if (!cell || !STATES.includes(cell.state)) throw new Error('Invalid source value state.');
    if (cell.state === 'numeric' ? !Number.isFinite(cell.value_ttpa) || cell.value_ttpa < 0 : cell.value_ttpa !== null) throw new Error('Capacity value and state disagree.');
    result.contributing_rows++; result.states[cell.state]++;
    if (cell.state === 'numeric') { result.known_numeric_sum_ttpa += cell.value_ttpa; result.numeric_rows++; }
    if (cell.state === '>0') result.has_unquantified_positive = true;
  }
  return result;
}

/** Sum only source crude-steel totals, retaining absence and every source state. */
export function plantCapacity(plant, bucket = 'operating') {
  const summary = aggregateCapacity([plant], bucket);
  return {
    ...summary,
    knownMtpa: summary.numeric_rows ? summary.known_numeric_sum_ttpa / 1000 : null,
    noSourceTranches: summary.contributing_rows === 0,
    sourceStatuses: plant.capacity.tranches.filter(row => STATUS_BUCKETS[bucket].includes(row.status)).map(row => row.status),
  };
}

/**
 * A route label needs positive operating route capacity or an explicit operating
 * equipment label. Plant-level equipment may also describe development, so is
 * not used here. An empty result means no evidenced route, not no technology.
 * Route values are breakdowns and must never be added to crude-steel totals.
 */
export function operatingRoutes(plant) {
  const operating = plant.capacity.tranches.filter(row => STATUS_BUCKETS.operating.includes(row.status));
  return STEEL_ROUTES.flatMap(route => {
    const summary = aggregateCapacity([plant], 'operating', route.field);
    const capacityEvidence = summary.known_numeric_sum_ttpa > 0 || summary.has_unquantified_positive;
    const equipmentEvidence = operating.some(row => row.equipment?.state === 'text' && row.equipment.values.includes(route.equipment));
    if (!capacityEvidence && !equipmentEvidence) return [];
    return [{
      field: route.field, label: route.label, ...summary,
      knownMtpa: summary.numeric_rows ? summary.known_numeric_sum_ttpa / 1000 : null,
      evidence: [...(capacityEvidence ? ['route-capacity'] : []), ...(equipmentEvidence ? ['operating-equipment'] : [])],
    }];
  });
}

/** Whole analytical scope only; camera, search and visible rows are not inputs. */
export function scopeCapacitySummary(plants) {
  const summaryFor = bucket => {
    const summary = aggregateCapacity(plants, bucket);
    return {...summary, knownMtpa: summary.numeric_rows ? summary.known_numeric_sum_ttpa / 1000 : null};
  };
  return {plantCount: plants.length, operating: summaryFor('operating'), development: summaryFor('development')};
}

/**
 * Rank known numeric components, not total plant capacity. share is a fraction
 * of the entire supplied scope's known operating component; it is null when
 * that plant has no numeric value or the known denominator is not positive.
 * Call this before a display-only search/filter to keep contributions stable.
 */
export function rankCapacityPlants(plants) {
  const denominator = scopeCapacitySummary(plants).operating.knownMtpa;
  return plants.map(plant => {
    const operating = plantCapacity(plant);
    return {
      plant, operating, development: plantCapacity(plant, 'development'), routes: operatingRoutes(plant),
      share: operating.knownMtpa !== null && denominator > 0 ? operating.knownMtpa / denominator : null,
    };
  }).sort((a, b) => {
    if (a.operating.knownMtpa === null && b.operating.knownMtpa !== null) return 1;
    if (b.operating.knownMtpa === null && a.operating.knownMtpa !== null) return -1;
    return (b.operating.knownMtpa ?? 0) - (a.operating.knownMtpa ?? 0)
      || String(a.plant.plant_name ?? a.plant.plant_id).localeCompare(String(b.plant.plant_name ?? b.plant.plant_id), 'en')
      || String(a.plant.plant_id).localeCompare(String(b.plant.plant_id), 'en');
  });
}

/** Exact area encoding: no minimum radius that would inflate small values. */
export function capacityRadius(knownMtpa, maxMtpa, maxRadius = 28) {
  if (knownMtpa === null || knownMtpa === undefined) return null;
  if (!Number.isFinite(knownMtpa) || knownMtpa < 0 || !Number.isFinite(maxMtpa) || maxMtpa < 0
    || !Number.isFinite(maxRadius) || maxRadius <= 0 || knownMtpa > maxMtpa) throw new Error('Invalid capacity symbol scale.');
  return knownMtpa === 0 ? 0 : Math.sqrt(knownMtpa / maxMtpa) * maxRadius;
}
export function formatCapacity(cell) {
  if (cell?.state === 'numeric') return `${cell.value_ttpa.toLocaleString('en-US', {maximumFractionDigits: 3})} kt/year`;
  if (cell?.state === '>0') return '>0 · unquantified positive';
  if (cell?.state === 'blank') return 'Blank source cell';
  if (cell?.state === 'N/A') return 'N/A';
  if (cell?.state === 'unknown') return 'Unknown';
  return 'Not provided';
}
export function usableOwnerId(value) { return typeof value === 'string' && /^E\d+$/.test(value) ? value : null; }
export function sourceText(value) { return value === '' || value === null || value === undefined ? 'Blank source cell' : String(value); }
export function initialEvidenceState(plants) {
  const germany = plants.find(p => p.country_area === 'Germany');
  return { question: 'tracked-capacity', scope: {region: germany?.region ?? '', country: germany ? 'Germany' : ''}, layers: {plants: true}, selectedId: null, hoverId: null, camera: {x: 0, y: 150, width: 1200, height: 490}, query: '', pins: [], comparisonVisible: false, route: null, perspective: 'capacity', ...EMPTY_SITE_DEPTH };
}
export function evidenceReducer(state, action, plants) {
  if (action.type === 'clearPins') return {...state, pins: [], comparisonVisible: false};
  if (action.type === 'compare') return state.pins.length === 2 ? {...state, comparisonVisible: true} : state;
  if (action.type === 'camera') return {...state, camera: {...action.camera}};
  if (action.type === 'hover') return {...state, hoverId: action.id};
  if (action.type === 'route') return action.value === null || STEEL_ROUTES.some(route => route.field === action.value) ? {...state, route: action.value} : state;
  if (action.type === 'perspective') return ['capacity', 'routes'].includes(action.value) ? {...state, perspective: action.value} : state;
  if (action.type === 'siteView') return SITE_VIEWS.includes(action.value) ? {...state, siteView: action.value} : state;
  if (action.type === 'pin') {
    if (!scopePlants(plants, state.scope).some(plant => plant.plant_id === action.id)) return state;
    if (state.pins.includes(action.id)) return {...state, pins: state.pins.filter(id => id !== action.id), comparisonVisible: false};
    return state.pins.length < 2 ? {...state, pins: [...state.pins, action.id], comparisonVisible: state.pins.length === 1} : state;
  }
  if (action.type === 'unpin') return {...state, pins: state.pins.filter(id => id !== action.id), comparisonVisible: false};
  if (action.type === 'product') return {...state, product: action.value ?? null};
  if (action.type === 'process') return {...state, processStage: action.value ? {...action.value} : null};
  if (action.type === 'year') return {...state, productionYear: action.value ?? null};
  if (action.type === 'search') {
    const matches = new Set(searchPlants(scopePlants(plants, state.scope), action.query).map(plant => plant.plant_id));
    return {...state, query: action.query, selectedId: matches.has(state.selectedId) ? state.selectedId : null, hoverId: matches.has(state.hoverId) ? state.hoverId : null, ...(!matches.has(state.selectedId) ? EMPTY_SITE_DEPTH : {})};
  }
  if (action.type === 'clear') return {...state, selectedId: null, hoverId: null, ...EMPTY_SITE_DEPTH};
  if (action.type === 'layer') return {...state, layers: {...state.layers, plants: action.visible}};
  if (action.type === 'country') {
    const found = plants.find(p => p.country_area === action.country);
    if (action.country !== '' && !found) return state;
    return {...state, scope: {region: found?.region ?? state.scope.region, country: found?.country_area ?? ''}, selectedId: null, hoverId: null, query: '', pins: [], comparisonVisible: false, ...EMPTY_SITE_DEPTH};
  }
  if (action.type === 'region') {
    if (action.region !== '' && !plants.some(plant => plant.region === action.region)) return state;
    return {...state, scope: {region: action.region, country: ''}, selectedId: null, hoverId: null, query: '', pins: [], comparisonVisible: false, ...EMPTY_SITE_DEPTH};
  }
  if (action.type === 'select') {
    const selectedId = scopePlants(plants, state.scope).some(p => p.plant_id === action.id) ? action.id : null;
    return {...state, selectedId, comparisonVisible: false, ...(selectedId !== state.selectedId ? EMPTY_SITE_DEPTH : {})};
  }
  return state;
}
