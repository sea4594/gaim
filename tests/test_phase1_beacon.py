"""Independent parity and release contracts for new Phase 1, not historical rules."""
import json
import random
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from experiments.phase1_beacon_engine import new_game, step
from scripts.build_pages import ROOT,build

DATA=json.loads((ROOT/'site/phase1-cases.json').read_text())

class Phase1BeaconTests(unittest.TestCase):
    def test_exact_python_replay_of_three_js_witnesses(self):
        self.assertEqual(DATA['ruleset'],'gaim/phase1-beacon-v2')
        self.assertEqual(len(DATA['games']),3)
        for case in DATA['games']:
            with self.subTest(case=case['id']):
                s=new_game(case['waves'])
                for rec in case['example']:
                    self.assertEqual(rec['before'],{k:s[k] for k in rec['before']})
                    old=deepcopy(s)
                    s=step(s,rec['plan'])
                    self.assertEqual(s,rec['after'])
                    self.assertNotEqual(s,old)
                self.assertEqual(s['finished'],'WIN')
                self.assertGreater(s['hull'],0)

    def test_generated_witness_check(self):
        p=subprocess.run(['node','scripts/generate_phase1_cases.mjs','--check'],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)

    def test_randomized_complete_python_and_browser_parity(self):
        random_cases=[]
        for seed in range(40):
            rng=random.Random(seed)
            waves=DATA['games'][seed%3]['waves'];s=new_game(waves);decisions=[]
            while s['finished'] is None:
                board=deepcopy(s['board']);r=s['round'];lv=s['levels'][:]
                if s['pending'] is not None:lv[s['pending']]+=1
                for i,t in enumerate(waves[r-1]):board.append(dict(t,id=f'r{r}t{i}',depth=2,held=False))
                edits=[]
                for t in rng.sample(board,min(2,len(board))):
                    if rng.random()>.65:continue
                    choices=[]
                    for delta in (-1,1):
                        if t['lane']+delta in (0,1,2):choices.append(dict(kind='SHIFT',token=t['id'],delta=delta))
                    if not t['held']:choices.append(dict(kind='HOLD',token=t['id']))
                    if s['coolant']>sum(e['kind']=='DAMP' for e in edits):choices.append(dict(kind='DAMP',token=t['id']))
                    if choices:edits.append(rng.choice(choices))
                p=dict(edits=edits,build=None,charge=False,shield=0,free=None)
                if s['power']>=2 and rng.random()<.5:
                    options=['charge'] if r<8 and s['beacon']<3 and any(lv[i]>0 and not s['outages'][i] for i in range(3)) else []
                    options += [i for i in range(3) if r<8 and lv[i]<2 and not s['outages'][i]]
                    if options:
                        project=rng.choice(options)
                        if project=='charge':p['charge']=True
                        else:p['build']=project
                remaining=s['power']-(2 if p['charge'] or p['build'] is not None else 0)
                p['shield']=rng.randrange(min(2,remaining)+1)
                # The Switchyard action exercises paid-edit follow-up as well.
                if lv[2]>0 and not s['outages'][2] and rng.random()<.5:
                    for t in rng.sample(board,len(board)):
                        if t['id'] in {a['token'] for a in edits}:continue
                        deltas=[d for d in (-2,-1,1,2) if abs(d)<=lv[2] and t['lane']+d in (0,1,2)]
                        if deltas:p['free']=dict(token=t['id'],delta=rng.choice(deltas));break
                try:
                    following=step(s,p)
                except ValueError as e:
                    if p['charge'] and 'polarity collision' in str(e):
                        p['charge']=False  # Without a match, the Beacon cannot be charged.
                        following=step(s,p)
                    else:
                        raise
                s=following
                decisions.append(dict(plan=p,expected=s))
            random_cases.append(dict(waves=waves,decisions=decisions))
        js=r'''
import assert from 'node:assert/strict';import fs from 'node:fs';
import {newGame,step} from './site/storm-v2.mjs';
for(const c of JSON.parse(fs.readFileSync(0,'utf8'))){
 let s=newGame(c.waves);
 for(const rec of c.decisions){s=step(s,rec.plan);assert.deepStrictEqual(s,rec.expected);}
}
console.log('40 randomized complete Phase 1 sessions match independent Python');
'''
        p=subprocess.run(['node','--input-type=module','-e',js],cwd=ROOT,
                         input=json.dumps(random_cases),capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)

    def test_published_site_contains_all_phase1_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            destination=Path(d);info=build(destination)
            self.assertEqual(info['play_mode'],'solo-phase1-beacon')
            for name in ('site/storm-v2.mjs','site/phase1-cases.json','play.html','rules.html'):
                self.assertTrue((destination/name).exists(),name)
            html=(destination/'play.html').read_text()
            self.assertIn('id="preview"',html)
            self.assertIn('id="beacon"',html)
            self.assertIn('id="shield"',html)
            self.assertIn('id="project"',html)

if __name__=='__main__':unittest.main()
