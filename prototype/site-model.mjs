import { plantCapacity, rankCapacityPlants, scopeCapacitySummary } from './gist-adapter.mjs';

// Display vocabulary for reviewed structured fields; no plant-level equipment
// summary is used to assign a route to an operating or cancelled status.
export const PROCESS_FIELDS = Object.freeze([
  { field: 'bf_iron_capacity_ttpa', code: 'BF', label: 'Blast furnace', output: 'Hot metal', material: 'iron' },
  { field: 'dri_iron_capacity_ttpa', code: 'DRI', label: 'Direct reduction', output: 'Direct-reduced iron', material: 'iron' },
  { field: 'other_iron_capacity_ttpa', code: 'Iron other/unspecified', label: 'Other ironmaking', output: 'Iron', material: 'iron' },
  { field: 'bof_steel_capacity_ttpa', code: 'BOF', label: 'Oxygen steelmaking', output: 'Crude steel', material: 'steel' },
  { field: 'eaf_steel_capacity_ttpa', code: 'EAF', label: 'Electric arc furnace', output: 'Crude steel', material: 'steel' },
  { field: 'if_steel_capacity_ttpa', code: 'IF', label: 'Induction furnace', output: 'Crude steel', material: 'steel' },
  { field: 'other_steel_capacity_ttpa', code: 'Steel other/unspecified', label: 'Other steelmaking', output: 'Crude steel', material: 'steel' },
]);
const ORDER = ['operating', 'operating pre-retirement', 'construction', 'announced', 'cancelled', 'mothballed', 'mothballed pre-retirement', 'retired'];

export function processBranches(plant) {
  return [...plant.capacity.tranches].sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status)).map(tranche => {
    const nodes = PROCESS_FIELDS.filter(field => {
      const cell = tranche[field.field];
      return cell?.state === 'numeric' && cell.value_ttpa > 0 || cell?.state === '>0'
        || tranche.equipment?.state === 'text' && tranche.equipment.values.includes(field.code);
    }).map(field => ({ ...field, cell: tranche[field.field] }));
    const paired = nodes.length === 2 && (
      nodes[0].code === 'BF' && nodes[1].code === 'BOF'
      || nodes[0].code === 'DRI' && nodes[1].code === 'EAF');
    return { status: tranche.status, nodes, paired, tranche };
  });
}

/** Missing observations stay explicit and break the drawn production line. */
export function productionSeries(plant) {
  const source = plant.production?.crude_steel_ttpa;
  return Array.from({ length: 6 }, (_, i) => {
    const year = String(2019 + i), cell = source?.[year];
    const numeric = cell?.state === 'numeric' && Number.isFinite(cell.value_ttpa) && cell.value_ttpa >= 0;
    return { year, state: cell?.state ?? 'not provided', mt: numeric ? cell.value_ttpa / 1000 : null };
  });
}

export function documentedProducts(plant) {
  return plant.steel_products?.state === 'text' ? [...plant.steel_products.values] : [];
}

// Exact source-token equality only. No similarity, substitution or supply claim.
export function matchingProductPlants(records, product) {
  return product ? rankCapacityPlants(records).filter(row => documentedProducts(row.plant).includes(product)) : [];
}

export function siteContribution(plant, records) {
  const own = plantCapacity(plant).knownMtpa;
  const total = scopeCapacitySummary(records).operating.knownMtpa;
  const inScope = records.some(record => record.plant_id === plant.plant_id);
  return { own, total, share: inScope && own !== null && total > 0 ? own / total : null };
}
