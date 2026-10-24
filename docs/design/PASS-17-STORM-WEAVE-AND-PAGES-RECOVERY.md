# GAIM Mechanics Pass 17 — Storm Weave vs Forecast Market; Pages publishing recovery

**Decision: no mechanics promotion.** Forecast Market v0.5 remains the leading
research candidate; production v0.1 reducer and multiplayer server stay fixed.

## Why this investigation

Private forecast facts did not reliably change decisions in Pass 15. A new
storm-assembly proposal offers something more concrete than secrecy for its
own sake: different teammates could influence where the storm travels and what
charge it carries. But co-authorship is not proved by partitioning two menus.

## Executable candidate: Storm Weave

Two public two-token storm offers have equal numbers of charge tokens. Players
may exchange the *signed-strength payloads* assigned to their lane routes.
The resulting two cards preserve **all four payloads, all four routes, and the
number of offered waves**. Neither storm disappears. The two offers remain
available; one is drafted now, the other remains available next round under
normal Forecast Market rules. A weave costs **one coolant** up front.

Example:
- Offer A routes `[L, C]`, payloads `[+2, -1]`.
- Offer B routes `[R, L]`, payloads `[-2, +1]`.
- After weave: A is `L -2, C +1`; B is `R +2, L -1`.

This is a meaningful alternative to acquiring more action verbs. Storm composition
may change what's valuable both now and later. However it requires learning a
new two-card interchange rule, and players could still defer all choices to one
expert.

## Paired research

The Python experiment starts from existing seeded boards after two rounds,
replaces only the two visible offered storms with synthetic same-length cards,
and compares the best plan found with and without a coolant-priced weave.
It tests two offer choices and the same first 10 legal initial edits, then
passes for the remaining three rounds. Outcome = a pre-existing short-horizon
heuristic. It is **not** an optimal solver, multiplayer simulation, or real
human win rate. Unlike some earlier design surveys, we account for the coolant
purchase itself.

| Four-round horizon | Unchanged better | Weave better | Tied |
|---|---:|---:|---:|
| 32 development boards | 4 | 1 | 27 |
| 32 holdout boards | 12 | 3 | 17 |

At three-round horizon, weave was worse in 19/32 development and 20/32 holdout
positions, better in 3/32 and 5/32 respectively. This is not a clear benefit.
A few catastrophic heuristic outcomes distort mean score, so we prioritize
paired better/worse/tie counts instead of interpreting means as a quality score.

## Rejected or deferred directions

- **Private component ownership:** one player knows routes, another knows
  signed payloads. Does not fix quarterbacking under voice chat; using it here
  would hide information rarely needed in these tactical positions.
- **Free weave:** predictably adds flexibility with no price, but that's not
  a demonstration of strategic improvement.
- **Weave plus existing Storm Market plus six verbs:** too much choice and
  instructional burden for the measured benefit.

A different future candidate worth testing is *team-authored delayed promises*
with independently valuable options and a meaningful commitment cost. Such a
system must be compared to equally costly open-information plans and eventually
played by real human pairs; otherwise it is just procedural theater.

## Pages diagnosis and remedy

The GitHub repository's root `index.html` contained the Phase 16 replay viewer,
but `https://sea4594.github.io/gaim/` still served Phase 6 README content on
October 24, 2026. A commit of HTML does not prove that Pages deployed it.
This pass installs an explicit `deploy-pages.yml`, checks the full release gate,
whitelists the static preview artifact, and stamps it with the source commit ID.
GitHub **Settings → Pages → Build and deployment → Source: GitHub Actions** is
the one-time prerequisite outside a local hotfix. See `docs/PAGES-DEPLOYMENT.md`.

## Verification

- Reference rules and Phase 6 golden traces unchanged.
- New tests: exact conservation, legal transforms, price, reproducibility;
  Pages artifact isolation and marker validation.
- Production TypeScript and online rooms remain separate from the static site.
- New public artifact contains only index, CSS, replay JS, golden JSON, a
  `.nojekyll` file, and its revision marker.

**Result:** archive Storm Weave as rejected in present form; do not modify the
shipping game or the provisional leading Forecast Market rules.
