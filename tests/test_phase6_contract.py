"""Contract tests independent of the prospective TypeScript server."""
import json
from pathlib import Path
import unittest

from phase6.contract import (
    ContractError, current_charges, normalize_edit, public_view, slot_owners,
    validate_plan,
)
from reference.charge_loom_v01 import State, Token, arrivals, start, step

ROOT = Path(__file__).resolve().parents[1]


class SlotAndPlanTests(unittest.TestCase):
    def test_slot_assignment_every_seat_count(self):
        self.assertEqual(slot_owners(1, 1), (0, 0, 0, 0))
        self.assertEqual(slot_owners(2, 1), (0, 1, 0, 1))
        self.assertEqual(slot_owners(3, 1), (0, 1, 2, 0))
        self.assertEqual(slot_owners(3, 2), (1, 2, 0, 1))
        self.assertEqual(slot_owners(3, 3), (2, 0, 1, 2))
        self.assertEqual(slot_owners(4, 9), (0, 1, 2, 3))
        for count in range(1, 5):
            for round_number in range(1, 10):
                owners = slot_owners(count, round_number)
                self.assertEqual(len(owners), 4)
                self.assertEqual(set(owners), set(range(count)))
        for wrong in (0, 5, True):
            with self.assertRaises(ContractError):
                slot_owners(wrong, 1)

    def test_two_shifts_are_genuinely_complementary(self):
        state = State(round=7, hp=5, progress=(2, 2, 1),
                      tokens=(Token(1, 0, 0, 1, 1), Token(2, 2, 0, -1, 1)), next_id=3)
        drafts = [
            {"slot": 0, "seat": 3, "action": {"kind": "SHIFT", "tokenId": 1, "direction": 1}},
            {"slot": 1, "seat": 0, "action": {"kind": "SHIFT", "tokenId": 2, "direction": -1}},
        ]
        actions = validate_plan(state, 4, drafts)
        self.assertEqual(actions, (("shift", 1, 1), ("shift", 2, -1)))
        self.assertEqual(step(state, actions).hp, 5)
        self.assertEqual(step(state, actions).progress, (2, 3, 1))
        self.assertEqual(step(state, validate_plan(state, 4, drafts[:1])).hp, 3)
        self.assertEqual(step(state, validate_plan(state, 4, drafts[1:])).hp, 3)

    def test_valid_plan_independent_of_slot_order(self):
        state = start(3)
        charges = current_charges(state)
        self.assertEqual(len(charges), 3)
        a = {"slot": 0, "seat": 0, "action": {"kind": "HOLD", "tokenId": charges[0].id}}
        b = {"slot": 1, "seat": 1, "action": {"kind": "HOLD", "tokenId": charges[1].id}}
        self.assertEqual(validate_plan(state, 4, [b, a]), validate_plan(state, 4, [a, b]))

    def test_reject_atomic_illegal_combined_plans(self):
        state = start(3)
        tokens = current_charges(state)
        first = {"slot": 0, "seat": 0, "action": {"kind": "HOLD", "tokenId": tokens[0].id}}
        with self.assertRaises(ContractError):
            validate_plan(state, 4, [first, {"slot": 1, "seat": 1, "action": first["action"]}])
        with self.assertRaises(ContractError):
            validate_plan(state, 4, [{"slot": 1, "seat": 0, "action": first["action"]}])
        with self.assertRaises(ContractError):
            validate_plan(state, 4, [{"slot": 0, "seat": True, "action": first["action"]}])
        with self.assertRaises(ContractError):
            validate_plan(state, 4, [{"slot": 0, "seat": 0, "action": {"kind": "SHIFT", "tokenId": tokens[0].id, "direction": 2}}])
        with self.assertRaises(ContractError):
            validate_plan(state, 4, [dict(first, action={"kind": "DAMP", "tokenId": 999})])
        with self.assertRaises(ContractError):
            validate_plan(state, 4, [dict(first, action={"kind": "HOLD", "tokenId": 1, "surprise": "!"})])

    def test_cooperative_four_slot_budget_is_not_four_actions_per_player(self):
        state = start(3)
        token_ids = [token.id for token in current_charges(state)]
        bad = [{"slot": i, "seat": 0, "action": {"kind": "HOLD", "tokenId": token_ids[i % 3]}} for i in range(4)]
        with self.assertRaises(ContractError):
            validate_plan(state, 4, bad)

    def test_serialization_and_preview_do_not_leak_seed(self):
        state = start(3)
        view = public_view(state, 4)
        self.assertNotIn("seed", view)
        self.assertNotIn("wavebook", view)
        self.assertEqual((view["completedRound"], view["planningRound"]), (0, 1))
        self.assertEqual(len(view["charges"]), len(arrivals(3, 1)))
        self.assertEqual(len(view["nextWave"]), len(arrivals(3, 2)))
        self.assertEqual([c["id"] for c in view["charges"]], [1, 2, 3])
        self.assertEqual(view["slotOwners"], [0, 1, 2, 3])
        self.assertIsNone(view["outcome"])
        self.assertEqual(json.loads(json.dumps(view)), view)
        s = state
        while not s.over:
            s = step(s, ())
        ended = public_view(s, 4)
        self.assertIsNone(ended["planningRound"])
        self.assertEqual(ended["slotOwners"], [])
        self.assertEqual(ended["nextWave"], [])
        if s.round == 9:
            self.assertEqual(ended["charges"], [])
        else:
            self.assertEqual(ended["charges"], [
                {"id":t.id,"lane":t.lane,"band":t.row,"polarity":"POSITIVE" if t.sign==1 else "NEGATIVE","strength":t.size,"alreadyHeld":bool(t.held)}
                for t in sorted(s.tokens)
            ])

    def test_public_view_consistent_for_all_player_counts(self):
        state = start(3)
        expected = public_view(state, 1)
        for count in (2, 3, 4):
            view = public_view(state, count)
            self.assertEqual(view["charges"], expected["charges"])
            self.assertEqual(view["capacitors"], expected["capacitors"])
            self.assertEqual(view["nextWave"], expected["nextWave"])
            self.assertEqual(len(view["slotOwners"]), 4)

    def test_every_verified_winning_plan_available_for_1_to_4_players(self):
        bank = json.loads((ROOT / "reference/verified-scenario-bank.json").read_text())
        for witness in bank["witnesses"]:
            for player_count in range(1, 5):
                state = start(witness["seed"])
                for record in witness["winning_trace"]:
                    owners = slot_owners(player_count, state.round + 1)
                    drafts = [
                        {"slot": i, "seat": owners[i], "action": (
                            {"kind": "SHIFT", "tokenId": action[1], "direction": action[2]}
                            if action[0] == "shift" else
                            {"kind": action[0].upper(), "tokenId": action[1]}
                        )}
                        for i, action in enumerate(record["actions"])
                    ]
                    flattened = validate_plan(state, player_count, drafts)
                    self.assertEqual(flattened, tuple(tuple(action) for action in record["actions"]))
                    state = step(state, flattened)
                self.assertEqual(state.over, "win")

    def test_reject_coolant_overspend_from_different_slots(self):
        state = State(round=7, hp=7, coolant=1, tokens=(
            Token(1, 0, 0, 1, 2), Token(2, 1, 0, -1, 2),
        ), next_id=3)
        owners = slot_owners(2, 8)
        drafts = [
            {"slot": 0, "seat": owners[0], "action": {"kind": "DAMP", "tokenId": 1}},
            {"slot": 1, "seat": owners[1], "action": {"kind": "DAMP", "tokenId": 2}},
        ]
        with self.assertRaises(ContractError):
            validate_plan(state, 2, drafts)
        self.assertEqual(state.coolant, 1)

    def test_fixture_scenarios_and_full_state_views(self):
        scenarios = json.loads((ROOT / "contracts/scenarios.v0.1.json").read_text())
        traces = json.loads((ROOT / "contracts/golden-traces.v0.1.json").read_text())
        self.assertEqual(scenarios["ruleset"], "charge-loom/v0.1")
        self.assertEqual(len(scenarios["scenarios"]), 7)
        self.assertEqual(len(traces["traces"]), 7)
        for scene, trace in zip(scenarios["scenarios"], traces["traces"]):
            self.assertEqual(scene["id"], trace["scenarioId"])
            state = start(scene["seed"])
            self.assertEqual(public_view(state, 4), trace["views"][0])
            for index, acts in enumerate(trace["actions"]):
                state = step(state, [tuple(a) for a in acts])
                self.assertEqual(public_view(state, 4), trace["views"][index + 1])
            self.assertEqual(state.over, "win")
            self.assertEqual(len(scene["waves"]), 7)


if __name__ == "__main__":
    unittest.main()
