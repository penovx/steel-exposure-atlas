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
const state={region:'World',filters:{country:null,owner:null,products:[],productMode:'any',route:null},site:null,camera:{zoom:1,x:0,y:0}};
const regions=['World','Europe','North America','Central & South America','Asia Pacific','Africa','Middle East','Eurasia'];
let base=[],matched=[],focusSet=null,ownerList=[],productList=[],nodePositions=new Map(),hover=null,view={s:1,tx:0,ty:0},size={w:700,h:470},pan=null,suppressUntil=0,queued=0,browseMode='site',browseSubset=null,renderCount=0;
const schemaExpected='steel-exposure-atlas/relational-entry-v2';
if(DATA.schema!==schemaExpected||all.length!==1293||lookup.size!==1293)throw new Error('Unexpected atlas data');
for(const p of all){for(const t of p.tranches)amount([t],'crude_steel_capacity_ttpa');if(!Number.isFinite(p.latitude)||!Number.isFinite(p.longitude))throw new Error('Invalid coordinates');}
const capCache=new Map(all.map(p=>[p.id,capacity(p)]));
const ownCache=new Map(all.map(p=>[p.id,usableOwner(p)]));
function current(){return state.site?matched.filter(p=>p.id===state.site):matched;}
function hasFilters(){const f=state.filters;return !!(f.country||f.owner||f.route||f.products.length);}
function isFocused(){return hasFilters()||!!state.site;}
function groupName(id){return all.find(p=>ownCache.get(p.id)===id)?.owner??id;}
function routeName(id){return ROUTES.find(r=>r.id===id)?.name??id;}
function labelFor(kind,id){return kind==='owner'?groupName(id):kind==='route'?routeName(id):id;}
function countryGroups(ps){const m=new Map();for(const p of ps){if(!m.has(p.country))m.set(p.country,{id:p.country,name:p.country,members:[]});m.get(p.country).members.push(p);}return [...m.values()].sort((a,b)=>b.members.length-a.members.length||a.name.localeCompare(b.name));}
function queueMap(){if(!queued)queued=requestAnimationFrame(()=>{queued=0;drawMap();});}
function update(){
 base=state.region==='World'?all:all.filter(p=>p.region===state.region);
 matched=filterPlants(base,state.filters);
 if(state.site&&!matched.some(p=>p.id===state.site))state.site=null;
 const chosen=current();focusSet=isFocused()?new Set(chosen.map(p=>p.id)):null;
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
 const modeToken=f.products.length>1?`<button class="path-token mode-token" type="button" data-toggle-mode><small>MATCH</small>${f.productMode==='all'?'All selected':'Any selected'}<span aria-hidden="true">↕</span></button>`:'';
 $('#selection-path').innerHTML=productTokens+scalarTokens+modeToken+(isFocused()?'<button class="path-token" type="button" data-clear-all><small>RESET</small>Clear selection<span aria-hidden="true">×</span></button>':'<span class="path-base"><small>WORLD</small> all supplied sites</span>');
 for(const b of $$('[data-remove-product]'))b.onclick=()=>choose('product',b.dataset.removeProduct);
 for(const b of $$('[data-remove]'))b.onclick=()=>{state.filters[b.dataset.remove]=null;state.site=null;update();};
 const mode=$('[data-toggle-mode]');if(mode)mode.onclick=()=>{state.filters.productMode=state.filters.productMode==='all'?'any':'all';update();};
 const reset=$('[data-clear-all]');if(reset)reset.onclick=clear;
 const c=total(chosen);$('#reading-title').textContent=isFocused()?`${num(chosen.length)} connected sites`:`${num(base.length)} tracked sites`;
 $('#reading-copy').textContent=isFocused()?'The view shows the intersection of your current place, company, product and production-method choices. Capacity remains plant-level source evidence, not available supply.':'Start with a place, company, product or production method. Each choice narrows the same underlying plant evidence.';
 $('#reading-capacity').textContent=c.known===null?'—':`${mt(c.known,1)} Mtpa`;
 $('#reading-companies').textContent=num(owners(chosen).length);
 $('#reading-products').textContent=num(products(chosen).length);
 $('#reading-methods').textContent=num(ROUTES.filter(r=>chosen.some(p=>hasRoute(p,r.id))).length);
 $('#scope-detail').textContent=`Scope: ${state.region}. Known operating crude steel capacity uses only status-specific operating and operating pre-retirement rows. Product labels come from plant source descriptions and are not product-line capacity.`;
 $('#reading-sources').disabled=!chosen.length;
 $('#reading-sources').onclick=()=>openSources(chosen);
}
function updateSize(){const el=$('#geography');size={w:Math.max(1,el.clientWidth),h:Math.max(1,el.clientHeight)};const svg=$('#geo-map');svg.setAttribute('viewBox',`0 0 ${size.w} ${size.h}`);}
function geoBox(){return {left:0,top:0,right:size.w,bottom:size.h};}
function project(p){
 const box=geoBox();const lat=bounded(p.latitude,-78,82),lon=p.longitude;
 const x=box.left+(lon+180)/360*(box.right-box.left);const y=box.top+(82-lat)/160*(box.bottom-box.top-54);
 const cx=size.w/2,cy=(size.h-54)/2;return [(x-cx)*state.camera.zoom+cx+state.camera.x,(y-cy)*state.camera.zoom+cy+state.camera.y];
}
function pathForCoordinates(coords){let d='';for(const ring of coords){for(let i=0;i<ring.length;i++){const [lon,lat]=ring[i];const [x,y]=project({longitude:lon,latitude:lat});d+=(i?'L':'M')+x.toFixed(1)+','+y.toFixed(1);}d+='Z';}return d;}
function featurePath(f){if(!f?.geometry)return '';if(f.geometry.type==='Polygon')return pathForCoordinates(f.geometry.coordinates);if(f.geometry.type==='MultiPolygon')return f.geometry.coordinates.map(pathForCoordinates).join('');return '';}
function drawMap(){
 updateSize();const geo=DATA.basemap;const land=$('#land-layer');land.replaceChildren();for(const f of geo.features){const d=featurePath(f);if(d)land.append(svgEl('path',{d,class:'country-shape'}));}
 const groups=aggregateGroups(base,p=>project(p),focusSet,state.camera.zoom);const labels=$('#label-layer');labels.replaceChildren();const countries=countryGroups(base).filter(c=>c.members.length).map(c=>{const xs=c.members.map(p=>project(p)[0]),ys=c.members.map(p=>project(p)[1]);return {...c,label:[xs.reduce((a,b)=>a+b,0)/xs.length,ys.reduce((a,b)=>a+b,0)/ys.length]};}).sort((a,b)=>b.members.length-a.members.length||a.name.localeCompare(b.name));
 const rectangles=[];for(const c of countries){
  const originalX=c.label[0],originalY=c.label[1];const name=c.name==='Bosnia and Herzegovina'?'BOSNIA & HERZ.':c.name.toUpperCase();const w=name.length*(size.w<450?6:7);let placed=null;
  const offsets=[[0,0],[0,-19],[0,19],[-26,-16],[26,16],[0,-38],[0,38],[-44,-25],[44,25],[-52,4],[52,-4],[0,58],[0,-58],[-70,-30],[70,30]];
  for(const [dx,dy]of offsets){const x=originalX+dx,y=originalY+dy;const rect={x:x-w/2,y:y-12,w,h:18};if(x<w/2+4||x>size.w-w/2-4||y<15||y>size.h-56)continue;if(rectangles.some(r=>rect.x<r.x+r.w+5&&rect.x+w>r.x-5&&rect.y<r.y+r.h+3&&rect.y+18>r.y-3))continue;if(groups.some(g=>{const rad=Math.max(10,circleRadius(g.known,size.w<450?.82:1)+5);return g.x+rad>rect.x&&g.x-rad<rect.x+rect.w&&g.y+rad>rect.y&&g.y-rad<rect.y+rect.h;}))continue;placed={x,y,rect};break;}
  if(!placed)continue;if(rectangles.length>=(size.w<450?9:17))break;const {x,y,rect}=placed;rectangles.push(rect);if(Math.hypot(x-originalX,y-originalY)>9)labels.append(svgEl('path',{d:`M${originalX},${originalY} L${x},${y+4}`,fill:'none',stroke:'#7695a8','stroke-opacity':.5,'stroke-width':.8,'pointer-events':'none'}));const n=svgEl('text',{x,y,'text-anchor':'middle',class:`country-label has-sites${c.name===state.filters.country?' is-selected':''}`,tabindex:0,role:'button','aria-label':`Explore ${c.name}`},name);n.addEventListener('click',()=>choose('country',c.name));n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose('country',c.name);}});labels.append(n);
 }
 const pointLayer=$('#plant-layer');pointLayer.replaceChildren();nodePositions=new Map();const selected=current();const labelIds=new Set(isFocused()?selected.slice().sort((a,b)=>(capCache.get(b.id).known??-1)-(capCache.get(a.id).known??-1)).slice(0,5).map(p=>p.id):[]);
 for(const g of groups){if(g.x<-20||g.x>size.w+20||g.y<-20||g.y>size.h+20)continue;const ids=g.members.map(p=>p.id);const r=circleRadius(g.known,size.w<450?.82:1);const visualR=r>0?r:3;const hit=Math.max(visualR+3,10);const group=svgEl('g',{class:`plant-node${!g.hot?' dim':''}${ids.includes(state.site)?' selected':''}`,transform:`translate(${g.x} ${g.y})`,tabindex:0,role:'button','data-members':ids.join(' '),'aria-label':g.members.length>1?`Open ${g.members.length} nearby sites`:g.members[0].name});group.append(svgEl('circle',{r:hit,class:'plant-hit'}));group.append(svgEl('circle',{r:visualR,class:r>0?'plant-disc':'plant-hollow'}));group.append(svgEl('circle',{r:visualR+5,class:'plant-focus'}));if(g.members.some(p=>p.accuracy==='approximate'))group.append(svgEl('circle',{r:visualR+2,fill:'none',stroke:'#d3cbb8','stroke-dasharray':'2 3','stroke-width':.8}));if(g.members.length>1)group.append(svgEl('text',{x:visualR+4,y:3,class:'cluster-text',style:'fill:#d1e1eb;paint-order:stroke;stroke:#0c1821;stroke-width:2'},String(g.members.length)));if(g.members.length===1&&labelIds.has(g.members[0].id)){const p=g.members[0];const text=p.city==='unknown'?p.name.replace(/ steel plant$/i,''):p.city;const toLeft=g.x>size.w*.64;group.append(svgEl('text',{x:toLeft?-visualR-7:visualR+7,y:-7,'text-anchor':toLeft?'end':'start',class:'plant-name'},text.length>29?text.slice(0,27)+'…':text));}const activate=()=>{if(performance.now()<suppressUntil)return;if(g.members.length===1)chooseSite(g.members[0].id);else openBrowse('site',ids);};group.addEventListener('click',activate);group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});group.addEventListener('pointermove',e=>{setHover('members',ids);const cap=total(g.members);showTip(g.members.length>1?`${g.members.length} nearby sites`:g.members[0].name,`${g.members.length>1?'Click to see each site · ':g.members[0].country+' · '}${cap.known===null?'No numeric operating crude-steel capacity':mt(cap.known)+' Mtpa known operating crude steel'}`,e);});group.addEventListener('pointerleave',()=>{setHover(null,null);hideTip();});pointLayer.append(group);for(const p of g.members)nodePositions.set(p.id,{x:g.x,y:g.y});}
 $('#zoom-level').textContent=state.camera.zoom.toFixed(1)+'×';$('#map-out').disabled=state.camera.zoom<=1;$('#map-in').disabled=state.camera.zoom>=3.2;drawEdges();applyEmphasis();
}
function drawEdges(){
 const stage=$('#connections-stage').getBoundingClientRect(),geo=$('#geography').getBoundingClientRect();const svg=$('#connection-lines');svg.setAttribute('viewBox',`0 0 ${stage.width} ${stage.height}`);const edges=$('#edge-layer');edges.replaceChildren();
 const port=(kind,id)=>{const n=$$('[data-port]').find(e=>e.dataset.port===kind+':'+id);if(!n)return null;const b=n.getBoundingClientRect();return kind==='owner'?{x:b.right-stage.left+4,y:b.top-stage.top+b.height/2}:kind==='route'?{x:b.left-stage.left-5,y:b.top-stage.top+13}:{x:b.left-stage.left+b.width/2,y:b.top-stage.top-15};};
 const visibleOwner=new Set(ownerList.map(g=>g.id));let records=isFocused()?current():base.filter(p=>visibleOwner.has(ownCache.get(p.id)));records=[...records].filter(p=>nodePositions.has(p.id)).sort((a,b)=>(capCache.get(b.id).known??-1)-(capCache.get(a.id).known??-1)||a.id.localeCompare(b.id)).slice(0,80);
 const connection=(p,to,type)=>{const pp=nodePositions.get(p.id);if(!pp||!to)return;const a={x:pp.x+geo.left-stage.left,y:pp.y+geo.top-stage.top};if(pp.x<8||pp.x>size.w-8||pp.y<8||pp.y>size.h-45)return;let d;if(stage.width<=760){const spine=stage.width/2+(type==='company'?-5:type==='product'?0:5);const bottom=geo.bottom-stage.top;d=`M${a.x},${a.y} C${a.x},${a.y+35} ${spine},${bottom-25} ${spine},${bottom+8} L${spine},${to.y-14} Q${spine},${to.y} ${to.x},${to.y}`;}else d=type==='product'?`M${a.x},${a.y} C${a.x},${a.y+(to.y-a.y)*.45} ${to.x},${a.y+(to.y-a.y)*.8} ${to.x},${to.y}`:`M${a.x},${a.y} C${a.x+(to.x-a.x)*.45},${a.y} ${to.x-(to.x-a.x)*.2},${to.y} ${to.x},${to.y}`;edges.append(svgEl('path',{d,class:`connection-edge ${type}`,'data-site':p.id}));};
 const selectedProducts=new Set(state.filters.products);
 for(const p of records){connection(p,port('owner',ownCache.get(p.id)),'company');for(const r of ROUTES)if(hasRoute(p,r.id))connection(p,port('route',r.id),'route-'+r.id);const tags=productList.filter(g=>p.products.values.includes(g.id));const linkedProducts=selectedProducts.size?tags.filter(g=>selectedProducts.has(g.id)):isFocused()?tags:tags.slice(0,1);for(const tag of linkedProducts)connection(p,port('product',tag.id),'product');}
}
function showTip(title,sub,event){const tip=$('#map-tip'),r=$('#geography').getBoundingClientRect();tip.innerHTML=`<strong>${esc(title)}</strong><span>${esc(sub)}</span>`;tip.hidden=false;const x=bounded(event.clientX-r.left+16,7,Math.max(7,r.width-tip.offsetWidth-7)),y=bounded(event.clientY-r.top+15,7,Math.max(7,r.height-tip.offsetHeight-8));tip.style.left=x+'px';tip.style.top=y+'px';}
function hideTip(){$('#map-tip').hidden=true;}
function openDialog(id){const d=$(id);if(!d.open)d.showModal();}
function closeDialog(n){const d=n.closest('dialog');if(d)d.close();}
$$('[data-close-dialog]').forEach(n=>n.onclick=()=>closeDialog(n));
for(const dialog of $$('dialog'))dialog.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();dialog.close();}},true);
function openBrowse(kind='site',ids=null){browseMode=kind;browseSubset=ids;$('#browse-query').value='';$('#browse-title').textContent=({site:'Find a plant.',owner:'Choose a company.',product:'Choose products.',route:'Choose a production method.'})[kind];$('#browse-note').textContent=kind==='site'?`Plants within ${state.region}${ids?' · selected membership':''}. All use the same interaction and evidence rules.`:kind==='owner'?'Names refer to the immediate owner or operator in the source. Distinct identities do not establish independent ultimate ownership.':kind==='product'?'Add or remove products from the current view. Product labels are plant-level source descriptions, not a guarantee of grade, product-line capacity or suitability.':'Only status-specific positive operating steelmaking capacity establishes a connection to these methods.';$('#browse-query').placeholder=kind==='site'?'Plant, municipality, company or country':'Search';renderBrowse();openDialog('#browse-dialog');}
function renderBrowse(){const q=$('#browse-query').value.trim().toLowerCase();let entries=[];if(browseMode==='site'){let pool=browseSubset?base.filter(p=>browseSubset.includes(p.id)):matched;entries=pool.map(p=>({id:p.id,name:p.name,sub:`${p.city} · ${p.country} · ${p.owner}`,count:capCache.get(p.id).known===null?'—':mt(capCache.get(p.id).known,2)+' Mtpa'}));}else if(browseMode==='owner'){entries=owners(base).map(g=>({id:g.id,name:g.name,sub:`${g.members.length} sites in ${state.region}`,count:g.members.length}));}else if(browseMode==='product'){entries=products(base).map(g=>({id:g.id,name:g.name,sub:`listed at ${g.members.length} plants`,count:g.members.length}));}else{entries=ROUTES.map(r=>({id:r.id,name:r.name,sub:'operating capacity evidence',count:base.filter(p=>hasRoute(p,r.id)).length}));}entries=entries.filter(e=>!q||(e.name+' '+e.sub+' '+e.id).toLowerCase().includes(q));$('#browse-result').innerHTML=entries.length?entries.map(e=>`<button type="button" class="browse-item" data-browse-kind="${browseMode}" data-browse-id="${esc(e.id)}"><span><strong>${esc(e.name)}</strong><small>${esc(e.sub)}</small></span><span class="browse-number">${esc(e.count)}</span></button>`).join(''):'<p class="empty-state">No matching records in this scope.</p>';for(const b of $$('[data-browse-kind]'))b.onclick=()=>{const kind=b.dataset.browseKind,id=b.dataset.browseId;if(kind==='site'){chooseSite(id);closeDialog(b);}else choose(kind,id);renderBrowse();};}
$('#browse-query').addEventListener('input',renderBrowse);
for(const b of $$('[data-open-facet]'))b.onclick=()=>openBrowse(b.dataset.openFacet);
$('#open-all-sites').onclick=()=>openBrowse('site');
$('#open-regions').onclick=()=>{const result=$('#region-result');result.innerHTML=regions.map(r=>`<button class="browse-item" type="button" data-region="${esc(r)}"><span><strong>${esc(r)}</strong><small>${r==='World'?'All supplied plant records':num(all.filter(p=>p.region===r).length)+' plant records'}</small></span></button>`).join('');for(const b of $$('[data-region]'))b.onclick=()=>{setRegion(b.dataset.region);closeDialog(b);};openDialog('#region-dialog');};
$('#clear-all').onclick=clear;
$('#map-in').onclick=()=>{state.camera.zoom=bounded(state.camera.zoom*1.32,1,3.2);queueMap();};$('#map-out').onclick=()=>{state.camera.zoom=bounded(state.camera.zoom/1.32,1,3.2);if(state.camera.zoom===1)state.camera.x=state.camera.y=0;queueMap();};$('#map-fit').onclick=()=>{state.camera={zoom:1,x:0,y:0};queueMap();};
$('#geo-map').addEventListener('keydown',e=>{const d=35;if(e.key==='ArrowLeft')state.camera.x+=d;else if(e.key==='ArrowRight')state.camera.x-=d;else if(e.key==='ArrowUp')state.camera.y+=d;else if(e.key==='ArrowDown')state.camera.y-=d;else return;e.preventDefault();queueMap();});
$('#geo-map').addEventListener('pointerdown',e=>{if(e.button!==0)return;pan={x:e.clientX,y:e.clientY,cx:state.camera.x,cy:state.camera.y};$('#geo-map').setPointerCapture?.(e.pointerId);});$('#geo-map').addEventListener('pointermove',e=>{if(!pan)return;state.camera.x=pan.cx+(e.clientX-pan.x);state.camera.y=pan.cy+(e.clientY-pan.y);suppressUntil=performance.now()+120;queueMap();});$('#geo-map').addEventListener('pointerup',()=>{pan=null;});$('#geo-map').addEventListener('pointercancel',()=>{pan=null;});
new ResizeObserver(()=>queueMap()).observe($('#connections-stage'));
function openSources(plants){const lines=plants.slice(0,25).map(p=>`<li><strong>${esc(p.name)}</strong><br><span>${esc(p.id)} · ${esc(p.country)} · ${esc(p.owner)}</span></li>`).join('');$('#source-content').innerHTML=`<p><strong>${num(plants.length)} selected plant records.</strong> Plant-product links mean the source lists the product at that plant. They do not establish product-line capacity, grade suitability, available supply or a buyer-supplier relationship.</p><ul>${lines}</ul>${plants.length>25?`<p>First 25 of ${num(plants.length)} records shown here.</p>`:''}`;openDialog('#sources-dialog');}
update();
window.__atlasReview={snapshot:()=>({state:JSON.parse(JSON.stringify(state)),scopeCount:base.length,selectedIds:current().map(p=>p.id),scopeCapacity:total(base),renderCount}),all};
})();
})();
