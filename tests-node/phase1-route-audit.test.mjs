import {test} from 'node:test';
import assert from 'node:assert/strict';
import {auditRoutes} from '../scripts/audit_phase1_routes.mjs';

test('each published storm has a viable path with each individual system',()=>{
  const results=auditRoutes();
  assert.equal(results.length,3);
  for(const {title,paths} of results){
    assert.equal(paths.length,3);
    for(const path of paths){
      assert(path.solutions>0,`${title}: system ${path.system} cannot win under archived tactics`);
      assert(path.bestHull>0,`${title}: system ${path.system} must survive`);
      assert(path.latestBuild<=4,`${title}: winning late-build objective checkbox should not be possible`);
    }
  }
});
