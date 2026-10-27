"""Independent Python/JavaScript reducer parity and real Pages artifact contracts."""
from __future__ import annotations
import json
import random
from copy import deepcopy
import subprocess
import tempfile
import unittest
from pathlib import Path

from experiments.redesign_phase3 import engine
from experiments.redesign_phase9.build_play_cases import OUTPUT, ROOT, render


class BrowserPlayRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(OUTPUT.read_text())

    def test_generated_witnesses_are_current(self):
        self.assertEqual(OUTPUT.read_text(),render())
        self.assertEqual(self.data['ruleset'],'redesign/phase3-storm-engine')
        self.assertEqual(len(self.data['games']),3)

    def test_all_witnesses_replay_with_authoritative_python_reducer(self):
        for case in self.data['games']:
            with self.subTest(case=case['id']):
                state=engine.new_game(case['waves'])
                self.assertEqual(len(case['example']),8)
                for item in case['example']:
                    for key in item['before']:
                        self.assertEqual(item['before'][key],state[key],key)
                    state=engine.step(state,item['plan'])
                    self.assertEqual(state,item['after'])
                self.assertEqual(state['finished'],'WIN')

    def test_browser_engine_exact_eight_round_parity_and_invalid_plans(self):
        js=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {newGame,step,beginning} from './site/play-engine.mjs';
const cases=JSON.parse(fs.readFileSync('./site/play-cases.json','utf8')).games;
for(const example of cases){
 let s=newGame(example.waves);
 for(const rec of example.example){
  assert.deepStrictEqual(s, { ...s });
  for(const [key,value] of Object.entries(rec.before)) assert.deepStrictEqual(s[key],value);
  assert.deepStrictEqual(step(s,rec.plan),rec.after);
  s=step(s,rec.plan);
 }
 assert.equal(s.finished,'WIN');
 assert.throws(()=>step(s,{}),/ended/);
}
const game=newGame(cases[0].waves);
assert.equal(beginning(game).board.length, cases[0].waves[0].length);
assert.throws(()=>step(game,{edits:[{kind:'SHIFT',token:'nonexistent',delta:1}]}),/not available/);
assert.throws(()=>step(game,{edits:[{kind:'DAMP',token:'r1t0'},{kind:'DAMP',token:'r1t1'},{kind:'DAMP',token:'r1t2'}]}),/two paid/);
assert.throws(()=>step(game,{build:3}),/Construction unavailable/);
console.log('Three complete Python/JS witness matches + invalid-plan checks passed');
'''
        p=subprocess.run(['node','--input-type=module','-e',js],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)

    def test_randomized_cross_language_state_parity(self):
        """Diversify real edits and builds beyond the three scripted win witnesses."""
        from experiments.redesign_phase3 import survey
        cases=[]
        for seed in range(700,735):
            rng=random.Random(seed)
            waves=survey.engine_waves(seed)
            s=engine.new_game(waves)
            decisions=[]
            while s['finished'] is None:
                r=s['round']
                board=deepcopy(s['board'])
                for i,t in enumerate(waves[r-1]):
                    board.append(dict(t,id=f'r{r}t{i}',depth=2,held=False))
                edits=[]
                targets=rng.sample(board,min(len(board),2))
                for t in targets:
                    choices=[]
                    for delta in (-1,1):
                        if t['lane']+delta in (0,1,2):
                            choices.append(dict(kind='SHIFT',token=t['id'],delta=delta))
                    if not t['held']:choices.append(dict(kind='HOLD',token=t['id']))
                    if s['coolant']>sum(a['kind']=='DAMP' for a in edits):
                        choices.append(dict(kind='DAMP',token=t['id']))
                    if choices and rng.random()<.65:edits.append(rng.choice(choices))
                levels=s['levels'][:]
                if s['pending'] is not None:levels[s['pending']]+=1
                eligible=[i for i in range(3) if levels[i]<2 and not s['outages'][i]]
                build=rng.choice(eligible) if s['power']>=2 and eligible and rng.random()<.70 else None
                excluded={a['token'] for a in edits}
                free=None
                if levels[2]>0 and not s['outages'][2] and rng.random()<.6:
                    for t in rng.sample(board,len(board)):
                        if t['id'] in excluded or (levels[2]==1 and t['depth']!=2):continue
                        deltas=[d for d in (-1,1) if t['lane']+d in (0,1,2)]
                        if deltas:
                            free=dict(token=t['id'],delta=rng.choice(deltas));break
                plan=dict(edits=edits,build=build,free=free)
                following=engine.step(s,plan)
                decisions.append(dict(plan=plan,expected=following))
                s=following
            cases.append(dict(waves=waves,decisions=decisions))
        js=r"""
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {newGame,step} from './site/play-engine.mjs';
for(const c of JSON.parse(fs.readFileSync(0,'utf8'))){
 let s=newGame(c.waves);
 for(const item of c.decisions){s=step(s,item.plan);assert.deepStrictEqual(s,item.expected);}
}
console.log('35 randomized full-session browser/Python comparisons matched');
"""
        p=subprocess.run(['node','--input-type=module','-e',js],cwd=ROOT,
                input=json.dumps(cases),text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)

    def test_site_build_contains_rules_and_playable_entry(self):
        from scripts.build_pages import build
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)
            info=build(target)
            self.assertTrue(info['playable'])
            self.assertEqual(info['play_mode'],'solo-experimental-storm-engine')
            for name in ('play.html','rules.html','site/play.js','site/play-engine.mjs','site/play-cases.json'):
                self.assertTrue((target/name).is_file(),name)
            html=(target/'index.html').read_text()
            self.assertIn('play.html',html)
            self.assertIn('rules.html',html)
            self.assertIn('eight-round',html.lower())
            rule=(target/'rules.html').read_text()
            for term in ('Dynamo','Aegis','Switchyard','HOLD','DAMP','SHIFT','round 8','outages'):
                self.assertIn(term,rule)
            self.assertNotIn('server/http.mjs',str(sorted(str(x) for x in target.rglob('*'))))

if __name__=='__main__':unittest.main()
