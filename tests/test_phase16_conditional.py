"""Guarded-orders research tests; production reducer must remain identical."""
import unittest
from experiments.phase06_lab import Experiment,step
from experiments.phase15_forecast_council import candidate_edits,make_world,resolve
from experiments.phase16_conditional_commitments import GuardedOrder,triggers,validate,execute,best_fixed,best_guarded

class ConditionalOrderTests(unittest.TestCase):
    def setUp(self):
        g=Experiment.new('market',seed=200)
        self.g=step(g,draft=0)

    def test_truthful_guard_on_selected_storm(self):
        self.assertTrue(triggers(((0,1,2),(0,-1,1)))['left'])
        self.assertFalse(triggers(((2,1,2),(0,-1,1)))['left'])
        self.assertTrue(triggers(((1,-1,2),(2,-1,2)))['negative'])

    def test_selected_branch_replays_original_engine(self):
        g=make_world(self.g,((0,1,1),(0,-1,1)),((2,1,1),(1,-1,1)))
        branch=next(a for a in candidate_edits(g) if a!=('pass',))
        rule=GuardedOrder('left',branch,('pass',))
        self.assertEqual(execute(g,0,rule),resolve(g,0,branch))
        self.assertEqual(execute(g,1,rule),resolve(g,1,('pass',)))

    def test_rejects_invalid_guards_and_unseen_token_branches(self):
        g=self.g
        with self.assertRaises(ValueError):validate(g,GuardedOrder('oracle',('pass',),('shift',1,1)))
        with self.assertRaises(ValueError):validate(g,GuardedOrder('left',('pass',),('pass',)))
        with self.assertRaises(ValueError):validate(g,GuardedOrder('left',('pass',),('hold',999)))
        with self.assertRaises(ValueError):execute(g,88,GuardedOrder('left',('pass',),('hold',1)))

    def test_single_truth_bit_can_change_best_order(self):
        a=('hold',1);b=('shift',1,1)
        tables=[{a:(10,10),b:(0,0)},{a:(0,0),b:(10,10)}]
        class F:pass
        class W:pass
        world=[]
        for n in (0,2):
            w=W();w.game=F();w.game.available=(0,1);w.game.deck=(((n,1,1),(n,-1,1)),((n,1,1),(n,-1,1)))
            world.append(w)
        self.assertEqual(best_fixed(tables),5)
        value,order=best_guarded(tables,world,('left',))
        self.assertEqual(value,10)
        self.assertEqual(order.kind,'left')

    def test_guard_never_worse_with_zero_slot_penalty_upper_bound(self):
        g=self.g
        w=[make_world(g,((0,1,1),(1,-1,1)),((2,1,2),(0,-1,1))) for _ in range(2)]
        from experiments.phase15_forecast_council import payoff_table
        t=[payoff_table(i) for i in w]
        self.assertGreaterEqual(best_guarded(t,w)[0],best_fixed(t))

if __name__=='__main__':unittest.main()
