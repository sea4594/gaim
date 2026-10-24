# GAIM Pages deployment: an explicit publishing contract

The static replay viewer is **already** present in the repo root (`index.html`, `site/`).
On October 24, 2026 the live URL still rendered the Phase 6 README even while
`index.html` was present on `main`. Merely pushing an index file was therefore
not sufficient to demonstrate a deployed update.

The `.github/workflows/deploy-pages.yml` workflow runs the full release gate,
packages *only* four whitelisted read-only assets plus `.nojekyll` and a
`build-info.json` stamp, and uses GitHub's Pages artifact deployment action.
No runtime server is needed and no research or backend source is published.

## One-time Pages configuration

Visit **GitHub repository → Settings → Pages → Build and deployment** and set
**Source** to **GitHub Actions**. Without this one-time repository setting, a
workflow may fail even if its YAML and game tests are correct. Then visit
**Actions → Deploy verified GAIM preview → Run workflow** on `main` if a
new push has not already triggered it. The green workflow **Deploy verified
preview** step establishes a successful deployment. The live page should show
`Pages artifact: Pass 17 · <short commit> · static replay` underneath its intro.

If the workflow fails, inspect its specific run. If the public site still shows
the Phase 6 README, it is not rendering the new Actions artifact; a browser
refresh alone cannot fix a source/deployment mismatch. Once deployed, use
https://sea4594.github.io/gaim/?v=pass17 to bypass cached navigation.

## Intentional constraints

- Verified v0.1 replay only; this is not a playable game or v0.5 simulation.
- 1–4-player headless room/server remains independent of the site.
- Static assets have no external dependencies or secrets.
- Replacing the site later does not affect core mechanics.
