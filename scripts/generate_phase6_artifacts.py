#!/usr/bin/env python3
"""Generate the v0.1 scenario content and parity snapshots from frozen Python.

Use --check in CI to catch drift; writes nothing in check mode.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference.charge_loom_v01 import start, step, wavebook
from phase6.contract import public_view

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "reference/verified-scenario-bank.json"
WAVES = ROOT / "contracts/scenarios.v0.1.json"
TRACES = ROOT / "contracts/golden-traces.v0.1.json"


def render() -> dict[Path, str]:
    bank = json.loads(BANK.read_text())
    scenarios = []
    all_traces = []
    for witness in bank["witnesses"]:
        seed = witness["seed"]
        waves = [
            [{"lane": lane, "polarity": sign, "strength": size} for lane, sign, size in wave]
            for wave in wavebook(seed)
        ]
        scenarios.append({"id": f"verified-{seed}", "seed": seed, "waves": waves})
        state = start(seed)
        snapshots = [public_view(state, 4)]
        for entry in witness["winning_trace"]:
            actions = [tuple(action) for action in entry["actions"]]
            state = step(state, actions)
            snapshots.append(public_view(state, 4))
        if state.over != "win":
            raise ValueError(f"Witness did not win: {seed}")
        all_traces.append({"scenarioId": f"verified-{seed}", "actions": [
            entry["actions"] for entry in witness["winning_trace"]
        ], "views": snapshots})
    return {
        WAVES: json.dumps({"ruleset": "charge-loom/v0.1", "source": "reference/charge_loom_v01.py", "scenarios": scenarios}, indent=2, sort_keys=True) + "\n",
        TRACES: json.dumps({"ruleset": "charge-loom/v0.1", "playerCount": 4, "traces": all_traces}, indent=2, sort_keys=True) + "\n",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, expected in render().items():
        if args.check:
            if not path.is_file() or path.read_text() != expected:
                raise SystemExit(f"OUT OF DATE: {path.relative_to(ROOT)}; rerun generator and review the diff")
            print(f"Verified {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected)
            print(f"Generated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
