"""Minimal no-framework Pages preview; verify it is an honest v0.1 replay."""
import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class PreviewContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html=(ROOT/'index.html').read_text()
        cls.js=(ROOT/'site/replay.js').read_text()
        cls.data=json.loads((ROOT/'contracts/golden-traces.v0.1.json').read_text())

    def test_every_demo_frame_comes_from_verified_replays(self):
        self.assertEqual(self.data['ruleset'],'charge-loom/v0.1')
        self.assertEqual(len(self.data['traces']),7)
        for trace in self.data['traces']:
            self.assertEqual(len(trace['views']),10)
            self.assertEqual(len(trace['actions']),9)
            self.assertEqual(trace['views'][-1]['outcome'],'win')

    def test_page_links_to_actual_golden_data_and_is_honest_about_status(self):
        self.assertIn('contracts/golden-traces.v0.1.json',self.js)
        self.assertIn('VERIFIED REPLAY · v0.1',self.html)
        self.assertIn('read-only replay',self.html)
        self.assertIn('not yet part of this replay',self.html)
        self.assertNotIn('https://cdn.',self.html)
        self.assertIn('viewport-fit=cover',self.html)

    def test_no_new_runtime_or_server_dependency(self):
        self.assertIn('type="module" src="./site/replay.js"',self.html)
        self.assertNotIn('server/http',self.js)
        self.assertNotIn('fetch("https:',self.js)
        self.assertTrue((ROOT/'site/style.css').exists())

if __name__=='__main__':unittest.main()
