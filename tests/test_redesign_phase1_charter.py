"""Small contract checks for the GAIM redesign evaluation charter (no gameplay changes)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "redesign"


class RedesignPhase1CharterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scorecard = json.loads((DIR / "design-scorecard.v1.json").read_text(encoding="utf-8"))

    def test_scorecard_is_well_formed_and_weighted(self):
        scores = self.scorecard["dimensions"]
        ids = [item["id"] for item in scores]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(sum(item["weight"] for item in scores), 100)
        self.assertTrue(all(0 < item["weight"] <= 100 for item in scores))
        self.assertEqual(self.scorecard["score_range"], [0, 4])

    def test_all_player_counts_and_baseline_status_are_explicit(self):
        self.assertEqual(self.scorecard["player_counts"], [1, 2, 3, 4])
        self.assertEqual(self.scorecard["rules_controls"]["production"], "charge-loom/v0.1")
        self.assertEqual(self.scorecard["rules_controls"]["research"], "forecast-market/v0.5")
        self.assertGreaterEqual(len(self.scorecard["hard_gates"]), 6)
        self.assertEqual(len(self.scorecard["phase2_candidates"]), 3)

    def test_docs_cover_rules_and_human_limits(self):
        charter = (DIR / "PHASE-01-DESIGN-CHARTER.md").read_text(encoding="utf-8")
        evaluation = (DIR / "PHASE-01-EVALUATION-PROTOCOL.md").read_text(encoding="utf-8")
        competition = (DIR / "PHASE-02-CANDIDATE-COMPETITION.md").read_text(encoding="utf-8")
        for term in ("portrait", "1–4", "co-op", "Forecast Market", "counterfactual"):
            self.assertIn(term.lower(), (charter + evaluation + competition).lower())
        for term in ("hard gates", "omniscient", "human", "holdout", "agency"):
            self.assertIn(term.lower(), evaluation.lower())
        for term in ("Candidate A", "Candidate B", "round sequence", "mechanics removed"):
            self.assertIn(term.lower(), competition.lower())


if __name__ == "__main__":
    unittest.main()
