"""Phase 7: exact counterfactual lab, seat-level CLI, static Pages integrity."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from experiments.redesign_phase7 import decision_lab,pass_play
from experiments.redesign_phase6.crew import STATIONS,staff_counts,work_units,staffed_step
from experiments.redesign_phase3 import engine
from scripts.build_pages import ASSETS,ROOT,build as build_pages


class ResearchLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=decision_lab.build()

    def test_exhaustive_precomputed_file_matches_reducer(self):
        on_disk=json.loads((ROOT/'site/crew-lab-data.json').read_text())
        self.assertEqual(json.loads(json.dumps(self.data)),on_disk)
        self.assertEqual(on_disk['ruleset'],'redesign/phase7-commitment-lab')
        audit=json.loads((ROOT/'docs/redesign/phase07-seat-counterfactual-audit.json').read_text())
        self.assertEqual(audit,on_disk['audit'])

    def test_all_512_outcomes_independent_of_choice_order(self):
        # The submitted sequence is public, but outcomes rely only on staffing
        # counts. This also proves that adding humans cannot mint actions.
        for name in decision_lab.SCENARIOS:
            for key,result in self.data['scenarios'][name]['outcomes'].items():
                choices=key.split('|')
                self.assertEqual(result,decision_lab.outcome(name,choices))
                if result['valid']:
                    for p in (1,2,3,4):
                        from experiments.redesign_phase6.crew import deterministic_assignment
                        assignment=deterministic_assignment(result['staff'],p,decision_lab.scenario(name)['round'])
                        out=staffed_step(decision_lab.scenario(name),p,assignment,result['orders'])
                        self.assertEqual(out['hull'],result['hull'])
                        self.assertEqual(out['power'],result['power'])

    def test_single_seat_choice_can_reverse_win(self):
        a=decision_lab.outcome('crisis',['nav','nav','control','engineer'])
        b=decision_lab.outcome('crisis',['nav','nav','engineer','engineer'])
        self.assertTrue(a['valid'] and b['valid'])
        self.assertEqual(a['following_finish'],'WIN')
        self.assertEqual(b['following_finish'],'LOSS_HULL')
        self.assertEqual(a['initial'],b['initial'])

    def test_exhaustive_audit_does_not_overclaim_agency(self):
        crisis=self.data['audit']['crisis'];mid=self.data['audit']['junction']
        self.assertEqual(crisis['total_seat_combinations'],256)
        self.assertEqual(mid['total_seat_combinations'],256)
        self.assertGreater(crisis['win_loss_changing_changes'],0)
        self.assertEqual(mid['win_loss_changing_changes'],0)
        self.assertGreater(crisis['illegal'],0)
        self.assertGreater(mid['state_changing_changes'],mid['win_loss_changing_changes'])

    def test_invalid_commitments_cannot_change_reducer_state(self):
        state=decision_lab.scenario('crisis');snapshot=copy.deepcopy(state)
        bad=decision_lab.outcome('crisis',['engineer']*4)
        self.assertFalse(bad['valid'])
        self.assertEqual(state,snapshot)
        self.assertRaises(ValueError,decision_lab.outcome,'crisis',['nav']*5)
        self.assertRaises(ValueError,decision_lab.scenario,'unrecognized')

    def test_pass_and_play_is_replayable_for_all_player_counts(self):
        for players in range(1,5):
            text=[]
            record=pass_play.run(players,271001,read=lambda prompt:'0',write=lambda line:text.append(str(line)))
            ending=pass_play.replay(record)
            self.assertEqual(ending['finished'],record['outcome'])
            self.assertTrue(1<=len(record['decisions'])<=8)
            for round in record['decisions']:
                allocation=round['assignment']
                self.assertEqual(sum(len(x) for x in allocation),4)
                self.assertEqual(len(allocation),players)
                self.assertEqual(tuple(len(x) for x in allocation),work_units(players,round['round']))
            self.assertTrue(any('FINAL RESULT' in line for line in text))

    def test_pass_and_play_replay_detects_tampering(self):
        record=pass_play.run(4,271009,read=lambda prompt:'0',write=lambda line:None)
        bad=copy.deepcopy(record)
        bad['decisions'][0]['hull']=300
        with self.assertRaisesRegex(ValueError,'Replay mismatch'):pass_play.replay(bad)

    def test_tactical_menus_restrict_duplicate_edits_and_hold_reuse(self):
        state=decision_lab.scenario('crisis');board=pass_play.incoming_board(state)
        nav=pass_play.edit_options(board,'nav',{'drifter'},1,7)
        self.assertFalse(any(a['token']=='drifter' for a in nav))
        control=pass_play.edit_options(board,'control',set(),0,7)
        self.assertFalse(any(a['kind']=='DAMP' for a in control))
        expired=pass_play.edit_options(board,'nav',set(),1,8)
        self.assertFalse(any(a['kind']=='HOLD' for a in expired))

    def test_pages_whitelists_only_research_demo_and_existing_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_pages(Path(tmp))
            present={str(p.relative_to(tmp)) for p in Path(tmp).rglob('*') if p.is_file()}
            self.assertEqual(present,set(ASSETS)|{'.nojekyll','build-info.json'})
            self.assertIn('crew-lab.html',present)
            self.assertNotIn('experiments/redesign_phase7/pass_play.py',present)
            html=(Path(tmp)/'crew-lab.html').read_text()
            self.assertIn('site/crew-lab.js',html)
            self.assertIn('crew-lab.html',(Path(tmp)/'index.html').read_text())
            js=(Path(tmp)/'site/crew-lab.js').read_text()
            self.assertIn('crew-lab-data.json',js)
            self.assertNotIn('eval(',js)


if __name__=='__main__':unittest.main()
