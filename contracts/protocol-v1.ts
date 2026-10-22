/** GAIM Phase 6 DESIGN CONTRACT ONLY. No production TypeScript server exists yet.
 * These types describe JSON. The Phase 7 server MUST runtime-validate inputs.
 * Never trust seat IDs, room IDs, or readiness asserted by an unauthenticated client.
 */
export type Polarity = "POSITIVE" | "NEGATIVE";
export type Lane = 0 | 1 | 2;
export type Band = 0 | 1 | 2;
export type Seat = 0 | 1 | 2 | 3;
export type Slot = 0 | 1 | 2 | 3;
export type Ruleset = "charge-loom/v0.1";

export interface ChargeView {
  id: number;
  lane: Lane;
  band: Band;
  polarity: Polarity;
  strength: 1 | 2 | 3;
  alreadyHeld: boolean;
}
export interface WaveCharge {
  lane: Lane;
  polarity: Polarity;
  strength: 1 | 2;
}
export interface EngineView {
  protocolVersion: 1;
  ruleset: Ruleset;
  completedRound: number; // 0..9, last round actually resolved
  planningRound: number | null; // next round, 1..9; null if ended
  hull: number; // can be <=0 on a breach loss; do not clamp
  capacitors: [number, number, number]; // 0..3
  coolant: number; // 0..3
  charges: ChargeView[]; // includes already-spawned upcoming-round arrivals
  nextWave: WaveCharge[]; // only one lookahead; NO token ids or seed
  slotOwners: Seat[]; // length 4 if planning; otherwise empty
  outcome: null | "win" | "loss: breach" | "loss: target";
}

export type GameEdit =
  | { kind: "SHIFT"; tokenId: number; direction: -1 | 1 }
  | { kind: "HOLD"; tokenId: number }
  | { kind: "DAMP"; tokenId: number };

export interface Draft {
  slot: Slot;
  seat: Seat; // server-assigned, never accepted from client as authority
  action: GameEdit;
}
export interface RoomSnapshot {
  roomId: string;
  revision: number; // increment for accepted room mutation
  phase: "lobby" | "planning" | "finished";
  seats: Array<{ seat: Seat; connected: boolean; ready: boolean }>;
  deadlineAt: string | null; // UTC ISO 8601; operational timer, NOT gameplay RNG
  proposals: Draft[];
  game: EngineView | null; // null while in lobby
}

/** Incoming wire messages all require a unique requestId. Session seat is
 * established from the secure room-issued resume secret at connection time.
 */
export type ClientMessage =
  | { type: "CREATE_ROOM"; requestId: string; ruleset: Ruleset; scenarioId: string }
  | { type: "JOIN_ROOM"; requestId: string; roomCode: string; resumeSecret?: string }
  | { type: "START_GAME"; requestId: string; roomId: string; expectedRevision: number }
  | { type: "SET_EDIT"; requestId: string; roomId: string; expectedRevision: number; slot: Slot; action: GameEdit | null }
  | { type: "SET_READY"; requestId: string; roomId: string; expectedRevision: number; ready: boolean }
  | { type: "GET_SNAPSHOT"; requestId: string; roomId: string };

export type ServerMessage =
  | { type: "ACK"; requestId: string; revision: number }
  | { type: "REJECT"; requestId: string; code: string; revision: number }
  | { type: "ROOM_SNAPSHOT"; snapshot: RoomSnapshot }
  | { type: "ROUND_RESOLVED"; roomId: string; revision: number; completedRound: number; outcome: EngineView["outcome"] };
