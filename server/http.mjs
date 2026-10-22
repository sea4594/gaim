/** Minimal HTTP + Server-Sent Events live room service. No external packages.
 * TLS termination required when exposed beyond localhost.
 */
import http from 'node:http';
import {randomBytes,createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {RoomStore,RoomError} from '../dist/src/rooms.js';
const scenarios=JSON.parse(readFileSync(new URL('../contracts/scenarios.v0.1.json',import.meta.url))).scenarios;
const token=()=>randomBytes(24).toString('base64url');
const hash=s=>createHash('sha256').update(s).digest('hex');
function json(res,status,data) {
  if(res.headersSent)return;
  res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff'});
  res.end(JSON.stringify(data));
}
async function readJSON(req){
  let total=0;const chunks=[];
  for await(const chunk of req){total+=chunk.length;if(total>32768)throw new RoomError('BAD_PAYLOAD','payload too large');chunks.push(chunk);}
  try{const val=JSON.parse(Buffer.concat(chunks).toString('utf8'));if(!val||typeof val!=='object'||Array.isArray(val))throw 0;return val;}
  catch{throw new RoomError('BAD_PAYLOAD','invalid JSON object');}
}
function requireFields(o,keys){if(Object.keys(o).sort().join(',')!==keys.sort().join(','))throw new RoomError('BAD_PAYLOAD','unexpected fields');}
const codeFormat=/^[A-Z2-9]{8}$/;
const idFormat=/^[0-9a-f]{24}$/;
export function createApp({now=()=>Date.now(),durationMs=75000}={}){
  const store=new RoomStore(scenarios,now,durationMs);
  const activeStreams=new Map();
  const ipRate=new Map();
  function identity(req){const h=req.headers.authorization; if(typeof h!=='string'||!/^Bearer [A-Za-z0-9_-]{32,}$/.test(h))throw new RoomError('UNAUTHORIZED','bearer credential required');return hash(h.slice(7));}
  function roomId(id){if(typeof id!=='string'||!idFormat.test(id))throw new RoomError('BAD_PAYLOAD','bad room id');return id;}
  function notifyStream(snap,res){if(!res.destroyed)res.write(`event: snapshot\ndata: ${JSON.stringify(snap)}\n\n`);}
  const server=http.createServer(async(req,res)=>{
    try {
      // Basic abuse controls. For production: also limit at TLS proxy.
      const ip=req.socket.remoteAddress??'unknown';const t=now();
      const rate=ipRate.get(ip)??{start:t,count:0};
      if(t-rate.start>=60000){rate.start=t;rate.count=0;}
      ipRate.set(ip,rate);
      if(++rate.count>300)throw new RoomError('RATE_LIMITED','request limit');
      const url=new URL(req.url??'/',`http://${req.headers.host??'localhost'}`);
      if(req.method==='GET'&&url.pathname==='/health'){json(res,200,{ok:true,ruleset:'charge-loom/v0.1'});return;}
      if(req.method==='POST'&&url.pathname==='/api'){
        const data=await readJSON(req);
        if(data.type==='CREATE_ROOM'){
          requireFields(data,['type','requestId','ruleset','scenarioId']);
          if(data.ruleset!=='charge-loom/v0.1')throw new RoomError('UNSUPPORTED_RULESET','unknown ruleset');
          if(typeof data.requestId!=='string'||!/^[A-Za-z0-9_-]{8,80}$/.test(data.requestId))throw new RoomError('BAD_PAYLOAD','invalid request ID');
          const id=randomBytes(12).toString('hex');const code=randomBytes(6).toString('base64').replace(/[^A-Z2-9]/gi,'').toUpperCase().replace(/[01IO]/g,'Q').slice(0,8).padEnd(8,'X');
          const secret=token();const result=store.create(id,code,data.scenarioId,hash(secret));
          json(res,200,{...result,roomCode:code,roomId:id,resumeSecret:secret,seat:0});return;
        }
        if(data.type==='JOIN_ROOM'){
          requireFields(data,['type','requestId','roomCode']);
          if(typeof data.requestId!=='string'||!/^[A-Za-z0-9_-]{8,80}$/.test(data.requestId)||typeof data.roomCode!=='string'||!codeFormat.test(data.roomCode))throw new RoomError('BAD_PAYLOAD','invalid join request');
          const secret=token();const result=store.join(data.roomCode,hash(secret));
          json(res,200,{...result,roomId:result.snapshot.roomId,seat:result.snapshot.seats.length-1,resumeSecret:secret});return;
        }
        const identityHash=identity(req);const id=roomId(data.roomId);
        if(data.type==='RESUME'){
          requireFields(data,['type','roomId']);
          const result=store.resume(id,identityHash);
          json(res,200,result);return;
        }
        if(data.type==='GET_SNAPSHOT'){
          requireFields(data,['type','roomId']);json(res,200,store.snapshot(id,identityHash));return;
        }
        const {roomId:removed,...command}=data;
        const result=store.command(id,identityHash,command);
        json(res,200,result);return;
      }
      if(req.method==='GET'&&url.pathname==='/events'){
        const id=roomId(url.searchParams.get('roomId'));const credential=identity(req);
        const existing=activeStreams.get(id+':'+credential);
        if(existing)existing.end(); // reconnect invalidates old stream
        store.snapshot(id,credential);
        res.writeHead(200,{'content-type':'text/event-stream','cache-control':'no-cache, no-transform','connection':'keep-alive','x-accel-buffering':'no'});
        activeStreams.set(id+':'+credential,res);
        notifyStream(store.snapshot(id,credential).snapshot,res);
        const unsubscribe=store.subscribe(id,credential,snap=>notifyStream(snap,res));
        const heartbeat=setInterval(()=>{if(!res.destroyed)res.write(': ping\n\n');},15000);
        req.on('close',()=>{
          clearInterval(heartbeat);unsubscribe();
          if(activeStreams.get(id+':'+credential)===res){activeStreams.delete(id+':'+credential);store.disconnect(id,credential);}
        });
        return;
      }
      json(res,404,{error:'NOT_FOUND'});
    } catch(e){
      const code=e instanceof RoomError?e.code:'SERVER_ERROR';
      const status=code==='RATE_LIMITED'?429:code==='UNAUTHORIZED'?401:code==='SERVER_ERROR'?500:409;
      if(code==='SERVER_ERROR')console.error('Unexpected server error',e);
      json(res,status,{error:code,message:e instanceof Error&&code!=='SERVER_ERROR'?e.message:'server failure'});
    }
  });
  const clock=setInterval(()=>store.tick(),200);clock.unref();
  const close=()=>new Promise((resolve,reject)=>{clearInterval(clock);for(const s of activeStreams.values())s.end();server.close(err=>err?reject(err):resolve());});
  return {server,store,close};
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
  const host=process.env.GAIM_HOST??'127.0.0.1';const port=Number(process.env.GAIM_PORT??8787);
  if(host!=='127.0.0.1'&&host!=='::1'&&process.env.GAIM_TLS_TERMINATED!=='1'){
    console.error('Refusing public binding without GAIM_TLS_TERMINATED=1 (HTTPS reverse proxy required)');process.exit(1);
  }
  if(!Number.isSafeInteger(port)||port<1||port>65535)throw Error('invalid port');
  const {server}=createApp();server.listen(port,host,()=>console.log(`GAIM headless server http://${host}:${port}`));
}
