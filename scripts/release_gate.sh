#!/usr/bin/env bash
# GAIM Phase 7 complete release gate. No tests may be skipped.
set -euo pipefail
cd "$(dirname "$0")/.."

# Avoid macOS' older /usr/bin/python3 shadowing Homebrew Python.
PYTHON="${GAIM_PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  for candidate in python3 python3.15 python3.14 python3.13 python3.12 python3.11 python3.10 \
    /opt/homebrew/bin/python3.11 /usr/local/bin/python3.11; do
    if command -v "$candidate" >/dev/null 2>&1 && \
      "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
      PYTHON="$candidate"; break
    fi
  done
fi
[[ -n "$PYTHON" ]] || { echo 'STOP: Requires Python 3.10+' >&2; exit 1; }
"$PYTHON" -c 'import sys; assert sys.version_info >= (3,10); print("Python",sys.version.split()[0])'

"$PYTHON" -m compileall -q reference phase6 scripts tests
"$PYTHON" reference/tests_v01.py
"$PYTHON" -m unittest discover -s tests -p 'test_*.py' -v
"$PYTHON" scripts/generate_phase6_artifacts.py --check

command -v node >/dev/null || { echo 'STOP: Requires Node.js 20+' >&2; exit 1; }
command -v npm >/dev/null || { echo 'STOP: Requires npm' >&2; exit 1; }
node -e 'if(+process.versions.node.split(".")[0]<20) process.exit(1)'
# Local vendored TypeScript 5.8.3 package; no npm registry dependency.
npm ci --offline --ignore-scripts --no-audit --no-fund
npm run build
npm run test:node
bash -n scripts/release_gate.sh
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
  git diff --cached --check
fi
printf '\nGAIM PHASE 7 FULL RELEASE GATE PASSED\n'
