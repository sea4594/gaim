"""Verify the Pages build packages only the pinned public replay assets."""
import json,tempfile,unittest
from pathlib import Path
from scripts.build_pages import ROOT,ASSETS,MARKER,build

class PagesDeployment(unittest.TestCase):
    def test_package_contains_only_public_replay_files(self):
        with tempfile.TemporaryDirectory() as d:
            result=build(Path(d))
            actual={str(p.relative_to(d)) for p in Path(d).rglob('*') if p.is_file()}
            self.assertEqual(actual,set(ASSETS)|{'.nojekyll','build-info.json'})
            self.assertEqual(result['artifact'],MARKER)
            self.assertEqual(result['playable'],False)
            self.assertEqual(result['scenario_count'],7)
    def test_rejects_overwriting_nonempty_destination(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'existing.txt').write_text('preserve')
            with self.assertRaises(ValueError):build(Path(d))
            self.assertEqual((Path(d)/'existing.txt').read_text(),'preserve')
    def test_no_dependency_on_external_assets(self):
        html=(ROOT/'index.html').read_text()
        js=(ROOT/'site/replay.js').read_text()
        workflow=(ROOT/'.github/workflows/deploy-pages.yml').read_text()
        self.assertIn('deployment-id',html)
        self.assertIn('build-info.json',js)
        self.assertIn('scripts/release_gate.sh',workflow)
        self.assertIn('actions/deploy-pages@v4',workflow)
        self.assertIn('pages: write',workflow)

if __name__=='__main__':unittest.main()
