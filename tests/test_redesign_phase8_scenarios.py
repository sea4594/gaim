"""Phase 8: reproducible strategic-scenario tournament and website integrity."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from experiments.redesign_phase8 import scenarios,build_exhibit
from experiments.redesign_phase3 import engine
from scripts.build_pages import ROOT,ASSETS,build

class StrategicScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=build_exhibit.build()

    def test_scenario_generation_is_stable_valid_and_public(self):
        for climate in scenarios.PROFILES:
            for seed in (0,82000,82004):
                waves=scenarios.waves(climate,seed)
                self.assertEqual(waves,scenarios.waves(climate,seed))
                self.assertEqual(len(waves),8)
                self.assertEqual(waves[-1],[])
                self.assertEqual(engine.new_game(waves)['hull'],6)
        with self.assertRaises(ValueError):scenarios.waves('not-a-scenario',0)
        with self.assertRaises(ValueError):scenarios.waves('harvest',-1)
        with self.assertRaises(ValueError):scenarios.run('harvest',0,'no-build-ever')

    def test_all_replay_rounds_match_real_engine(self):
        for climate, seeds in self.data['examples'].items():
            for seed, strategies in seeds.items():
                for mode,record in strategies.items():
                    state=engine.new_game(record['waves'])
                    for frame in record['snapshots']:
                        self.assertEqual(state['round'],frame['round'])
                        state=engine.step(state,copy.deepcopy(frame['plan']))
                        for field in ('board','hull','coolant','power','levels','pending','outages'):
                            self.assertEqual(state[field],frame[field])
                    self.assertEqual(state['finished'],record['outcome'])
                    self.assertEqual(state['levels'],record['levels'])
                    self.assertEqual(len(state['history']),record['rounds'])
                    self.assertTrue(all('waves' not in t for t in record['snapshots']))

    def test_holdout_is_distinct_and_climate_effect_is_visible(self):
        audit=self.data['audit'];self.assertEqual(audit['ruleset'],'redesign/phase8-scenario-climates')
        a=audit['sets']['development'];b=audit['sets']['holdout']
        self.assertNotEqual(a['start'],b['start'])
        self.assertEqual((a['n'],b['n']),(40,40))
        for row in (a,b):
            for climate,metrics in row['profiles'].items():
                self.assertEqual(set(metrics['wins']),set(scenarios.STRATEGIES))
                self.assertLessEqual(max(metrics['wins'].values()),40)
                self.assertEqual(metrics['different_winning_paths']+metrics['only_one_winning_path']+metrics['all_lose'],40)
        self.assertGreater(a['profiles']['harvest']['wins']['dynamo_switchyard'], a['profiles']['siege']['wins']['dynamo_switchyard'])
        self.assertGreater(b['profiles']['harvest']['wins']['dynamo_switchyard'], b['profiles']['siege']['wins']['dynamo_switchyard'])

    def test_data_matches_exact_generator_and_has_no_false_claims(self):
        disk=json.loads((ROOT/'site/strategy-lab-data.json').read_text())
        self.assertEqual(disk,self.data)
        self.assertEqual(sorted(int(n) for n in disk['examples']['harvest']),build_exhibit.SEEDS)
        self.assertIn('not playable online multiplayer',disk['notice'])
        self.assertIn('no Switchyard free-shift search',disk['audit']['policy'])

    def test_site_artifact_contains_live_browser_demo_only(self):
        with tempfile.TemporaryDirectory() as temp:
            build(Path(temp))
            present={str(p.relative_to(temp)) for p in Path(temp).rglob('*') if p.is_file()}
            self.assertEqual(present,set(ASSETS)|{'.nojekyll','build-info.json'})
            self.assertIn('strategy-lab.html',(Path(temp)/'index.html').read_text())
            self.assertIn('site/strategy-lab-data.json',(Path(temp)/'site/strategy-lab.js').read_text())
            self.assertIn('storm climate',(Path(temp)/'strategy-lab.html').read_text().lower())
            self.assertNotIn('experiments/redesign_phase8/scenarios.py',present)
            self.assertNotIn('server/http.mjs',present)
            self.assertNotIn('eval(',(Path(temp)/'site/strategy-lab.js').read_text())

if __name__=='__main__':unittest.main()
