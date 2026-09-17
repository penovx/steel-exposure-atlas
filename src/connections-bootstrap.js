const GIST_URL = new URL('../public/data/gist-plants.v1.json', import.meta.url);
const BASEMAP_URL = new URL('../public/data/ne_110m_admin_0_countries.v5.1.1.geojson', import.meta.url);
const EXPECTED_SCHEMA = 'steel-exposure-atlas/gist-plant-v1.0';
const EXPECTED_PLANTS = 1293;
const EXPECTED_GIST_SHA256 = '6D9C2CBAC1DBC25068AF5DD69736FF7E44D6074E220BDB5880054487F28A3EC3';
const REGIONS = ['World','Europe','North America','Central & South America','Asia Pacific','Africa','Middle East','Eurasia'];
const REGION_BOUNDS = {
  World: [-180,-60,180,85],
  Europe: [-25,33,45,72],
  'North America': [-170,10,-50,82],
  'Central & South America': [-120,-60,-30,35],
  'Asia Pacific': [55,-50,180,70],
  Africa: [-25,-40,60,40],
  'Middle East': [20,8,70,46],
  Eurasia: [20,35,180,82],
};
const COUNTRY_ALIASES = new Map([
  ['Turkey','Türkiye'],['Türkiye','Türkiye'],['Czechia','Czech Republic'],
  ['United States of America','United States'],['United States','United States'],
  ['Republic of Korea','South Korea'],['South Korea','South Korea'],
  ['North Macedonia','North Macedonia'],['Macedonia','North Macedonia'],
  ['Bosnia and Herzegovina','Bosnia and Herzegovina'],
]);

function stateObject(v){
  if(!v || typeof v !== 'object') return {state:'blank',value_ttpa:null};
  return {state:v.state, value_ttpa:v.value_ttpa ?? null};
}
function valueList(v){return v?.state==='text' && Array.isArray(v.values) ? v.values : [];}
function transformPlant(p){
  return {
    id:p.plant_id,
    name:p.plant_name,
    country:p.country_area,
    region:p.region,
    city:p.municipality,
    latitude:Number(p.latitude),
    longitude:Number(p.longitude),
    accuracy:p.coordinate_accuracy,
    owner:p.owner_name,
    ownerId:p.owner_gem_entity_id,
    products:{state:p.steel_products?.state ?? 'blank',values:valueList(p.steel_products)},
    sectors:{state:p.end_user_sectors?.state ?? 'blank',values:valueList(p.end_user_sectors)},
    tranches:(p.capacity?.tranches ?? []).map(t=>({
      status:t.status,
      crude_steel_capacity_ttpa:stateObject(t.crude_steel_capacity_ttpa),
      bof_steel_capacity_ttpa:stateObject(t.bof_steel_capacity_ttpa),
      eaf_steel_capacity_ttpa:stateObject(t.eaf_steel_capacity_ttpa),
      if_steel_capacity_ttpa:stateObject(t.if_steel_capacity_ttpa),
      other_steel_capacity_ttpa:stateObject(t.other_steel_capacity_ttpa),
    })),
    production:p.production?.crude_steel_ttpa ?? null,
    source_url:p.wiki_url,
  };
}
function featureName(f){
  const raw=f?.properties?.NAME_EN || f?.properties?.ADMIN || f?.properties?.NAME || '';
  return COUNTRY_ALIASES.get(raw) || raw;
}
function eachRing(geometry,fn){
  if(!geometry)return;
  if(geometry.type==='Polygon') for(const ring of geometry.coordinates) fn(ring);
  else if(geometry.type==='MultiPolygon') for(const poly of geometry.coordinates) for(const ring of poly) fn(ring);
}
function rawProject(lon,lat,lat0){
  const rad=Math.PI/180, R=6371;
  return [R*lon*rad*Math.cos(lat0*rad), -R*lat*rad];
}
function intersectsBounds(geometry,b){
  let hit=false; eachRing(geometry,ring=>{if(hit)return; for(const [lon,lat] of ring){if(lon>=b[0]&&lon<=b[2]&&lat>=b[1]&&lat<=b[3]){hit=true;break;}}}); return hit;
}
function buildMap(region,plants,basemap){
  const bounds=REGION_BOUNDS[region] || REGION_BOUNDS.World;
  const lat0=(bounds[1]+bounds[3])/2;
  const p0=rawProject(bounds[0],bounds[3],lat0), p1=rawProject(bounds[2],bounds[1],lat0);
  const extent=[Math.min(p0[0],p1[0]),Math.min(p0[1],p1[1]),Math.max(p0[0],p1[0]),Math.max(p0[1],p1[1])];
  const countries=[];
  for(const f of basemap.features || []){
    if(region!=='World' && !intersectsBounds(f.geometry,bounds)) continue;
    const rings=[]; eachRing(f.geometry,ring=>rings.push(ring.map(([lon,lat])=>rawProject(lon,lat,lat0))));
    if(!rings.length)continue;
    const name=featureName(f);
    const lx=Number(f.properties?.LABEL_X),ly=Number(f.properties?.LABEL_Y);
    let label;
    if(Number.isFinite(lx)&&Number.isFinite(ly)) label=rawProject(lx,ly,lat0);
    else {
      const pts=rings.flat(); const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);
      label=[(Math.min(...xs)+Math.max(...xs))/2,(Math.min(...ys)+Math.max(...ys))/2];
    }
    countries.push({name,rings,label,label_geo:[lx,ly]});
  }
  const positions={}; for(const p of plants){positions[p.id]=rawProject(p.longitude,p.latitude,lat0);}
  return {countries,positions,extent,projection:'local-equirectangular'};
}
async function fetchJson(url,label){
  const response=await fetch(url,{credentials:'same-origin',cache:'no-store'});
  if(!response.ok)throw new Error(`${label} is unavailable (${response.status}).`);
  return response.json();
}
async function fetchPinnedGist(){
  const response=await fetch(GIST_URL,{credentials:'same-origin',cache:'no-store'});
  if(!response.ok)throw new Error(`Reviewed GIST extract is unavailable (${response.status}).`);
  const sourceText=new TextDecoder().decode(await response.arrayBuffer());
  const normalizedText=sourceText.replace(/\r\n/g,'\n');
  const canonicalBytes=new TextEncoder().encode(normalizedText);
  const digest=await crypto.subtle.digest('SHA-256',canonicalBytes);
  const hash=[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('').toUpperCase();
  if(hash!==EXPECTED_GIST_SHA256)throw new Error('Reviewed GIST extract failed the pinned SHA-256 check.');
  return {raw:JSON.parse(normalizedText),hash};
}

async function boot(){
  const status=document.querySelector('#startup-status');
  try{
    const [{raw,hash},basemap]=await Promise.all([fetchPinnedGist(),fetchJson(BASEMAP_URL,'Reviewed Natural Earth basemap')]);
    if(raw?.meta?.schema!==EXPECTED_SCHEMA)throw new Error(`Unexpected GIST schema: ${raw?.meta?.schema ?? 'missing'}`);
    if(!Array.isArray(raw.plants)||raw.plants.length!==EXPECTED_PLANTS)throw new Error('Unexpected plant count in reviewed GIST extract.');
    if(basemap?.type!=='FeatureCollection'||!Array.isArray(basemap.features))throw new Error('Natural Earth basemap is not a GeoJSON FeatureCollection.');
    const plants=raw.plants.map(transformPlant);
    const ids=new Set(plants.map(p=>p.id)); if(ids.size!==EXPECTED_PLANTS)throw new Error('Duplicate plant IDs in runtime extract.');

    const mapCache={};
    const ensureMap=(region)=>{
      if(mapCache[region]) return mapCache[region];
      const scoped=region==='World'?plants:plants.filter(p=>p.region===region);
      mapCache[region]=buildMap(region,scoped,basemap);
      return mapCache[region];
    };

    ensureMap('Europe');
    ensureMap('World');
    const maps=new Proxy(mapCache,{
      get(target,property,receiver){
        if(typeof property==='string' && REGIONS.includes(property)) return ensureMap(property);
        return Reflect.get(target,property,receiver);
      },
    });

    window.__ATLAS_DATA__={schema:'steel-exposure-atlas/relational-entry-v2',source:raw.meta,json_sha256:hash,plants,maps};
    if(status)status.hidden=true;
    await import('./connections-core.js?v=20260916-3');

    const pending=REGIONS.filter(region=>!mapCache[region]);
    const warmNext=()=>{
      const region=pending.shift();
      if(!region) return;
      ensureMap(region);
      if(pending.length){
        if('requestIdleCallback' in window) requestIdleCallback(warmNext,{timeout:500});
        else setTimeout(warmNext,0);
      }
    };
    if(pending.length){
      if('requestIdleCallback' in window) requestIdleCallback(warmNext,{timeout:500});
      else setTimeout(warmNext,0);
    }
  }catch(error){
    console.error(error);
    if(status){status.hidden=false;status.classList.add('is-error');status.textContent=`Atlas data could not be loaded. ${error.message}`;}
  }
}
boot();