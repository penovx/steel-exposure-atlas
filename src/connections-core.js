(()=>{
// Pure, identical rules for every plant. There are no featured IDs or names.
const OPERATING = new Set(['operating','operating pre-retirement']);
const ROUTES = [
 {id:'BOF',field:'bof_steel_capacity_ttpa',name:'Basic oxygen furnace',color:'#8ebbd8'},
 {id:'EAF',field:'eaf_steel_capacity_ttpa',name:'Electric arc furnace',color:'#c9bbf0'},
 {id:'IF',field:'if_steel_capacity_ttpa',name:'Induction furnace',color:'#e8cd96'},
 {id:'Other',field:'other_steel_capacity_ttpa',name:'Other steelmaking',color:'#a2b0bb'}
];
function amount(rows,field) {
 const result={known:null,numeric:0,positive:0,unknown:0,blank:0,na:0};
 for(const row of rows){const v=row[field];if(!v)throw new Error('Missing measure: '+field);
  if(v.state==='numeric'){
   if(typeof v.value_ttpa!=='number'||!Number.isFinite(v.value_ttpa)||v.value_ttpa<0)throw new Error('Invalid numeric capacity');
   result.known=(result.known??0)+v.value_ttpa;result.numeric++;
  }else{
   if(v.value_ttpa!==null)throw new Error('Nonnumeric value must stay null');
   const keys={'>0':'positive','unknown':'unknown','blank':'blank','N/A':'na'};
   if(!keys[v.state])throw new Error('Unexpected measure state: '+v.state);
   result[keys[v.state]]++;
  }
 }
 return result;
}
function total(plants,field='crude_steel_capacity_ttpa') {
 return amount(plants.flatMap(p=>p.tranches.filter(t=>OPERATING.has(t.status))),field);
}
function usableOwner(p){return typeof p.ownerId==='string'&&/^E\d+$/.test(p.ownerId)&&typeof p.owner==='string'&&p.owner.trim()!==''&&!['unknown','n/a'].includes(p.owner.trim().toLowerCase())?p.ownerId:null;}
function hasRoute(p,id){const route=ROUTES.find(r=>r.id===id);return !!route&&p.tranches.some(t=>OPERATING.has(t.status)&&(t[route.field].state==='>0'||t[route.field].state==='numeric'&&t[route.field].value_ttpa>0));}
function filterPlants(plants,filters,ignore=null){
 const selectedProducts=Array.isArray(filters.products)?filters.products:(filters.product?[filters.product]:[]);
 const productMode=filters.productMode==='all'?'all':'any';
 return plants.filter(p=>{
  const productMatch=ignore==='product'||selectedProducts.length===0||(productMode==='all'?selectedProducts.every(id=>p.products.values.includes(id)):selectedProducts.some(id=>p.products.values.includes(id)));
  return (ignore==='country'||!filters.country||p.country===filters.country)&&(ignore==='owner'||!filters.owner||usableOwner(p)===filters.owner)&&productMatch&&(ignore==='route'||!filters.route||hasRoute(p,filters.route));
 });
}
function owners(plants){const groups=new Map();for(const p of plants){const id=usableOwner(p);if(!id)continue;if(!groups.has(id))groups.set(id,{id,name:p.owner,members:[],names:new Set()});const group=groups.get(id);group.members.push(p);group.names.add(p.owner);}return [...groups.values()].sort((a,b)=>b.members.length-a.members.length||a.name.localeCompare(b.name,'en'));}
function products(plants){const groups=new Map();for(const p of plants)for(const name of new Set(p.products.values)){if(!groups.has(name))groups.set(name,{id:name,name,members:[]});groups.get(name).members.push(p);}return [...groups.values()].sort((a,b)=>b.members.length-a.members.length||a.name.localeCompare(b.name,'en'));}
function capacity(p){return total([p]);}
function circleRadius(value,scale=1){return value===null||value<=0?0:Math.sqrt(value/1000)*3.3*scale;}
function aggregateGroups(plants,position,focused,zoom=1){
 const result=[];const threshold=zoom>2?5:zoom>1.4?9:13;
 for(const p of [...plants].sort((a,b)=>a.id.localeCompare(b.id))){
  const [x,y]=position(p);if(!Number.isFinite(x)||!Number.isFinite(y))continue;
  const cap=capacity(p);const hot=focused===null||focused.has(p.id);const kind=cap.known!==null&&cap.known>0?'numeric':'other';
  const target=result.find(g=>g.hot===hot&&g.kind===kind&&Math.hypot(g.x-x,g.y-y)<threshold);
  if(target){const n=target.members.length;target.x=(target.x*n+x)/(n+1);target.y=(target.y*n+y)/(n+1);target.members.push(p);target.known=target.known===null?cap.known:cap.known===null?target.known:target.known+cap.known;target.positive+=cap.positive;}
  else result.push({x,y,hot,kind,members:[p],known:cap.known,positive:cap.positive});
 }
 return result;
}

'use strict';
(() => {
const $=(q,root=document)=>root.querySelector(q), $$=(q,root=document)=>[...root.querySelectorAll(q)];
const NS='http://www.w3.org/2000/svg';
const svgEl=(tag,attrs={},text)=>{const n=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;return n;};
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=(v,d=0)=>Number(v).toLocaleString('en-GB',{maximumFractionDigits:d,minimumFractionDigits:d});
const mt=(v,d=2)=>v===null?'—':num(v/1000,d);
const bounded=(v,a,b)=>Math.max(a,Math.min(v,b));
const DATA=window.__ATLAS_DATA__;if(!DATA)throw new Error('Atlas runtime data was not loaded.');
const all=DATA.plants;const lookup=new Map(all.map(p=>[p.id,p]));
const state={region:'Europe',filters:{country:null,owner:null,products:[],productMode:'any',route:null},site:null,camera:{zoom:1,x:0,y:0}};
const regions=['World','Europe','North America','Central & South America','Asia Pacific','Africa','Middle East','Eurasia'];
let base=[],matched=[],focusSet=null,companyHighlightSet=null,ownerList=[],productList=[],nodePositions=new Map(),hover=null,view={s:1,tx:0,ty:0},size={w:700,h:470},pan=null,suppressUntil=0,queued=0,browseMode='site',browseSubset=null,renderCount=0;
const schemaExpected='steel-exposure-atlas/relational-entry-v2';
if(DATA.schema!==schemaExpected||all.length!==1293||lookup.size!==1293)throw new Error('Unexpected atlas data');
for(const p of all){for(const t of p.tranches)amount([t],'crude_steel_capacity_ttpa');if(!Number.isFinite(p.latitude)||!Number.isFinite(p.longitude))throw new Error('Invalid coordinates');}
const capCache=new Map(all.map(p=>[p.id,capacity(p)]));
const ownCache=new Map(all.map(p=>[p.id,usableOwner(p)]));
function current(){return state.site?matched.filter(p=>p.id===state.site):matched;}
function hasFilters(){const f=state.filters;return !!(f.country||f.owner||f.route||f.products.length);}
function isFocused(){return hasFilters()||!!state.site;}
function hasMapFocus(){const f=state.filters;return !!(state.site||f.country||f.route||f.products.length);}
function groupName(id){return all.find(p=>ownCache.get(p.id)===id)?.owner??id;}
function routeName(id){return ROUTES.find(r=>r.id===id)?.name??id;}
function labelFor(kind,id){return kind==='owner'?groupName(id):kind==='route'?routeName(id):id;}
function countryGroups(ps){const m=new Map();for(const p of ps){if(!m.has(p.country))m.set(p.country,{id:p.country,name:p.country,members:[]});m.get(p.country).members.push(p);}return [...m.values()].sort((a,b)=>b.members.length-a.members.length||a.name.localeCompare(b.name));}
function queueMap(){if(!queued)queued=requestAnimationFrame(()=>{queued=0;drawMap();});}
function update(){
 base=state.region==='World'?all:all.filter(p=>p.region===state.region);
 matched=filterPlants(base,state.filters);
 if(state.site&&!matched.some(p=>p.id===state.site))state.site=null;
 const chosen=current(),chosenIds=new Set(chosen.map(p=>p.id));
 focusSet=hasMapFocus()?chosenIds:null;
 companyHighlightSet=state.filters.owner?new Set(base.filter(p=>ownCache.get(p.id)===state.filters.owner).map(p=>p.id)):null;
 $('#region-title').textContent=state.region;$('#scope-meta').textContent=`${num(base.length)} tracked sites · June 2026`;
 $('#clear-all').hidden=!isFocused();
 const availableOwners=owners(base),selectionOwners=new Set(owners(chosen).map(g=>g.id));
 ownerList=[...availableOwners].sort((a,b)=>Number(selectionOwners.has(b.id))-Number(selectionOwners.has(a.id))||b.members.length-a.members.length||a.name.localeCompare(b.name)).slice(0,5);
 // A selected company is retained even for an empty cross-filter result.
 if(state.filters.owner&&!ownerList.some(g=>g.id===state.filters.owner)){const g=availableOwners.find(o=>o.id===state.filters.owner);if(g)ownerList=[g,...ownerList.slice(0,4)];}
 $('#company-total').textContent=num(availableOwners.length);
 $('#company-nodes').innerHTML=ownerList.map(g=>{
  const related=chosen.filter(p=>ownCache.get(p.id)===g.id).length;
  const select=state.filters.owner===g.id;const dim=isFocused()&&!related;
  return `<button class="company-node${select?' is-selected':''}${dim?' dim':''}" data-owner="${esc(g.id)}" data-port="owner:${esc(g.id)}" type="button" aria-pressed="${select}" aria-label="${esc(g.name)}, ${g.members.length} sites in ${esc(state.region)}"><span class="company-name">${esc(g.name)}</span><span class="company-count">${g.members.length}</span><span class="company-sub">${isFocused()?`${related} connected · `:''}${g.members.length} sites in scope</span></button>`;
 }).join('');
 const methodMax=Math.max(0,...ROUTES.map(r=>total(base,r.field).known??0));
 $('#method-nodes').innerHTML=ROUTES.map(r=>{
  const complete=total(base,r.field),selected=total(chosen,r.field),value=isFocused()?selected:complete;
  const count=chosen.filter(p=>hasRoute(p,r.id)).length;
  const pct=methodMax>0?(value.known??0)/methodMax*100:0;
  const valid=base.some(p=>hasRoute(p,r.id));
  return `<button class="method-node${state.filters.route===r.id?' is-selected':''}${isFocused()&&!count?' dim':''}" style="--method-color:${r.color};--pct:${pct}%" data-route="${r.id}" data-port="route:${r.id}" type="button" aria-pressed="${state.filters.route===r.id}" ${valid?'':'disabled'}><span class="method-name">${r.name}</span><strong class="method-value">${mt(value.known,value.known>0&&value.known<1000?3:1)}${value.positive?'+':''}<small> Mtpa*</small></strong><span class="method-sub">${count} sites · ${r.id==='Other'?'unspecified':r.id}</span><span class="method-track"><i class="method-fill"></i></span></button>`;
 }).join('');
 const allProducts=products(base),selectedProducts=new Set(state.filters.products),selectionProducts=new Set(products(chosen).map(g=>g.id));
 const rankedProducts=[...allProducts].sort((a,b)=>Number(selectedProducts.has(b.id))-Number(selectedProducts.has(a.id))||Number(selectionProducts.has(b.id))-Number(selectionProducts.has(a.id))||b.members.length-a.members.length||a.name.localeCompare(b.name));
 productList=[...rankedProducts.filter(g=>selectedProducts.has(g.id)),...rankedProducts.filter(g=>!selectedProducts.has(g.id))];
 $('#product-nodes').innerHTML=productList.map(g=>{const n=chosen.filter(p=>p.products.values.includes(g.id)).length;const selected=selectedProducts.has(g.id);return `<button class="product-node${selected?' is-selected':''}${isFocused()&&!n?' dim':''}" type="button" data-product="${esc(g.id)}" data-port="product:${esc(g.id)}" aria-pressed="${selected}" aria-label="${esc(g.name)}, listed at ${g.members.length} plants"><i class="product-port" aria-hidden="true"></i>${esc(g.name)}<span>${isFocused()?n:g.members.length}</span>${selected?'<b class="product-remove" aria-hidden="true">×</b>':''}</button>`;}).join('');
 renderReading(chosen,availableOwners);bindFacets();hover=null;hideTip();queueMap();
 $('#announcement').textContent=isFocused()?`${chosen.length} connected sites in ${state.region}.`: `${base.length} sites in ${state.region}. Choose any connection.`;
 renderCount++;
}
function bindFacets(){for(const [selector,key]of [['[data-owner]','owner'],['[data-product]','product'],['[data-route]','route']])for(const b of $$(selector)){b.onclick=()=>choose(key,b.dataset[key]);b.onpointerenter=()=>setHover(key,b.dataset[key]);b.onpointerleave=()=>setHover(null,null);b.onfocus=()=>setHover(key,b.dataset[key]);b.onblur=()=>setHover(null,null);}}
function choose(kind,id){state.site=null;if(kind==='product'){const set=new Set(state.filters.products);set.has(id)?set.delete(id):set.add(id);state.filters.products=[...set];}else state.filters[kind]=state.filters[kind]===id?null:id;update();}
function chooseSite(id){if(!base.some(p=>p.id===id))return;const fresh=!matched.some(p=>p.id===id);if(fresh)state.filters={country:null,owner:null,products:[],productMode:'any',route:null};state.site=state.site===id?null:id;update();if(fresh)$('#announcement').textContent='A new path starts at this plant; incompatible previous selections were cleared.';}
function clear(){state.filters={country:null,owner:null,products:[],productMode:'any',route:null};state.site=null;update();}
function setRegion(region){if(!regions.includes(region))return;state.region=region;state.filters={country:null,owner:null,products:[],productMode:'any',route:null};state.site=null;state.camera={zoom:1,x:0,y:0};update();}
function matchingHover(kind,id){if(kind==='site')return new Set([id]);if(kind==='members')return new Set(id);if(kind==='country')return new Set(base.filter(p=>p.country===id).map(p=>p.id));if(kind==='owner')return new Set(base.filter(p=>ownCache.get(p.id)===id).map(p=>p.id));if(kind==='route')return new Set(base.filter(p=>hasRoute(p,id)).map(p=>p.id));if(kind==='product')return new Set(base.filter(p=>p.products.values.includes(id)).map(p=>p.id));return null;}
function setHover(kind,id){hover=kind?{kind,id,ids:matchingHover(kind,id)}:null;applyEmphasis();}
function applyEmphasis(){const active=hover?.ids??focusSet;for(const n of $$('.plant-node')){const ids=n.dataset.members.split(' ');n.classList.toggle('dim',!!active&&!ids.some(id=>active.has(id)));}for(const n of $$('.connection-edge')){const hot=!active||active.has(n.dataset.site);n.classList.toggle('dim',!hot);n.classList.toggle('strong',!!active&&hot);}for(const [selector,key]of [['[data-owner]','owner'],['[data-route]','route'],['[data-product]','product']])for(const n of $$(selector)){const set=matchingHover(key,n.dataset[key]);n.classList.toggle('dim',!!active&&![...active].some(id=>set.has(id)));}}
function renderReading(chosen,availableOwners){
 const f=state.filters;
 const productTokens=f.products.map(v=>`<button class="path-token" type="button" data-remove-product="${esc(v)}"><small>PRODUCT</small>${esc(v)}<span aria-hidden="true">×</span></button>`).join('');
 const scalarTokens=[['country','PLACE'],['owner','COMPANY'],['route','METHOD']].filter(([k])=>f[k]).map(([k,label])=>`<button class="path-token" type="button" data-remove="${k}"><small>${label}</small>${esc(labelFor(k,f[k]))}<span aria-hidden="true">×</span></button>`).join('');
 const modeToken=f.products.length>1?`<button class="path-token mode-token" type="button" id="product-mode-token"><small>PRODUCT MATCH</small>${f.productMode==='all'?'All selected':'Any selected'}<span aria-hidden="true">↗</span></button>`:'';
 $('#selection-path').innerHTML=`<span class="path-base">${esc(state.region)} <span aria-hidden="true">/</span></span>`+scalarTokens+productTokens+modeToken+(state.site?`<button class="path-token" type="button" data-remove="site"><small>PLANT</small>${esc(lookup.get(state.site).city==='unknown'?lookup.get(state.site).name:lookup.get(state.site).city)}<span aria-hidden="true">×</span></button>`:'');
 for(const n of $$('[data-remove]'))n.onclick=()=>{if(n.dataset.remove==='site')state.site=null;else state.filters[n.dataset.remove]=null;update();};
 for(const n of $$('[data-remove-product]'))n.onclick=()=>choose('product',n.dataset.removeProduct);
 if($('#product-mode-token'))$('#product-mode-token').onclick=()=>openBrowse('product');
 const cap=total(chosen),full=total(base),own=owners(chosen),missing=chosen.filter(p=>!ownCache.get(p.id)).length;
 const countryCount=new Set(base.map(p=>p.country)).size;
 let title=`${num(base.length)} steel sites across ${num(countryCount)} countries.`,description='Ownership, products and steelmaking methods are linked to the same plants. Narrowing one dimension updates the others while the geographic scope stays fixed.',kicker='CURRENT SCOPE';
 if(isFocused()){
  kicker=`${chosen.length} CONNECTED ${chosen.length===1?'SITE':'SITES'} · ${new Set(chosen.map(p=>p.country)).size} ${new Set(chosen.map(p=>p.country)).size===1?'COUNTRY':'COUNTRIES'}`;
  const productTitle=f.products.length?`${f.products.join(f.productMode==='all'?' + ':' / ')}`:null;
  title=state.site?lookup.get(state.site).name:f.owner?groupName(f.owner):productTitle?productTitle:f.route?routeName(f.route):f.country;
  description=state.site?'Its company, products and production methods connect this plant to other sites in the same scope.':f.owner?'These locations share the company named by GEM as their immediate owner or operator. Different company names elsewhere do not prove separate ultimate ownership.':f.route?'These sites have positive operating capacity for this steelmaking method in the June 2026 snapshot. Other methods may coexist at the same site.':f.products.length?`These plants list ${f.products.length>1?(f.productMode==='all'?'all selected products':'at least one selected product'):'this product'}. Their steelmaking capacity is not product-specific capacity or available supply.`:f.country?'The map and connected fields describe the plants within this place.':'The same plants are being read through several connected dimensions.';
  if(!chosen.length){title='No sites connect all these choices.';description='Remove a selection above to widen the view. This is a result within the supplied snapshot, not evidence that no such supplier exists.';}
 }
 $('#reading-kicker').textContent=kicker;$('#reading-title').textContent=title;$('#reading-description').textContent=description;
 $('#inspect-selection').innerHTML=`${state.site?'Check this plant’s evidence':isFocused()?'Inspect these sites':'Browse this region'} <span aria-hidden="true">↗</span>`;
 $('#connection-caption').textContent=isFocused()?`${chosen.length} connected sites of ${base.length} in ${state.region}. Product and technology connections describe the same plants, not material flows.`:'The same plants connect geography, companies, products and steelmaking methods.';
 $('#summary-data').hidden=!!state.site;$('#site-detail').hidden=!state.site;
 if(!state.site){
  const displayCap=cap.known===null?'Not quantified':`${mt(cap.known,3)}${cap.positive?' +':''} Mtpa`;
  $('#summary-data').innerHTML=`<div class="summary-row"><span>${isFocused()?'Connected sites':'Tracked sites in scope'}</span><strong>${num(chosen.length)}</strong></div><div class="summary-row"><span>Known operating crude-steel capacity</span><strong>${displayCap}</strong></div><div class="summary-row"><span>Companies named as owner / operator</span><strong>${own.length}${missing?' + ?':''}</strong></div><p class="summary-note">${missing?`${missing} sites do not have one usable company identity. `:''}${cap.positive?'Additional positive capacity is not quantified. ':''}Counts are not counts of independent suppliers. ${isFocused()?`Full ${esc(state.region)} scope: ${full.known===null?'no numeric total':mt(full.known,3)+' Mtpa'} of known operating crude-steel capacity. `:''}Map movement does not change the analytical scope.</p>`;
 }else renderSiteDetail(lookup.get(state.site));
}
function renderSiteDetail(p){
 const routeRows=p.tranches.flatMap(t=>ROUTES.filter(r=>t[r.field].state==='numeric'||t[r.field].state==='>0').map(r=>({r,t,v:t[r.field]})));
 const productButtons=p.products.values.slice(0,12).map(v=>`<button type="button" data-product="${esc(v)}">${esc(v)}</button>`).join('');
 const vals=p.production?Object.values(p.production).filter(v=>v.state==='numeric').map(v=>v.value_ttpa):[];const max=vals.length?Math.max(...vals):0;
 const production=p.production?`<p class="summary-note">Reported crude-steel production · thousand tonnes · gaps remain gaps</p><div class="production-history">${Object.entries(p.production).map(([yr,v])=>`<div class="production-column"><em>${v.state==='numeric'?num(v.value_ttpa):'—'}</em><i style="--h:${v.state==='numeric'&&max>0?v.value_ttpa/max*43:0}px;${v.state==='numeric'?'':'visibility:hidden'}"></i><span>${yr}</span></div>`).join('')}</div>`:'';
 $('#site-detail').innerHTML=`<div class="site-details"><h3>${esc(p.city==='unknown'?p.name:p.city)}</h3><div class="detail-rows"><div><span>Country</span><button class="detail-button" data-country-action="${esc(p.country)}">${esc(p.country)} ↗</button></div><div><span>Company</span>${ownCache.get(p.id)?`<button class="detail-button" data-owner="${esc(p.ownerId)}">${esc(p.owner)} ↗</button>`:`<span>${esc(p.owner)}</span>`}</div>${routeRows.map(({r,t,v})=>`<div><button class="detail-button" data-route="${r.id}">${r.id}</button><span>${v.state==='numeric'?mt(v.value_ttpa,2)+' Mtpa':'Positive, unquantified'}<br><small>${esc(t.status)}</small></span></div>`).join('')}</div><div class="details-products">${productButtons}</div>${production}<p class="summary-note">${esc(p.name)}<br>Location: ${esc(p.accuracy)} according to GEM. Capacity figures are not product-specific or available supply.</p></div>`;
 $$('[data-country-action]').forEach(n=>n.onclick=()=>choose('country',n.dataset.countryAction));
}
function pathRings(rings){return rings.map(r=>'M'+r.map(pt=>pt.join(',')).join('L')+'Z').join('');}
function fit(){const box=$('#geography').getBoundingClientRect();size={w:box.width,h:box.height};const extent=DATA.maps[state.region].extent;const [x0,y0,x1,y1]=extent;const padding=size.w<450?28:35;const safeH=size.h-52;const s=Math.min((size.w-padding*2)/(x1-x0),(safeH-padding*2)/(y1-y0));const z=state.camera.zoom;view={s:s*z,tx:size.w/2-(x0+x1)/2*s*z+state.camera.x,ty:safeH/2-(y0+y1)/2*s*z+state.camera.y+7};}
function pos(p){const xy=DATA.maps[state.region].positions[p.id];return xy?[xy[0]*view.s+view.tx,xy[1]*view.s+view.ty]:[NaN,NaN];}
function drawMap(){
 fit();const svg=$('#geo-map');svg.setAttribute('viewBox',`0 0 ${size.w} ${size.h}`);$('#map-clip-rect').setAttribute('width',size.w);$('#map-clip-rect').setAttribute('height',size.h);
 const map=DATA.maps[state.region],land=$('#land-layer'),countries=new Map(countryGroups(base).map(g=>[g.id,g]));
 land.replaceChildren();for(const c of map.countries){const n=svgEl('path',{d:pathRings(c.rings),class:`land${countries.has(c.name)?' with-sites':''}${state.filters.country===c.name?' selected':''}`,'data-geo-name':c.name});n.addEventListener('click',()=>{if(performance.now()>suppressUntil&&countries.has(c.name))choose('country',c.name);});if(countries.has(c.name)){n.addEventListener('pointermove',e=>showTip(c.name,`${countries.get(c.name).members.length} sites · click to follow`,e));n.addEventListener('pointerleave',hideTip);}land.append(n);}
 land.setAttribute('transform',`translate(${view.tx} ${view.ty}) scale(${view.s})`);
 const groups=aggregateGroups(base,pos,focusSet,state.camera.zoom);
 const labels=$('#country-labels');labels.replaceChildren();const rectangles=[];
 const labelCandidates=map.countries.filter(c=>countries.has(c.name)).sort((a,b)=>Number(b.name===state.filters.country)-Number(a.name===state.filters.country)||(countries.get(b.name)?.members.length??0)-(countries.get(a.name)?.members.length??0));
 for(const c of labelCandidates){
  const originalX=c.label[0]*view.s+view.tx,originalY=c.label[1]*view.s+view.ty;
  const name=c.name==='Bosnia and Herzegovina'?'BOSNIA & HERZ.':c.name.toUpperCase();
  const w=name.length*(size.w<450?6:7);let placed=null;
  const offsets=[[0,0],[0,-19],[0,19],[-26,-16],[26,16],[0,-38],[0,38],[-44,-25],[44,25],[-52,4],[52,-4],[0,58],[0,-58],[-70,-30],[70,30]];
  for(const [dx,dy]of offsets){const x=originalX+dx,y=originalY+dy;const rect={x:x-w/2,y:y-12,w,h:18};
   if(x<w/2+4||x>size.w-w/2-4||y<15||y>size.h-56)continue;
   if(rectangles.some(r=>rect.x<r.x+r.w+5&&rect.x+w>r.x-5&&rect.y<r.y+r.h+3&&rect.y+18>r.y-3))continue;
   if(groups.some(g=>{const rad=Math.max(10,circleRadius(g.known,size.w<450?.82:1)+5);return g.x+rad>rect.x&&g.x-rad<rect.x+rect.w&&g.y+rad>rect.y&&g.y-rad<rect.y+rect.h;}))continue;
   placed={x,y,rect};break;
  }
  if(!placed)continue;if(rectangles.length>=(size.w<450?9:17))break;
  const {x,y,rect}=placed;rectangles.push(rect);
  if(Math.hypot(x-originalX,y-originalY)>9)labels.append(svgEl('path',{d:`M${originalX},${originalY} L${x},${y+4}`,fill:'none',stroke:'#7695a8','stroke-opacity':.5,'stroke-width':.8,'pointer-events':'none'}));
  const n=svgEl('text',{x,y,'text-anchor':'middle',class:`country-label has-sites${c.name===state.filters.country?' is-selected':''}`,tabindex:0,role:'button','aria-label':`Explore ${c.name}`},name);
  n.addEventListener('click',()=>choose('country',c.name));n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose('country',c.name);}});labels.append(n);
 }
 const pointLayer=$('#plant-layer');pointLayer.replaceChildren();nodePositions=new Map();const selected=current();const labelIds=new Set(isFocused()?selected.slice().sort((a,b)=>(capCache.get(b.id).known??-1)-(capCache.get(a.id).known??-1)).slice(0,5).map(p=>p.id):[]);
 for(const g of groups){if(g.x<-20||g.x>size.w+20||g.y<-20||g.y>size.h+20)continue;const ids=g.members.map(p=>p.id);const companyMatch=!!companyHighlightSet&&ids.some(id=>companyHighlightSet.has(id));const r=circleRadius(g.known,size.w<450?.82:1);const visualR=r>0?r:3;const hit=Math.max(visualR+3,10);const group=svgEl('g',{class:`plant-node${!g.hot?' dim':''}${companyMatch?' company-match':''}${ids.includes(state.site)?' selected':''}`,transform:`translate(${g.x} ${g.y})`,tabindex:0,role:'button','data-members':ids.join(' '),'aria-label':g.members.length>1?`Open ${g.members.length} nearby sites`:g.members[0].name});
  group.append(svgEl('circle',{r:hit,class:'plant-hit'}));group.append(svgEl('circle',{r:visualR,class:r>0?'plant-disc':'plant-hollow'}));group.append(svgEl('circle',{r:visualR+5,class:'plant-focus'}));
  if(g.members.some(p=>p.accuracy==='approximate'))group.append(svgEl('circle',{r:visualR+2,fill:'none',stroke:'#d3cbb8','stroke-dasharray':'2 3','stroke-width':.8}));
  if(g.members.length>1)group.append(svgEl('text',{x:visualR+4,y:3,class:'cluster-text',style:'fill:#d1e1eb;paint-order:stroke;stroke:#0c1821;stroke-width:2'},String(g.members.length)));
  if(g.members.length===1&&labelIds.has(g.members[0].id)){const p=g.members[0];const text=p.city==='unknown'?p.name.replace(/ steel plant$/i,''):p.city;const toLeft=g.x>size.w*.64;group.append(svgEl('text',{x:toLeft?-visualR-7:visualR+7,y:-7,'text-anchor':toLeft?'end':'start',class:'plant-name'},text.length>29?text.slice(0,27)+'…':text));}
  const activate=()=>{if(performance.now()<suppressUntil)return;if(g.members.length===1)chooseSite(g.members[0].id);else openBrowse('site',ids);};group.addEventListener('click',activate);group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});
  group.addEventListener('pointermove',e=>{setHover('members',ids);const cap=total(g.members);showTip(g.members.length>1?`${g.members.length} nearby sites`:g.members[0].name,`${g.members.length>1?'Click to see each site · ':g.members[0].country+' · '}${cap.known===null?'No numeric operating crude-steel capacity':mt(cap.known)+' Mtpa known operating crude steel'}`,e);});group.addEventListener('pointerleave',()=>{setHover(null,null);hideTip();});pointLayer.append(group);for(const p of g.members)nodePositions.set(p.id,{x:g.x,y:g.y});
 }
 $('#zoom-level').textContent=state.camera.zoom.toFixed(1)+'×';$('#map-out').disabled=state.camera.zoom<=1;$('#map-in').disabled=state.camera.zoom>=3.2;
 drawEdges();applyEmphasis();
}
function drawEdges(){
 const stage=$('#connections-stage').getBoundingClientRect(),geo=$('#geography').getBoundingClientRect();const svg=$('#connection-lines');svg.setAttribute('viewBox',`0 0 ${stage.width} ${stage.height}`);const edges=$('#edge-layer');edges.replaceChildren();
 const port=(kind,id)=>{const n=$$('[data-port]').find(e=>e.dataset.port===kind+':'+id);if(!n)return null;const b=n.getBoundingClientRect();return kind==='owner'?{x:b.right-stage.left+4,y:b.top-stage.top+b.height/2}:kind==='route'?{x:b.left-stage.left-5,y:b.top-stage.top+13}:{x:b.left-stage.left+b.width/2,y:b.top-stage.top-15};};
 const visibleOwner=new Set(ownerList.map(g=>g.id));
 let records=isFocused()?current():base.filter(p=>visibleOwner.has(ownCache.get(p.id)));
 // Deterministic level of detail, never a hand-picked example. All members remain
 // in counts and can be inspected; dense selections use the largest marks first.
 records=[...records].filter(p=>nodePositions.has(p.id)).sort((a,b)=>(capCache.get(b.id).known??-1)-(capCache.get(a.id).known??-1)||a.id.localeCompare(b.id)).slice(0,80);
 const connection=(p,to,type)=>{const pp=nodePositions.get(p.id);if(!pp||!to)return;const a={x:pp.x+geo.left-stage.left,y:pp.y+geo.top-stage.top};if(pp.x<8||pp.x>size.w-8||pp.y<8||pp.y>size.h-45)return;let d;
 if(stage.width<=760){const spine=stage.width/2+(type==='company'?-5:type==='product'?0:5);const bottom=geo.bottom-stage.top;
  d=`M${a.x},${a.y} C${a.x},${a.y+35} ${spine},${bottom-25} ${spine},${bottom+8} L${spine},${to.y-14} Q${spine},${to.y} ${to.x},${to.y}`;
 }else d=type==='product'?`M${a.x},${a.y} C${a.x},${a.y+(to.y-a.y)*.45} ${to.x},${a.y+(to.y-a.y)*.8} ${to.x},${to.y}`:`M${a.x},${a.y} C${a.x+(to.x-a.x)*.45},${a.y} ${to.x-(to.x-a.x)*.2},${to.y} ${to.x},${to.y}`;edges.append(svgEl('path',{d,class:`connection-edge ${type}`,'data-site':p.id}));};
 for(const p of records){connection(p,port('owner',ownCache.get(p.id)),'company');for(const r of ROUTES)if(hasRoute(p,r.id))connection(p,port('route',r.id),'route-'+r.id);const tags=productList.filter(g=>p.products.values.includes(g.id));const linkedProducts=selectedProducts.size?tags.filter(g=>selectedProducts.has(g.id)):tags.slice(0,1);for(const tag of linkedProducts)connection(p,port('product',tag.id),'product');}
}
function showTip(title,sub,event){const tip=$('#map-tip'),r=$('#geography').getBoundingClientRect();tip.innerHTML=`<strong>${esc(title)}</strong><span>${esc(sub)}</span>`;tip.hidden=false;const x=bounded(event.clientX-r.left+16,7,Math.max(7,r.width-tip.offsetWidth-7)),y=bounded(event.clientY-r.top+15,7,Math.max(7,r.height-tip.offsetHeight-8));tip.style.left=x+'px';tip.style.top=y+'px';}
function hideTip(){$('#map-tip').hidden=true;}
function openDialog(id){const d=$(id);if(!d.open)d.showModal();}
function closeDialog(n){const d=n.closest('dialog');if(d)d.close();}
$$('[data-close-dialog]').forEach(n=>n.onclick=()=>closeDialog(n));
for(const dialog of $$('dialog'))dialog.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();dialog.close();}},true);
function openBrowse(kind='site',ids=null){
 browseMode=kind;browseSubset=ids;$('#browse-query').value='';
 $('#browse-title').textContent=({site:'Find a plant.',owner:'Choose a company.',product:'Choose products.',route:'Choose a production method.'})[kind];
 $('#browse-note').textContent=kind==='site'?`Plants within ${state.region}${ids?' · selected membership':''}. All use the same interaction and evidence rules.`:kind==='owner'?'Names refer to the immediate owner or operator in the source. Distinct identities do not establish independent ultimate ownership.':kind==='product'?'Add or remove products from the current view. Product labels are plant-level source descriptions, not a guarantee of grade, product-line capacity or suitability.':'Only status-specific positive operating steelmaking capacity establishes a connection to these methods.';
 $('#browse-query').placeholder=kind==='site'?'Plant, municipality, company or country':'Search';renderBrowse();openDialog('#browse-dialog');
}
function renderBrowse(){const q=$('#browse-query').value.trim().toLowerCase();let entries=[];
 if(browseMode==='site'){let pool=browseSubset?base.filter(p=>browseSubset.includes(p.id)):matched;entries=pool.map(p=>({id:p.id,name:p.name,sub:`${p.country} · ${p.owner}`,search:[p.name,p.country,p.owner,p.city,p.id].join(' '),value:capCache.get(p.id).known===null?'—':mt(capCache.get(p.id).known,2),kind:'site'}));}
 else if(browseMode==='owner')entries=owners(filterPlants(base,state.filters,'owner')).map(g=>({id:g.id,name:g.name,sub:`${g.members.length} sites · ${new Set(g.members.map(p=>p.country)).size} countries`,search:g.name,value:g.members.length,kind:'owner'}));
 else if(browseMode==='product'){
  const pool=filterPlants(base,{...state.filters,products:[]},'product');
  entries=products(pool).map(g=>({id:g.id,name:g.name,sub:'Plant product description',search:g.name,value:g.members.length,kind:'product',selected:state.filters.products.includes(g.id)}));
 } else entries=ROUTES.map(r=>({id:r.id,name:r.name,sub:'Positive operating capacity',search:r.name+' '+r.id,value:base.filter(p=>hasRoute(p,r.id)).length,kind:'route'}));
 entries=entries.filter(g=>g.search.toLowerCase().includes(q));
 const mode=state.filters.productMode;
 const productTools=browseMode==='product'?`<div class="product-picker-tools"><div><span>Selected</span><strong>${state.filters.products.length}</strong></div><div class="match-toggle" role="group" aria-label="How selected products should match"><button type="button" data-product-mode="any" aria-pressed="${mode==='any'}">Any</button><button type="button" data-product-mode="all" aria-pressed="${mode==='all'}">All</button></div><button type="button" class="clear-products" ${state.filters.products.length?'':'disabled'}>Clear products</button></div>`:'';
 $('#browse-count').textContent=`${entries.length} results${browseMode==='site'?' · capacity in Mtpa, not available supply':browseMode==='product'?' · counts are plants listing each product':''}`;
 $('#browse-result').innerHTML=productTools+(entries.length?entries.map(g=>`<button class="browse-item${g.selected?' is-selected':''}" type="button" data-browse-id="${esc(g.id)}" data-browse-kind="${g.kind}" aria-pressed="${g.kind==='product'?String(!!g.selected):'false'}">${g.kind==='product'?`<span class="browse-check" aria-hidden="true">${g.selected?'✓':''}</span>`:''}<span><strong>${esc(g.name)}</strong><small>${esc(g.sub)}</small></span><span class="browse-number">${esc(g.value)}</span></button>`).join(''):'<p class="empty">No matching entries. Try a different name or clear your selection.</p>');
 for(const b of $$('[data-browse-id]'))b.onclick=()=>{if(b.dataset.browseKind==='site'){chooseSite(b.dataset.browseId);$('#browse-dialog').close();}else if(b.dataset.browseKind==='product'){choose('product',b.dataset.browseId);renderBrowse();}else{choose(b.dataset.browseKind,b.dataset.browseId);$('#browse-dialog').close();}};
 for(const b of $$('[data-product-mode]'))b.onclick=()=>{state.filters.productMode=b.dataset.productMode;state.site=null;update();renderBrowse();};
 const cp=$('.clear-products');if(cp)cp.onclick=()=>{state.filters.products=[];state.site=null;update();renderBrowse();};
}
function evidence(){
 const p=state.site?lookup.get(state.site):null;
 const optional=p?`<section class="source-section"><h3>${esc(p.name)}</h3><p>${esc(p.country)} · location accuracy: ${esc(p.accuracy)}</p><p>Immediate owner/operator: ${esc(p.owner)}<br>GEM plant ID: <code>${esc(p.id)}</code><br>GEM entity ID: <code>${esc(p.ownerId)}</code></p><p><a href="${/^https:\/\/(www\.)?gem\.wiki\//.test(p.source_url)?esc(p.source_url):'https://globalenergymonitor.org/projects/global-iron-steel-tracker/'}" target="_blank" rel="noreferrer">Plant source page ↗</a></p></section>`:'';
 $('#source-content').innerHTML=optional+`<section class="source-section"><h3>One visual field, several ways in</h3><p>Companies connect to plants through an identical, single GEM immediate-owner/operator identity. A product connection means that the plant lists the product. A production-method connection requires positive capacity in the statuses “operating” or “operating pre-retirement”. Those methods need not produce every product listed by the plant.</p><p>Lines show associations, never shipments, supplier relationships or corporate headquarters. No plant, company or pair receives a special entry treatment. Company labels are ordered by the number of sites, then name; product labels by the number of matching sites, then name.</p></section><section class="source-section"><h3>Reading the overview</h3><p>The five company groups with the most sites in the geographic scope appear first; all other companies are available through “All companies”. Overview lines follow those groups to their plants and operating methods, with one visible product link per plant. Product links terminate at visible product nodes. Selected products stay in the product strip and can be combined using Any or All matching. For density, at most 80 visible plant connections are drawn, ordered by known operating crude-steel capacity then stable plant ID. Counts and totals still include all selected plants.</p><p>Close map marks are grouped for readability. Their circle area represents the sum of the known operating crude-steel components. Group numbers count members, not an additional measure of capacity. Hollow symbols indicate no positive quantified operating crude-steel value; a source zero is not silently treated as missing. Dashed outer rings retain approximate coordinate status.</p></section><section class="source-section"><h3>What the numbers include</h3><p>Operating capacity sums only the source statuses “operating” and “operating pre-retirement”. Crude-steel totals and method breakdowns are never added together. N/A, unknown, blank and positive-but-unquantified values remain separate in the calculation. A plus sign indicates an additional positive unquantified amount.</p><p>Products are multi-valued and not comprehensive. The product picker can add or remove several product descriptions; Any matches at least one selected product and All requires every selected product. Product counts cannot be added to produce a total. The capacity of plants listing a product is not capacity for that product or available supply. Moving the camera never changes the population. Explicit selections are shown below the graphic; removing one restores its dimension.</p></section><section class="source-section"><h3>Global Energy Monitor</h3><p>Global Energy Monitor, Global Iron and Steel Tracker, June 2026 (V1) release. Retrieved 2026-09-14. Distributed under <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">CC BY 4.0</a>. This is a transformed extract with calculations and presentation by Steel Exposure Atlas. Global Energy Monitor does not endorse the project.</p><p>The 1,293 tracked plants are not all operating steel suppliers. Regional names are preserved from GEM. Relationships have not been independently reverified as current. Multiple or unresolved company identities are not forced into a single company. Parent text is not used. The public-data snapshot cannot establish supplier qualification, available volume or independence of ultimate control.</p><p>Source extract SHA-256:<br><code>${DATA.json_sha256}</code></p></section><section class="source-section"><h3>Cartography and local review</h3><p>Natural Earth 1:110m Admin 0 Countries v5.1.1, public domain, loaded from the reviewed local project artifact. Boundaries are cartographic context, not an endorsement of territorial claims.</p><p>Regional views use a lightweight local equirectangular fit over the reviewed Natural Earth geometry. Only geographic names and shapes are retained. Country membership comes from GIST, never spatial guessing from these shapes. No live map tiles, external fonts, accounts or analytics are used. Runtime requests are same-origin reads of the reviewed local data artifacts.</p><p>No water-stress, trade, emissions or buyer-supplier layer is present. This visual connects fields within GIST; it is not yet a multi-publisher finding. This integration remains pre-publication until the repository release checklist is completed.</p></section>`;
 openDialog('#sources-dialog');
}
$('#browse-query').oninput=renderBrowse;
for(const b of $$('[data-open-facet]'))b.onclick=()=>openBrowse(b.dataset.openFacet);
$('#open-all-sites').onclick=()=>openBrowse('site');$('#inspect-selection').onclick=()=>state.site?evidence():openBrowse('site',current().map(p=>p.id));
for(const id of ['open-sources','map-basis','footer-sources'])$('#'+id).onclick=evidence;
$('#clear-all').onclick=clear;$('#brand-home').onclick=e=>{e.preventDefault();setRegion('Europe');window.scrollTo({top:0,behavior:'smooth'});};
$('#open-regions').onclick=()=>{$('#region-choices').innerHTML=regions.map(r=>`<button class="browse-item" data-region="${r}"><span><strong>${r}</strong><small>${r==='World'?'All supplied region labels':r===state.region?'Current geography':'Follow the same relationships in this region'}</small></span><span class="browse-number">${num(r==='World'?all.length:all.filter(p=>p.region===r).length)}</span></button>`).join('');for(const b of $$('[data-region]'))b.onclick=()=>{setRegion(b.dataset.region);$('#regions-dialog').close();};openDialog('#regions-dialog');};
function zoom(factor){state.camera.zoom=bounded(state.camera.zoom*factor,1,3.2);if(state.camera.zoom===1)state.camera.x=state.camera.y=0;queueMap();}
$('#map-in').onclick=()=>zoom(1.32);$('#map-out').onclick=()=>zoom(1/1.32);$('#map-fit').onclick=()=>{state.camera={zoom:1,x:0,y:0};queueMap();};
const mapSvg=$('#geo-map');mapSvg.onkeydown=e=>{const actions={'+':()=>zoom(1.32),'=':()=>zoom(1.32),'-':()=>zoom(1/1.32),Home:()=>{state.camera={zoom:1,x:0,y:0};queueMap();},ArrowLeft:()=>{state.camera.x+=35;queueMap();},ArrowRight:()=>{state.camera.x-=35;queueMap();},ArrowUp:()=>{state.camera.y+=35;queueMap();},ArrowDown:()=>{state.camera.y-=35;queueMap();}};if(e.target===mapSvg&&actions[e.key]){e.preventDefault();actions[e.key]();}};
mapSvg.addEventListener('pointerdown',e=>{if(e.pointerType==='touch'||e.button!==0)return;pan={id:e.pointerId,startX:e.clientX,startY:e.clientY,x:state.camera.x,y:state.camera.y,moved:false};});
window.addEventListener('pointermove',e=>{if(!pan||pan.id!==e.pointerId)return;const dx=e.clientX-pan.startX,dy=e.clientY-pan.startY;if(Math.hypot(dx,dy)>5){pan.moved=true;mapSvg.classList.add('dragging');state.camera.x=bounded(pan.x+dx,-size.w,size.w);state.camera.y=bounded(pan.y+dy,-size.h,size.h);hideTip();queueMap();}});
window.addEventListener('pointerup',e=>{if(!pan||pan.id!==e.pointerId)return;if(pan.moved)suppressUntil=performance.now()+200;pan=null;mapSvg.classList.remove('dragging');});
// No wheel handler: ordinary page scrolling and native pinch zoom are preserved.
new ResizeObserver(queueMap).observe($('#connections-stage'));
update();
window.__atlasReview={snapshot:()=>({state:structuredClone(state),scopeCount:base.length,matchedIds:matched.map(p=>p.id),selectedIds:current().map(p=>p.id),mapFocusIds:focusSet?[...focusSet]:[],companyHighlightIds:companyHighlightSet?[...companyHighlightSet]:[],scopeCapacity:total(base),selectedCapacity:total(current()),ownerGroups:owners(current()).map(g=>({id:g.id,count:g.members.length})),renderCount}),all,model:{amount,total,hasRoute,filterPlants,owners,products,circleRadius},choose,setRegion,clear,chooseSite};
})();

})();