# Temporary verified replay viewer

Site entry point: `../index.html`. Assets: `style.css`, `replay.js`.

This is **not the production UI**. It is a light, no-build, no-backend portrait page using the committed, independently verified `../contracts/golden-traces.v0.1.json`. There is no new gameplay logic in the webpage; it just draws nine rounds of recorded states.

To preview locally, from the repository root run `python3 -m http.server 8080` and open `http://localhost:8080/`. The page needs HTTP, not `file://`, to fetch the JSON fixture.

To replace later, delete `index.html` and `site/` and use the eventual game's own frontend build. Do not regenerate golden traces to match webpage output: the trace is authoritative.
