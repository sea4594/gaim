/** Deterministic Phase 1 playable cases derived from the archived Phase 9 storms. */
import fs from 'node:fs';
import {newGame,step,beginning} from '../site/storm-v2.mjs';
const root=new URL('../',import.meta.url);
const historic=JSON.parse(fs.readFileSync(new URL('site/play-cases.json',root),'utf8'));
const key=['round','hull','power','coolant','levels','pending','outages','board','beacon'];
const clone=x=>structuredClone(x);
function planFor(game,record,id){
 const p={edits:clone(record.plan.edits||[]),build:null,charge:false,shield:0,free:null};
 if(game.round===1) p.build=id==='5000'?2:id==='5009'?1:0;
 else if(id==='5009'){
   if([3,4,7].includes(game.round))p.charge=true;
   if([5,6].includes(game.round))p.shield=1;
 }else if(game.beacon<3&&game.power>=2)p.charge=true;
 // Under Switchyard, demonstrate an actively useful free Shift of a NEAR charge.
 // It replaces one paid Shift of the same token while leaving other edits intact.
 const entered=beginning(game);
 if(entered.levels[2]>0&&!game.outages[2]){
   const ix=p.edits.findIndex(a=>a.kind==='SHIFT');
   if(ix>=0){const action=p.edits.splice(ix,1)[0];p.free={token:action.token,delta:action.delta};}
 }
 return p;
}
const games=historic.games.map(c=>{
 let game=newGame(c.waves);const example=[];
 for(const rec of c.example){
   const before=Object.fromEntries(key.map(k=>[k,clone(game[k])]));
   const plan=planFor(game,rec,c.id);
   game=step(game,plan);
   example.push({before,plan,after:clone(game)});
 }
 if(game.finished!=='WIN')throw Error(`No winning Phase 1 witness for ${c.id}: ${game.finished}`);
 return {id:c.id,title:c.title,description:c.description,waves:c.waves,example};
});
const output=JSON.stringify({ruleset:'gaim/phase1-beacon-v2',games},null,2)+'\n';
const file=new URL('site/phase1-cases.json',root);
if(process.argv.includes('--check')){
 if(fs.readFileSync(file,'utf8')!==output)throw Error('Phase 1 cases are stale; regenerate them');
 console.log('Phase 1 playable cases current: 3 winning full-game witnesses');
}else{
 fs.writeFileSync(file,output);
 console.log('Generated 3 Phase 1 complete winning witness cases');
}
