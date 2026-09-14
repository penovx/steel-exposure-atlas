import { renderCountries, renderGraticule } from './map/render-world.js';

const LOCAL_BASEMAP = './public/data/ne_110m_admin_0_countries.v5.1.1.geojson';
const DEVELOPMENT_BASEMAP = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.1/geojson/ne_110m_admin_0_countries.geojson';

const graticuleLayer = document.querySelector('#graticule-layer');
const countryLayer = document.querySelector('#country-layer');
const mapStatus = document.querySelector('#map-status');
const aboutButton = document.querySelector('#about-button');
const aboutPanel = document.querySelector('#about-panel');
const aboutClose = document.querySelector('#about-close');

renderGraticule(graticuleLayer);
loadBasemap();

aboutButton.addEventListener('click', () => {
  aboutPanel.showModal();
  aboutButton.setAttribute('aria-expanded', 'true');
});

aboutClose.addEventListener('click', () => aboutPanel.close());
aboutPanel.addEventListener('close', () => aboutButton.setAttribute('aria-expanded', 'false'));

async function loadBasemap() {
  try {
    const { data, source } = await loadBasemapData();
    const renderedCount = renderCountries(countryLayer, data);
    mapStatus.textContent = `${renderedCount} country features · ${source}`;
  } catch (error) {
    mapStatus.classList.add('is-error');
    mapStatus.textContent = 'Basemap not available. Run the approved data fetch step locally.';
    console.error(error);
  }
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
