import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {newGame,resolveRound,publicView,slotOwners,RuleError} from '../dist/src/engine.js';
const scenarios=JSON.parse(readFileSync(new URL('../contracts/scenarios.v0.1.json',import.meta.url))).scenarios;
const bank=JSON.parse(readFileSync(new URL('../contracts/golden-traces.v0.1.json',import.meta.url))).traces;
const convert=action=>({kind:action[0].toUpperCase(),tokenId:action[1],...(action[0]==='shift'?{direction:action[2]}:{})});
for(const trace of bank){
  test(`complete exact Python parity: ${trace.scenarioId} (all 10 views)`,()=>{
    let state=newGame();const scenario=scenarios.find(s=>s.id===trace.scenarioId);
    assert.deepStrictEqual(publicView(state,scenario,4),trace.views[0]);
    for(let round=0;round<9;round++){
      state=resolveRound(state,scenario,trace.actions[round].map(convert));
      assert.deepStrictEqual(publicView(state,scenario,4),trace.views[round+1],`round ${round+1}`);
    }
    assert.equal(state.outcome,'win');
  });
}
test('equitable assignment 1-4 players without changing action budget',()=>{
  assert.deepEqual(slotOwners(1,1),[0,0,0,0]);
  assert.deepEqual(slotOwners(2,1),[0,1,0,1]);
  assert.deepEqual(slotOwners(3,2),[1,2,0,1]);
  assert.deepEqual(slotOwners(4,6),[1,2,3,0]);
});
test('all invalid combined plans fail atomically',()=>{
  const s=scenarios[0];const start=newGame();
  const original=JSON.stringify(start);
  const token=publicView(start,s,1).charges[0];
  const wrong=[
    [{kind:'HOLD',tokenId:token.id},{kind:'DAMP',tokenId:token.id}],
    [{kind:'SHIFT',tokenId:token.id,direction:0}],
    [{kind:'SHIFT',tokenId:token.id,direction:1,unexpected:true}],
    [{kind:'DAMP',tokenId:999999}],
    [{kind:'HOLD',tokenId:true}],
    Array(5).fill({kind:'DAMP',tokenId:token.id})
  ];
  for(const w of wrong)assert.throws(()=>resolveRound(start,s,w),RuleError);
  assert.equal(JSON.stringify(start),original);
});
test('pure reducer is reproducible; terminal games reject further changes',()=>{
  const s=scenarios[0];let a=newGame(),b=newGame();
  for(let i=0;i<9;i++){a=resolveRound(a,s,[]);b=resolveRound(b,s,[]);assert.deepEqual(a,b);if(a.outcome)break;}
  assert.ok(a.outcome);
  assert.throws(()=>resolveRound(a,s,[]),e=>e.code==='GAME_FINISHED');
});
test('exact cooperative pair of shifts',()=>{
  const sc={id:'manual',waves:Array.from({length:9},()=>[])};
  const seed={completedRound:7,hull:5,capacitors:[2,2,1],coolant:3,nextTokenId:3,outcome:null,
    charges:[{id:1,lane:0,band:0,polarity:'POSITIVE',strength:1,alreadyHeld:false},{id:2,lane:2,band:0,polarity:'NEGATIVE',strength:1,alreadyHeld:false}]};
  const one=resolveRound(seed,sc,[{kind:'SHIFT',tokenId:1,direction:1}]);
  const both=resolveRound(seed,sc,[{kind:'SHIFT',tokenId:1,direction:1},{kind:'SHIFT',tokenId:2,direction:-1}]);
  assert.equal(one.hull,3);assert.equal(both.hull,5);assert.deepEqual(both.capacitors,[2,3,1]);
});
