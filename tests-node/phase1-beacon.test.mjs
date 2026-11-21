import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {newGame,step,beginning} from '../site/storm-v2.mjs';
const cases=JSON.parse(fs.readFileSync(new URL('../site/phase1-cases.json',import.meta.url))).games;
const blank=()=>Array.from({length:8},()=>[]);
test('three complete Phase 1 winning examples are exact deterministic states',()=>{
 for(const c of cases){
   let s=newGame(c.waves);
   assert.equal(c.example.length,8);
   for(const rec of c.example){
     for(const [k,v] of Object.entries(rec.before))assert.deepEqual(s[k],v,`${c.id} before ${k}`);
     const original=structuredClone(s);
     assert.deepEqual(step(s,rec.plan),rec.after);
     assert.deepEqual(s,original,'reducer may not mutate caller state');
     s=step(s,rec.plan);
   }
   assert.equal(s.finished,'WIN');
   assert.equal(s.beacon,3);
   assert(s.hull>0);
   assert.throws(()=>step(s,{}),/ended/);
 }
});
test('Beacon and construction compete for one project slot; valid builds activate only next round',()=>{
 let s=newGame(blank());
 assert.throws(()=>step(s,{charge:true,build:1}),/Beacon OR construction/);
 assert.throws(()=>step(s,{charge:true,shield:1}),/Not enough Power/);
 assert.throws(()=>step(s,{charge:1}),/true or false/);
 assert.throws(()=>step(s,{charge:true,shield:-1}),/Shield must cost/);
 s=step(s,{build:1});assert.deepEqual(s.levels,[0,0,0]);assert.equal(s.pending,1);
 s=step(s,{});assert.equal(s.levels[1],1);
 let x=newGame(blank());x.beacon=3;
 assert.throws(()=>step(x,{charge:true}),/already charged/);
 x=newGame(blank());x.round=8;
 assert.throws(()=>step(x,{build:1}),/Construction unavailable/);
});
test('Aegis requires a paid shield, and outages disable its multiplier',()=>{
 const waves=blank();waves[0]=[{lane:1,sign:1,strength:3}];
 let s=step(newGame(waves),{});
 s.levels[1]=1;
 const no=step(s,{}),one=step(s,{shield:1}),two=step(s,{shield:2});
 assert.equal(no.history.at(-1).damage,3);
 assert.equal(one.history.at(-1).damage,1);
 assert.equal(two.history.at(-1).damage,0);
 assert.equal(two.history.at(-1).shieldSpent,2);
 assert.equal(one.power,1);
 const outage=structuredClone(s);outage.outages[1]=true;
 assert.equal(step(outage,{shield:1}).history.at(-1).damage,2);
});
test('forecast and status do not affect reducer, invalid edits are rejected',()=>{
 const c=cases[0];let s=newGame(c.waves);
 assert.deepEqual(beginning(s).board.map(x=>x.id),['r1t0','r1t1']);
 assert.deepEqual(s.board,[]);
 assert.throws(()=>step(s,{edits:[{kind:'SHIFT',token:'unknown',delta:1}]}),/not available/);
 assert.throws(()=>step(s,{edits:[{kind:'SHIFT',token:'r1t0',delta:-1}]}),/adjacent lane/);
 assert.throws(()=>step(s,{edits:[{kind:'DAMP',token:'r1t0'},{kind:'HOLD',token:'r1t0'}]}),/one paid intervention/);
});
test('winning objective cannot be met without Beacon and an online system',()=>{
 let s=newGame(blank());
 s.round=8;s.power=2;s.beacon=3;
 assert.equal(step(s,{}).finished,'LOSS_OBJECTIVE');
 s.levels[0]=1;s.outages[0]=true;
 assert.equal(step(s,{}).finished,'LOSS_OBJECTIVE');
 s.outages[0]=false;
 assert.equal(step(s,{}).finished,'WIN');
});
