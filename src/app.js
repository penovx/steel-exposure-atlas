import { renderCountries, renderGraticule, renderPlants } from './map/render-world.js';

const LOCAL_BASEMAP = './public/data/ne_110m_admin_0_countries.v5.1.1.geojson';
const DEVELOPMENT_BASEMAP = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.1/geojson/ne_110m_admin_0_countries.geojson';
const LOCAL_GIST = './public/data/gist-plants.v1.json';
const EXPECTED_GIST_SCHEMA = 'steel-exposure-atlas/gist-plant-v1.0';

const graticuleLayer = document.querySelector('#graticule-layer');
const countryLayer = document.querySelector('#country-layer');
const plantLayer = document.querySelector('#plant-layer');
const mapStatus = document.querySelector('#map-status');
const mapCredit = document.querySelector('#map-credit');
const mapKicker = document.querySelector('#map-kicker');
const mapHeading = document.querySelector('#map-heading');
const mapDescription = document.querySelector('#map-description');
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const productionMode = document.querySelector('#production-mode');
const plantInspector = document.querySelector('#plant-inspector');
const aboutButton = document.querySelector('#about-button');
const aboutPanel = document.querySelector('#about-panel');
const aboutClose = document.querySelector('#about-close');

let basemapFeatureCount = 0;
let plantCount = 0;

renderGraticule(graticuleLayer);
loadBasemap();
loadPlantData();

for (const button of modeButtons) {
  button.addEventListener('click', () => setMode(button.dataset.mode));
}

aboutButton.addEventListener('click', () => {
  aboutPanel.showModal();
  aboutButton.setAttribute('aria-expanded', 'true');
});

aboutClose.addEventListener('click', () => aboutPanel.close());
aboutPanel.addEventListener('close', () => aboutButton.setAttribute('aria-expanded', 'false'));

async function loadBasemap() {
  try {
    const { data, source } = await loadBasemapData();
    basemapFeatureCount = renderCountries(countryLayer, data);
    mapStatus.textContent = `${basemapFeatureCount} country features · ${source}`;
  } catch (error) {
    mapStatus.classList.add('is-error');
    mapStatus.textContent = 'Basemap not available. Run the approved data fetch step locally.';
    console.error(error);
  }
}

async function loadPlantData() {
  try {
    const response = await fetch(LOCAL_GIST);
    if (!response.ok) {
      productionMode.disabled = true;
      productionMode.querySelector('small').textContent = 'local extract required';
      return;
    }

    const payload = await response.json();
    validatePlantPayload(payload);
    plantCount = renderPlants(plantLayer, payload.plants, { onSelect: showPlantDetail });
    productionMode.disabled = false;
    productionMode.querySelector('small').textContent = `${plantCount.toLocaleString('en-US')} plants`;
    setPlantPlaceholder('Select Production, then choose a plant on the map.');
  } catch (error) {
    productionMode.disabled = true;
    productionMode.querySelector('small').textContent = 'validation failed';
    setPlantPlaceholder('The local steel-plant extract failed validation and was not shown.');
    console.error(error);
  }
}

function validatePlantPayload(payload) {
  if (payload?.meta?.schema !== EXPECTED_GIST_SCHEMA) {
    throw new Error(`Unexpected GIST schema: ${payload?.meta?.schema ?? '(missing)'}`);
  }
  if (!Array.isArray(payload.plants) || payload.plants.length === 0) {
    throw new Error('GIST extract does not contain a non-empty plants array.');
  }
  if (payload.meta.production_years?.includes('2025')) {
    throw new Error('The v1 plant extract unexpectedly includes 2025 in the published production years.');
  }
}

function setMode(mode) {
  if (mode === 'production' && productionMode.disabled) return;

  for (const button of modeButtons) {
    button.classList.toggle('is-active', button.dataset.mode === mode);
  }

  const productionActive = mode === 'production';
  plantLayer.hidden = !productionActive;

  if (productionActive) {
    mapKicker.textContent = 'STEEL PRODUCTION SITES';
    mapHeading.textContent = 'Where steel capacity actually sits.';
    mapDescription.textContent = 'Each point is a reviewed Global Iron and Steel Tracker plant record. Approximate coordinates remain visibly distinct; plant proximity does not imply a sourcing relationship.';
    mapStatus.textContent = `${plantCount.toLocaleString('en-US')} steel plants · GIST June 2026 (V1) · transformed extract`;
    mapCredit.textContent = 'Natural Earth · Steel data: Global Energy Monitor · CC BY 4.0';
    return;
  }

  mapKicker.textContent = 'PUBLIC DATA, CONNECTED';
  mapHeading.textContent = 'See the structure before judging the risk.';
  mapDescription.textContent = 'The atlas will connect production sites, trade patterns, water-stress indicators and legal-entity relationships without turning them into a single black-box score.';
  mapStatus.textContent = basemapFeatureCount
    ? `${basemapFeatureCount} country features · local reviewed file`
    : 'Loading approved basemap…';
  mapCredit.textContent = 'Natural Earth 1:110m · v5.1.1';
}

function showPlantDetail(plant) {
  plantInspector.replaceChildren();
  plantInspector.append(label('PLANT DETAIL'));

  const heading = document.createElement('h3');
  heading.textContent = plant.plant_name || plant.plant_id || 'Unnamed plant';
  plantInspector.append(heading);

  const location = [plant.municipality, plant.subnational_unit, plant.country_area]
    .filter((value) => value && String(value).toLowerCase() !== 'unknown')
    .join(', ');
  plantInspector.append(detailRow('Location', location || 'Not reported'));
  plantInspector.append(detailRow('Owner', displaySourceValue(plant.owner_name)));
  plantInspector.append(detailRow('Parent', displaySourceValue(plant.parent_display)));
  plantInspector.append(detailRow('Coordinates', plant.coordinate_accuracy === 'approximate' ? 'Approximate' : 'Exact'));

  const operatingCapacity = plant.capacity?.summary?.operating?.crude_steel_capacity;
  if (operatingCapacity) {
    const known = Number(operatingCapacity.known_numeric_sum_ttpa ?? 0);
    const formatted = known > 0 ? `${(known / 1000).toLocaleString('en-US', { maximumFractionDigits: 2 })} Mtpa` : 'No numeric value reported';
    plantInspector.append(detailRow('Known operating crude capacity', formatted));

    if (operatingCapacity.has_unknown || operatingCapacity.has_unquantified_positive) {
      const note = document.createElement('p');
      note.className = 'plant-data-note';
      note.textContent = 'Some operating capacity is unknown or only reported as greater than zero, so the numeric value is not a complete total.';
      plantInspector.append(note);
    }
  }
}

function setPlantPlaceholder(text) {
  plantInspector.replaceChildren(label('PLANT DETAIL'));
  const paragraph = document.createElement('p');
  paragraph.className = 'plant-placeholder';
  paragraph.textContent = text;
  plantInspector.append(paragraph);
}

function label(text) {
  const paragraph = document.createElement('p');
  paragraph.className = 'panel-label';
  paragraph.textContent = text;
  return paragraph;
}

function detailRow(name, value) {
  const row = document.createElement('div');
  row.className = 'plant-detail-row';

  const key = document.createElement('span');
  key.textContent = name;
  const content = document.createElement('strong');
  content.textContent = value;

  row.append(key, content);
  return row;
}

function displaySourceValue(value) {
  if (value === null || value === undefined || value === '') return 'Not reported';
  const text = String(value).trim();
  return text.toLowerCase() === 'unknown' ? 'Unknown in source' : text;
}

async function loadBasemapData() {
  const localResponse = await fetch(LOCAL_BASEMAP);
  if (localResponse.ok) {
    return { data: await localResponse.json(), source: 'local reviewed file' };
  }

  if (!isDevelopmentHost()) {
    throw new Error(`Reviewed local basemap missing (${localResponse.status}).`);
  }

  const fallbackResponse = await fetch(DEVELOPMENT_BASEMAP);
  if (!fallbackResponse.ok) {
    throw new Error(`Development basemap fallback failed (${fallbackResponse.status}).`);
  }

  return { data: await fallbackResponse.json(), source: 'pinned development fallback' };
}

function isDevelopmentHost() {
  return ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
}
