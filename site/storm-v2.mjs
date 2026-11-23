/**
 * GAIM improvement Phase 1: Beacon network iteration (v2) solo ruleset.
 * Historical Phase 3 engine remains untouched for reference parity.
 * Deterministic and entirely local; no random or network behavior.
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
    levels:[0,0,0],pending:null,outages:[false,false,false],beacon:0,finished:null,history:[]};
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
  const charge=plan.charge??false, shield=plan.shield??0;
  if(typeof charge!=='boolean')throw Error('Beacon order must be true or false');
  if(!Number.isInteger(shield)||shield<0||shield>2)throw Error('Shield must cost 0, 1 or 2 Power');
  if(charge&&build!==null)throw Error('Choose Beacon OR construction, not both');
  if(charge&&s.beacon>=3)throw Error('Beacon is already charged');
  if(charge&&r===8)throw Error('The Beacon must be fully charged before the final storm');
  if(charge&&!s.levels.some((lev,i)=>lev>0&&!offline[i]))throw Error('The Beacon needs at least one online upgraded system');
  if(charge&&s.power<2)throw Error('Not enough Power to charge Beacon');
  if(s.power-(build!==null||charge?2:0)<shield)throw Error('Not enough Power for the shield');
  if(edits.length>2)throw Error('Only two paid interventions per round');
  const used=new Set();let damp=0;
  for(const a of edits){
    validateEdit(s.board,a);
    if(used.has(a.token))throw Error('Each charge can receive only one paid intervention');
    used.add(a.token);if(a.kind==='DAMP')damp++;
  }
  if(damp>s.coolant)throw Error('Not enough coolant');
  if(build!==null){
    if(r===8 || ![0,1,2].includes(build) || s.power<2 || s.levels[build]>=2 || offline[build])throw Error('Construction unavailable: check power, level or outage');
  }
  if(free!==null){
    if(s.levels[2]===0||offline[2])throw Error('Switchyard is unavailable');
    const t=target(s.board,free.token);
    if(!t || ![-2,-1,1,2].includes(free.delta) || Math.abs(free.delta)>s.levels[2] || ![0,1,2].includes(t.lane+free.delta))throw Error('Invalid Switchyard move');
  }
  if(build!==null){s.power-=2;s.pending=build;}
  if(charge){s.power-=2;s.beacon++;}
  s.power-=shield;
  const stopped=new Set();for(const a of edits)apply(s.board,a,stopped);
  if(free!==null){
    const t=target(s.board,free.token);
    if(!t || ![0,1,2].includes(t.lane+free.delta))throw Error('Switchyard target no longer available or legal');
    t.lane+=free.delta;
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
  if(charge&&total_match===0)throw Error('Charging the Beacon requires a polarity collision this round');
  const bonus=s.levels[0]>0&&!offline[0]&&((s.levels[0]===1&&matches[0]>0)||(s.levels[0]===2&&total_match>0))?s.levels[0]:0;
  const defense=shield*(1+(offline[1]?0:s.levels[1])),damage=Math.max(0,raw-defense);
  s.power=Math.min(8,s.power+total_match+bonus);s.hull-=damage;
  s.outages=leaks.map(v=>v>=2);
  let deadline=0;
  if(r===8){deadline=s.board.reduce((a,t)=>a+t.strength,0);s.hull-=deadline;}
  if(s.hull<=0)s.finished='LOSS_HULL';
  else if(r===8)s.finished=s.beacon===3&&s.levels.some((lev,i)=>lev>0&&!offline[i])?'WIN':'LOSS_OBJECTIVE';
  s.history.push({round:r,edits:clone(edits),build,charge,shieldSpent:shield,free:clone(free),matched:matches,raw:leaks,
    bonus,shield:defense,damage,deadline,offline,next_outages:[...s.outages],hull:s.hull,
    power:s.power,beacon:s.beacon,levels:[...s.levels],outcome:s.finished});
  if(s.finished===null)s.round++;
  return s;
}
