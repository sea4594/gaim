# Phase 7 — Headless TypeScript engine and online cooperative rooms

**Status:** Implemented prototype, not deployed, no graphical UI. **Ruleset:** `charge-loom/v0.1` (unchanged). **Protocol:** Phase 6-compatible semantics transported by JSON/HTTP and authenticated SSE.

## Components

- `src/engine.ts`: pure reducer, planning projection, atomic validation, exact Python golden-trace parity for seven verified scenarios (70 state views).
- `src/rooms.ts`: in-memory authoritative 1–4-seat room lifecycle, drafts, readiness, fixed four-slot assignment, revision compare-and-swap, per-seat request-id idempotency, disconnect/reconnect, one deadline-driven resolution transaction per round.
- `server/http.mjs`: live HTTP POST endpoint (`/api`), SSE (`/events?roomId=...`) for low-latency live snapshots, `/health`; 32 KiB request cap, rate limit, bearer authorization, random 192-bit resume tokens (SHA-256 hashes stored in room memory), no shared secrets in broadcast snapshots.
- `server/client.mjs`: JSON terminal commands for create, join, resume, start, edit, clear, ready, snapshot, and watch.
- `tests-node/`: exact cross-language conformance, negative cases, multiplayer and HTTP/SSE integration, full 9-round replays for every player count.

**Why SSE instead of WebSocket?** Gameplay actions are tiny, discrete POST messages and require authorization, revision conflict handling, and idempotency. SSE publishes every state mutation immediately. This accomplishes networked real-time cooperative planning without adding a third-party WebSocket dependency. A portrait browser UI could use `fetch()` streaming. No polished UI is implemented.

## Local operation

Requires Python >=3.10 and Node >=20. TypeScript compiler is included as a pinned vendored tarball; no npm network needed.

```bash
bash scripts/release_gate.sh
npm run server
# in another terminal:
node server/client.mjs create verified-3
node server/client.mjs join EIGHTCHR
node server/client.mjs snapshot ROOM_ID RESUME_SECRET
node server/client.mjs ready ROOM_ID RESUME_SECRET true
node server/client.mjs start ROOM_ID HOST_RESUME_SECRET
node server/client.mjs edit ROOM_ID RESUME_SECRET 0 '{"kind":"HOLD","tokenId":1}'
node server/client.mjs clear ROOM_ID RESUME_SECRET 0
node server/client.mjs watch ROOM_ID RESUME_SECRET
```

Starting requires every lobby participant ready. Every planning round has 75 seconds by default; all players ready locks sooner. `watch` connects to an authenticated SSE stream; actions are HTTP POSTs. `resume` with the original secret rebinds the same seat. Each accepted mutation advances `revision`, so concurrent editors must refresh and retry with a **new request ID** after `STALE_REVISION`.

Example endpoint request with authentication: `POST /api` `Authorization: Bearer <resumeSecret>` JSON `{"type":"SET_EDIT","roomId":"...","requestId":"unique_12345","expectedRevision":9,"slot":0,"action":{"kind":"SHIFT","tokenId":1,"direction":1}}`. Tokens are **private bearer credentials**: never paste publicly or add to source control.

## Verification and safeguards

`bash scripts/release_gate.sh` retains every Phase 5/6 Python test and artifact regeneration check, then builds TypeScript and runs Node tests. It fails closed on missing requirements and on regression. GitHub Actions runs the same gate on Node 22 and Python 3.11. The TypeScript compiler tarball is locally vendored and SHA-512 locked in `package-lock.json`, making the build repeatable offline.

The room reducer and idempotency cache run synchronously on the Node event loop. Deadline and all-ready resolution therefore cannot execute concurrently within one server process. Invalid replacements are rolled back atomically. Clients cannot send authoritative state or spoof a seat number; secrets authorize the actual seat. The client does not see the Python seed or hidden future waves.

## Honest limitations / Phase 8 priorities

- **No deployment or internet-accessible instance yet.** Default bind is localhost. Public exposure requires HTTPS/TLS termination (`GAIM_TLS_TERMINATED=1`) and a proxy with rate limits, origin policy and monitoring. Do not expose the prototype directly to the internet.
- **In-memory only.** Restart loses rooms, credentials, and games. No horizontal scaling or durable event store; basic request-id caching is for a room lifetime, not across crashes.
- **No polished mobile UI, account system, matchmaking, telemetry, or voice integration.** CLI/SSE tests confirm remote protocol behavior only; no human co-op usability or latency tests yet.
- **Some engagement problems remain.** Four edit slots are often underused, and quarterbacking has not been addressed. 3 sessions per player count with people remain an explicit acceptance prerequisite.
- **Scenario bank is selective** (seven independently verified winning witness paths), not a guarantee of easy, fair, or enjoyable gameplay. More scenario diversity and strategic difficulty evaluation are Phase 8 tasks.

## Version compatibility

Source-of-truth game mechanics remain `reference/charge_loom_v01.py` plus the fixed Phase 6 JSON traces. Changing them needs a documented ruleset version and new conformance traces. `RoomStore` is operational scaffolding, not a modification of the frozen gameplay engine.
