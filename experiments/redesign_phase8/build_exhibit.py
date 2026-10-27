"""Generate a deterministic static, read-only scenario explorer for GitHub Pages."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .scenarios import PROFILES,STRATEGIES,run,summary

ROOT=Path(__file__).resolve().parents[2]
TARGET=ROOT/'site/strategy-lab-data.json'
SEEDS=[82000,82001,82002,82003,82004]


def build():
    audit=summary(n=40)
    examples={}
    for climate in PROFILES:
        examples[climate]={}
        for seed in SEEDS:
            examples[climate][str(seed)]={strategy:run(climate,seed,strategy,True) for strategy in STRATEGIES}
    return {'ruleset':'redesign/phase8-scenario-exhibit','type':'research-only/reducer-generated',
            'notice':'Automated public-current-wave heuristic policy replays, not playable online multiplayer or demonstrated optimal decisions. Every outcome was resolved by the Phase 3 Storm Engine reducer.',
            'climates':PROFILES,'strategies':STRATEGIES,'audit':audit,'examples':examples}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    raw=json.dumps(build(),sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n'
    if args.check:
        if not TARGET.exists() or TARGET.read_text()!=raw:
            raise SystemExit('Phase 8 exhibit file is stale. Regenerate intentionally.')
        print('Phase 8 exhibit matches exact reducer-generated data')
    else:
        TARGET.parent.mkdir(parents=True,exist_ok=True)
        TARGET.write_text(raw)
        print('Wrote',TARGET, len(raw),'bytes')

if __name__=='__main__':main()
