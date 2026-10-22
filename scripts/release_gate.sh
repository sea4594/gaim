#!/usr/bin/env bash
# The complete Phase 6 gate; strict, offline and no third-party dependencies.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! python3 -c 'import sys; sys.exit(sys.version_info < (3,10))' >/dev/null 2>&1; then
  for d in /opt/homebrew/opt/python@3.11/libexec/bin /usr/local/opt/python@3.11/libexec/bin; do
    if [[ -x "$d/python3" ]]; then
      export PATH="$d:$PATH"
      break
    fi
  done
fi
command -v python3 >/dev/null || { echo 'Python 3 required' >&2; exit 1; }
python3 - <<'PY'
import sys
assert sys.version_info >= (3, 10), 'GAIM Phase 6 requires Python >=3.10'
print('Python',sys.version.split()[0])
PY
python3 -m compileall -q reference phase6 scripts tests
python3 reference/tests_v01.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/generate_phase6_artifacts.py --check
bash -n scripts/release_gate.sh
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --check
  git diff --cached --check
fi
printf '\nPHASE 6 RELEASE GATE PASSED\n'
