// Presentation ONLY: every combination was executed by the Python research reducer.
// Never pretend that these precomputed outcomes are live multiplayer gameplay.
const stationNames={nav:'Navigation · shift drifter',control:'Control · damp threat',engineer:'Engineering · build a system',dispatch:'Dispatch · cover Right'};
const $=id=>document.getElementById(id);
let dataset=null;
let assignments=['nav','engineer','engineer','dispatch'];
const orderText=(name,detail)=>{
  if(name==='nav')return 'SHIFT drifter toward Center';
  if(name==='control')return 'DAMP the Right-lane threat';
  if(name==='engineer')return 'Build '+(detail.build===1?'Aegis':'Dynamo');
  return 'COVER the Right-lane breach';
};
function show(){
  if(!dataset)return;
  const name=$('scenario').value;
  const record=dataset.scenarios[name];
  const state=record.state;
  $('intro').textContent=record.intro;
  $('initial-hull').textContent=state.hull;
  $('initial-power').textContent=state.power;
  $('initial-coolant').textContent=state.coolant;
  $('initial-levels').textContent=state.levels.join(' · ');
  const key=assignments.join('|');
  const outcome=record.outcomes[key];
  const valid=outcome.valid;
  $('legality').textContent=valid?'LEGAL PLAN':'CANNOT EXECUTE';
  $('result-stats').hidden=!valid;
  const verdict=$('verdict');verdict.className='verdict';
  if(!valid){verdict.textContent='Commitments conflict';verdict.classList.add('bad');$('reason').textContent=outcome.reason;}
  else{
    let message='Round resolves';
    if(outcome.following_finish==='WIN')message='Victory after the following round';
    else if(outcome.following_finish==='LOSS_HULL')message='Settlement destroyed';
    else if(outcome.following_finish==='LOSS_SYSTEMS')message='Settlement survives, objective fails';
    if(outcome.following_finish==='WIN'){}else if(outcome.following_finish)verdict.classList.add('bad');else verdict.classList.add('warn');
    verdict.textContent=message;
    $('reason').textContent=name==='crisis'?'Outcome includes an eighth-round no-action follow-up for victory validation.':'Midgame outcomes show one resolved round; the final outcome is intentionally unknown.';
    $('hull').textContent=outcome.hull;
    $('power').textContent=outcome.power;
    $('blocked').textContent=outcome.blocked;
    $('pending').textContent=outcome.pending===null?'None':['Dynamo','Aegis','Switchyard'][outcome.pending];
  }
  const orders=$('orders');orders.replaceChildren();
  if(valid){
    for(const [name,action] of Object.entries(outcome.orders)){
      const chip=document.createElement('span');chip.textContent=orderText(name,action);orders.append(chip);
    }
    if(!orders.childNodes.length)orders.textContent='No active duty orders';
  }else orders.textContent='None; invalid plans are not applied.';
  const audit=dataset.audit[name];
  $('audit').textContent=`Exhaustive audit: ${audit.legal} of ${audit.total_seat_combinations} four-seat allocations are legal; ${audit.unique_end_states} distinct outcomes. ${audit.win_loss_changing_changes} of ${audit.legal_single_seat_changes} legal one-seat alternatives change a win/loss result (counting both directions).`;
}
async function init(){
  try{
    const response=await fetch('./site/crew-lab-data.json',{cache:'no-cache'});
    if(!response.ok)throw Error(`HTTP ${response.status}`);
    dataset=await response.json();
    if(dataset.ruleset!=='redesign/phase7-commitment-lab')throw Error('Unknown research data');
    const seats=$('seats');
    for(let i=0;i<4;i++){
      const container=document.createElement('div');container.className='seat';
      const label=document.createElement('label');label.textContent=`Seat ${i+1}`;
      label.htmlFor=`seat-${i}`;
      const select=document.createElement('select');select.id=`seat-${i}`;
      for(const [key,title] of Object.entries(stationNames)){
        const option=document.createElement('option');option.value=key;option.textContent=title;select.append(option);
      }
      select.value=assignments[i];select.addEventListener('change',()=>{assignments[i]=select.value;show();});
      container.append(label,select);seats.append(container);
    }
    $('scenario').addEventListener('change',show);
    function preset(choices){assignments=choices;choices.forEach((value,i)=>$(`seat-${i}`).value=value);show();}
    $('spread').addEventListener('click',()=>preset(['nav','control','engineer','dispatch']));
    $('support').addEventListener('click',()=>preset(['nav','engineer','engineer','dispatch']));
    show();
  }catch(error){$('verdict').textContent='Research data unavailable';$('reason').textContent=error.message;}
}
init();
