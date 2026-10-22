"""Self-contained exact rule tests for Charge Loom v0.1.
Run `python3 tests_v01.py` in this directory; stdlib only.
"""
import json
from pathlib import Path
import unittest
from charge_loom_v01 import State, Token, start, step, arrivals, wavebook

class CoreRulesTests(unittest.TestCase):
    def test_two_player_interlock(self):
        s=State(round=7,hp=5,progress=(2,2,1),tokens=(Token(1,0,0,1,1),Token(2,2,0,-1,1)),next_id=3,seed=7)
        for a in [[],[('shift',1,1)],[('shift',2,-1)]]:
            n=step(s,a)
            self.assertEqual((n.hp,n.progress),(3,(2,2,1)))
        both=step(s,[('shift',1,1),('shift',2,-1)])
        reversed_edits=step(s,[('shift',2,-1),('shift',1,1)])
        self.assertEqual((both.hp,both.progress),(5,(2,3,1)))
        self.assertEqual(reversed_edits,both)

    def test_multi_turn_risk_correct(self):
        q=State(round=7,hp=3,progress=(3,2,1),coolant=1,tokens=(Token(1,1,0,1,1),Token(2,1,0,-1,1),Token(3,2,1,-1,2)),next_id=4,seed=1)
        lose=step(step(q,[]),[])
        self.assertEqual(lose.over,'loss: target')
        prepared=step(q,[('hold',1)])
        self.assertEqual((prepared.hp,prepared.tokens[0].size),(2,2))
        won=step(prepared,[('shift',1,1)])
        self.assertEqual((won.hp,won.progress,won.over),(2,(3,2,3),'win'))

    def test_end_purge_prevents_exploit(self):
        s=State(round=8,hp=3,progress=(3,3,2),tokens=(Token(1,0,0,1,3),),next_id=2)
        f=step(s,[('hold',1)])
        self.assertEqual(f.over,'loss: breach')
        self.assertEqual(f.tokens,())
        self.assertEqual(f.hp,0)

    def test_damp_resource_and_hazard(self):
        s=State(round=7,hp=4,progress=(2,2,2),coolant=1,tokens=(Token(1,0,0,1,2),),next_id=2)
        self.assertEqual(step(s,[]).hp,2)
        self.assertEqual((step(s,[('damp',1)]).hp,step(s,[('damp',1)]).coolant),(3,0))
        self.assertEqual(step(s,[('hold',1)]).tokens[0].size,3)

    def test_caps_and_matching_arithmetic(self):
        s=State(round=7,hp=6,progress=(3,0,0),tokens=(Token(1,0,0,1,3),Token(2,0,0,-1,1),Token(3,1,0,1,2),Token(4,1,0,-1,2)),next_id=5)
        f=step(s,[])
        self.assertEqual(f.hp,4)
        self.assertEqual(f.progress,(3,2,0))

    def test_replays_and_invariants_150_seeds(self):
        for seed in range(150):
            self.assertEqual(sum(len(x) for x in wavebook(seed)),18)
            self.assertEqual(sum(1 for wave in wavebook(seed) for _,sign,_ in wave if sign==1),9)
            state=start(seed)
            while not state.over:
                a=step(state,())
                self.assertEqual(a,step(state,()))
                self.assertLessEqual(max(a.progress),3)
                self.assertGreaterEqual(min(a.progress),0)
                self.assertTrue(all(0<=t.lane<=2 and 0<=t.row<=2 and 1<=t.size<=3 for t in a.tokens))
                self.assertGreaterEqual(a.coolant,0)
                state=a
            if state.round==9:
                self.assertEqual(state.tokens,())

    def test_bad_actions_rejected(self):
        s=start(0)
        for acts in [[('shift',999,1)],[('hold',1),('shift',1,1)],[('damp',1),('damp',1)],[('bogus',1)], [('pass',)]*5]:
            with self.subTest(actions=acts):
                with self.assertRaises(ValueError): step(s,acts)

    def test_verified_witness_bank(self):
        bank=json.loads((Path(__file__).parent/'verified-scenario-bank.json').read_text())
        self.assertGreaterEqual(len(bank['witnesses']),7)
        for w in bank['witnesses']:
            s=start(w['seed'])
            for r in w['winning_trace']:
                s=step(s,[tuple(x) for x in r['actions']])
                self.assertEqual(s.round,r['round'])
                self.assertEqual(s.hp,r['hp'])
                self.assertEqual(list(s.progress),r['progress'])
                self.assertEqual(s.over,r['outcome'])
            self.assertEqual(s.over,'win')

if __name__=='__main__':unittest.main(verbosity=2)
