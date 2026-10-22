/** Charge Loom v0.1 authoritative, deterministic, side-effect-free reducer.
 * Explicit scenario schedules avoid Python/JS seeded-RNG incompatibilities.
 */
import type { ChargeView, EngineView, GameEdit, WaveCharge } from '../contracts/protocol-v1.js';

export interface ScenarioWave { lane: number; polarity: number; strength: number }
export interface Scenario { id: string; waves: ScenarioWave[][] }
export interface CompletedState {
  completedRound: number;
  hull: number;
  capacitors: [number, number, number];
  coolant: number;
  charges: ChargeView[];
  nextTokenId: number;
  outcome: EngineView['outcome'];
}
export class RuleError extends Error {
  constructor(public readonly code: string, message: string) { super(message); this.name = 'RuleError'; }
}
const fail = (code: string, message: string): never => { throw new RuleError(code, message); };
const int = (v: unknown): v is number => typeof v === 'number' && Number.isSafeInteger(v);
const keys = (v: object, names: string[]): boolean => Object.keys(v).sort().join(',') === names.sort().join(',');

export function newGame(): CompletedState {
  return {completedRound: 0, hull: 7, capacitors: [0,0,0], coolant: 3, charges: [], nextTokenId: 1, outcome: null};
}
export function slotOwners(count: number, planningRound: number): [number, number, number, number] {
  if (!int(count) || count < 1 || count > 4 || !int(planningRound) || planningRound < 1 || planningRound > 9)
    return fail('BAD_PAYLOAD', 'player count or planning round invalid');
  const first = (planningRound - 1) % count;
  return [0,1,2,3].map(n => (first+n) % count) as [number,number,number,number];
}
export function projectedCharges(state: CompletedState, scenario: Scenario): ChargeView[] {
  const tokens = state.charges.map(t => ({...t}));
  if (state.outcome !== null) return tokens.sort((a,b) => a.id - b.id);
  for (const [index, wave] of (scenario.waves[state.completedRound] ?? []).entries()) {
    tokens.push({id: state.nextTokenId + index, lane: wave.lane as 0|1|2, band: 2,
      polarity: wave.polarity === 1 ? 'POSITIVE' : 'NEGATIVE',
      strength: wave.strength as 1|2|3, alreadyHeld: false});
  }
  return tokens.sort((a,b)=>a.id-b.id);
}
export function publicView(state: CompletedState, scenario: Scenario, playerCount: number): EngineView {
  const finished = state.outcome !== null;
  const next = finished ? [] : (scenario.waves[state.completedRound+1] ?? []);
  return {
    protocolVersion: 1, ruleset: 'charge-loom/v0.1',
    completedRound: state.completedRound, planningRound: finished ? null : state.completedRound+1,
    hull: state.hull, capacitors: [...state.capacitors] as [number,number,number], coolant: state.coolant,
    charges: projectedCharges(state, scenario),
    nextWave: next.map(w => ({lane:w.lane as 0|1|2, polarity:w.polarity === 1 ? 'POSITIVE':'NEGATIVE',strength:w.strength as 1|2})) as WaveCharge[],
    slotOwners: finished ? [] : slotOwners(playerCount, state.completedRound+1) as (0|1|2|3)[],
    outcome: state.outcome
  };
}
export function validateEdit(action: unknown): asserts action is GameEdit {
  if (!action || typeof action !== 'object' || Array.isArray(action)) return fail('BAD_PAYLOAD','edit must be an object');
  const a = action as Record<string, unknown>;
  if (!int(a.tokenId) || a.tokenId <= 0) return fail('ILLEGAL_EDIT','tokenId must be a positive integer');
  if (a.kind === 'SHIFT') {
    if (!keys(a,['kind','tokenId','direction']) || !int(a.direction) || (a.direction !== -1 && a.direction !== 1))
      return fail('ILLEGAL_EDIT','SHIFT requires integer direction -1 or +1');
  } else if (a.kind === 'HOLD' || a.kind === 'DAMP') {
    if (!keys(a,['kind','tokenId'])) return fail('ILLEGAL_EDIT','unexpected edit fields');
  } else return fail('ILLEGAL_EDIT','unknown edit kind');
}
/** Validate ALL edits without side effects; missing slots are PASS. */
export function validatePlan(state: CompletedState, scenario: Scenario, edits: unknown): GameEdit[] {
  if (state.outcome !== null || state.completedRound >= 9) return fail('GAME_FINISHED','game ended');
  if (!Array.isArray(edits) || edits.length > 4) return fail('ILLEGAL_EDIT','maximum four edits');
  const tokens = projectedCharges(state,scenario);
  const used = new Set<number>(); let coolant = state.coolant;
  for (const raw of edits) {
    validateEdit(raw);
    const a = raw as GameEdit;
    if (used.has(a.tokenId)) return fail('TOKEN_ALREADY_PLANNED','token already targeted');
    used.add(a.tokenId);
    const t = tokens.find(t=>t.id===a.tokenId);
    if (!t) return fail('ILLEGAL_EDIT','token not on planning board');
    if (a.kind === 'SHIFT' && (t.lane + a.direction < 0 || t.lane + a.direction > 2))
      return fail('ILLEGAL_EDIT','shift exits the board');
    if (a.kind === 'HOLD' && t.alreadyHeld) return fail('ILLEGAL_EDIT','token already held');
    if (a.kind === 'DAMP' && --coolant < 0) return fail('INSUFFICIENT_COOLANT','coolant exhausted');
  }
  return edits as GameEdit[];
}
export function resolveRound(state: CompletedState, scenario: Scenario, edits: unknown): CompletedState {
  const actions = validatePlan(state,scenario,edits);
  let charges = projectedCharges(state,scenario);
  const held = new Set<number>();
  let coolant = state.coolant;
  for (const action of actions) {
    const idx = charges.findIndex(t=>t.id===action.tokenId);
    const t = charges[idx]!;
    if (action.kind === 'SHIFT') charges[idx] = {...t,lane:(t.lane+action.direction) as 0|1|2};
    if (action.kind === 'HOLD') {charges[idx]={...t,strength:Math.min(3,t.strength+1) as 1|2|3,alreadyHeld:true};held.add(t.id);}
    if (action.kind === 'DAMP') {coolant--;charges[idx]={...t,strength:(t.strength-1) as 1|2|3};}
  }
  charges=charges.filter(t=>t.strength>0).map(t=>held.has(t.id)?t:{...t,band:(t.band-1) as 0|1|2});
  const breached=charges.filter(t=>t.band<0);
  charges=charges.filter(t=>t.band>=0);
  let hull=state.hull;
  const capacitors=[...state.capacitors] as [number,number,number];
  for(let lane=0;lane<3;lane++) {
    const positive=breached.filter(t=>t.lane===lane&&t.polarity==='POSITIVE').reduce((n,t)=>n+t.strength,0);
    const negative=breached.filter(t=>t.lane===lane&&t.polarity==='NEGATIVE').reduce((n,t)=>n+t.strength,0);
    capacitors[lane]=Math.min(3,capacitors[lane]!+Math.min(positive,negative));
    hull-=Math.abs(positive-negative);
  }
  const completedRound=state.completedRound+1;
  if(completedRound===9) {hull-=charges.reduce((n,t)=>n+t.strength,0);charges=[];}
  let outcome: CompletedState['outcome']=null;
  if(hull<=0) outcome='loss: breach';
  else if(completedRound===9) outcome=(Math.min(...capacitors)>=2&&capacitors.reduce((a,b)=>a+b,0)>=8)?'win':'loss: target';
  const arrivals=scenario.waves[state.completedRound]?.length??0;
  return {completedRound,hull,capacitors,coolant,charges:charges.sort((a,b)=>a.id-b.id),nextTokenId:state.nextTokenId+arrivals,outcome};
}
