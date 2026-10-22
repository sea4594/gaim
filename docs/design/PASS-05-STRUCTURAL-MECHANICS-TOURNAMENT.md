# GAIM Mechanical Discovery — Pass 05: Timing, Forecast Drafting, Mission Design

**Status:** experimental only. **Selected research challenger:** Charge Loom with Delayed Bridge + Flip + Accelerate. **Production remains v0.1, unchanged.**

## Executive decision

Pass 05 tried changing *what players control*, not just granting stronger buttons. A timed intervention that lets a charge descend **two bands instead of one** is the strongest new addition for another research pass. Its most important feature isn't that it increases solver success: it creates verifiable *correct-time versus wrong-time* dilemmas that complement HOLD, rather than replacing it.

The two-offer Storm Draft has a potentially stronger long-term identity, especially for multiplayer, but requires a planner that evaluates future waves under *only publicly visible information*. The simple bot didn't learn to exercise the choice. Keep the draft as a **separate rival**, not as part of the recommended next ruleset. Variable missions showed promise as content architecture but their thresholds require balancing. Passive reactor Heat penalized productive play and failed this pass.

## What we actually implemented

Each of the following lives in `experiments/phase05_lab.py` as an immutable, opt-in variant around the Phase 04 research core; none affects `src/engine.ts` or `server/http.mjs`.

### 1. Accelerate — action timing / fast-vs-slow power

- **Action:** `('accelerate', token_id)`. One shared edit.
- **Eligibility:** charge is in FAR (row 2) or SOON (row 1); it cannot already have another edit that round.
- **Effect:** it moves one additional row toward breach *before* the usual automatic one-row advance. From FAR it ends at NOW; from SOON it breaches this round.
- **Cost:** consumes one of four shared edits, no coolant or power. The cost is opportunity and arriving prematurely, rather than a second resource.
- **Potential:** synchronize a future charge with an imminent opposite-polarity charge; alternatively, accidentally breach ahead of a planned countercharge.
- **Relationship to HOLD:** HOLD delays a token and increases its magnitude. Accelerate rushes a token without increasing magnitude. They have **opposing consequences**, not just different prices.

**Verified favorable witness:** Round 9, Center has +1 in SOON and −1 in NOW, hull 1, capacitors 3/2/3. Doing nothing causes breach death; Accelerate +1 causes a simultaneous cancellation and wins with hull 1 and capacitors 3/3/3.

**Verified unfavorable witness:** Round 7, same lane has +2 and −2 both in SOON, hull 3, capacitors 3/3/3. Letting them travel together cancels safely next round; Accelerating only +2 causes two separate breaches over two rounds and hull death. See `tests/test_phase05_lab.py`.

**Unresolved:** more flexible actions can trivially improve win rates by lowering difficulty. Test future-aware bots, action usefulness and human comprehensibility before promotion.

### 2. Storm Draft — limited public forecasting / tactical deck draft

- For the seven active-wave rounds, display two public wave offers; choose **exactly one** to arrive now. The other remains offered next round, joined by the next face-up wave card.
- The choice is a **mandatory planning decision that does not consume one of the four edits**. When no choice is specified, the reference experiment defaults to the older wave; real UI would require an explicit choice.
- Both wave offers list every token's lane, sign and strength. The unseen deck is NOT visible to the player; only its fixed seeded contents are known internally for deterministic replay.
- Only seven waves total. Each one is chosen exactly once; final two rounds remain cleanup. Not taking a storm now does **not** erase it.
- This is a change to the turn structure, not an extra stronger combat action.

**Exact branch witness:** A starting +1 charge in Center FAR and visible offers [Center −1, Left +1] requires choosing the Center −1 first for a match. Choosing Left +1 instead leaves the Center pair unsynchronized and fails the mission. No extra resources were created. Oldest-first drafting reproduces the original fixed wave order exactly for all tested seeds.

**Failure of the current evaluation:** In the development set, the one-round greedy policy chose the newer wave **0 times**. Incoming waves arrive in FAR and don't breach until later, so a one-step evaluator sees no immediate reason to reorder them. A zero-value result here is a **planner limitation**, not evidence that draft choice lacks strategic potential.

**Next experiment required:** compare public-information 3-turn planning against a clairvoyant oracle and against the original fixed-wave generator; only retain the draft if ordinary players can anticipate enough consequences without exhaustive calculation. Also test whether an additional obligatory choice each round actually improves 4-player participation or merely slows everyone down.

### 3. Reactor Heat — throughput penalty

- If any lane matches strength ≥2 this round, heat increases by one.
- On reaching two heat, venting deals **two hull damage** and resets heat to zero.
- Heat does not generate useful resources; there is no extra player action to manipulate it.

**Decision:** reject as designed. It is a punitive upkeep track that complicates otherwise desirable matches, without producing a sufficiently distinctive compensating benefit. The one-step policy fell sharply. A voluntary *push-your-luck* reactor with a reward might be worth a later clean-sheet experiment, but that is a different rule, not a tweak to keep now.

### 4. Public mission cards — varied victory requirements

Four executable mission contracts use the SAME board and collision rules:

| Public mission | Exact win requirements (plus surviving round 9) |
|---|---|
| Standard | Every capacitor ≥2 and total ≥8 |
| Shield | Every capacitor ≥2, total ≥7, hull ≥4 |
| Choreography | Every capacitor ≥2, total ≥7, and at least one round with matches in ≥2 lanes |
| Voltage | Every capacitor ≥1, total ≥7, and strength-2+ matches in at least two **different** lanes at some point |

Missions are public at round one. Choreography and Voltage are tracked by the pure research game state and tested with exact final-round fixtures.

**Decision:** keep as a **scenario-content test**. The goals change what a team values, but today's thresholds have different inherent difficulty and the benchmark policy is not sufficiently mission-aware. The data must not be read as a balanced mission mode roster.

### 5. Rule pruning — an attempt to *reduce* complexity

We also tested Accelerate while removing each of DAMP, HOLD or FLIP. This is important: a new action should earn a place in the game rather than merely adding another button.

- Without HOLD, many important future amplification routes disappear. The paired benchmark fell substantially.
- Without DAMP, dangerous leaks become harder to manage, particularly with only seven starting hull.
- Without FLIP, the bot won slightly more development games but survived fewer; removed is a major economic tradeoff, and the effect reversed on holdout. **Don't read higher wins as a design win.**

## Paired complete-session evidence

Same exact seeds, same **myopic one-round greedy policy**; it can consider each permitted edit but undervalues delayed Bridge investments and offered waves. These are automated feasibility probes, NOT statements of player satisfaction or optimal play.

| Rules | Development wins (64) | Independent holdout wins (32) | Dev survivals (64) | Holdout survivals (32) |
|---|---:|---:|---:|---:|
| Bridge + Flip control | 23 | 9 | 38 | 15 |
| + Storm Draft | 23 | 9 | 38 | 15 |
| + Accelerate | **34** | **17** | **52** | **21** |
| + Storm Draft + Accelerate | 34 | 17 | 52 | 21 |
| + Reactor Heat | 8 | 4 | 15 | 5 |
| + Accelerate, remove DAMP | 25 | 16 | 38 | 18 |
| + Accelerate, remove HOLD | 15 | 8 | 48 | 21 |
| + Accelerate, remove FLIP | 36 | 15 | 43 | 17 |

**No causal claim about fun:** Adding an optional action can only broaden the legal action set. An improved greedy win rate may mean the rules are less punishing, not that decision quality improved. The core success criterion for Accelerate is that the same action has reproducible *good* and *bad* timing applications and interacts with existing HOLD/SHIFT constraints.

The synthetically generated one-edit final-round survey (1,000 states) had 53 solvable without Accelerate, 60 with. This is a constrained comparison of zero/one-edit plans, **not** exhaustive search over all four actions; terminal leakage also makes a late acceleration unusually safe to test. Its results should carry little weight in the final selection.

### Mission diagnostics (64 identical seeds)

| Mission | Greedy wins | Survivals | Caution |
|---|---:|---:|---|
| Standard | 23 | 38 | Original hard 8-power constraint |
| Shield | 11 | 39 | Easier energy target but tighter hull condition |
| Choreography | 26 | 37 | Explicit multi-lane round requirement |
| Voltage | 32 | 37 | Relaxed lane threshold; not directly comparable |

These are **not** balanced mission difficulty estimates and do not yet demonstrate strategy diversity.

## Provisional selection rubric

| Candidate | Distinct decision value | Rules burden | Robustness so far | Decision |
|---|---|---|---|---|
| Bridge + Flip (control) | Known economic risk and response | Five edits | Reference for comparison | Preserve unchanged in production |
| **Bridge + Flip + Accelerate** | Positive and negative timing reversals; pairs with HOLD | One simple verb | Improvements in dev and holdout | **Research winner** |
| Add Storm Draft | Big strategic promise, player authorship | One mandatory new phase | Planner fails to exercise it yet | Separate challenger |
| Add Reactor Heat | Larger matches punish team | New persistent track | Weak baseline and poor utility | Reject |
| Add Missions | Different incentive structures | A public goal card and stats | Content hypothesis only | Reserve for controlled tuning |
| Remove HOLD, DAMP or FLIP | Fewer rules | Simpler | Losses or degraded tradeoffs | Reject for now |

No variant has been shown to be 'best possible', or to offer endless replayability. The current strength of evidence supports **one candidate worth adversarial follow-up**, not a permanent rules freeze.

## Cooperation and replayability gate (still unsolved)

- All experiments retain four *interchangeable* shared edits and full common knowledge. None proves that four people independently have worthwhile decisions. That is still a **critical open failure** of the co-op-first mission.
- Ordinary seeded waves are not fairness-verified under partial knowledge. Storm Draft could improve agency but could also create analysis paralysis.
- Bridge remains mostly unused by the one-turn greedy policy. Test a rollout planner that understands its delayed payoff before claiming the combined economy is deep.
- Test mission variety with **solution-policy diversity**, not simply different win thresholds.
- Investigate diminishing returns from `Accelerate` to ensure it doesn't trivialize the hard endgame.

## Reproducing the research

```bash
python3 -m unittest tests.test_phase05_lab -v
python3 -m experiments.phase05_survey --games 64 --finales 1000
bash scripts/release_gate.sh
```

Detailed raw counts, seed ranges, policy caveats and synthetic final-round examples are stored in `docs/design/pass05-results.json`. The system under test is a **Python mechanics laboratory**. No changes to the production TypeScript engine, networking, or live rooms have been authorized in this pass.

### Outside mechanical reference

The idea of fast and slow powers interacting with predictable forthcoming threats is established in games like *Spirit Island* (https://boardgamegeek.com/boardgame/162886/spirit-island). Here we are borrowing a broad family of mechanics rather than its rules or IP. Charge Loom's timing tradeoff arises from collision and amplification, not an ability card system.
