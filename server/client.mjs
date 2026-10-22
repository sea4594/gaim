/** CLI client for headless remote co-op. Credentials remain in local process.
 * Usage: node server/client.mjs create verified-3; join ABCDEFGH; resume ROOM_ID TOKEN
 * Or use: snapshot ROOM_ID TOKEN | ready ROOM_ID TOKEN true | start ROOM_ID TOKEN
 *         edit ROOM_ID TOKEN SLOT 'JSON_EDIT' | clear ROOM_ID TOKEN SLOT
 *         watch ROOM_ID TOKEN
 */
const [, ,verb,...args]=process.argv;
const endpoint=process.env.GAIM_URL??'http://127.0.0.1:8787';
if(!verb){console.error('Commands: create, join, resume, snapshot, ready, start, edit, clear, watch');process.exit(2);}
let data,secret;
const requestId=()=>globalThis.crypto.randomUUID().replaceAll('-','');
if(verb==='create')data={type:'CREATE_ROOM',requestId:requestId(),ruleset:'charge-loom/v0.1',scenarioId:args[0]??'verified-3'};
else if(verb==='join')data={type:'JOIN_ROOM',requestId:requestId(),roomCode:args[0]};
else if(verb==='watch'){
  const [roomId,token]=args;
  const response=await fetch(`${endpoint}/events?roomId=${encodeURIComponent(roomId)}`,{headers:{authorization:`Bearer ${token}`}});
  if(!response.ok)throw Error(await response.text());
  for await(const chunk of response.body)process.stdout.write(Buffer.from(chunk).toString('utf8'));
  process.exit(0);
} else {
  const [roomId,token]=args;secret=token;
  if(verb==='resume')data={type:'RESUME',roomId};
  if(verb==='snapshot')data={type:'GET_SNAPSHOT',roomId};
  if(['start','ready','edit','clear'].includes(verb)){
    const snapshot=await fetch(`${endpoint}/api`,{method:'POST',headers:{'content-type':'application/json',authorization:`Bearer ${secret}`},body:JSON.stringify({type:'GET_SNAPSHOT',roomId})});
    const result=await snapshot.json();if(!snapshot.ok)throw Error(JSON.stringify(result));
    const common={roomId,requestId:requestId(),expectedRevision:result.revision};
    if(verb==='start')data={...common,type:'START_GAME'};
    if(verb==='ready')data={...common,type:'SET_READY',ready:(args[2]??'true')==='true'};
    if(verb==='edit')data={...common,type:'SET_EDIT',slot:Number(args[2]),action:JSON.parse(args[3])};
    if(verb==='clear')data={...common,type:'SET_EDIT',slot:Number(args[2]),action:null};
  }
}
if(!data)throw Error('invalid arguments');
const response=await fetch(`${endpoint}/api`,{method:'POST',headers:{'content-type':'application/json',...(secret?{authorization:`Bearer ${secret}`}:{})},body:JSON.stringify(data)});
const body=await response.json();console.log(JSON.stringify(body,null,2));if(!response.ok)process.exit(1);
