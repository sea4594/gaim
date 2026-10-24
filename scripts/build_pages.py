"""Build an intentionally tiny static GAIM preview artifact for GitHub Pages.

Only audited, read-only files go public. Never publish research, server code,
private data or a network endpoint as part of the static preview.
"""
from __future__ import annotations
import argparse,json,os,shutil,subprocess,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ASSETS=("index.html", "site/style.css", "site/replay.js", "contracts/golden-traces.v0.1.json")
MARKER='gaim-pages/pass17'


def build(destination:Path):
    destination=destination.resolve()
    if destination==ROOT or ROOT in destination.parents and destination.parts[-1] in ('docs','site','contracts'):
        raise ValueError('refusing to overwrite source tree')
    data=json.loads((ROOT/ASSETS[-1]).read_text())
    if data.get('ruleset')!='charge-loom/v0.1' or len(data.get('traces',[]))!=7:
        raise ValueError('verified scenario contract changed unexpectedly')
    html=(ROOT/'index.html').read_text()
    js=(ROOT/'site/replay.js').read_text()
    if 'site/replay.js' not in html or 'site/style.css' not in html or 'contracts/golden-traces.v0.1.json' not in js:
        raise ValueError('preview asset references are inconsistent')
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('destination must be empty')
    for asset in ASSETS:
        target=destination/asset;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/asset,target)
    # GitHub Pages must not run Jekyll over the artifact.
    (destination/'.nojekyll').write_text('')
    sha=os.environ.get('GITHUB_SHA','')
    if not sha:
        result=subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=ROOT,capture_output=True,text=True)
        sha=result.stdout.strip() if result.returncode==0 else 'local-check'
    if not (sha=='local-check' or len(sha)>=7 and all(c in '0123456789abcdef' for c in sha.lower())):
        raise ValueError('invalid source commit identifier')
    info={'artifact':MARKER,'source_commit':sha,'replay_ruleset':data['ruleset'],
          'scenario_count':len(data['traces']),'playable':False}
    (destination/'build-info.json').write_text(json.dumps(info,sort_keys=True,indent=2)+'\n')
    return info


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='_site');parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:info=build(Path(tmp))
    else:info=build(Path(args.out))
    print('Verified Pages artifact:',json.dumps(info,sort_keys=True))

if __name__=='__main__':main()
