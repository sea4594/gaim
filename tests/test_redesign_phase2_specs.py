"""Phase 2 small deterministic arithmetic probes. NOT complete game engines.

These cover the exact published 8-round fixtures without pretending that
Phase 3's implementation, multiplayer balance or human fun are verified.
"""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs' / 'redesign'
F = json.loads((DOCS / 'phase02-sanity-fixtures.json').read_text())


def resolve_breach(tokens):
    """Each lane sums signs; paired strength generates a match, remainder leaks."""
    energy = 0
    raw = 0
    lanes = set()
    lane_m = [0, 0, 0]
    lane_damage = [0, 0, 0]
    for lane in range(3):
        plus = sum(t['strength'] for t in tokens if t['lane'] == lane and t['sign'] == 1)
        minus = sum(t['strength'] for t in tokens if t['lane'] == lane and t['sign'] == -1)
        amt = min(plus, minus)
        damage = abs(plus-minus)
        energy += amt
        raw += damage
        lane_m[lane] = amt
        lane_damage[lane] = damage
        if amt:
            lanes.add(lane)
    return energy, raw, lanes, lane_m, lane_damage


def basic_breach_loop(rounds, before_movement=None):
    """Common two-band progression: enter FAR (depth 2), move to NEAR (1), breach (0)."""
    board = []
    for index, new_wave in enumerate(rounds, 1):
        for charge in new_wave:
            board.append(dict(charge, depth=2, sourceRound=index))
        if before_movement:
            board = before_movement(index, board)
        board = [dict(t, depth=t['depth']-1) for t in board]
        breached = [t for t in board if t['depth'] == 0]
        board = [t for t in board if t['depth'] > 0]
        yield index, breached, board


def probe_engine(with_builds=True):
    fixture = F['engine']
    levels = [0, 0, 0]
    pending = None
    power, hull = 2, 6
    for round_n, breached, board in basic_breach_loop(fixture['rounds']):
        if pending is not None:
            levels[pending] += 1
            pending = None
        b = fixture['builds'].get(str(round_n)) if with_builds else None
        if b is not None:
            assert power >= 2 and levels[b] < 2
            power -= 2
            pending = b
        energy, damage, lanes, _, _ = resolve_breach(breached)
        # No breach damage in the published Engine sanity fixture.
        assert damage == 0
        bonus = int(levels[0] >= 2 and bool(lanes) or levels[0] == 1 and 0 in lanes)
        power = min(8, power + energy + bonus)
        hull -= max(0, damage - levels[1])
        if round_n == 8:
            hull -= sum(t['strength'] for t in board)
    win = hull > 0 and sum(l == 2 for l in levels) >= 2
    return {'levels': levels, 'hull': hull, 'power': power, 'outcome':'WIN' if win else 'LOSS_SYSTEMS'}


def probe_operations(with_damp=True):
    fixture = F['operations']
    hull = 4 + fixture['playerCount']
    matched_strong = False
    precision = 0
    rounds = fixture['rounds']
    def edits(round_n, board):
        if round_n != fixture['damp']['round'] or not with_damp: return board
        targets=[t for t in board if t['sourceRound']==2 and t['lane']==0 and t['depth']==1]
        assert len(targets) == 1 and targets[0]['strength']==1
        return [t for t in board if t is not targets[0]]
    for round_n, breached, board in basic_breach_loop(rounds,edits):
        match, damage, lanes, lane_matches, lane_damage = resolve_breach(breached)
        hull -= damage
        matched_strong |= max(lane_matches)>=2
        if lane_matches[1]>0 and lane_damage[1]==0: precision+=1
        if hull<=0:
            return {'outcome':'LOSS_HULL','hull':hull,'lastRound':round_n}
        if round_n==8:
            hull -= sum(t['strength'] for t in board)
    finished = [name for name, ok in [('deep_capture',matched_strong),('precision_route',precision>=2)] if ok]
    return {'outcome':'WIN' if hull>0 and len(finished)>=2 else 'LOSS_TARGET','hull':hull,'missionsCompleted':finished}


class Phase2RulebookChecks(unittest.TestCase):
    def test_specs_exist_and_distinct(self):
        a = (DOCS/'PHASE-02A-STORM-ENGINE-RULEBOOK.md').read_text()
        b = (DOCS/'PHASE-02B-STORM-OPERATIONS-RULEBOOK.md').read_text()
        for field in ('## 2.','## 3.','## 4.','## 5.','## 6.','## 7.','## 8.'):
            self.assertIn(field,a)
            self.assertIn(field,b)
        for keyword in ('BUILD','Dynamo','Aegis','Switchyard','offline'):
            self.assertIn(keyword,a)
        for keyword in ('FLIP','DAMP','PASS','READY','mission','hand','initiative'):
            self.assertIn(keyword,b)

    def test_common_collision_accounting(self):
        e,d,lanes,matches,leaks=resolve_breach([{'lane':0,'sign':1,'strength':3},{'lane':0,'sign':-1,'strength':1}])
        self.assertEqual((e,d,lanes,matches,leaks),(1,2,{0},[1,0,0],[2,0,0]))

    def test_engine_full_fixture(self):
        actual=probe_engine()
        expected=F['engine']['expected']
        for k,v in expected.items():self.assertEqual(actual[k],v)
        self.assertEqual(actual['power'],8)

    def test_engine_no_build_fails_on_systems(self):
        outcome=probe_engine(False)
        self.assertEqual(outcome['outcome'],F['engine']['noBuildOutcome'])
        self.assertEqual(outcome['hull'],6)

    def test_operations_full_fixture(self):
        actual=probe_operations()
        expected=F['operations']['expected']
        for k,v in expected.items():self.assertEqual(actual[k],v)

    def test_operations_without_damp_loses(self):
        actual=probe_operations(False)
        self.assertEqual(actual['outcome'],F['operations']['noDampOutcome'])
        self.assertEqual(actual['lastRound'],7)

    def test_operations_wave_counts(self):
        for i,wave in enumerate(F['operations']['rounds']):
            self.assertEqual(len(wave),3 if i<6 else 0)
        for p in range(1,5):
            self.assertEqual(4+p, {1:5,2:6,3:7,4:8}[p])

    def test_engine_wave_sizing_and_sign(self):
        self.assertEqual(len(F['engine']['rounds']),8)
        self.assertTrue(all(c['sign'] in (-1,1) for wave in F['engine']['rounds'] for c in wave))
        self.assertEqual(len(F['engine']['rounds'][0]),2)

if __name__ == '__main__':unittest.main()
