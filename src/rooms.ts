/** In-memory, server-authoritative co-op room protocol. All mutations synchronous.
 * Deliberately no persistence: process restart ends active games.
 */
import type { GameEdit, RoomSnapshot } from '../contracts/protocol-v1.js';
import {newGame,publicView,resolveRound,slotOwners,validatePlan,validateEdit,RuleError} from './engine.js';
import type {CompletedState,Scenario} from './engine.js';

interface Member { hash: string; ready: boolean; connected: boolean; }
interface Cached { fingerprint: string; response: Reply }
export type Reply = { revision: number; snapshot: RoomSnapshot };
export type Command =
  | {type:'START_GAME';expectedRevision:number;requestId:string}
  | {type:'SET_READY';expectedRevision:number;requestId:string;ready:boolean}
  | {type:'SET_EDIT';expectedRevision:number;requestId:string;slot:number;action:GameEdit|null};
export class RoomError extends Error {
  constructor(public readonly code: string, message: string) {super(message);this.name='RoomError';}
}
function check(b:boolean,code:string,msg:string): asserts b {if(!b)throw new RoomError(code,msg);}
function isInteger(v:unknown):v is number{return typeof v==='number'&&Number.isSafeInteger(v);}
function sameKeys(v:object,names:string[]):boolean {return Object.keys(v).sort().join('|')===names.sort().join('|');}
interface InternalRoom {
  id:string;code:string;scenario:Scenario;phase:'lobby'|'planning'|'finished';revision:number;
  seats:Member[];game:CompletedState|null;drafts:Map<number,GameEdit>;deadlineAt:number|null;
  dedup:Map<string,Cached>;listeners:Set<(snapshot:RoomSnapshot)=>void>;
}
export class RoomStore {
  private rooms = new Map<string,InternalRoom>();
  constructor(private readonly scenarios:Scenario[],private readonly clock:()=>number=()=>Date.now(),private readonly durationMs=75000) {}
  private room(id:string):InternalRoom {const r=this.rooms.get(id);check(!!r,'UNAUTHORIZED','unknown room');return r;}
  private seat(r:InternalRoom,hash:string):number {const idx=r.seats.findIndex(s=>s.hash===hash);check(idx>=0,'UNAUTHORIZED','invalid seat credential');return idx;}
  private changed(r:InternalRoom):void {r.revision++;const snap=this.view(r);for(const cb of r.listeners)cb(snap);}
  private view(r:InternalRoom):RoomSnapshot {
    const owners=r.game&&r.game.outcome===null?slotOwners(r.seats.length,r.game.completedRound+1):[];
    return {roomId:r.id,revision:r.revision,phase:r.phase,
      seats:r.seats.map((s,i)=>({seat:i as 0|1|2|3,ready:s.ready,connected:s.connected})),
      deadlineAt:r.deadlineAt===null?null:new Date(r.deadlineAt).toISOString(),
      proposals:[...r.drafts.entries()].sort((a,b)=>a[0]-b[0]).map(([slot,action])=>({slot:slot as 0|1|2|3,seat:owners[slot] as 0|1|2|3,action:{...action}})),
      game:r.game?publicView(r.game,r.scenario,r.seats.length):null};
  }
  create(roomId:string,roomCode:string,scenarioId:string,credentialHash:string):Reply {
    check(!this.rooms.has(roomId),'BAD_PAYLOAD','room already exists');
    const scenario=this.scenarios.find(s=>s.id===scenarioId);
    check(!!scenario,'UNKNOWN_SCENARIO','only verified scenarios permitted');
    check(![...this.rooms.values()].some(r=>r.code===roomCode),'BAD_PAYLOAD','room code already used');
    const r:InternalRoom={id:roomId,code:roomCode,scenario,phase:'lobby',revision:0,
      seats:[{hash:credentialHash,ready:false,connected:true}],game:null,drafts:new Map(),deadlineAt:null,dedup:new Map(),listeners:new Set()};
    this.rooms.set(roomId,r);return {revision:r.revision,snapshot:this.view(r)};
  }
  findCode(code:string):string|null {return [...this.rooms.values()].find(r=>r.code===code)?.id??null;}
  join(code:string,credentialHash:string):Reply {
    const id=this.findCode(code);check(id!==null,'UNAUTHORIZED','invalid room code');const r=this.room(id);
    check(r.phase==='lobby','GAME_ALREADY_STARTED','game in progress');
    check(r.seats.length<4,'ROOM_FULL','only four seats');
    check(!r.seats.some(s=>s.hash===credentialHash),'UNAUTHORIZED','duplicate credential');
    r.seats.push({hash:credentialHash,ready:false,connected:true});this.changed(r);
    return {revision:r.revision,snapshot:this.view(r)};
  }
  resume(id:string,hash:string):Reply {const r=this.room(id);const seat=this.seat(r,hash);r.seats[seat]!.connected=true;this.changed(r);return {revision:r.revision,snapshot:this.view(r)};}
  disconnect(id:string,hash:string):void {const r=this.room(id);const seat=this.seat(r,hash);if(r.seats[seat]!.connected){r.seats[seat]!.connected=false;this.changed(r);}}
  snapshot(id:string,hash:string):Reply {const r=this.room(id);this.seat(r,hash);return {revision:r.revision,snapshot:this.view(r)};}
  subscribe(id:string,hash:string,listener:(snap:RoomSnapshot)=>void):()=>void {
    const r=this.room(id);this.seat(r,hash);r.listeners.add(listener);return ()=>r.listeners.delete(listener);
  }
  private plan(r:InternalRoom):GameEdit[] {
    check(!!r.game,'GAME_FINISHED','missing game');
    const actions=[...r.drafts.entries()].sort((a,b)=>a[0]-b[0]).map(([,a])=>a);
    try{return validatePlan(r.game,r.scenario,actions);}catch(e){
      if(e instanceof RuleError)throw new RoomError(e.code,e.message);throw e;
    }
  }
  private lock(r:InternalRoom):void {
    if(r.phase!=='planning'||!r.game)return;
    const actions=this.plan(r);
    r.game=resolveRound(r.game,r.scenario,actions);
    r.drafts.clear();
    if(r.game.outcome!==null){r.phase='finished';r.deadlineAt=null;}
    else{r.deadlineAt=this.clock()+this.durationMs;}
    for(const s of r.seats)s.ready=false;
    this.changed(r);
  }
  tick():void {for(const r of this.rooms.values())if(r.phase==='planning'&&r.deadlineAt!==null&&this.clock()>=r.deadlineAt)this.lock(r);}
  command(id:string,hash:string,raw:unknown):Reply {
    const r=this.room(id);const seat=this.seat(r,hash);
    check(!!raw&&typeof raw==='object'&&!Array.isArray(raw),'BAD_PAYLOAD','command object required');
    const cmd=raw as Record<string,unknown>;
    const type=cmd.type;
    check(type==='START_GAME'||type==='SET_READY'||type==='SET_EDIT','BAD_PAYLOAD','unknown command');
    const fields=type==='START_GAME'?['type','requestId','expectedRevision']:
      type==='SET_READY'?['type','requestId','expectedRevision','ready']:
      ['type','requestId','expectedRevision','slot','action'];
    check(sameKeys(cmd,fields),'BAD_PAYLOAD','unexpected or missing command fields');
    check(typeof cmd.requestId==='string'&&/^[A-Za-z0-9_-]{8,80}$/.test(cmd.requestId),'BAD_PAYLOAD','invalid request ID');
    const key=seat+':'+cmd.requestId;
    const fingerprint=JSON.stringify(cmd);
    const cached=r.dedup.get(key);
    if(cached){check(cached.fingerprint===fingerprint,'IDEMPOTENCY_CONFLICT','requestId reused with different payload');return cached.response;}
    check(isInteger(cmd.expectedRevision),'BAD_PAYLOAD','expectedRevision must be integer');
    check(cmd.expectedRevision===r.revision,'STALE_REVISION','refresh current snapshot');
    if(type==='START_GAME'){
      check(r.phase==='lobby','GAME_ALREADY_STARTED','not in lobby');
      check(seat===0,'UNAUTHORIZED','host seat required');
      check(r.seats.every(s=>s.ready),'ALREADY_READY','all players must be lobby ready');
      r.game=newGame();r.phase='planning';r.deadlineAt=this.clock()+this.durationMs;
      for(const s of r.seats)s.ready=false;
      this.changed(r);
    } else if(type==='SET_READY') {
      check(typeof cmd.ready==='boolean','BAD_PAYLOAD','ready must be boolean');
      check(r.phase!=='finished','GAME_FINISHED','game ended');
      check(r.phase==='planning'||r.phase==='lobby','BAD_PAYLOAD','bad phase');
      check(r.seats[seat]!.ready!==cmd.ready,'ALREADY_READY','ready state unchanged');
      r.seats[seat]!.ready=cmd.ready;this.changed(r);
      if(r.phase==='planning'&&r.seats.every(s=>s.ready))this.lock(r);
    } else {
      check(r.phase==='planning'&&!!r.game,'GAME_FINISHED','game is not planning');
      check(isInteger(cmd.slot)&&cmd.slot>=0&&cmd.slot<4,'BAD_PAYLOAD','invalid slot');
      const owner=slotOwners(r.seats.length,r.game.completedRound+1)[cmd.slot];
      check(owner===seat,'NOT_OWNER','slot belongs to another seat');
      check(!r.seats[seat]!.ready,'ALREADY_READY','unready before changing edits');
      if(cmd.action!==null){
        try{validateEdit(cmd.action);}catch(e){if(e instanceof RuleError)throw new RoomError(e.code,e.message);throw e;}
      }
      const prior=r.drafts.get(cmd.slot);
      if(cmd.action===null)r.drafts.delete(cmd.slot);
      else r.drafts.set(cmd.slot,cmd.action as GameEdit);
      try{this.plan(r);}catch(e){
        if(prior===undefined)r.drafts.delete(cmd.slot);else r.drafts.set(cmd.slot,prior);
        throw e;
      }
      this.changed(r);
    }
    const response={revision:r.revision,snapshot:this.view(r)};
    // Room-scoped cache for the session lifetime. Never replay state mutations.
    r.dedup.set(key,{fingerprint,response});
    return response;
  }
}
