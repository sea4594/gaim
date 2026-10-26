"""Phase 4 adversarial tournament safeguards, research only."""
import json
import unittest
from pathlib import Path
from copy import deepcopy
from experiments.redesign_phase3 import engine, operations
from experiments.redesign_phase3.survey import operations_waves
from experiments.redesign_phase4.tournament import run_tournament, with_best_free
from experiments.redesign_phase4.rotation import rotating_policy, play_rotating

DOCS=Path(__file__).resolve().parents[1]/'docs/redesign'

class Phase4SelectionTests(unittest.TestCase):
    def test_small_tournament_replays_exactly(self):
        self.assertEqual(run_tournament(3, 74000),run_tournament(3, 74000))

    def test_rotating_agent_only_spends_held_cards(self):
        for n in (1,2,3,4):
            s=operations.new_game(operations_waves(74001,n),n,
                    ('deep_capture','precision_route','double_pulse'),74001)
            for _ in range(5):
                if s['finished']: break
                p=rotating_policy(s)
                self.assertEqual(len(p),n)
                for seat,actions in enumerate(p):
                    self.assertLessEqual(len(actions),2 if n==1 else 1)
                    for a in actions:self.assertIn(a['kind'],s['hands'][seat])
                s=operations.step(s,p)

    def test_priority_rotation_is_deterministic(self):
        for n in (2,3,4):
            self.assertEqual(play_rotating(74002,n),play_rotating(74002,n))

    def test_free_switchyard_has_a_real_valid_use(self):
        waves=[[] for _ in range(8)]
        s=engine.new_game(waves)
        s['levels']=[0,0,2]
        s['board']=[dict(id='pos',lane=0,sign=1,strength=1,depth=1,held=False),
                    dict(id='neg',lane=1,sign=-1,strength=1,depth=1,held=False)]
        default=engine.step(s,dict(edits=[]))
        p=with_best_free(s,dict(edits=[]))
        self.assertIn('free',p)
        improved=engine.step(s,p)
        self.assertEqual(improved['hull'],s['hull'])
        self.assertLess(default['hull'],improved['hull'])
        self.assertEqual(s['board'][0]['lane'],0) # never mutated

    def test_saved_evidence_is_well_formed(self):
        for kind in ('development','holdout'):
            result=json.loads((DOCS/f'phase04-comparison-{kind}.json').read_text())
            n=40
            for path in ('dynamo_aegis','aegis_switchyard','dynamo_switchyard'):
                r=result['engine'][path]
                self.assertTrue(0<=r['baseline_wins']<=n)
                self.assertTrue(0<=r['free_policy_wins']<=n)
                self.assertTrue(r['free_helped']>=0 and r['free_hurt']>=0)
            for nplayers in (1,2,3,4):
                r=result['operations'][str(nplayers)]
                self.assertEqual(len(r['active_player_actions']),nplayers)
                self.assertTrue(0<=r['active_wins']<=n)
                self.assertTrue(0<=r['pass_wins']<=n)
            rr=json.loads((DOCS/f'phase04-rotation-{kind}.json').read_text())
            for nplayers in (2,3,4):
                self.assertEqual(len(rr[str(nplayers)]['rotated_order_card_uses']),nplayers)

if __name__=='__main__':unittest.main()
