import { renderCountries, project } from '../src/map/render-world.js';
import { GIST_SHA256, validatePinnedPayload, valuesFor, scopePlants, searchPlants, aggregateCapacity, plantCapacity, operatingRoutes, rankCapacityPlants, scopeCapacitySummary, capacityRadius, formatCapacity, sourceText, usableOwnerId, CAPACITY_FIELDS, initialEvidenceState, evidenceReducer } from './gist-adapter.mjs';
import { renderSiteExplorer, renderSiteComparison } from './site-explorer.mjs';

const $ = id => document.getElementById(id);
const svgNS = 'http://www.w3.org/2000/svg';
const map = $('evidence-map');
let plants = [], state, history = [], allResults = false, drag = null, mapAvailable = false, siteSignature = '', ranksVisible = false;
const el = (tag, text, className) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (className) node.className = className; return node; };
const svgel = (tag, attributes) => { const node = document.createElementNS(svgNS, tag); for (const [k,v] of Object.entries(attributes)) node.setAttribute(k, v); return node; };
const scoped = () => scopePlants(plants, state.scope);
const count = value => value.toLocaleString('en-US');
const mtpa = value => value === null ? 'Not quantified' : value.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const percent = value => `${(value * 100).toLocaleString('en-US', {maximumFractionDigits: 1})}%`;
const routeNames = {bof_steel_capacity_ttpa:'Basic oxygen furnace',eaf_steel_capacity_ttpa:'Electric arc furnace',if_steel_capacity_ttpa:'Induction furnace',other_steel_capacity_ttpa:'Other steelmaking'};
const scopeName = () => state.scope.country || state.scope.region || 'All tracked countries / areas';
const snapshot = () => ({...structuredClone(state), ranksVisible});
const GIST_DATA_URL = new URL('../public/data/gist-plants.v1.json', import.meta.url);
const BASEMAP_DATA_URL = new URL('../public/data/ne_110m_admin_0_countries.v5.1.1.geojson', import.meta.url);

async function readLocal(path) {
  const url = path instanceof URL ? path : new URL(path, import.meta.url);
  const response = await fetch(url, {credentials: 'omit', cache: 'no-store'});
  if (!response.ok) throw new Error(`Local file unavailable (${response.status}): ${url.pathname.split('/').pop()}`);
  return response;
}
async function load() {
  const [gist, basemap] = await Promise.allSettled([
    (async () => {
      const bytes = await (await readLocal(GIST_DATA_URL)).arrayBuffer();
      if (!globalThis.crypto?.subtle) throw new Error('SHA-256 verification requires a secure local context; open this prototype through http://127.0.0.1.');
      const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x => x.toString(16).padStart(2,'0')).join('');
      return validatePinnedPayload(JSON.parse(new TextDecoder().decode(bytes)), digest);
    })(),
    (async () => (await readLocal(BASEMAP_DATA_URL)).json())(),
  ]);
  if (gist.status === 'rejected') {
    $('load-status').classList.add('error');
    $('load-status').textContent = `The reviewed GIST evidence cannot be displayed. ${gist.reason.message} No remote fallback was requested. Restore the reviewed local artifact to continue.`;
    $('integrity-note').textContent = 'GIST integrity not verified; no plant data displayed.';
    return;
  }
  plants = gist.value.plants; state = initialEvidenceState(plants);
  const requestedPlant = new URLSearchParams(location.search).get('plant');
  const linkedPlant = plants.find(plant => plant.plant_id === requestedPlant);
  if (linkedPlant) {
    state = evidenceReducer(state,{type:'country',country:linkedPlant.country_area},plants);
    state = evidenceReducer(state,{type:'select',id:linkedPlant.plant_id},plants);
  }
  if (basemap.status === 'fulfilled') {
    try { renderCountries($('countries'), basemap.value); mapAvailable = true; }
    catch { /* The source list remains usable without a basemap. */ }
  }
  $('integrity-note').textContent = `Extract SHA-256 verified (${GIST_SHA256.slice(0,12)}…).`;
  $('load-status').textContent = `${count(plants.length)} unique plants · 1,845 source status tranches · local extract verified${mapAvailable ? '' : ' · local basemap unavailable; use the plant list'}`;
  $('load-status').hidden = mapAvailable;
  $('workspace').hidden = false;
  $('region').replaceChildren(new Option('All GEM regions', ''), ...valuesFor(plants, 'region').map(v => new Option(v,v)));
  state.camera = fittedCamera(scoped());
  wire(); render(true);
}

function dispatch(action, remember = true) {
  if (remember) history.push(snapshot());
  const hadSelection=Boolean(state.selectedId);
  state = evidenceReducer(state, action, plants);
  if (action.type === 'select') ranksVisible = false;
  const geographicChange=action.type==='country' || action.type==='region';
  if(geographicChange) allResults=false;
  render(geographicChange || hadSelection!==Boolean(state.selectedId));
}
function fittedCamera(records) {
  const wholeWidth=Math.max(1,map.clientWidth),height=Math.max(1,map.clientHeight);
  const overview = !state?.selectedId && wholeWidth > 820;
  const availableWidth=wholeWidth > 820 ? wholeWidth * (overview ? .6 : .48) : wholeWidth;
  const ratio = availableWidth/height;
  if (!records.length) return {x:0,y:150,width:1200,height:1200/ratio};
  const positions = records.map(p => project([p.longitude,p.latitude]));
  const xs = positions.map(p => p[0]), ys = positions.map(p => p[1]);
  const centerX = (Math.min(...xs)+Math.max(...xs))/2, centerY = (Math.min(...ys)+Math.max(...ys))/2;
  const fittedWidth = Math.min(1200, Math.max(35, (Math.max(...xs)-Math.min(...xs))*1.65, (Math.max(...ys)-Math.min(...ys))*1.55*ratio));
  const width=fittedWidth*wholeWidth/availableWidth;
  return {x:centerX-fittedWidth/2-(overview ? width*.38 : 0),y:centerY-fittedWidth/ratio/2,width,height:fittedWidth/ratio};
}
function setCamera(camera) {
  const width = Math.max(12,Math.min(1500,camera.width)), ratio = map.clientWidth / Math.max(1,map.clientHeight);
  dispatch({type:'camera',camera:{...camera,width,height:width/ratio}},false);
}
function zoom(factor) {
  const c = state.camera, nextWidth = Math.max(12,Math.min(1500,c.width*factor));
  const nextHeight = nextWidth * c.height/c.width;
  setCamera({x:c.x+(c.width-nextWidth)/2,y:c.y+(c.height-nextHeight)/2,width:nextWidth,height:nextHeight});
}
function render(fitSelection=false) {
  const focusKey = document.activeElement?.dataset?.focusKey;
  const records = scoped();
  const layout = document.querySelector('.evidence-layout');
  layout.classList.toggle('has-site', Boolean(state.selectedId));
  layout.classList.toggle('show-ranks', ranksVisible);
  $('toggle-ranking').setAttribute('aria-pressed',String(ranksVisible));
  $('show-comparison').hidden=state.pins?.length!==2;
  $('show-comparison').setAttribute('aria-pressed',String(Boolean(state.comparisonVisible)));
  if (fitSelection) {
    state.camera = fittedCamera(records);
  }
  $('region').value = state.scope.region;
  const allowed = state.scope.region ? plants.filter(p => p.region === state.scope.region) : plants;
  $('country').replaceChildren(new Option('All countries / areas',''),...valuesFor(allowed,'country_area').map(v => new Option(v,v)));
  $('country').value = state.scope.country;
  $('scope-label').textContent = `${scopeName()} · ${count(records.length)} tracked plants · June 2026`;
  $('capacity-heading').textContent = `Capacity in ${scopeName()}`;
  $('overview-question').textContent = `What shapes steel capacity in ${state.scope.country || state.scope.region || 'the world'}?`;
  $('active-map-context').textContent = `${scopeName()} · Operating crude steel${state.route ? ` · Highlight: ${routeNames[state.route]}` : ''}`;
  $('map-perspective').value=state.perspective ?? 'capacity';$('route-filter').value=state.route ?? '';
  $('route-legend').hidden=state.perspective!=='routes';
  $('back').disabled = history.length === 0;
  $('clear-selection').disabled = !state.selectedId;
  $('plant-search').value = state.query;
  $('quick-search').value = state.query;
  $('plants-layer').checked = state.layers.plants;
  $('map-preview').textContent = state.product ? `Highlighted sites list “${state.product}” in the source; absent labels do not prove non-production.` : 'Select a site to explore capacity, technology and reported production.';
  renderCapacity(records); renderMap(records); renderList(records); renderSelectedSite(records); renderComparison(records);
  if (focusKey) [...document.querySelectorAll('[data-focus-key]')].find(n => n.dataset.focusKey === focusKey)?.focus({preventScroll:true});
}
function renderCapacity(records) {
  const summary = scopeCapacitySummary(records);
  const rows = [['operating', 'Known operating capacity'], ['development', 'Known development capacity']]
    .map(([key,label]) => ({key,label,...summary[key]}));
  const max = Math.max(1,...rows.map(row => row.knownMtpa ?? 0));
  $('capacity-bars').replaceChildren(...rows.map(row => {
    const root = el('div',undefined,`capacity-row ${row.key}`);
    const label = el('span',row.label,'bucket');
    const number = el('strong',row.knownMtpa === null ? 'Not quantified' : `${mtpa(row.knownMtpa)}`);
    if (row.knownMtpa !== null) number.append(el('small',' Mtpa'));
    const track = el('div',undefined,'track'), fill = el('div',undefined,'fill');
    fill.style.width = `${(row.knownMtpa ?? 0)/max*100}%`; track.append(fill); track.setAttribute('aria-hidden','true');
    const sitesWithNumeric = records.filter(p => plantCapacity(p,row.key).numeric_rows > 0).length;
    const context = row.has_unquantified_positive ? '+ unquantified positive capacity' : row.contributing_rows ? `${sitesWithNumeric} ${sitesWithNumeric===1 ? 'site' : 'sites'} with numeric source values` : 'No source tranches in this status bucket';
    root.append(label,number,track,el('span',context,`capacity-states${row.has_unquantified_positive ? ' has-unquantified' : ''}`));
    return root;
  }));
  const ranked = rankCapacityPlants(records).filter(row => row.share !== null);
  const leaders = ranked.slice(0,5), share = leaders.reduce((sum,row) => sum+row.share,0);
  $('capacity-story').textContent = leaders.length && summary.operating.knownMtpa > 0
    ? `${leaders.length} sites account for ${percent(share)} of the known operating component.`
    : 'The source does not establish a positive numeric operating-capacity denominator.';
  const routeFields = [['bof_steel_capacity_ttpa','BOF'],['eaf_steel_capacity_ttpa','EAF'],['if_steel_capacity_ttpa','IF'],['other_steel_capacity_ttpa','Other']];
  const routes = routeFields.map(([field,label]) => ({field,label,...aggregateCapacity(records,'operating',field)}));
  const largest = Math.max(1,...routes.map(row => row.known_numeric_sum_ttpa));
  $('routes-overview').replaceChildren(...routes.map(row => {
    const item=el('button',undefined,'route-component');
    item.setAttribute('aria-label',`Highlight ${routeNames[row.field]} sites`);
    item.setAttribute('aria-pressed',String(state.route===row.field));
    item.addEventListener('click',()=>dispatch({type:'route',value:state.route===row.field ? null : row.field}));
    const label=el('span',row.label);
    const value=el('strong',row.numeric_rows ? `${mtpa(row.known_numeric_sum_ttpa/1000)} Mtpa${row.has_unquantified_positive ? ' +' : ''}` : row.has_unquantified_positive ? '>0 · unquantified' : 'Not quantified');
    const track=el('div',undefined,'route-track'), fill=el('span'); fill.style.width=`${row.known_numeric_sum_ttpa/largest*100}%`;track.append(fill);track.setAttribute('aria-hidden','true');
    item.append(label,value,track); return item;
  }));
  $('coverage-detail').replaceChildren(...rows.map(row => el('p',
    `${row.label}: ${row.numeric_rows} numeric source tranches out of ${row.contributing_rows}; ${row.states['>0']} unquantified positive, ${row.states.unknown} unknown, ${row.states['N/A']} not applicable, ${row.states.blank} blank. Known amounts do not estimate missing values.`)),
    el('p','Operating route breakdowns may be incomplete and are not added to the crude-steel total. Capacity describes the June 2026 source snapshot, not actual production or available supply.'));
}
function mapGroups(records) {
  const pinnedOrSelected = new Set([state.selectedId,...(state.pins ?? [])].filter(Boolean));
  if (state.camera.width > 450) {
    const countries = new Map();
    for (const p of records.filter(p=>!pinnedOrSelected.has(p.plant_id))) { if (!countries.has(p.country_area)) countries.set(p.country_area,[]); countries.get(p.country_area).push(p); }
    return [...countries].map(([country,members]) => ({members,country})).concat(records.filter(p=>pinnedOrSelected.has(p.plant_id)).map(p=>({members:[p]})));
  }
  const size = state.camera.width / Math.max(1,map.clientWidth) * 29;
  const bins = new Map();
  for (const p of records) {
    const [x,y] = project([p.longitude,p.latitude]);
    const key = pinnedOrSelected.has(p.plant_id) ? `focus-${p.plant_id}` : `${Math.floor(x/size)}:${Math.floor(y/size)}`;
    if (!bins.has(key)) bins.set(key,[]); bins.get(key).push(p);
  }
  // Merge overlapping symbols, not just points sharing a grid cell.
  const groups=[...bins.values()].map(members=>({members}));
  const px=state.camera.width/Math.max(1,map.clientWidth);
  const total=scopeCapacitySummary(records).operating.knownMtpa ?? 0;
  const geometry=group=>{
    const points=group.members.map(p=>project([p.longitude,p.latitude]));
    const amount=scopeCapacitySummary(group.members).operating.knownMtpa;
    return {x:points.reduce((s,p)=>s+p[0],0)/points.length,y:points.reduce((s,p)=>s+p[1],0)/points.length,r:capacityRadius(amount,total,65) ?? 6};
  };
  for(let changed=true;changed;){
    changed=false;
    outer: for(let i=0;i<groups.length;i++) for(let j=i+1;j<groups.length;j++){
      if([...groups[i].members,...groups[j].members].some(p=>pinnedOrSelected.has(p.plant_id)))continue;
      const a=geometry(groups[i]),b=geometry(groups[j]);
      if(Math.hypot(a.x-b.x,a.y-b.y)<(a.r+b.r+10)*px){groups[i].members.push(...groups[j].members);groups.splice(j,1);changed=true;break outer;}
    }
  }
  return groups;
}
function renderMap(records) {
  const c = state.camera; map.setAttribute('viewBox',`${c.x} ${c.y} ${c.width} ${c.height}`);
  const scale = c.width / Math.max(1,map.clientWidth);
  const scopeCapacity = scopeCapacitySummary(records).operating.knownMtpa;
  const topIds=new Set(rankCapacityPlants(records).filter(row=>row.operating.knownMtpa>0).slice(0,5).map(row=>row.plant.plant_id));
  for (const country of $('countries').children) country.classList.toggle('is-scope', records.some(p => p.country_area === country.dataset.name));
  $('map-level').textContent = !mapAvailable ? 'Basemap unavailable' : c.width > 450 ? 'Country capacity groups' : 'Operating capacity · Mtpa';
  $('map-points').replaceChildren();
  $('site-leaders').replaceChildren();
  if (!state.layers.plants || !mapAvailable) return;
  const groups=mapGroups(records).map(group=>({...group,summary:scopeCapacitySummary(group.members).operating}));
  for (const group of groups.sort((a,b)=>(b.summary.knownMtpa ?? 0)-(a.summary.knownMtpa ?? 0))) {
    const {members,country,summary} = group, positions = members.map(p => project([p.longitude,p.latitude]));
    const x = positions.reduce((n,p) => n+p[0],0)/positions.length, y = positions.reduce((n,p) => n+p[1],0)/positions.length;
    if (x < c.x-scale*50 || x > c.x+c.width+scale*50 || y < c.y-scale*50 || y > c.y+c.height+scale*50) continue;
    const first = members[0], selected = members.some(p => p.plant_id === state.selectedId);
    const radius = capacityRadius(summary.knownMtpa, scopeCapacity ?? 0, 65);
    const r = (radius ?? 0)*scale;
    const approximate = members.some(p => p.coordinate_accuracy === 'approximate');
    const mixed = summary.has_unquantified_positive || summary.states.unknown>0 || summary.states.blank>0;
    const label = members.length>1 ? `${country || 'Nearby-site group'} · ${members.length} sites` : first.plant_name;
    const valueLabel = summary.knownMtpa === null ? 'operating capacity not quantified' : `${mtpa(summary.knownMtpa)} Mtpa known operating capacity`;
    const root = svgel('g',{class:`point${selected?' is-selected':''}${approximate?' is-approximate':''}${mixed?' is-partial':''}`,tabindex:'0',role:'button','data-focus-key':`point-${first.plant_id}`,'aria-label':`${label}; ${valueLabel}${mixed ? '; non-numeric source states also present' : ''}${approximate ? '; includes approximate coordinates' : ''}`});
    root.dataset.plantIds = members.map(p=>p.plant_id).join(' ');
    root.dataset.knownMtpa = summary.knownMtpa ?? '';
    const sourceRoutes=[...new Set(members.flatMap(p=>operatingRoutes(p).map(route=>route.field)))];
    const routeClass=sourceRoutes.length>1?'mixed':sourceRoutes.length===0?'unknown':sourceRoutes[0].split('_')[0];
    if(state.perspective==='routes')root.classList.add(`route-colour-${routeClass}`);
    const matchesProduct = !state.product || members.some(p=>p.steel_products?.values?.includes(state.product));
    const matchesRoute = !state.route || members.some(p=>operatingRoutes(p).some(route=>route.field===state.route));
    if(!selected && (!matchesProduct || !matchesRoute)) root.classList.add('is-dim');
    if(state.product && matchesProduct)root.classList.add('is-product');
    if(state.route && matchesRoute)root.classList.add('is-route');
    if(state.pins?.some(id=>members.some(p=>p.plant_id===id)))root.classList.add('is-pinned');
    root.append(svgel('circle',{cx:x,cy:y,r:Math.max(12*scale,r),class:'hit-target'}));
    if(summary.knownMtpa === null) root.append(svgel('path',{d:`M ${x} ${y-6*scale} L ${x+6*scale} ${y} L ${x} ${y+6*scale} L ${x-6*scale} ${y} Z`,class:'unknown-symbol'}));
    else if(summary.knownMtpa === 0) root.append(svgel('path',{d:`M ${x-5*scale} ${y-5*scale} L ${x+5*scale} ${y+5*scale} M ${x-5*scale} ${y+5*scale} L ${x+5*scale} ${y-5*scale}`,class:'zero-symbol'}));
    else root.append(svgel('circle',{cx:x,cy:y,r,class:'capacity-symbol'}));
    if((radius ?? 0)>13) {const text=svgel('text',{x,y:y+3.5*scale,'font-size':11*scale});text.textContent=mtpa(summary.knownMtpa);root.append(text);}
    if(mixed){const text=svgel('text',{x:x+r+4*scale,y:y-r+4*scale,'font-size':12*scale,class:'partial-marker'});text.textContent=summary.has_unquantified_positive?'+':'?';root.append(text);}
    if(members.length>1){const text=svgel('text',{x,y:y+Math.max(r,8*scale)+13*scale,'font-size':10*scale,'stroke-width':3*scale,class:'map-label'});text.textContent=`${members.length} sites`;root.append(text);}
    const pinIndex=state.pins?.indexOf(first.plant_id) ?? -1;
    if(selected || pinIndex>=0 || members.some(p=>topIds.has(p.plant_id)) || country && members.length > 30) {
      const text=svgel('text',{x,y:y-Math.max(r,8*scale)-8*scale,'font-size':11*scale,'stroke-width':3*scale,class:'map-label'});
      const cities=[...new Set(members.map(p=>p.municipality).filter(v=>v && v!=='unknown'))];
      const groupLabel=members.length>1 ? `${cities.length===1?cities[0]:'Nearby sites'} · ${members.length} sites` : first.plant_name.replace(/ steel plant$/i,'').replace(/ Steel Works$/i,'');
      text.textContent=country || `${pinIndex>=0?`${String.fromCharCode(65+pinIndex)} · `:''}${groupLabel}`;
      if((x-c.x)/scale<160)text.setAttribute('text-anchor','start');root.append(text);
    }
    const activate=()=>{
      if(country && members.length>1)dispatch({type:'country',country});
      else if(members.length>1){
        history.push(snapshot());state.camera=fittedCamera(members);
        const city=members[0].municipality;
        state=evidenceReducer(state,{type:'search',query:city && members.every(p=>p.municipality===city) ? city : ''},plants);
        ranksVisible=true;render();
      }
      else dispatch({type:'select',id:first.plant_id});
    };
    root.addEventListener('click',event=>{if(!drag?.moved)activate();event.stopPropagation();});
    root.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();activate();}});
    root.addEventListener('pointerenter',()=>preview(members));root.addEventListener('focus',()=>preview(members));
    root.addEventListener('pointerleave',()=>preview([]));root.addEventListener('blur',()=>preview([]));
    $('map-points').append(root);
  }
  if(state.selectedId && map.clientWidth>650){
    const selected=records.find(p=>p.plant_id===state.selectedId);
    if(selected){const [x,y]=project([selected.longitude,selected.latitude]);const endX=c.x+c.width*.56,endY=c.y+c.height*.32;
      $('site-leaders').append(svgel('path',{d:`M ${x} ${y} L ${endX-12*scale} ${y} L ${endX} ${endY}`,class:'site-leader'}));
    }
  }
}
function preview(members) {
  const ids = new Set(members.map(p=>p.plant_id));
  state = evidenceReducer(state,{type:'hover',id:members[0]?.plant_id ?? null},plants);
  const amount = members.length ? scopeCapacitySummary(members).operating : null;
  $('map-preview').textContent = members.length ? `${members.length > 1 ? `${members.length} grouped sites` : members[0].plant_name} · ${amount.knownMtpa === null ? 'operating capacity not quantified' : `${mtpa(amount.knownMtpa)} Mtpa known operating capacity`}${amount.has_unquantified_positive ? ' + unquantified positive' : ''}${members.some(p => p.coordinate_accuracy === 'approximate') ? ' · approximate coordinates present' : ''}` : state.product ? `Source product highlight: ${state.product}. Missing labels are unclassified.` : 'Select a site to explore capacity, technology and reported production.';
  for (const row of document.querySelectorAll('.plant-row')) row.classList.toggle('is-hover',ids.has(row.dataset.plantId));
  for (const point of $('map-points').children) point.classList.toggle('is-hover',point.dataset.plantIds.split(' ').some(id=>ids.has(id)));
  for (const segment of document.querySelectorAll('[data-plant-id]')) segment.classList.toggle('is-hover',ids.has(segment.dataset.plantId));
}
function renderList(records) {
  const matchIds = new Set(searchPlants(records,state.query).map(p=>p.plant_id));
  const ranked = rankCapacityPlants(records);
  const found = ranked.map((row,index)=>({...row,rank:index+1})).filter(row=>matchIds.has(row.plant.plant_id));
  const visible = allResults ? found : found.slice(0,100);
  $('records-heading').textContent = `${count(records.length)} tracked sites`;
  $('list-note').textContent = state.query ? `${found.length} search matches · country capacity denominator unchanged.` : 'Share of the known operating component in this scope.';
  $('plant-list').replaceChildren();
  if(!found.length)$('plant-list').append(el('p','No plants match this search. Clear the search or change the geographic scope.','empty'));
  for(const item of visible){
    const {plant,operating,routes,share,rank}=item;
    const row=el('button',undefined,`plant-row${plant.plant_id===state.selectedId?' is-selected':''}`);
    row.dataset.plantId=plant.plant_id;row.dataset.focusKey=`row-${plant.plant_id}`;row.setAttribute('aria-pressed',String(plant.plant_id===state.selectedId));
    const title=el('span',plant.plant_name,'plant-name');title.prepend(el('span',String(rank).padStart(2,'0'),'plant-rank'));
    const measure=el('div',undefined,'plant-measure');
    measure.append(el('strong',operating.knownMtpa===null?'Not quantified':`${mtpa(operating.knownMtpa)} Mtpa${operating.has_unquantified_positive?' +':''}`));
    measure.append(el('span',share===null?'No numeric share':`${percent(share)} of known scope`));
    const track=el('div',undefined,'plant-share-track'), fill=el('span');fill.style.width=`${(share ?? 0)*100}%`;track.append(fill);track.setAttribute('aria-hidden','true');
    row.append(title,measure,track,el('small',`${routes.map(r=>r.label).join(' / ') || 'Operating route not established'} · ${plant.municipality || plant.country_area}${plant.coordinate_accuracy==='approximate'?' · approximate location':''}`));
    row.addEventListener('click',()=>dispatch({type:'select',id:plant.plant_id}));
    row.addEventListener('pointerenter',()=>preview([plant]));row.addEventListener('pointerleave',()=>preview([]));
    row.addEventListener('focus',()=>preview([plant]));row.addEventListener('blur',()=>preview([]));
    $('plant-list').append(row);
  }
  if(visible.length<found.length){const more=el('button',`Show all ${count(found.length)} matching sites`);more.addEventListener('click',()=>{allResults=true;renderList(records);});$('plant-list').append(more);}
}
function renderSelectedSite(records) {
  const plant=records.find(p=>p.plant_id===state.selectedId),target=$('site-explorer');
  target.hidden=!plant || state.comparisonVisible;
  if(!plant){target.replaceChildren();siteSignature='';return;}
  const signature=JSON.stringify([plant.plant_id,state.product,state.processStage,state.productionYear,state.siteView,state.route,state.pins]);
  if(signature===siteSignature && target.childElementCount)return;
  const samePlant=target.dataset.plantId===plant.plant_id && target.dataset.siteView===(state.siteView || 'process');
  const scrollTop=samePlant ? target.scrollTop : 0, innerScroll=samePlant ? target.firstElementChild?.scrollTop ?? 0 : 0;
  const panel=renderSiteExplorer({
    plant, records, scopeName:scopeName(), state,
    onSelect:id=>dispatch({type:'select',id}),
    onHover:value=>preview(Array.isArray(value)?value:records.filter(p=>p.plant_id===value)),
    onProduct:value=>dispatch({type:'product',value}),
    onProcess:value=>dispatch({type:'process',value}),
    onYear:value=>dispatch({type:'year',value}),
    onRoute:value=>dispatch({type:'route',value}),
    onPin:id=>dispatch({type:'pin',id}),
    onSiteView:value=>dispatch({type:'siteView',value}),
    onClose:()=>dispatch({type:'clear'}),
    sourceDetails:buildSourceDetails(plant),
  });
  target.replaceChildren(panel);target.scrollTop=scrollTop;panel.scrollTop=innerScroll;
  target.dataset.plantId=plant.plant_id;target.dataset.siteView=state.siteView || 'process';siteSignature=signature;
}
function renderComparison(records) {
  const target=$('map-comparison');target.hidden=state.pins?.length!==2 || !state.comparisonVisible;
  target.replaceChildren();if(target.hidden)return;
  target.append(renderSiteComparison({records,state,onSelect:id=>dispatch({type:'select',id}),onUnpin:id=>dispatch({type:'unpin',id}),onHover:members=>preview(members),onClose:()=>dispatch({type:'clearPins'})}));
}
function buildSourceDetails(plant) {
  const box = el('section',undefined,'detail');
  box.append(el('p','Source facts · selected plant','eyebrow'),el('h3',plant.plant_name),el('p',plant.plant_id,'detail-id'));
  box.append(el('p',`${sourceText(plant.municipality)}, ${plant.country_area} · ${plant.coordinate_accuracy} coordinates`));
  if (plant.coordinate_accuracy==='approximate') box.append(el('p','Approximate location: no basin assignment or site-level water claim is established.','caveat'));
  const dl = el('dl');
  for (const [name,value] of [['Immediate owner / operator (GEM)',sourceText(plant.owner_name)],['Immediate-owner GEM identity',usableOwnerId(plant.owner_gem_entity_id) || `${sourceText(plant.owner_gem_entity_id)} · no usable identity established`],['Parent display · unparsed source text',sourceText(plant.parent_display)]]) dl.append(el('dt',name),el('dd',value));
  box.append(dl,el('p','Parent text is not a resolved relationship or an ownership network.','caveat'));
  for (const tranche of [...plant.capacity.tranches].sort((a,b)=>Number(!a.status.startsWith('operating'))-Number(!b.status.startsWith('operating')))) {
    box.append(el('p',`Source status: ${tranche.status}`,'tranche-heading'));
    const table = el('table'), head = el('thead'), header = el('tr'); header.append(el('th','Capacity'),el('th','Source value')); head.append(header); table.append(head);
    const body = el('tbody');
    for (const key of ['crude_steel_capacity_ttpa','iron_capacity_ttpa']) { const row = el('tr');row.append(el('td',CAPACITY_FIELDS[key]),el('td',formatCapacity(tranche[key])));body.append(row); }
    table.append(body);box.append(table);
    const details=el('details');details.append(el('summary','Technology breakdowns (not additional capacity)'));
    const routes=el('table'), routebody=el('tbody');
    for(const [key,label] of Object.entries(CAPACITY_FIELDS).filter(([key])=>!['crude_steel_capacity_ttpa','iron_capacity_ttpa'].includes(key))){const row=el('tr');row.append(el('th',label),el('td',formatCapacity(tranche[key])));routebody.append(row);}
    routes.append(routebody);details.append(routes);box.append(details);
  }
  box.append(el('p','kt/year = thousand tonnes per year. Capacity is not production or available supply.','caveat'));
  try { const url = new URL(plant.wiki_url); if(url.protocol==='https:' && url.hostname==='www.gem.wiki'){const link=el('a','Open GEM source page ↗');link.href=url.href;link.target='_blank';link.rel='noreferrer';box.append(link);} } catch { box.append(el('p','No usable source-page URL.')); }
  return box;
}
function wire() {
  $('quick-search').addEventListener('input',event=>{ranksVisible=Boolean(event.target.value);allResults=false;dispatch({type:'search',query:event.target.value},false);});
  $('route-filter').addEventListener('change',event=>dispatch({type:'route',value:event.target.value || null}));
  $('map-perspective').addEventListener('change',event=>dispatch({type:'perspective',value:event.target.value}));
  $('show-comparison').addEventListener('click',()=>dispatch({type:'compare'}));
  $('toggle-ranking').addEventListener('click',()=>{ranksVisible=!ranksVisible;render();});
  $('region').addEventListener('change',event=>dispatch({type:'region',region:event.target.value}));
  $('country').addEventListener('change',event=>dispatch({type:'country',country:event.target.value}));
  $('plant-search').addEventListener('input',event=>{allResults=false;dispatch({type:'search',query:event.target.value},false);});
  $('plants-layer').addEventListener('change',event=>dispatch({type:'layer',visible:event.target.checked}));
  $('clear-selection').addEventListener('click',()=>dispatch({type:'clear'}));
  $('back').addEventListener('click',()=>{if(history.length){state=history.pop();ranksVisible=Boolean(state.ranksVisible);allResults=false;render();}});
  $('reset-investigation').addEventListener('click',()=>{history.push(snapshot());state=initialEvidenceState(plants);state.camera=fittedCamera(scoped());allResults=false;render(true);});
  $('reset-camera').addEventListener('click',()=>setCamera(fittedCamera(scoped())));
  $('zoom-in').addEventListener('click',()=>zoom(.7)); $('zoom-out').addEventListener('click',()=>zoom(1/.7));
  map.addEventListener('wheel',event=>{event.preventDefault();zoom(event.deltaY>0?1.15:1/1.15);},{passive:false});
  map.addEventListener('keydown',event=>{
    if(event.target!==map)return;
    const c=state.camera;
    if(['+','=','-','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)) event.preventDefault();
    if(event.key==='+'||event.key==='=')zoom(.7);if(event.key==='-')zoom(1/.7);
    if(event.key.startsWith('Arrow'))setCamera({...c,x:c.x+(event.key==='ArrowLeft'?-.12:event.key==='ArrowRight'?.12:0)*c.width,y:c.y+(event.key==='ArrowUp'?-.12:event.key==='ArrowDown'?.12:0)*c.height});
  });
  map.addEventListener('pointerdown',event=>{if(event.target.closest('.point'))return;drag={x:event.clientX,y:event.clientY,camera:{...state.camera},moved:false};map.setPointerCapture(event.pointerId);});
  map.addEventListener('pointermove',event=>{if(!drag)return;const dx=event.clientX-drag.x,dy=event.clientY-drag.y;drag.moved=drag.moved||Math.abs(dx)+Math.abs(dy)>4;setCamera({...drag.camera,x:drag.camera.x-dx/map.clientWidth*drag.camera.width,y:drag.camera.y-dy/map.clientHeight*drag.camera.height});});
  const finish=()=>{drag=null;};map.addEventListener('pointerup',finish);map.addEventListener('pointercancel',finish);
  let lastMapSize='';
  new ResizeObserver(()=>{
    const size=`${map.clientWidth}:${map.clientHeight}`;
    if(state && size!==lastMapSize && map.clientWidth && map.clientHeight){lastMapSize=size;setCamera(state.camera);}
  }).observe(map);
}
load();
