import { project, renderCountries, renderGraticule, renderPlants } from './map/render-world.js';

const LOCAL_BASEMAP = './public/data/ne_110m_admin_0_countries.v5.1.1.geojson';
const DEVELOPMENT_BASEMAP = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.1/geojson/ne_110m_admin_0_countries.geojson';
const LOCAL_GIST = './public/data/gist-plants.v1.json';
const EXPECTED_GIST_SCHEMA = 'steel-exposure-atlas/gist-plant-v1.0';
const BASE_VIEW = { x: 0, y: 0, width: 1200, height: 650 };
const BASE_ASPECT = BASE_VIEW.width / BASE_VIEW.height;
const MIN_VIEW_WIDTH = 150;

const worldMap = document.querySelector('#world-map');
const mapStage = document.querySelector('#map-stage');
const graticuleLayer = document.querySelector('#graticule-layer');
const countryLayer = document.querySelector('#country-layer');
const plantLayer = document.querySelector('#plant-layer');
const mapStatus = document.querySelector('#map-status');
const mapCredit = document.querySelector('#map-credit');
const mapKicker = document.querySelector('#map-kicker');
const mapHeading = document.querySelector('#map-heading');
const mapDescription = document.querySelector('#map-description');
const mapTooltip = document.querySelector('#map-tooltip');
const mapSummary = document.querySelector('#map-summary');
const mapHint = document.querySelector('#map-hint');
const zoomInButton = document.querySelector('#zoom-in');
const zoomOutButton = document.querySelector('#zoom-out');
const zoomResetButton = document.querySelector('#zoom-reset');
const zoomLevel = document.querySelector('#zoom-level');
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const productionMode = document.querySelector('#production-mode');
const focusPanel = document.querySelector('#focus-panel');
const regionSelect = document.querySelector('#region-select');
const countrySelect = document.querySelector('#country-select');
const clearFocusButton = document.querySelector('#clear-focus');
const focusStats = document.querySelector('#focus-stats');
const plantInspector = document.querySelector('#plant-inspector');
const aboutButton = document.querySelector('#about-button');
const aboutPanel = document.querySelector('#about-panel');
const aboutClose = document.querySelector('#about-close');

let basemapFeatureCount = 0;
let plantCount = 0;
let plantRecords = [];
let currentView = { ...BASE_VIEW };
let activeMode = 'context';
let dragState = null;

renderGraticule(graticuleLayer);
loadBasemap();
loadPlantData();
wireMapNavigation();

for (const button of modeButtons) {
  button.addEventListener('click', () => setMode(button.dataset.mode));
}

regionSelect.addEventListener('change', () => {
  rebuildCountryOptions(regionSelect.value);
  countrySelect.value = '';
  focusFromSelectors();
});
countrySelect.addEventListener('change', focusFromSelectors);
clearFocusButton.addEventListener('click', clearFocus);

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
    wireCountryHover();
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
    plantRecords = payload.plants;
    plantCount = renderPlants(plantLayer, plantRecords, {
      onSelect: showPlantDetail,
      onHover: showPlantTooltip,
      onLeave: hideTooltip,
    });
    productionMode.disabled = false;
    productionMode.querySelector('small').textContent = `${plantCount.toLocaleString('en-US')} plants`;
    populateRegionOptions();
    rebuildCountryOptions('');
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
  activeMode = mode;

  for (const button of modeButtons) {
    button.classList.toggle('is-active', button.dataset.mode === mode);
  }

  const productionActive = mode === 'production';
  mapStage.classList.toggle('is-production', productionActive);
  focusPanel.hidden = !productionActive;
  mapSummary.hidden = !productionActive;

  if (productionActive) {
    plantLayer.removeAttribute('hidden');
    mapKicker.textContent = 'STEEL PRODUCTION SITES';
    mapHeading.textContent = 'Explore the industrial footprint.';
    mapDescription.textContent = 'Zoom, pan or focus by region and country. Hover for context; select a plant for ownership and capacity detail.';
    mapStatus.textContent = `${plantCount.toLocaleString('en-US')} steel plants · GIST June 2026 (V1) · transformed extract`;
    mapCredit.textContent = 'Natural Earth · Steel data: Global Energy Monitor · CC BY 4.0';
    mapHint.textContent = 'Scroll to zoom · drag to pan · hover a country or plant';
    setFocusedPlants(plantRecords, 'World production', { fit: false });
    return;
  }

  plantLayer.setAttribute('hidden', '');
  clearPointFocus();
  resetMapView();
  mapKicker.textContent = 'PUBLIC DATA, CONNECTED';
  mapHeading.textContent = 'See the structure before judging the risk.';
  mapDescription.textContent = 'The atlas will connect production sites, trade patterns, water-stress indicators and legal-entity relationships without turning them into a single black-box score.';
  mapStatus.textContent = basemapFeatureCount
    ? `${basemapFeatureCount} country features · local reviewed file`
    : 'Loading approved basemap…';
  mapCredit.textContent = 'Natural Earth 1:110m · v5.1.1';
  mapHint.textContent = 'Scroll to zoom · drag to pan · hover a country';
}

function populateRegionOptions() {
  const regions = uniqueValues(plantRecords, 'region');
  for (const region of regions) regionSelect.append(new Option(region, region));
}

function rebuildCountryOptions(region) {
  const previous = countrySelect.value;
  const source = region ? plantRecords.filter((plant) => plant.region === region) : plantRecords;
  countrySelect.replaceChildren(new Option('All countries / areas', ''));
  for (const country of uniqueValues(source, 'country_area')) {
    countrySelect.append(new Option(country, country));
  }
  if ([...countrySelect.options].some((option) => option.value === previous)) {
    countrySelect.value = previous;
  }
}

function uniqueValues(records, key) {
  return [...new Set(records
    .map((record) => String(record?.[key] ?? '').trim())
    .filter((value) => value && value.toLowerCase() !== 'unknown'))]
    .sort((a, b) => a.localeCompare(b, 'en'));
}

function focusFromSelectors() {
  const region = regionSelect.value;
  const country = countrySelect.value;
  const matches = plantRecords.filter((plant) => {
    if (region && plant.region !== region) return false;
    if (country && plant.country_area !== country) return false;
    return true;
  });
  setFocusedPlants(matches, country || region || 'World production');
}

function clearFocus() {
  regionSelect.value = '';
  rebuildCountryOptions('');
  countrySelect.value = '';
  setFocusedPlants(plantRecords, 'World production', { fit: false });
  resetMapView();
}

function focusCountry(country, region = '') {
  if (!country) return;
  regionSelect.value = region && [...regionSelect.options].some((option) => option.value === region) ? region : '';
  rebuildCountryOptions(regionSelect.value);
  if ([...countrySelect.options].some((option) => option.value === country)) {
    countrySelect.value = country;
    focusFromSelectors();
  }
}

function focusOwner(plant) {
  const ownerId = String(plant.owner_gem_entity_id ?? '').trim();
  if (!ownerId) return;
  const matches = plantRecords.filter((candidate) => String(candidate.owner_gem_entity_id ?? '').trim() === ownerId);
  setFocusedPlants(matches, `Owner · ${displaySourceValue(plant.owner_name)}`);
}

function focusParentLabel(plant) {
  const parent = String(plant.parent_display ?? '').trim();
  if (!parent || parent.toLowerCase() === 'unknown') return;
  const matches = plantRecords.filter((candidate) => String(candidate.parent_display ?? '').trim() === parent);
  setFocusedPlants(matches, `Parent label · ${parent}`);
}

function setFocusedPlants(matches, labelText, { fit = true } = {}) {
  const ids = new Set(matches.map((plant) => plant.plant_id));
  for (const point of plantLayer.querySelectorAll('.plant-point')) {
    point.classList.toggle('is-dimmed', !ids.has(point.dataset.plantId));
  }

  const approximate = matches.filter((plant) => plant.coordinate_accuracy === 'approximate').length;
  const knownCapacity = matches.reduce((sum, plant) => {
    const value = Number(plant.capacity?.summary?.operating?.crude_steel_capacity?.known_numeric_sum_ttpa ?? 0);
    return sum + (Number.isFinite(value) ? value : 0);
  }, 0);

  const capacityMtpa = knownCapacity / 1000;
  focusStats.replaceChildren(
    statChip(`${matches.length.toLocaleString('en-US')}`, 'plants'),
    statChip(`${capacityMtpa.toLocaleString('en-US', { maximumFractionDigits: 1 })}`, 'Mtpa known op. crude'),
    statChip(`${approximate.toLocaleString('en-US')}`, 'approx. coords'),
  );
  mapSummary.textContent = `${labelText} · ${matches.length.toLocaleString('en-US')} plants · ${capacityMtpa.toLocaleString('en-US', { maximumFractionDigits: 1 })} Mtpa known operating crude capacity`;

  if (fit && matches.length) fitPlants(matches);
}

function statChip(value, labelText) {
  const wrapper = document.createElement('div');
  const strong = document.createElement('strong');
  const span = document.createElement('span');
  strong.textContent = value;
  span.textContent = labelText;
  wrapper.append(strong, span);
  return wrapper;
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
  plantInspector.append(actionRow('Location', location || 'Not reported', plant.country_area ? () => focusCountry(plant.country_area, plant.region) : null, 'Focus map on this country / area'));
  plantInspector.append(actionRow('Owner', displaySourceValue(plant.owner_name), plant.owner_gem_entity_id ? () => focusOwner(plant) : null, 'Highlight plants with the same immediate GEM owner entity ID'));
  plantInspector.append(actionRow('Parent', displaySourceValue(plant.parent_display), usableParent(plant.parent_display) ? () => focusParentLabel(plant) : null, 'Highlight exact matching parent source labels; this is not resolved corporate hierarchy'));
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

function usableParent(value) {
  if (value === null || value === undefined) return false;
  const text = String(value).trim();
  return Boolean(text) && text.toLowerCase() !== 'unknown';
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

function actionRow(name, value, action, titleText) {
  if (!action) return detailRow(name, value);
  const row = document.createElement('div');
  row.className = 'plant-detail-row';
  const key = document.createElement('span');
  key.textContent = name;
  const button = document.createElement('button');
  button.className = 'detail-action';
  button.type = 'button';
  button.textContent = value;
  button.title = titleText;
  button.addEventListener('click', action);
  row.append(key, button);
  return row;
}

function displaySourceValue(value) {
  if (value === null || value === undefined || value === '') return 'Not reported';
  const text = String(value).trim();
  return text.toLowerCase() === 'unknown' ? 'Unknown in source' : text;
}

function showPlantTooltip(plant, event) {
  mapTooltip.replaceChildren();
  const heading = document.createElement('strong');
  heading.textContent = plant.plant_name || plant.plant_id || 'Steel plant';
  const location = document.createElement('span');
  location.textContent = [plant.municipality, plant.country_area].filter(Boolean).join(', ');
  const capacity = Number(plant.capacity?.summary?.operating?.crude_steel_capacity?.known_numeric_sum_ttpa ?? 0);
  const metric = document.createElement('span');
  metric.textContent = capacity > 0 ? `${(capacity / 1000).toLocaleString('en-US', { maximumFractionDigits: 2 })} Mtpa known operating crude` : 'Operating crude capacity not numerically reported';
  mapTooltip.append(heading, location, metric);
  positionTooltip(event);
}

function showCountryTooltip(name, event) {
  if (!name || activeMode !== 'production') return;
  mapTooltip.replaceChildren();
  const heading = document.createElement('strong');
  heading.textContent = name;
  const hint = document.createElement('span');
  hint.textContent = 'Country context';
  mapTooltip.append(heading, hint);
  positionTooltip(event);
}

function positionTooltip(event) {
  mapTooltip.hidden = false;
  const rect = mapStage.getBoundingClientRect();
  const x = Math.min(Math.max(event.clientX - rect.left + 14, 12), rect.width - 270);
  const y = Math.min(Math.max(event.clientY - rect.top + 14, 12), rect.height - 110);
  mapTooltip.style.transform = `translate(${x}px, ${y}px)`;
}

function hideTooltip() {
  mapTooltip.hidden = true;
}

function wireCountryHover() {
  for (const country of countryLayer.querySelectorAll('.country')) {
    country.addEventListener('pointerenter', (event) => showCountryTooltip(country.dataset.name, event));
    country.addEventListener('pointermove', (event) => showCountryTooltip(country.dataset.name, event));
    country.addEventListener('pointerleave', hideTooltip);
  }
}

function wireMapNavigation() {
  zoomInButton.addEventListener('click', () => zoomAtCenter(0.76));
  zoomOutButton.addEventListener('click', () => zoomAtCenter(1.32));
  zoomResetButton.addEventListener('click', resetMapView);

  worldMap.addEventListener('wheel', (event) => {
    event.preventDefault();
    zoomAtClient(event.deltaY > 0 ? 1.18 : 0.84, event.clientX, event.clientY);
  }, { passive: false });

  worldMap.addEventListener('dblclick', (event) => {
    if (event.target.closest?.('.plant-point')) return;
    event.preventDefault();
    zoomAtClient(0.62, event.clientX, event.clientY);
  });

  worldMap.addEventListener('pointerdown', (event) => {
    if (event.button !== 0 || event.target.closest?.('.plant-point')) return;
    hideTooltip();
    worldMap.setPointerCapture(event.pointerId);
    dragState = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, view: { ...currentView } };
    worldMap.classList.add('is-panning');
  });

  worldMap.addEventListener('pointermove', (event) => {
    if (!dragState || dragState.pointerId !== event.pointerId) return;
    const rect = worldMap.getBoundingClientRect();
    const dx = (event.clientX - dragState.x) * (dragState.view.width / rect.width);
    const dy = (event.clientY - dragState.y) * (dragState.view.height / rect.height);
    setViewBox({
      ...dragState.view,
      x: dragState.view.x - dx,
      y: dragState.view.y - dy,
    });
  });

  const endDrag = (event) => {
    if (!dragState || dragState.pointerId !== event.pointerId) return;
    dragState = null;
    worldMap.classList.remove('is-panning');
  };
  worldMap.addEventListener('pointerup', endDrag);
  worldMap.addEventListener('pointercancel', endDrag);
}

function zoomAtCenter(factor) {
  const rect = worldMap.getBoundingClientRect();
  zoomAtClient(factor, rect.left + rect.width / 2, rect.top + rect.height / 2);
}

function zoomAtClient(factor, clientX, clientY) {
  const rect = worldMap.getBoundingClientRect();
  const px = currentView.x + ((clientX - rect.left) / rect.width) * currentView.width;
  const py = currentView.y + ((clientY - rect.top) / rect.height) * currentView.height;
  const width = clamp(currentView.width * factor, MIN_VIEW_WIDTH, BASE_VIEW.width);
  const height = width / BASE_ASPECT;
  const rx = (px - currentView.x) / currentView.width;
  const ry = (py - currentView.y) / currentView.height;
  setViewBox({ x: px - rx * width, y: py - ry * height, width, height });
}

function fitPlants(plants) {
  if (!plants.length) return;
  if (plants.length === plantRecords.length) {
    resetMapView();
    return;
  }

  const points = plants.map((plant) => project([plant.longitude, plant.latitude]));
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  const width = clamp(Math.max(maxX - minX + 100, (maxY - minY + 100) * BASE_ASPECT, 220), MIN_VIEW_WIDTH, BASE_VIEW.width);
  const height = width / BASE_ASPECT;
  setViewBox({ x: centerX - width / 2, y: centerY - height / 2, width, height });
}

function resetMapView() {
  setViewBox({ ...BASE_VIEW });
}

function setViewBox(next) {
  const width = clamp(next.width, MIN_VIEW_WIDTH, BASE_VIEW.width);
  const height = width / BASE_ASPECT;
  const x = clamp(next.x, BASE_VIEW.x, BASE_VIEW.width - width);
  const y = clamp(next.y, BASE_VIEW.y, BASE_VIEW.height - height);
  currentView = { x, y, width, height };
  worldMap.setAttribute('viewBox', `${x.toFixed(2)} ${y.toFixed(2)} ${width.toFixed(2)} ${height.toFixed(2)}`);
  const zoom = BASE_VIEW.width / width;
  zoomLevel.textContent = `${zoom.toFixed(1)}×`;
  updatePlantMarkerScale(zoom);
}

function updatePlantMarkerScale(zoom) {
  const scale = Math.sqrt(zoom);
  for (const point of plantLayer.querySelectorAll('.plant-point')) {
    const base = Number(point.dataset.baseRadius || 2.8);
    point.setAttribute('r', (base / scale).toFixed(2));
  }
}

function clearPointFocus() {
  for (const point of plantLayer.querySelectorAll('.plant-point')) {
    point.classList.remove('is-dimmed');
  }
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
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
