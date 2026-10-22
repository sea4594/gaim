import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {RoomStore} from '../dist/src/rooms.js';
import {createApp} from '../server/http.mjs';
const scenarios=JSON.parse(readFileSync(new URL('../contracts/scenarios.v0.1.json',import.meta.url))).scenarios;
const call=(store,id,key,type,revision,extra={},requestId='unique_001')=>store.command(id,key,{type,expectedRevision:revision,requestId,...extra});
test('seat ownership, readiness and revision-safe duplicate commands',()=>{
  let time=1000;const store=new RoomStore(scenarios,()=>time,500);
  const id='abcdefabcdefabcdefabcdef';const code='TESTABCD';
  store.create(id,code,'verified-3','secret0');store.join(code,'secret1');
  assert.throws(()=>store.command(id,'wrong',{type:'START_GAME'}),e=>e.code==='UNAUTHORIZED');
  let a=store.snapshot(id,'secret0');
  a=call(store,id,'secret0','SET_READY',a.revision,{ready:true},'r0011111');
  a=call(store,id,'secret1','SET_READY',a.revision,{ready:true},'r0022222');
  a=call(store,id,'secret0','START_GAME',a.revision,{},'r0033333');
  assert.equal(a.snapshot.phase,'planning');assert.deepEqual(a.snapshot.game.slotOwners,[0,1,0,1]);
  const firstToken=a.snapshot.game.charges[0];
  const bad={type:'SET_EDIT',expectedRevision:a.revision,requestId:'r0044444',slot:1,action:{kind:'HOLD',tokenId:firstToken.id}};
  assert.throws(()=>store.command(id,'secret0',bad),e=>e.code==='NOT_OWNER');
  const valid={...bad,slot:0};
  const v=store.command(id,'secret0',valid);
  assert.deepEqual(store.command(id,'secret0',valid),v);
  assert.throws(()=>store.command(id,'secret0',{...valid,action:null}),e=>e.code==='IDEMPOTENCY_CONFLICT');
  assert.throws(()=>store.command(id,'secret0',{...valid,requestId:'r0055555'}),e=>e.code==='STALE_REVISION');
  assert.throws(()=>store.command(id,'secret1',{...valid,requestId:'r0066666',expectedRevision:v.revision,slot:1}),e=>e.code==='TOKEN_ALREADY_PLANNED');
  assert.deepEqual(store.snapshot(id,'secret0').snapshot.proposals,v.snapshot.proposals);
  let b=call(store,id,'secret0','SET_READY',v.revision,{ready:true},'r0077777');
  assert.throws(()=>call(store,id,'secret0','SET_EDIT',b.revision,{slot:0,action:null},'r0088888'),e=>e.code==='ALREADY_READY');
  b=call(store,id,'secret1','SET_READY',b.revision,{ready:true},'r0099999');
  assert.equal(b.snapshot.game.completedRound,1);
  assert.equal(b.snapshot.revision,b.revision);
  assert.equal(b.snapshot.proposals.length,0);
  store.disconnect(id,'secret1');assert.equal(store.snapshot(id,'secret0').snapshot.seats[1].connected,false);
  store.resume(id,'secret1');assert.equal(store.snapshot(id,'secret0').snapshot.seats[1].connected,true);
  // timed round locks without waiting for disconnected teammates
  time=2000;store.tick();assert.equal(store.snapshot(id,'secret1').snapshot.game.completedRound,2);
  store.tick();assert.equal(store.snapshot(id,'secret1').snapshot.game.completedRound,2);
});
test('server HTTP create/join/resume, authentication, stale revisions, and SSE',async t=>{
  const app=createApp({durationMs:8000});
  await new Promise(ok=>app.server.listen(0,'127.0.0.1',ok));
  t.after(async()=>await app.close());
  const base=`http://127.0.0.1:${app.server.address().port}`;
  async function post(body,secret){const resp=await fetch(`${base}/api`,{method:'POST',headers:{'content-type':'application/json',...(secret?{authorization:`Bearer ${secret}`}:{})},body:JSON.stringify(body)});return {status:resp.status,body:await resp.json()};}
  const first=await post({type:'CREATE_ROOM',requestId:'create1234',ruleset:'charge-loom/v0.1',scenarioId:'verified-3'});
  assert.equal(first.status,200);const {roomId,roomCode,resumeSecret}=first.body;
  assert.ok(resumeSecret.length>=32);assert.equal(first.body.snapshot.game,null);
  assert.equal(JSON.stringify(first.body.snapshot).includes(resumeSecret),false);
  const second=await post({type:'JOIN_ROOM',requestId:'join12345',roomCode});assert.equal(second.status,200);
  const sn=await post({type:'GET_SNAPSHOT',roomId},resumeSecret);assert.equal(sn.status,200);
  const bad=await post({type:'GET_SNAPSHOT',roomId},'abcdefghijklmnopqrstuvwxyz123456');assert.equal(bad.status,401);
  const res=await post({type:'RESUME',roomId},second.body.resumeSecret);assert.equal(res.status,200);
  const fresh=await post({type:'GET_SNAPSHOT',roomId},resumeSecret);
  assert.equal(fresh.body.snapshot.seats.length,2);
  const stale=await post({type:'SET_READY',roomId,requestId:'setready11',expectedRevision:0,ready:true},resumeSecret);
  assert.equal(stale.status,409);assert.equal(stale.body.error,'STALE_REVISION');
  // SSE must supply an authenticated initial snapshot and then updates.
  const ctrl=new AbortController();
  const eventResp=await fetch(`${base}/events?roomId=${roomId}`,{headers:{authorization:`Bearer ${resumeSecret}`},signal:ctrl.signal});
  assert.equal(eventResp.status,200);assert.match(eventResp.headers.get('content-type'),/text\/event-stream/);
  const reader=eventResp.body.getReader();
  const part=await reader.read();assert.match(Buffer.from(part.value).toString('utf8'),/event: snapshot/);
  ctrl.abort();await reader.cancel().catch(()=>{});
});
test('HTTP rejects oversized or malformed requests',async t=>{
  const app=createApp();await new Promise(ok=>app.server.listen(0,'127.0.0.1',ok));t.after(()=>app.close());
  const url=`http://127.0.0.1:${app.server.address().port}/api`;
  const malformed=await fetch(url,{method:'POST',body:'nope'});assert.equal(malformed.status,409);
  const big=await fetch(url,{method:'POST',body:'x'.repeat(34000)});assert.equal(big.status,409);
});
const golden=JSON.parse(readFileSync(new URL('../contracts/golden-traces.v0.1.json',import.meta.url))).traces;
test('complete nine-round live room witness works for every player count 1..4',()=>{
  const witness=golden[0];
  for(let players=1;players<=4;players++){
    const room=`a${players}`.padEnd(24,'a');const code=`AAAAAAA${players}`;
    const store=new RoomStore(scenarios,()=>10000,75000);
    store.create(room,code,witness.scenarioId,'seat0');
    for(let seat=1;seat<players;seat++)store.join(code,`seat${seat}`);
    let rev=store.snapshot(room,'seat0').revision;
    let nonce=0;
    const issue=(seat,type,rest={})=>{
      const result=call(store,room,`seat${seat}`,type,rev,rest,`request${++nonce}`);
      rev=result.revision;return result.snapshot;
    };
    for(let seat=0;seat<players;seat++)issue(seat,'SET_READY',{ready:true});
    issue(0,'START_GAME');
    for(let r=0;r<9;r++){
      const view=store.snapshot(room,'seat0').snapshot.game;
      for(let slot=0;slot<witness.actions[r].length;slot++){
        const [kind,tokenId,direction]=witness.actions[r][slot];
        issue(view.slotOwners[slot],'SET_EDIT',{slot,action:{kind:kind.toUpperCase(),tokenId,...(direction===undefined?{}:{direction})}});
      }
      for(let seat=0;seat<players;seat++){
        const snapshot=issue(seat,'SET_READY',{ready:true});
        if(seat===players-1)assert.deepEqual(snapshot.game,
          witness.views[r+1].slotOwners.length===4&&players!==4?
          {...witness.views[r+1],slotOwners:snapshot.game.slotOwners}:
          witness.views[r+1]);
      }
    }
    const final=store.snapshot(room,'seat0').snapshot;
    assert.equal(final.phase,'finished');assert.equal(final.game.outcome,'win');
    assert.throws(()=>issue(0,'SET_READY',{ready:true}),e=>e.code==='GAME_FINISHED');
  }
});
