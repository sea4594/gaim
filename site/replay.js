// Read-only mechanics display. Canonical verified states are stored in the repo.
// Do not import research rules or network/server logic into the Pages preview.
const byId = (id) => document.getElementById(id);
let traces = [];
let currentTrace = null;
let frame = 0;

function text(id, value) { byId(id).textContent = String(value); }
function describe(action) {
  const [verb, id, dir] = action;
  if (verb === 'shift') return `SHIFT #${id} ${dir < 0 ? '←' : '→'}`;
  if (verb === 'hold') return `HOLD #${id}`;
  if (verb === 'damp') return `DAMP #${id}`;
  return String(verb).toUpperCase();
}
function draw() {
  if (!currentTrace) return;
  const view = currentTrace.views[frame];
  text('round', `${view.completedRound} / 9`);
  text('hull', `${Math.max(0,view.hull)} / 7`);
  text('coolant', `${view.coolant} / 3`);
  text('power', `${view.capacitors.reduce((a,b)=>a+b,0)} / 8`);
  for (let lane = 0; lane < 3; lane++) {
    const column = byId(`lane-${lane}`);
    column.replaceChildren();
    // Golden traces store band 2=FAR and 0=NOW; render FAR on top.
    for (const band of [2,1,0]) {
      const cell = document.createElement('div');
      cell.className = 'cell';
      cell.setAttribute('aria-label', `${['Left','Center','Right'][lane]} lane, ${['Now','Soon','Far'][band]}`);
      const tokens = view.charges.filter(c => c.lane===lane && c.band===band);
      if (!tokens.length) {
        const empty=document.createElement('span'); empty.className='empty'; empty.textContent='·'; cell.append(empty);
      }
      for (const token of tokens) {
        const chip=document.createElement('span');
        chip.className=`charge ${token.polarity==='POSITIVE'?'plus':'minus'}`;
        chip.textContent=`${token.polarity==='POSITIVE'?'+':'−'}${token.strength}`;
        chip.title=`Charge ${token.id}${token.alreadyHeld?' · held once':''}`;
        if (token.alreadyHeld) {
          const mark=document.createElement('small'); mark.textContent='HELD'; chip.append(mark);
        }
        cell.append(chip);
      }
      column.append(cell);
    }
    const amount = view.capacitors[lane];
    text(`cap-${lane}`, `${amount} / 3`);
    byId(`fill-${lane}`).style.setProperty('--fill', `${amount/3*100}%`);
  }
  const actions = frame===0 ? [] : currentTrace.actions[frame-1];
  const orders=byId('orders'); orders.replaceChildren();
  text('edits-heading', frame===0?'PLANNED EDITS':'EDITS APPLIED IN THIS ROUND');
  if (!actions.length) orders.textContent=frame===0?'Start of session: no edits applied.':'No edits this round.';
  for (const action of actions) {
    const chip=document.createElement('span');chip.className='order-chip';chip.textContent=describe(action);orders.append(chip);
  }
  const upcoming=view.nextWave||[];
  const forecast=byId('next-wave');forecast.replaceChildren();
  if (!upcoming.length) forecast.textContent='No additional incoming wave';
  for (const wave of upcoming) {
    const chip=document.createElement('span');chip.className='order-chip';
    chip.textContent=`${['L','C','R'][wave.lane]} ${wave.polarity==='POSITIVE'?'+':'−'}${wave.strength}`;
    forecast.append(chip);
  }
  text('outcome',view.outcome==='win'?'✓ Victory':view.outcome?'Defeat':frame===0?'Start of match':`Round ${frame} resolved`);
  byId('previous').disabled=frame===0;
  byId('next').disabled=frame===currentTrace.views.length-1;
}
function selectTrace(id) {
  currentTrace=traces.find(t=>t.scenarioId===id)||traces[0]; frame=0; draw();
}
async function initialize() {
  try {
    const response=await fetch('./contracts/golden-traces.v0.1.json',{cache:'no-cache'});
    if (!response.ok) throw new Error(`Replay file unavailable (${response.status})`);
    const data=await response.json();
    if (data.ruleset!=='charge-loom/v0.1'||!Array.isArray(data.traces)||!data.traces.length) throw new Error('Unexpected replay format');
    traces=data.traces;
    const select=byId('scenario');select.replaceChildren();
    for (const trace of traces) {
      const option=document.createElement('option');option.value=trace.scenarioId;option.textContent=trace.scenarioId.replace('verified-','Verified seed ');select.append(option);
    }
    select.addEventListener('change',()=>selectTrace(select.value));
    byId('previous').addEventListener('click',()=>{if(frame>0){frame--;draw();}});
    byId('next').addEventListener('click',()=>{if(frame<currentTrace.views.length-1){frame++;draw();}});
    document.addEventListener('keydown',event=>{
      if (event.target instanceof HTMLElement && ['SELECT','BUTTON','INPUT'].includes(event.target.tagName))return;
      if (event.key==='ArrowLeft' && frame>0){frame--;draw();}
      if (event.key==='ArrowRight' && frame<currentTrace.views.length-1){frame++;draw();}
    });
    selectTrace(traces[0].scenarioId);
  } catch (error) {
    text('outcome','Replay unavailable');
    text('orders',`${error.message}. Source remains available in the repository.`);
    byId('previous').disabled=true;byId('next').disabled=true;
  }
}
initialize();
