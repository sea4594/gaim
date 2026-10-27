/**
 * Browser implementation of the experimental Phase 3 Storm Engine reducer.
 * Research-only. Keep parity-tested against experiments/redesign_phase3/engine.py.
 * No network, no randomness after the fixed wavebook is loaded.
 */
const clone = x => structuredClone(x);
export const SYSTEMS = ['Dynamo', 'Aegis', 'Switchyard'];
export const LANES = ['Left', 'Center', 'Right'];
export function newGame(waves) {
  if (!Array.isArray(waves) || waves.length !== 8) throw Error('Expected eight storm rounds');
  for (const wave of waves) for (const t of wave) {
    if (![0,1,2].includes(t.lane) || ![-1,1].includes(t.sign) || !(t.strength >= 1 && t.strength <= 3)) throw Error('Invalid storm');
  }
  return {round:1,waves:clone(waves),board:[],hull:6,power:2,coolant:2,
    levels:[0,0,0],pending:null,outages:[false,false,false],finished:null,history:[]};
}
export function beginning(state) {
  const s=clone(state);
  if(s.finished!==null) return s;
  if(s.pending!==null){s.levels[s.pending]++;s.pending=null;}
  s.waves[s.round-1].forEach((t,i)=>s.board.push({...clone(t),id:`r${s.round}t${i}`,depth:2,held:false}));
  return s;
}
function target(board,id){return board.find(t=>t.id===id);}
function validateEdit(board,a){
  const t=target(board,a.token);
  if(!t) throw Error('That charge is not available');
  if(a.kind==='SHIFT'){
    if(![-1,1].includes(a.delta)|| ![0,1,2].includes(t.lane+a.delta)) throw Error('A Shift must move to an adjacent lane');
  }else if(a.kind==='HOLD'){
    if(t.held) throw Error('A charge can be Held only once');
  }else if(a.kind!=='DAMP')throw Error('Unknown charge intervention');
}
function apply(board,a,stopped){
  const t=target(board,a.token);
  if(!t)throw Error('Action target removed earlier in the plan');
  if(a.kind==='SHIFT')t.lane+=a.delta;
  else if(a.kind==='HOLD'){t.held=true;t.strength=Math.min(3,t.strength+1);stopped.add(t.id);}
  else if(a.kind==='DAMP'){t.strength--;if(t.strength===0)board.splice(board.indexOf(t),1);}
}
export function step(state,plan={}){
  if(state.finished!==null) throw Error('This match has already ended');
  const s=beginning(state), r=s.round, offline=[...state.outages];
  const edits=plan.edits||[], build=plan.build??null, free=plan.free??null;
  if(edits.length>2)throw Error('Only two paid interventions per round');
  const used=new Set();let damp=0;
  for(const a of edits){
    validateEdit(s.board,a);
    if(used.has(a.token))throw Error('Each charge can receive only one paid intervention');
    used.add(a.token);if(a.kind==='DAMP')damp++;
  }
  if(damp>s.coolant)throw Error('Not enough coolant');
  if(build!==null){
    if(![0,1,2].includes(build) || s.power<2 || s.levels[build]>=2 || offline[build])throw Error('Construction unavailable: check power, level or outage');
  }
  if(free!==null){
    if(s.levels[2]===0||offline[2])throw Error('Switchyard is unavailable');
    const t=target(s.board,free.token);
    if(!t || (s.levels[2]===1 && t.depth!==2) || ![-1,1].includes(free.delta))throw Error('Invalid Switchyard move');
  }
  if(build!==null){s.power-=2;s.pending=build;}
  const stopped=new Set();for(const a of edits)apply(s.board,a,stopped);
  if(free!==null){
    const t=target(s.board,free.token);
    if(!t || (s.levels[2]===1 && t.depth!==2))throw Error('Switchyard target no longer available');
    validateEdit(s.board,{...free,kind:'SHIFT'});
    apply(s.board,{...free,kind:'SHIFT'},stopped);
  }
  s.coolant-=damp;
  const breached=[];const kept=[];
  for(const old of s.board){
    const t={...old};if(!stopped.has(t.id))t.depth--;
    if(t.depth===0)breached.push(t);else kept.push(t);
  }
  s.board=kept;
  const matches=[0,0,0],leaks=[0,0,0];
  for(let lane=0;lane<3;lane++){
    const positive=breached.filter(t=>t.lane===lane&&t.sign===1).reduce((a,t)=>a+t.strength,0);
    const negative=breached.filter(t=>t.lane===lane&&t.sign===-1).reduce((a,t)=>a+t.strength,0);
    matches[lane]=Math.min(positive,negative);leaks[lane]=Math.abs(positive-negative);
  }
  const total_match=matches.reduce((a,b)=>a+b,0),raw=leaks.reduce((a,b)=>a+b,0);
  const bonus=Number(s.levels[0]>0&&!offline[0]&&((s.levels[0]===1&&matches[0]>0)||(s.levels[0]===2&&total_match>0)));
  const defense=offline[1]?0:s.levels[1],damage=Math.max(0,raw-defense);
  s.power=Math.min(8,s.power+total_match+bonus);s.hull-=damage;
  s.outages=leaks.map(v=>v>=2);
  let deadline=0;
  if(r===8){deadline=s.board.reduce((a,t)=>a+t.strength,0);s.hull-=deadline;}
  if(s.hull<=0)s.finished='LOSS_HULL';
  else if(r===8)s.finished=s.levels.filter((lev,i)=>lev===2&&!offline[i]).length>=2?'WIN':'LOSS_SYSTEMS';
  s.history.push({round:r,edits:clone(edits),build,free:clone(free),matched:matches,raw:leaks,
    bonus,shield:defense,damage,deadline,offline,next_outages:[...s.outages],hull:s.hull,
    power:s.power,levels:[...s.levels],outcome:s.finished});
  if(s.finished===null)s.round++;
  return s;
}
