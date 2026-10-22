# Phase 6 — Online cooperation, room protocol, and acceptance criteria

**Status:** PROVISIONAL multiplayer **contract**, not an implemented server. **Primary risk:** 4-player engagement.  
**Target:** 1–4 players in a portrait-smartphone browser, headless server first. Game logic must be identical regardless of player count.

## 1. Separate three kinds of state

1. **GameState — authoritative, deterministic.** Completed rounds, hull, power, coolant, active charge IDs, next ID, scenario content, terminal outcome. Only the game reducer may change it. `GameState` has no user ID, network state, or countdown.
2. **PlanningState — mutable drafts for one next round.** Seat ownership of four editing slots, per-slot proposals, ready flags, revision and deadline. The room server owns and validates it. It does **not** move charges or spend coolant until the round locks.
3. **RoomState — networking and membership.** Room ID, room code, seat mapping, resume secrets (server-only), host seat, connected flags, member join/leave, and lobby/playing/finished status. Secrets are never in snapshots or event logs.

The authoritative transition is:

`completed state -> spawn-projected planning view -> legal per-seat edits -> lock joint plan -> exactly one reducer call -> completed state -> repeat`.

`CompletedRound` and `PlanningRound` must never be confused. A planning view includes this round's already spawned and editable tokens, but stored `GameState` is still the previous completed round.

## 2. Cooperative authorship v0.1 — exactly four shared slots

**Chosen for Phase 7 prototype, explicitly NOT validated for engagement:** There are always four optional edit slots. The actions are NOT four per player. Every slot may be blank (PASS). Seats are stable indices assigned in join order at game start, 0..N-1. The eligible owner of slot index `j` on planning round `r` with `N` active seats is `(r - 1 + j) mod N`.

| Players | Round 1: owners of slots 0,1,2,3 | Round 2 | Rationale |
|---|---|---|---|
| 1 | `0,0,0,0` | same | Solo can plan all four independent edits, no extra characters |
| 2 | `0,1,0,1` | `1,0,1,0` | Two edits per person; total options unchanged |
| 3 | `0,1,2,0` | `1,2,0,1` | Extra edit rotates between teammates |
| 4 | `0,1,2,3` | same | Each player owns one optional slot |

The rule retains **exactly the same possible joint action sets** for 1–4 participants: slot ownership changes authorship, not the engine's action budget. This is essential for same-seed fairness comparisons. If a four-player game feels passive, changing these ownership rules is a design revision, NOT something to cover up with extra unneeded verbs.

**Shared planning, not hidden individual commands:** all pending legal drafts are visible to all teammates, along with ready state; players may discuss. A player can edit/clear only their owned slots. The server authenticates a connection to a seat using its issued secret; it does not trust a seat number in a message. When the owning player marks READY, their slots are frozen until a subsequent `SET_READY(false)` arrives **before** the round locks. There is no separate player-specific inventory or unit.

**Atomic conflict rules:** one edit per token per round. Each incoming `SET_EDIT` is tentatively applied to its assigned slot, then the server validates the **entire** combined draft plan against the post-spawn board. If two players target the same token, the later arriving request is rejected with `TOKEN_ALREADY_PLANNED` and no state change. If the proposed edits would overspend coolant, reject as a unit with `INSUFFICIENT_COOLANT`. No draft can target next round's preview. The server serializes requests and applies each mutation transactionally. The first accepted draft for a token keeps that claim until cleared; don't silently override a teammate.

All valid joint plans commute across different tokens under the frozen rules; the server resolves them in increasing slot order for stable logs. Conflicting plans never partially resolve, so ordering does not change the result of an accepted plan.

## 3. Lifecycle — one concrete prototype policy

**Lobby**: `CREATE_ROOM(scenarioId)` selects one of seven witness-verified scenarios; creates an unguessable room ID, short invite code, and a securely random host resume secret. `JOIN_ROOM` adds up to four seats. Existing occupied seats are never reassigned mid-match. Host may `START_GAME` only after all occupants are marked ready and at least one player is present. Seat count is fixed for the nine-round game. It may change only by starting a new game, not when sockets drop.

**Planning**: server sends a `ROOM_SNAPSHOT` including post-arrival charges, the **next** wave preview, current shared draft actions, four slot owners, and ready status. A 75-second round planning deadline is a *provisional operational default*, not a gameplay balancing decision. The server resolves when every occupied seat is ready or the deadline passes, whichever occurs first. Missing or disconnected seats contribute PASS for their empty slots; accepted drafts remain even after disconnection. Do not pause the authoritative clock on one player's disconnection. Send a brief result and open the next round. The full nine rounds should normally be quick, but no game-duration guarantee is asserted.

**Result**: exactly one `ROUND_RESOLVED` event followed by authoritative snapshot per round. If the reducer returns a win or loss, phase becomes `finished` and all future edits are rejected. A completed room can be viewed/replayed but not continued or silently reset.

**Reconnection**: returning user presents the original room resume secret over a secure connection. Server binds to the previously assigned seat, invalidates any older simultaneous socket for that seat, returns complete current snapshot (not only missed deltas). Reconnect must never rerun a round or allocate a new seat. An unoccupied seat's token must not be guessable from the invite code. Initial prototype may store rooms in memory; **server process restarts would then end active sessions** and must be documented to players, not quietly represented as robust persistence.

**Timers**: server time is authoritative. Deadline is persisted as an absolute UTC timestamp within room state; use monotonic timing when actively waiting, and compare UTC on recovery. Exactly one server-side round-lock transaction may win, whether triggered by all-ready, deadline, or concurrent clients.

## 4. Wire protocol v1

The type-only schema is `contracts/protocol-v1.ts`. Each incoming request contains a unique `requestId`. State-changing requests also contain `expectedRevision`. A reply is ACK or REJECT with the current revision. Broadcast full `ROOM_SNAPSHOT` on accepted state changes and reconnect; `ROUND_RESOLVED` may accompany a snapshot but is never itself sufficient to reconstruct state.

| Client message | Required effect |
|---|---|
| `CREATE_ROOM` | Create a new lobby tied to a verified scenario ID; return room ID, invite code, and private resume token directly to creator only |
| `JOIN_ROOM` | Join unoccupied lobby seat or resume an existing seat using its secret; no joining as an additional player after start |
| `START_GAME` | Host only, all joined players lobby-ready, lock player count and scenario; begin round 1 projection |
| `SET_EDIT` | Authenticated seat owns slot, not ready, revision current; null clears an owned slot; validate replacement and the whole plan atomically |
| `SET_READY` | Toggle ready only before lock; once every player ready, atomically resolve round; lobby readiness is tracked separately |
| `GET_SNAPSHOT` | Return current authoritative room snapshot; this command is read-only |

**Idempotency:** A `(roomId, authenticatedSeat, requestId)` can change the room at most once. Replaying the same request with identical payload returns the cached response. Reusing a request ID with different payload returns `IDEMPOTENCY_CONFLICT`. The cache should cover the room's lifetime, or record durable request IDs if persistence is added. Clients must not generate a new request ID when retrying the same action.

**Revision checks:** Every accepted room mutation increments `revision`. A stale expected revision returns `STALE_REVISION` plus a current snapshot; no mutation occurs. Clients retry by inspecting the new board, not automatically replaying potentially dangerous edits. `GET_SNAPSHOT` does not increment revision. Simultaneous ready/timeouts must use a single lock or transaction.

**Error codes:** `BAD_PAYLOAD`, `UNAUTHORIZED`, `ROOM_FULL`, `GAME_ALREADY_STARTED`, `NOT_OWNER`, `ALREADY_READY`, `STALE_REVISION`, `TOKEN_ALREADY_PLANNED`, `INSUFFICIENT_COOLANT`, `ILLEGAL_EDIT`, `IDEMPOTENCY_CONFLICT`, `GAME_FINISHED`, `UNSUPPORTED_RULESET`, `UNKNOWN_SCENARIO`.

### Example authored draft

```json
{"slot":0,"seat":0,"action":{"kind":"SHIFT","tokenId":2,"direction":1}}
```

`seat` in a returned draft is derived by the **server**; clients send only `slot` plus `action`. A client cannot grant itself another player's seat by spoofing request JSON.

### Security and reliability baseline

- TLS (`wss://`) outside localhost; validate Origin, payload size, frame size and message frequency; reject unknown fields.
- Use cryptographically secure, ≥128-bit random resume secrets; hash tokens at rest if persisted; never log or broadcast secrets.
- Invite codes are not authorization to take over an existing seat.
- Validate all requests at the server, including room phase, seat ownership, token IDs, and coolant budget. No client-supplied game state, hull or scenario override.
- Serial, authoritative round resolution: each round emits one event with an incremented room revision. Reject any attempts to resolve an already completed round.
- For a first deploy, use in-memory rooms if necessary, but be candid about data loss on restart. Durable storage and scaling can be added only once mechanics are validated.

## 5. Evidence-based engagement gate (currently UNSATISFIED)

A winning bot trace is not a human-session usability or cooperation test. The Phase 5 witness bank contains 63 rounds: **7 rounds with 0 edits, 7 with 1, 17 with 2, 19 with 3, 13 with 4** (mean 2.38). Thus **50/63 rounds did not require all four slots** in those selected solutions. We must not hide that fact behind decorative per-player gestures.

Before treating the four-player room model as final, run at least **three sessions per player count (1,2,3,4)** with actual people, chosen from the same witness-verified scenario pool. Record:

- Edits proposed and applied **per person** and per round; voluntary passes.
- Meaningful joint action dependencies, including who originated a non-obvious idea.
- Whether any person directs the whole team, and whether an individual can influence a decision before it locks.
- Wins/losses, understood reasons for failure, game length, time spent waiting.
- Whether solo works without pretending to control multiple character classes.

**Provisional review thresholds (not claims of current success):** each player reports at least two meaningful decisions in a nine-round game; in ≥75% of four-player rounds, at least three teammates actively contribute to planning; after one explanation, a majority of participants correctly predict 3/4 shown breach outcomes. These are not necessarily all engine edits: co-planning can count **only** if evidenced by observed communication, not a subjective assumption. If these thresholds fail, try shared collaborative proposals, round objectives, or revised slot authorship **and re-test** before shipping the network game.

Do not automatically increase the team's edit count with more players: that makes cooperation an unearned numerical advantage and complicates fairness. Do not add a fourth action simply to fill idle slots. If no viable authorship model makes the game engaging for four, reopen Phase 5 and pivot.

## 6. Phase 7 acceptance gate (technical)

Complete only when there is a real 1–4-player **server** that:

1. Executes the *exact* golden traces in `contracts/golden-traces.v0.1.json` using the same explicit scenario files, from TypeScript.
2. Enforces all quotas, duplicates, coolant limits, terminal lock, seed privacy, idempotency, and revision races.
3. Exposes create/join/ready/set-edit/snapshot/reconnect flows through a text/headless client.
4. Runs disconnect, timeout, simultaneous ready, malicious payload, and duplicate command tests.
5. Passes the Phase 6 release gate **plus** TypeScript and network tests.
6. Documents remaining human co-op engagement risks, without describing untested design goals as verified.

Phase 6 concludes with *design and executable contract validation*, not delivery of the server.
