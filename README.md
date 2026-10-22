# GAIM — Charge Loom (Phase 6)

GAIM is an experimental **1–4-player portrait-mobile cooperative strategy game**. Charge Loom is the selected *provisional* v0.1 design. **Phase 6 formalizes the rules and multiplayer contract; there is no deployed online game or graphical UI yet.**

## This checkpoint

- **Canonical v0.1 mechanics:** `reference/charge_loom_v01.py` and `docs/design/PHASE-05-DECISION-AND-V01-RULES.md` (unaltered from Phase 5).
- **Exact game-engine implementation specification:** `docs/architecture/PHASE-06-ENGINE-CONTRACT.md`.
- **Online room and cooperative action design:** `docs/architecture/PHASE-06-COOP-ROOM-AND-ACCEPTANCE.md`.
- **Typed message contract:** `contracts/protocol-v1.ts` (declarations only; no production server).
- **Verified scenario content:** `contracts/scenarios.v0.1.json` (seven explicit, reproducible wave schedules).
- **Golden traces:** `contracts/golden-traces.v0.1.json` (all rounds and state views for the seven verified wins).
- **Executable boundary validator:** `phase6/contract.py` (joint action and slot ownership contract, not a network room implementation).
- **Full release gate:** `scripts/release_gate.sh`.

### Run the release gate locally

Requires Python **3.10+**; all steps are offline and use only the standard library.

```bash
bash scripts/release_gate.sh
```

It checks the original eight Phase 5 tests, new Phase 6 contract tests, all seven witness replays, generated content integrity, syntax, and whitespace. It is also the gate required by the hotfix installer before committing and pushing to `main`.

### Try the authoritative prototype (terminal)

```bash
python3 reference/play_cli_v01.py --seed 3
```

The original Python CLI can run arbitrary research seeds; only the seven scenarios `3, 8, 10, 14, 15, 17, 18` are currently witness-verified. Verified **does not mean balanced or human-fun**.

### Regenerate v0.1 parity artifacts after an intentional, reviewed rules change

```bash
python3 scripts/generate_phase6_artifacts.py
bash scripts/release_gate.sh
```

Golden artifacts are intentionally checked into the repository so the future TypeScript engine has a stable independent target. **Do not regenerate to hide a regression.** Modify the ruleset ID and scenario IDs if gameplay changes intentionally.

## Remaining work

- **Phase 7:** TypeScript game reducer, full cross-language parity, authoritative online co-op rooms, headless client, tests.
- **Phase 8:** simulations, fairness analysis, human cooperative playtests, strategy diversity, fix actual design weaknesses.
- **Phase 9:** final mechanical and implementation review, documentation, handoff.

### Primary open risk

Four-player participation is **not validated**. Across 63 winning-witness rounds, only 13 used four actions. The four-slot seat rotation is a testable hypothesis, not a proven solution to the inactive-player or quarterbacking problem. If human testing fails, revise the design rather than making cosmetic additions.
