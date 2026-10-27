/* Static research exhibit, not authoritative production gameplay. */
const $ = id => document.getElementById(id);
const climate = $('climate');
const strategy = $('strategy');
const seed = $('seed');
const round = $('round');
let data = null;
const names = ['Dynamo', 'Aegis', 'Switchyard'];
const questions = {
  harvest: 'Do we exploit predictable collisions to expand production, or spend the same power on protection against the occasional unmatched charge?',
  fracture: 'When charges land in the wrong lanes, is it better to improve movement options, invest in production, or absorb damage through Aegis?',
  siege: 'Should we invest early in protection to preserve hull, even if that delays the infrastructure needed to win by round eight?'
};
function el(tag,className,text){
  const node=document.createElement(tag);
  if(className)node.className=className;
  if(text!==undefined)node.textContent=String(text);
  return node;
}
function render(){
  if(!data)return;
  const kind=climate.value, key=seed.value, plan=strategy.value;
  const game=data.examples[kind][key][plan];
  const idx=Math.max(0,Math.min(game.snapshots.length-1,Number(round.value)-1));
  const frame=game.snapshots[idx];
  const final=idx===game.snapshots.length-1;
  round.max=String(game.snapshots.length);
  round.value=String(idx+1);
  $('round-label').textContent=`${idx+1} / ${game.snapshots.length}`;
  $('hull').textContent=Math.max(0,frame.hull);
  $('power').textContent=frame.power;
  $('coolant').textContent=frame.coolant;
  $('climate-desc').textContent=data.climates[kind].pitch;
  $('discussion-prompt').textContent=questions[kind];
  const status=$('play-status');status.className='play-status';
  if(final){
    const won=game.outcome==='WIN';
    status.textContent=won?'VICTORY — two settlement systems restored':'DEFEAT — '+game.outcome.replace('LOSS_','').toLowerCase().replace('_',' ');
    status.classList.add(won?'win':'lose');
  }else status.textContent=`Round ${frame.round} completed · ${game.rounds-frame.round} rounds remaining`;
  const systems=$('systems');systems.replaceChildren();
  names.forEach((name,i)=>{
    const box=el('div','system'+(frame.outages[i]?' off':''));
    box.append(el('b','',name),el('span','',frame.levels[i]+'/2 '+(frame.outages[i]?'OFFLINE':frame.pending===i?'PENDING':'BUILT')));
    systems.append(box);
  });
  const board=$('board');board.replaceChildren();
  ['LEFT','CENTER','RIGHT'].forEach((laneName,lane)=>{
    const row=el('div','lane');row.append(el('div','lane-name',laneName));
    [2,1,0].forEach(depth=>{
      const cell=el('div','cell');
      const charges=frame.board.filter(t=>t.lane===lane&&t.depth===depth);
      if(!charges.length)cell.append(el('span','empty','·'));
      for(const t of charges)cell.append(el('span','charge '+(t.sign===1?'pos':'neg'),`${t.sign===1?'+':'−'}${t.strength}`));
      row.append(cell);
    });
    board.append(row);
  });
  $('event').textContent=`${frame.matched.reduce((a,b)=>a+b,0)} collision energy · ${frame.damage} hull damage${frame.deadline?' · '+frame.deadline+' final unresolved-charge damage':''}${frame.plan.build===undefined||frame.plan.build===null?'': ' · upgrading '+names[frame.plan.build]}`;
  const edits=$('edits');edits.replaceChildren();
  if(!frame.plan.edits.length)edits.append(el('span','', 'No paid charge edits'));
  else for(const action of frame.plan.edits)edits.append(el('span','',`${action.kind} ${action.token}${action.delta?' '+(action.delta>0?'→':'←'):''}`));
  $('previous').disabled=idx===0;
  $('next').disabled=final;
  const stats=data.audit.sets.holdout.profiles[kind];
  const comparison=$('comparison');comparison.replaceChildren();
  Object.entries(data.strategies).forEach(([strategyKey,label])=>{
    const box=el('div','comparison-row');
    const left=el('div');left.append(el('span','',label));
    const track=el('div','track');const fill=el('div','fill');
    fill.style.width=(stats.wins[strategyKey]/data.audit.sets.holdout.n*100)+'%';
    track.append(fill);left.append(track);box.append(left,el('b','',`${stats.wins[strategyKey]}/${data.audit.sets.holdout.n}`));comparison.append(box);
  });
  $('set-note').textContent=`Across these 40 holdout storms: ${stats.different_winning_paths} allow ≥2 of the 3 tested upgrade orders to win; ${stats.all_lose} defeat all three. The bot does not optimize Switchyard's free move.`;
}
for(const control of [climate,strategy,seed])control.addEventListener('change',()=>{round.value='1';render();});
round.addEventListener('input',render);
$('previous').addEventListener('click',()=>{round.value=String(Number(round.value)-1);render();});
$('next').addEventListener('click',()=>{round.value=String(Number(round.value)+1);render();});
try{
  const response=await fetch('./site/strategy-lab-data.json',{cache:'no-store'});
  if(!response.ok)throw Error(`HTTP ${response.status}`);
  data=await response.json();
  if(data.ruleset!=='redesign/phase8-scenario-exhibit')throw Error('Unrecognized research dataset');
  render();
}catch(error){$('play-status').textContent='Could not load verified scenario data: '+String(error.message||error);}
