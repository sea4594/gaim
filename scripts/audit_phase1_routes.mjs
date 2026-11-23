/** Reproducible (not human) Phase 1 project-scheduling audit.
 * Hold archived storm tactics and published shielding constant; vary one
 * infrastructure build and three Beacon orders across the eight rounds.
 * This measures objective feasibility and forbids late checkbox upgrades;
 * it does NOT measure fun, balance, or optimal strategies.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {newGame,step} from '../site/storm-v2.mjs';

export function auditRoutes(){
  const cases=JSON.parse(fs.readFileSync(new URL('../site/phase1-cases.json',import.meta.url))).games;
  const archived=JSON.parse(fs.readFileSync(new URL('../site/play-cases.json',import.meta.url))).games;
  const output=[];
  for(const current of cases){
    const prior=archived.find(c=>c.id===current.id);
    if(!prior)throw Error(`Missing archived scenario ${current.id}`);
    const tactics=prior.example.map((e,i)=>({edits:e.plan.edits,shield:current.example[i].plan.shield,free:null}));
    const paths=[];
    for(const system of [0,1,2]){
      let solutions=0,earliestBuild=Infinity,latestBuild=0,bestHull=-Infinity;
      function visit(state,round,built,charged,buildRound){
        if(state.finished!==null){
          if(state.finished==='WIN'&&built&&charged===3){
            solutions++;
            earliestBuild=Math.min(earliestBuild,buildRound);
            latestBuild=Math.max(latestBuild,buildRound);
            bestHull=Math.max(bestHull,state.hull);
          }
          return;
        }
        if(9-round < (built?0:1)+(3-charged))return;
        const orders=['none'];
        if(!built)orders.push('build');
        if(charged<3)orders.push('charge');
        for(const order of orders){
          const p={...tactics[round-1],build:order==='build'?system:null,charge:order==='charge'};
          try{visit(step(state,p),round+1,built||order==='build',charged+(order==='charge'),order==='build'?round:buildRound);}
          catch(e){if(!(e instanceof Error))throw e;/* Illegal schedules are excluded. */}
        }
      }
      visit(newGame(current.waves),1,false,0,null);
      paths.push({system,solutions,earliestBuild:solutions?earliestBuild:null,latestBuild:solutions?latestBuild:null,bestHull:solutions?bestHull:null});
    }
    output.push({id:current.id,title:current.title,paths});
  }
  return output;
}

if(process.argv[1]&&pathToFileURL(process.argv[1]).href===import.meta.url){
  console.log(JSON.stringify(auditRoutes(),null,2));
}
