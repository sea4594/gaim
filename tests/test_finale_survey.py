"""Pinned small-state survey for reproducible A/B mechanics experiments."""
import unittest
from experiments.finale_survey import survey


class FinaleSurveyTests(unittest.TestCase):
    def test_small_survey_is_deterministic_and_never_breaks_baseline(self):
        a = survey(120, seed=406)
        self.assertEqual(a, survey(120, seed=406))
        self.assertEqual(a['results']['baseline']['winnable'], 23)
        self.assertEqual(a['results']['barrier']['winnable'], 24)
        self.assertEqual(a['results']['relay']['winnable'], 23)
        self.assertGreaterEqual(a['results']['bridge']['winnable'], 23)
        self.assertGreater(a['results']['bridge']['power_spend_winning_plans'], 0)


if __name__ == '__main__':
    unittest.main()
