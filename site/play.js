import {beginning,newGame,step,SYSTEMS,LANES} from './play-engine.mjs';
const $=id=>document.getElementById(id);
const clone=x=>structuredClone(x);
let cases=[],game=null,caseFile=null,edits=[],build=null,free=null,selected=null,lastReport=null;
const line=(sign,n)=>`${sign===1?'+':'−'}${n}`;
const tokenText=t=>`${line(t.sign,t.strength)} · ${t.id}`;
function current(){return game?beginning(game):null;}
function showError(msg){$('error').textContent=msg;$('error').hidden=false;}
function clearError(){$('error').hidden=true;}
function start(){
  caseFile=cases.find(c=>c.id===$('scenario').value)||cases[0];
  game=newGame(caseFile.waves);edits=[];build=null;free=null;selected=null;lastReport=null;
  $('scenario-note').textContent=caseFile.description;
  clearError();render();
}
function plan(){return {edits:clone(edits),build,free:clone(free)};}
function upcoming(s){return s.board.find(t=>t.id===selected);}
function disableOrders(finished){
  for(const id of ['shift-left','shift-right','hold','damp','build','free-token','free-dir','clear-edits','hint','resolve'])$(id).disabled=finished;
}
function render(){
  if(!game)return;
  const finished=game.finished!==null,s=finished?game:current();
  $('round').textContent=`${finished?game.round:game.round} / 8`;
  $('hull').textContent=String(game.hull);$('power').textContent=String(game.power);
  $('coolant').textContent=String(game.coolant);
  $('status').textContent=finished
    ? (game.finished==='WIN'?'VICTORY — Two systems restored. The settlement survives!':`GAME OVER — ${game.finished==='LOSS_HULL'?'Hull was exhausted.':'Fewer than two active systems reached level 2.'}`)
    : game.round===1?
      "Round 1: these charges have just arrived FAR, so none can breach yet. Think about investing your starting 2 Power, then resolve. The danger reaches you next round." :
      `Round ${game.round}: choose up to two interventions and one construction order, then RESOLVE. The FAR charges will move to NEAR; current NEAR charges will breach unless held.`;
  const disabled=finished;
  const used=new Set(edits.map(e=>e.token));
  $('board').replaceChildren();
  for(let lane=0;lane<3;lane++){
    const laneEl=document.createElement('div');laneEl.className='lane';
    const title=document.createElement('div');title.className='lane-title';title.textContent=LANES[lane].toUpperCase();laneEl.append(title);
    for(const depth of [2,1]){
      const band=document.createElement('div');band.className=`band ${depth===1?'near':'far'}`;
      const tag=document.createElement('span');tag.className='band-name';tag.textContent=depth===1?'NEAR · BREACH':'FAR · ARRIVAL';band.append(tag);
      const tokens=s.board.filter(t=>t.lane===lane&&t.depth===depth);
      if(!tokens.length){const empty=document.createElement('div');empty.className='empty';empty.textContent='— empty —';band.append(empty);}
      for(const t of tokens){
        const b=document.createElement('button');b.type='button';b.className=`token ${t.sign===-1?'negative':'positive'}${t.id===selected?' selected':''}${used.has(t.id)?' used':''}`;
        b.disabled=finished;b.setAttribute('aria-pressed',String(t.id===selected));
        b.setAttribute('aria-label',`${LANES[lane]} ${depth===1?'near':'far'} charge ${t.sign===1?'positive':'negative'} strength ${t.strength}${t.held?' previously held':''}`);
        b.textContent=`${line(t.sign,t.strength)} ${t.held?'⏸':''}`;
        b.addEventListener('click',()=>{selected=t.id;render();});band.append(b);
      }
      laneEl.append(band);
    }
    $('board').append(laneEl);
  }
  $('edit-count').textContent=`${edits.length} / 2`;
  const t=upcoming(s),valid=!!t&&!used.has(selected)&&edits.length<2&&!finished;
  $('selected').textContent=t?`${LANES[t.lane]} · ${t.depth===2?'FAR':'NEAR'} · ${tokenText(t)}${used.has(t.id)?' (already assigned an edit)':''}`:'Tap a charge on the board';
  $('shift-left').disabled=!valid||t.lane===0;
  $('shift-right').disabled=!valid||t.lane===2;
  $('hold').disabled=!valid||t.held;
  $('damp').disabled=!valid||edits.filter(e=>e.kind==='DAMP').length>=game.coolant;
  $('clear-edits').disabled=finished||!edits.length;
  $('planned-edits').textContent=edits.length?edits.map((e,i)=>`${i+1}. ${e.kind}${e.kind==='SHIFT'?(e.delta===-1?' LEFT':' RIGHT'):''} ${e.token}`).join(' · '):'No edits planned.';
  const sel=$('build'),value=build===null?'':String(build);sel.replaceChildren();
  const no=new Option('No construction','');sel.add(no);
  for(let i=0;i<3;i++){
    const active=s.levels[i],offline=game.outages[i],eligible=game.power>=2&&active<2&&!offline;
    const op=new Option(`${SYSTEMS[i]}: level ${active} → ${active+1}${offline?' (offline)':!eligible?' (unavailable)':''}`,String(i));op.disabled=finished||!eligible;sel.add(op);
  }
  if(value!==''&&!Array.from(sel.options).some(o=>o.value===value&&!o.disabled))build=null;
  sel.value=build===null?'':String(build);sel.disabled=finished;
  $('systems').replaceChildren();
  const effects=[s.levels[0]===2?'Bonus Power on any matched lane':'Bonus Power from matched Left charges', 'Absorb 1 damage per level each round', s.levels[2]===2?'Free Shift of any charge':'Free Shift of a FAR charge'];
  SYSTEMS.forEach((name,i)=>{
    const div=document.createElement('div');div.className='system';
    const left=document.createElement('span');left.textContent=`${name} · ${s.levels[i]}/2`;
    const right=document.createElement('span');right.className=game.outages[i]?'offline':'desc';right.textContent=game.outages[i]?'OFFLINE this round':game.pending===i?'UPGRADE ACTIVE NOW':effects[i];
    div.append(left,right);$('systems').append(div);
  });
  const yard=s.levels[2]>0&&!game.outages[2]&&!finished;
  $('yard-details').hidden=!yard;
  const freeToken=$('free-token'),oldFree=free?.token||'';freeToken.replaceChildren();freeToken.add(new Option('No free Shift',''));
  if(yard){for(const t of s.board.filter(t=>s.levels[2]===2||t.depth===2))freeToken.add(new Option(`${LANES[t.lane]} ${tokenText(t)}`,t.id));}
  if(oldFree&&!Array.from(freeToken.options).some(o=>o.value===oldFree))free=null;
  freeToken.value=free?.token||'';$('free-dir').value=String(free?.delta??-1);
  freeToken.disabled=!yard;$('free-dir').disabled=!yard;
  $('resolve').disabled=finished;$('hint').disabled=finished;
  $('resolve').textContent=finished?'Match complete':'Resolve round →';
  const report=$('report');if(lastReport){report.hidden=false;report.className=`report ${finished?(game.finished==='WIN'?'success':'failure'):''}`;report.replaceChildren();
    const h=document.createElement('h3');h.textContent=lastReport.title;report.append(h);
    for(const p of lastReport.lines){const el=document.createElement('p');el.textContent=p;report.append(el);}
  }else report.hidden=true;
}
function addAction(kind,delta){
  const s=current(),t=upcoming(s);if(!t||edits.length>=2||edits.some(a=>a.token===t.id))return;
  edits.push({kind,token:t.id,...(kind==='SHIFT'?{delta}:{})});selected=null;clearError();render();
}
function resolve(){
  clearError();const round=game.round;
  try{
    const s=step(game,plan()),h=s.history.at(-1);
    game=s;edits=[];build=null;free=null;selected=null;
    const matched=h.matched.reduce((a,b)=>a+b,0),raw=h.raw.reduce((a,b)=>a+b,0);
    const lines=[`Collisions made ${matched} Power${h.bonus?` + ${h.bonus} Dynamo bonus`:''}. ${raw} raw leakage; Aegis absorbed up to ${h.shield}; Hull lost ${h.damage}.`,
     `Hull ${h.hull} · Stored Power ${h.power} · Active upgrade levels ${h.levels.join(' / ')}.`,
     h.build!==null?`${SYSTEMS[h.build]} construction ordered. Its level activates at the START of the next round.`:'No construction this round.'];
    if(h.deadline)lines.push(`Deadline: ${h.deadline} additional Hull damage from unresolved charges.`);
    if(h.next_outages.some(Boolean))lines.push(`Warning: ${h.next_outages.map((x,i)=>x?SYSTEMS[i]:null).filter(Boolean).join(', ')} unavailable next round from lane leakage.`);
    if(game.finished==='WIN')lines.push('You completed two level-2 systems while keeping Hull above zero.');
    else if(game.finished==='LOSS_SYSTEMS')lines.push('Your Hull survived, but fewer than two level-2 systems were available at the deadline.');
    lastReport={title:game.finished?`Round ${round} · ${game.finished==='WIN'?'Victory':'Defeat'}`:`Round ${round} resolved`,lines};
    render();
  }catch(e){showError(e.message);}
}
function same(a,b){
  if(a===b)return true;
  if(a===null||b===null||typeof a!=='object'||typeof b!=='object')return false;
  if(Array.isArray(a)!==Array.isArray(b))return false;
  const ak=Object.keys(a),bk=Object.keys(b);
  return ak.length===bk.length&&ak.every(k=>Object.hasOwn(b,k)&&same(a[k],b[k]));
}
function hint(){
  const stepRecord=caseFile.example[game.round-1];if(!stepRecord){showError('No sample plan for this round.');return;}
  const actual={round:game.round,hull:game.hull,power:game.power,coolant:game.coolant,levels:game.levels,pending:game.pending,outages:game.outages,board:game.board};
  if(!same(actual,stepRecord.before)){
    showError('That sample plan only applies to its original sequence. You have changed the state: use your own judgement from here.');return;
  }
  const p=stepRecord.plan;edits=clone(p.edits||[]);build=p.build??null;free=p.free??null;selected=null;clearError();render();
  $('status').textContent='Example plan loaded. You can revise it or press RESOLVE. Try to understand why these edits and investments were chosen.';
}
async function init(){
  try{
    const resp=await fetch('./site/play-cases.json',{cache:'no-store'});if(!resp.ok)throw Error('Example scenarios did not load');
    const data=await resp.json();if(data.ruleset!=='redesign/phase3-storm-engine'||data.games.length!==3)throw Error('Scenario data is not verified');
    cases=data.games;$('scenario').replaceChildren();for(const c of cases)$('scenario').add(new Option(c.title,c.id));start();
  }catch(e){$('status').textContent=`Unable to start: ${e.message}. Check that the GitHub Pages deployment completed.`;showError(e.message);}
}
$('scenario').addEventListener('change',start);$('restart').addEventListener('click',start);
$('shift-left').addEventListener('click',()=>addAction('SHIFT',-1));$('shift-right').addEventListener('click',()=>addAction('SHIFT',1));
$('hold').addEventListener('click',()=>addAction('HOLD'));$('damp').addEventListener('click',()=>addAction('DAMP'));
$('clear-edits').addEventListener('click',()=>{edits=[];selected=null;render();});
$('build').addEventListener('change',e=>{build=e.target.value===''?null:Number(e.target.value);render();});
$('free-token').addEventListener('change',e=>{free=e.target.value?{token:e.target.value,delta:Number($('free-dir').value)}:null;render();});
$('free-dir').addEventListener('change',e=>{if(free)free.delta=Number(e.target.value);render();});
$('hint').addEventListener('click',hint);$('resolve').addEventListener('click',resolve);
init();
