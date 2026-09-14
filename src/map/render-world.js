const SVG_NS = 'http://www.w3.org/2000/svg';
const WIDTH = 1200;
const MAP_TOP = 160;
const MAP_BOTTOM = 620;

export function renderGraticule(group) {
  group.textContent = '';

  for (let longitude = -180; longitude <= 180; longitude += 30) {
    const line = document.createElementNS(SVG_NS, 'line');
    const [x1, y1] = project([longitude, -70]);
    const [x2, y2] = project([longitude, 80]);
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('class', 'graticule');
    group.append(line);
  }

  for (let latitude = -60; latitude <= 60; latitude += 30) {
    const line = document.createElementNS(SVG_NS, 'line');
    const [x1, y1] = project([-180, latitude]);
    const [x2, y2] = project([180, latitude]);
    line.setAttribute('x1', x1);
    line.setAttribute('y1', y1);
    line.setAttribute('x2', x2);
    line.setAttribute('y2', y2);
    line.setAttribute('class', 'graticule');
    group.append(line);
  }
}

export function renderCountries(group, featureCollection) {
  if (featureCollection?.type !== 'FeatureCollection' || !Array.isArray(featureCollection.features)) {
    throw new Error('Basemap is not a valid GeoJSON FeatureCollection.');
  }

  const fragment = document.createDocumentFragment();
  for (const feature of featureCollection.features) {
    if (!feature?.geometry) continue;
    const pathData = geometryToPath(feature.geometry);
    if (!pathData) continue;

    const path = document.createElementNS(SVG_NS, 'path');
    path.setAttribute('d', pathData);
    path.setAttribute('class', 'country');
    path.dataset.iso3 = feature.properties?.ISO_A3 ?? '';
    path.dataset.name = feature.properties?.NAME_EN ?? feature.properties?.ADMIN ?? '';
    if (path.dataset.name) {
      const title = document.createElementNS(SVG_NS, 'title');
      title.textContent = path.dataset.name;
      path.append(title);
    }
    fragment.append(path);
  }

  group.replaceChildren(fragment);
  return group.childElementCount;
}

export function renderPlants(group, plants, { onSelect } = {}) {
  if (!Array.isArray(plants)) {
    throw new Error('Plant data must contain a plants array.');
  }

  const fragment = document.createDocumentFragment();

  for (const plant of plants) {
    const latitude = Number(plant?.latitude);
    const longitude = Number(plant?.longitude);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      throw new Error(`Plant ${plant?.plant_id ?? '(unknown)'} has invalid coordinates.`);
    }

    const [x, y] = project([longitude, latitude]);
    const point = document.createElementNS(SVG_NS, 'circle');
    const approximate = plant.coordinate_accuracy === 'approximate';

    point.setAttribute('cx', x.toFixed(2));
    point.setAttribute('cy', y.toFixed(2));
    point.setAttribute('r', approximate ? '3.2' : '2.8');
    point.setAttribute('class', `plant-point${approximate ? ' is-approximate' : ''}`);
    point.setAttribute('tabindex', '0');
    point.setAttribute('role', 'button');
    point.setAttribute('aria-label', plant.plant_name || plant.plant_id || 'Steel plant');
    point.dataset.plantId = plant.plant_id ?? '';

    const title = document.createElementNS(SVG_NS, 'title');
    const location = [plant.municipality, plant.country_area].filter(Boolean).join(', ');
    title.textContent = [plant.plant_name, location, plant.owner_name].filter(Boolean).join(' · ');
    point.append(title);

    if (typeof onSelect === 'function') {
      const selectPoint = () => {
        group.querySelector('.plant-point.is-selected')?.classList.remove('is-selected');
        point.classList.add('is-selected');
        onSelect(plant);
      };

      point.addEventListener('click', selectPoint);
      point.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          selectPoint();
        }
      });
    }

    fragment.append(point);
  }

  group.replaceChildren(fragment);
  return group.childElementCount;
}

function geometryToPath(geometry) {
  if (geometry.type === 'Polygon') return polygonToPath(geometry.coordinates);
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.map(polygonToPath).join(' ');
  return '';
}

function polygonToPath(rings) {
  return rings.map((ring) => {
    if (!Array.isArray(ring) || ring.length === 0) return '';
    return ring.map((position, index) => {
      const [x, y] = project(position);
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`;
    }).join(' ') + ' Z';
  }).join(' ');
}

export function project([longitude, latitude]) {
  const x = ((Number(longitude) + 180) / 360) * WIDTH;
  const usableHeight = MAP_BOTTOM - MAP_TOP;
  const y = MAP_TOP + ((90 - Number(latitude)) / 180) * usableHeight;
  return [x, y];
}
