import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {aggregateCapacity, capacityRadius, CAPACITY_FIELDS, evidenceReducer, formatCapacity, GIST_SHA256, initialEvidenceState, operatingRoutes, plantCapacity, rankCapacityPlants, scopeCapacitySummary, scopePlants, searchPlants, usableOwnerId, validatePinnedPayload} from '../prototype/gist-adapter.mjs';

const cell = (state,value_ttpa=null) => ({state,value_ttpa});
const plant = (plant_id,country_area,region,tranches,extra={}) => ({plant_id,plant_name:plant_id,country_area,region,capacity:{tranches},...extra});
const tranche = (status,value,route=9999) => ({status,crude_steel_capacity_ttpa:value,eaf_steel_capacity_ttpa:cell('numeric',route)});
const fullTranche = (status, total, overrides = {}) => ({
  ...Object.fromEntries(Object.keys(CAPACITY_FIELDS).map(field => [field, cell('N/A')])),
  status, crude_steel_capacity_ttpa: total, equipment: {state:'unknown', values:[]}, ...overrides,
});

test('capacity uses source totals separately by explicit bucket, never adds route values',()=>{
  const records=[plant('A','Germany','Europe',[tranche('operating',cell('numeric',200)),tranche('construction',cell('numeric',500))]),plant('B','Germany','Europe',[tranche('operating pre-retirement',cell('numeric',30))])];
  assert.equal(aggregateCapacity(records,'operating').known_numeric_sum_ttpa,230);
  assert.equal(aggregateCapacity(records,'development').known_numeric_sum_ttpa,500);
  assert.throws(()=>aggregateCapacity(records,'all'));
});
test('every non-numeric state survives aggregation and display; missing rows are not zero',()=>{
  const records=['unknown','N/A','>0','blank'].map((s,i)=>plant(String(i),'A','R',[tranche('operating',cell(s))]));
  const value=aggregateCapacity(records,'operating');
  assert.equal(value.numeric_rows,0);assert.equal(value.contributing_rows,4);assert.equal(value.has_unquantified_positive,true);
  for(const s of ['unknown','N/A','>0','blank'])assert.equal(value.states[s],1);
  assert.match(formatCapacity(cell('blank')),/Blank/);assert.match(formatCapacity(cell('>0')),/unquantified/);assert.equal(formatCapacity(cell('N/A')),'N/A');
  assert.equal(aggregateCapacity([],'operating').contributing_rows,0);
});

test('plant measures keep operating, development, unknown and blank components separate',()=>{
  const record=plant('A','Germany','Europe',[
    fullTranche('operating',cell('numeric',2000),{eaf_steel_capacity_ttpa:cell('numeric',2000),iron_capacity_ttpa:cell('numeric',9000)}),
    fullTranche('operating pre-retirement',cell('unknown')),
    fullTranche('announced',cell('numeric',500)),
    fullTranche('construction',cell('blank')),
  ]);
  const before=structuredClone(record), operating=plantCapacity(record), development=plantCapacity(record,'development');
  assert.equal(operating.knownMtpa,2);
  assert.equal(development.knownMtpa,.5);
  assert.equal(operating.states.unknown,1);
  assert.equal(development.states.blank,1);
  assert.deepEqual(operating.sourceStatuses,['operating','operating pre-retirement']);
  assert.deepEqual(record,before,'Reading capacity must not mutate the source object');
});

test('unknown, N/A, positive-unquantified and absent operating values are not numeric zero',()=>{
  for(const state of ['unknown','N/A','>0','blank']){
    const summary=plantCapacity(plant(state,'A','R',[fullTranche('operating',cell(state))]));
    assert.equal(summary.knownMtpa,null);
    assert.equal(summary.states[state],1);
    assert.equal(summary.noSourceTranches,false);
    assert.equal(summary.has_unquantified_positive,state==='>0');
  }
  const noOperating=plantCapacity(plant('Development only','A','R',[fullTranche('construction',cell('numeric',1000))]));
  assert.equal(noOperating.knownMtpa,null);assert.equal(noOperating.noSourceTranches,true);
  const zero=plantCapacity(plant('Reported zero','A','R',[fullTranche('operating',cell('numeric',0))]));
  assert.equal(zero.knownMtpa,0);assert.equal(zero.numeric_rows,1);
  assert.equal(scopeCapacitySummary([]).operating.knownMtpa,null);
});

test('available steel routes use operating evidence and never borrow iron or development equipment',()=>{
  const record=plant('Mixed','A','R',[
    fullTranche('operating',cell('numeric',3000),{
      bof_steel_capacity_ttpa:cell('numeric',3000), eaf_steel_capacity_ttpa:cell('unknown'),
      if_steel_capacity_ttpa:cell('numeric',0), other_steel_capacity_ttpa:cell('>0'),
      bf_iron_capacity_ttpa:cell('numeric',9000),
      equipment:{state:'text',values:['EAF','BF','DRI']},
    }),
    fullTranche('construction',cell('numeric',500),{if_steel_capacity_ttpa:cell('numeric',500),equipment:{state:'text',values:['IF']}}),
  ],{main_production_equipment:{state:'text',values:['BOF','EAF','IF','BF','DRI']}});
  const routes=operatingRoutes(record);
  assert.deepEqual(routes.map(route=>route.label),['BOF','EAF','Other / unspecified']);
  assert.equal(routes[0].knownMtpa,3);
  assert.equal(routes[1].knownMtpa,null);assert.equal(routes[1].states.unknown,1);
  assert.deepEqual(routes[1].evidence,['operating-equipment']);
  assert.equal(routes[2].has_unquantified_positive,true);assert.equal(routes[2].knownMtpa,null);
  assert.equal(plantCapacity(record).knownMtpa,3,'Route/iron capacity is not added to source crude total');
  assert.deepEqual(operatingRoutes(plant('Only development','A','R',[record.capacity.tranches[1]])),[]);
});

test('ranking and contributions use known operating crude totals, with unknown after reported zero',()=>{
  const records=[
    plant('B','A','R',[fullTranche('operating',cell('numeric',1000))],{plant_name:'Beta'}),
    plant('D','A','R',[fullTranche('operating',cell('unknown'))],{plant_name:'Unreported'}),
    plant('C','A','R',[fullTranche('operating',cell('numeric',0))],{plant_name:'Zero'}),
    plant('A','A','R',[fullTranche('operating',cell('numeric',1000))],{plant_name:'Alpha'}),
    plant('E','A','R',[fullTranche('operating',cell('numeric',2000)),fullTranche('construction',cell('numeric',9000))],{plant_name:'Largest'}),
  ];
  const before=records.map(record=>record.plant_id), ranked=rankCapacityPlants(records);
  assert.deepEqual(ranked.map(row=>row.plant.plant_id),['E','A','B','C','D']);
  assert.deepEqual(ranked.map(row=>row.share),[.5,.25,.25,0,null]);
  assert.equal(ranked[0].development.knownMtpa,9);
  assert.equal(scopeCapacitySummary(records).operating.knownMtpa,4);
  assert.equal(scopeCapacitySummary(records).operating.states.unknown,1);
  assert.deepEqual(records.map(record=>record.plant_id),before,'Ranking must not reorder source records');
});

test('all-zero and unquantified-only populations have no meaningful percentage denominator',()=>{
  const records=[plant('Zero','A','R',[fullTranche('operating',cell('numeric',0))]),plant('Positive unknown','A','R',[fullTranche('operating',cell('>0'))])];
  assert.deepEqual(rankCapacityPlants(records).map(row=>row.share),[null,null]);
  const summary=scopeCapacitySummary(records);
  assert.equal(summary.operating.knownMtpa,0);
  assert.equal(summary.operating.has_unquantified_positive,true);
  assert.equal(rankCapacityPlants([records[1]])[0].operating.knownMtpa,null);
});

test('camera and search leave known country operating-capacity denominator unchanged',()=>{
  const records=[plant('Berlin','Germany','Europe',[fullTranche('operating',cell('numeric',1000))]),plant('Bremen','Germany','Europe',[fullTranche('operating',cell('numeric',3000))]),plant('Paris','France','Europe',[fullTranche('operating',cell('numeric',9000))])];
  const state=initialEvidenceState(records), scope=scopePlants(records,state.scope);
  const search=evidenceReducer(state,{type:'search',query:'Berlin'},records);
  const moved=evidenceReducer(search,{type:'camera',camera:{x:0,y:0,width:1,height:1}},records);
  assert.equal(scopeCapacitySummary(scopePlants(records,moved.scope)).operating.knownMtpa,4);
  const ranked=rankCapacityPlants(scope);
  const visibleIds=new Set(searchPlants(scope,moved.query).map(record=>record.plant_id));
  assert.equal(ranked.filter(row=>visibleIds.has(row.plant.plant_id))[0].share,.25);
});

test('capacity bubble area scales in direct proportion to known capacity without a visual minimum',()=>{
  const small=capacityRadius(1,4,20), large=capacityRadius(4,4,20);
  assert.equal(small,10);assert.equal(large,20);
  assert.equal((Math.PI*large**2)/(Math.PI*small**2),4);
  assert.equal(capacityRadius(.01,4,20),1);
  assert.equal(capacityRadius(0,4,20),0);
  assert.equal(capacityRadius(null,4,20),null);
  assert.equal(capacityRadius(0,0,20),0);
  assert.throws(()=>capacityRadius(-1,4));
  assert.throws(()=>capacityRadius(5,4));
  assert.throws(()=>capacityRadius(1,4,0));
});

test('invalid numeric/source-state combinations fail before entering capacity calculations',()=>{
  for(const value of [cell('numeric',NaN),cell('numeric',-1),cell('numeric','100'),cell('unknown',0)]){
    assert.throws(()=>plantCapacity(plant('Invalid','A','R',[fullTranche('operating',value)])),/disagree/);
  }
});
test('camera, layer and local search preserve the analytical denominator',()=>{
  const records=[plant('Berlin','Germany','Europe',[]),plant('Paris','France','Europe',[])];
  const state=initialEvidenceState(records);
  for(const action of [{type:'camera',camera:{x:1,y:2,width:30,height:20}},{type:'layer',visible:false},{type:'search',query:'absent'}]){
    const next=evidenceReducer(state,action,records);assert.deepEqual(next.scope,state.scope);assert.equal(scopePlants(records,next.scope).length,1);
  }
  assert.equal(searchPlants(scopePlants(records,state.scope),'absent').length,0);
});
test('scope changes reconcile region, clear stale selection and preserve all tranche statuses',()=>{
  const records=[plant('Berlin','Germany','Europe',[]),plant('Tokyo','Japan','Asia',[])];
  let state=initialEvidenceState(records);state=evidenceReducer(state,{type:'select',id:'Berlin'},records);
  state=evidenceReducer(state,{type:'country',country:'Japan'},records);
  assert.deepEqual(state.scope,{region:'Asia',country:'Japan'});assert.equal(state.selectedId,null);
  assert.equal(evidenceReducer(state,{type:'select',id:'Berlin'},records).selectedId,null);
  assert.deepEqual(evidenceReducer(state,{type:'region',region:'Europe'},records).scope,{region:'Europe',country:''});
});
test('search clears selection and hover outside its matches without changing scope or camera',()=>{
  const records=[plant('Berlin','Germany','Europe',[]),plant('Bremen','Germany','Europe',[])];
  let state=initialEvidenceState(records);
  state=evidenceReducer(state,{type:'select',id:'Berlin'},records);
  state=evidenceReducer(state,{type:'hover',id:'Berlin'},records);
  const matched=evidenceReducer(state,{type:'search',query:'Berl'},records);
  assert.equal(matched.selectedId,'Berlin');assert.equal(matched.hoverId,'Berlin');
  const absent=evidenceReducer(matched,{type:'search',query:'no matching plant'},records);
  assert.equal(absent.selectedId,null);assert.equal(absent.hoverId,null);
  assert.deepEqual(absent.scope,state.scope);assert.deepEqual(absent.camera,state.camera);
  assert.equal(scopePlants(records,absent.scope).length,2);
});
test('owner identity usability does not convert arbitrary parent text into an identity',()=>{
  assert.equal(usableOwnerId('E100001016181'),'E100001016181');
  for(const v of ['unknown','',null,'N/A','Parent [100%]','E123; E456'])assert.equal(usableOwnerId(v),null);
});

test('site product, process and year detail leave scope, selected plant and capacity denominator unchanged',()=>{
  const records=[plant('Berlin','Germany','Europe',[fullTranche('operating',cell('numeric',1000))]),plant('Bremen','Germany','Europe',[fullTranche('operating',cell('numeric',3000))])];
  const initial=initialEvidenceState(records);
  assert.equal(initial.product,null);assert.equal(initial.processStage,null);assert.equal(initial.productionYear,null);
  const selected=evidenceReducer(initial,{type:'select',id:'Bremen'},records);
  const stage={status:'operating',field:'bof_steel_capacity_ttpa'};
  let depth=evidenceReducer(selected,{type:'product',value:'finished rolled'},records);
  depth=evidenceReducer(depth,{type:'process',value:stage},records);
  depth=evidenceReducer(depth,{type:'year',value:'2024'},records);
  assert.equal(depth.product,'finished rolled');assert.deepEqual(depth.processStage,stage);assert.equal(depth.productionYear,'2024');
  assert.equal(depth.selectedId,'Bremen');assert.deepEqual(depth.scope,selected.scope);assert.deepEqual(depth.camera,selected.camera);
  assert.equal(scopeCapacitySummary(scopePlants(records,depth.scope)).operating.knownMtpa,4);
  assert.equal(rankCapacityPlants(scopePlants(records,depth.scope)).find(row=>row.plant.plant_id==='Bremen').share,.75);
  assert.equal(selected.product,null);assert.notEqual(depth.processStage,stage,'Reducer owns its process object');
  for(const type of ['product','process','year'])depth=evidenceReducer(depth,{type,value:null},records);
  assert.equal(depth.product,null);assert.equal(depth.processStage,null);assert.equal(depth.productionYear,null);
});

test('switching site or analytical scope clears stale product, process and production-year detail',()=>{
  const records=[plant('Berlin','Germany','Europe',[]),plant('Bremen','Germany','Europe',[]),plant('Paris','France','Europe',[])];
  let state=evidenceReducer(initialEvidenceState(records),{type:'select',id:'Bremen'},records);
  state=evidenceReducer(state,{type:'product',value:'hot rolled coil'},records);
  state=evidenceReducer(state,{type:'process',value:{status:'operating',field:'bof_steel_capacity_ttpa'}},records);
  state=evidenceReducer(state,{type:'year',value:'2023'},records);
  assert.equal(evidenceReducer(state,{type:'select',id:'Bremen'},records).product,'hot rolled coil');
  assert.equal(evidenceReducer(state,{type:'search',query:'Bremen'},records).productionYear,'2023');
  for(const action of [{type:'select',id:'Berlin'},{type:'select',id:'not-in-scope'},{type:'country',country:'France'},{type:'region',region:'Europe'},{type:'clear'},{type:'search',query:'Berlin'}]){
    const next=evidenceReducer(state,action,records);
    assert.equal(next.product,null);assert.equal(next.processStage,null);assert.equal(next.productionYear,null);
  }
});

test('route highlight accepts steel routes only and changes neither scope nor capacity denominator',()=>{
  const records=[plant('Bremen','Germany','Europe',[fullTranche('operating',cell('numeric',1000))]),plant('Berlin','Germany','Europe',[fullTranche('operating',cell('numeric',3000))])];
  let state=evidenceReducer(initialEvidenceState(records),{type:'select',id:'Bremen'},records);
  assert.equal(state.route,null);assert.equal(state.perspective,'capacity');assert.equal(state.siteView,'process');
  const selected=state;
  for(const field of ['bof_steel_capacity_ttpa','eaf_steel_capacity_ttpa','if_steel_capacity_ttpa','other_steel_capacity_ttpa']){
    state=evidenceReducer(state,{type:'route',value:field},records);
    assert.equal(state.route,field);
    assert.deepEqual(state.scope,selected.scope);assert.deepEqual(state.camera,selected.camera);assert.equal(state.selectedId,'Bremen');
    assert.equal(scopeCapacitySummary(scopePlants(records,state.scope)).operating.knownMtpa,4);
    assert.equal(rankCapacityPlants(scopePlants(records,state.scope)).find(row=>row.plant.plant_id==='Bremen').share,.25);
  }
  for(const invalid of ['iron_capacity_ttpa','crude_steel_capacity_ttpa','BF','unreviewed-route',undefined]){
    assert.equal(evidenceReducer(state,{type:'route',value:invalid},records),state);
  }
  assert.equal(evidenceReducer(state,{type:'route',value:null},records).route,null);
});

test('site comparison pins toggle within scope, stop at two and preserve analytical state',()=>{
  const records=[plant('Bremen','Germany','Europe',[]),plant('Berlin','Germany','Europe',[]),plant('Hamburg','Germany','Europe',[]),plant('Paris','France','Europe',[])];
  const selected=evidenceReducer(initialEvidenceState(records),{type:'select',id:'Bremen'},records);
  let state=evidenceReducer(selected,{type:'pin',id:'Bremen'},records);
  state=evidenceReducer(state,{type:'pin',id:'Berlin'},records);
  assert.deepEqual(state.pins,['Bremen','Berlin']);assert.deepEqual(selected.pins,[]);
  for(const id of ['Hamburg','Paris','Unknown'])assert.equal(evidenceReducer(state,{type:'pin',id},records),state);
  assert.deepEqual(state.scope,selected.scope);assert.deepEqual(state.camera,selected.camera);assert.equal(state.selectedId,'Bremen');
  state=evidenceReducer(state,{type:'pin',id:'Bremen'},records);
  assert.deepEqual(state.pins,['Berlin']);
  state=evidenceReducer(state,{type:'pin',id:'Hamburg'},records);
  assert.deepEqual(state.pins,['Berlin','Hamburg']);
  assert.deepEqual(evidenceReducer(state,{type:'unpin',id:'Berlin'},records).pins,['Hamburg']);
  assert.deepEqual(evidenceReducer(state,{type:'unpin',id:'absent'},records).pins,state.pins);
});

test('site view and perspective accept explicit modes without changing selection or route',()=>{
  const records=[plant('Bremen','Germany','Europe',[])];
  let state=evidenceReducer(initialEvidenceState(records),{type:'select',id:'Bremen'},records);
  state=evidenceReducer(state,{type:'route',value:'bof_steel_capacity_ttpa'},records);
  for(const value of ['process','projects','products','production','source']){
    state=evidenceReducer(state,{type:'siteView',value},records);
    assert.equal(state.siteView,value);assert.equal(state.selectedId,'Bremen');assert.equal(state.route,'bof_steel_capacity_ttpa');
  }
  assert.equal(evidenceReducer(state,{type:'siteView',value:'unreviewed-network'},records),state);
  for(const value of ['routes','capacity']){
    state=evidenceReducer(state,{type:'perspective',value},records);
    assert.equal(state.perspective,value);assert.equal(state.siteView,'source');assert.equal(state.selectedId,'Bremen');
  }
  assert.equal(evidenceReducer(state,{type:'perspective',value:'risk'},records),state);
});

test('selection reset preserves comparison and route; geography changes clear pins and retain the route',()=>{
  const records=[plant('Bremen','Germany','Europe',[]),plant('Berlin','Germany','Europe',[]),plant('Paris','France','Europe',[])];
  let state=evidenceReducer(initialEvidenceState(records),{type:'select',id:'Bremen'},records);
  state=evidenceReducer(state,{type:'pin',id:'Bremen'},records);
  state=evidenceReducer(state,{type:'route',value:'bof_steel_capacity_ttpa'},records);
  state=evidenceReducer(state,{type:'siteView',value:'production'},records);
  assert.equal(evidenceReducer(state,{type:'select',id:'Bremen'},records).siteView,'production');
  for(const action of [{type:'select',id:'Berlin'},{type:'clear'}]){
    const next=evidenceReducer(state,action,records);
    assert.equal(next.siteView,'process');assert.equal(next.route,'bof_steel_capacity_ttpa');assert.deepEqual(next.pins,['Bremen']);
  }
  for(const action of [{type:'country',country:'France'},{type:'region',region:'Europe'}]){
    const next=evidenceReducer(state,action,records);
    assert.equal(next.siteView,'process');assert.equal(next.selectedId,null);assert.equal(next.route,'bof_steel_capacity_ttpa');assert.deepEqual(next.pins,[]);
  }
});

test('unsupported geography cannot silently broaden or replace the analytical population',()=>{
  const records=[plant('Bremen','Germany','Europe',[]),plant('Paris','France','Europe',[]),plant('Tokyo','Japan','Asia',[])];
  const state=initialEvidenceState(records);
  for(const action of [{type:'country',country:'Not a source country'},{type:'country'},{type:'region',region:'Unsupported region'},{type:'region'}]){
    assert.equal(evidenceReducer(state,action,records),state);
  }
  const allRegion=evidenceReducer(state,{type:'country',country:''},records);
  assert.deepEqual(allRegion.scope,{region:'Europe',country:''});
  assert.equal(scopePlants(records,allRegion.scope).length,2);
  const allWorld=evidenceReducer(state,{type:'region',region:''},records);
  assert.deepEqual(allWorld.scope,{region:'',country:''});
  assert.equal(scopePlants(records,allWorld.scope).length,3);
});

test('comparison opens after the second pin and site inspection can return without discarding either pin',()=>{
  const records=[plant('Bremen','Germany','Europe',[]),plant('Berlin','Germany','Europe',[])];
  const initial=initialEvidenceState(records);assert.equal(initial.comparisonVisible,false);
  let state=evidenceReducer(initial,{type:'pin',id:'Bremen'},records);
  assert.equal(state.comparisonVisible,false);assert.equal(evidenceReducer(state,{type:'compare'},records),state);
  state=evidenceReducer(state,{type:'pin',id:'Berlin'},records);
  assert.equal(state.comparisonVisible,true);
  const comparisonSnapshot=structuredClone(state);
  const inspected=evidenceReducer(state,{type:'select',id:'Bremen'},records);
  assert.equal(inspected.comparisonVisible,false);assert.deepEqual(inspected.pins,['Bremen','Berlin']);
  const reopened=evidenceReducer(inspected,{type:'compare'},records);
  assert.equal(reopened.comparisonVisible,true);assert.equal(reopened.selectedId,'Bremen');
  assert.deepEqual(reopened.scope,initial.scope);assert.deepEqual(reopened.camera,initial.camera);
  assert.deepEqual(state,comparisonSnapshot,'Later interactions must leave a saved back snapshot unchanged');
  assert.equal(evidenceReducer(reopened,{type:'select',id:'Bremen'},records).comparisonVisible,false,'Selecting even the same site must reveal it');
  for(const action of [{type:'unpin',id:'Berlin'},{type:'pin',id:'Bremen'},{type:'country',country:'Germany'},{type:'region',region:'Europe'}]){
    assert.equal(evidenceReducer(reopened,action,records).comparisonVisible,false);
  }
});

test('clear comparison preserves the selected site, its depth, the route and camera',()=>{
  const records=[plant('Bremen','Germany','Europe',[]),plant('Berlin','Germany','Europe',[])];
  let state=evidenceReducer(initialEvidenceState(records),{type:'select',id:'Bremen'},records);
  for(const action of [{type:'route',value:'bof_steel_capacity_ttpa'},{type:'product',value:'hot rolled'},{type:'siteView',value:'products'},{type:'pin',id:'Bremen'},{type:'pin',id:'Berlin'}])state=evidenceReducer(state,action,records);
  const snapshot=structuredClone(state), cleared=evidenceReducer(state,{type:'clearPins'},records);
  assert.deepEqual(cleared,{...state,pins:[],comparisonVisible:false});
  assert.deepEqual(state,snapshot);
});
test('pinned local artifact matches its bytes and release contract when supplied',async t=>{
  let bytes;try{bytes=await readFile(new URL('../public/data/gist-plants.v1.json',import.meta.url));}catch(error){if(error.code==='ENOENT'){t.skip('Reviewed local artifact is intentionally not bundled.');return;}throw error;}
  const digest=createHash('sha256').update(bytes).digest('hex').toUpperCase();assert.equal(digest,GIST_SHA256);
  const data=JSON.parse(bytes);assert.equal(validatePinnedPayload(data,digest).plants.length,1293);
  assert.throws(()=>validatePinnedPayload(data,'0'.repeat(64)),/SHA-256/);
  const invalid=structuredClone(data);invalid.meta.production_years.push('2025');assert.throws(()=>validatePinnedPayload(invalid,digest),/production years/);
});
