/* Loopback-only QA server: local SQLite implements the D1 interface.
 * The development identity below is never imported by the production Worker.
 */
import http from 'node:http';
import {DatabaseSync} from 'node:sqlite';
import {readFile,readdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import worker from '../worker/index.mjs';
export const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
export function database(filename=':memory:'){
 const db=new DatabaseSync(filename);
 const prepare=sql=>{let values=[];return{bind(...args){values=args;return this},async all(){return{results:db.prepare(sql).all(...values)}},async first(){return db.prepare(sql).get(...values)||null},execute(){const r=db.prepare(sql).run(...values);return{meta:{changes:Number(r.changes)}}}}};
 return{prepare,async batch(statements){db.exec('BEGIN');try{const results=statements.map(s=>s.execute());db.exec('COMMIT');return results}catch(e){db.exec('ROLLBACK');throw e}},exec:sql=>db.exec(sql),close:()=>db.close()};
}
export async function migrate(db){for(const file of (await readdir(path.join(root,'drizzle'))).filter(f=>f.endsWith('.sql')).sort())db.exec(await readFile(path.join(root,'drizzle',file),'utf8'))}
export function assets(directory){const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.csv':'text/csv; charset=utf-8','.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.zip':'application/zip'};return{async fetch(request){const url=new URL(request.url),relative=url.pathname==='/'?'index.html':decodeURIComponent(url.pathname.slice(1));const file=path.resolve(directory,relative);if(!file.startsWith(directory+path.sep))return new Response('Forbidden',{status:403});try{return new Response(await readFile(file),{headers:{'Content-Type':types[path.extname(file)]||'application/octet-stream'}})}catch{return new Response('Not found',{status:404})}}}}
export async function serve({port=0,dbFile=':memory:',migrations=true}={}){
 const DB=database(dbFile);if(migrations)await migrate(DB);const env={DB,REVIEW_OWNER_EMAIL:'local-reviewer@sites.test',ASSETS:assets(path.join(root,'dist'))};
 const server=http.createServer(async(req,res)=>{try{
  if(req.url==='/embedded'){res.setHeader('Content-Type','text/html');res.end('<iframe style="width:1400px;height:1100px" src="/?view=qualified" sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"></iframe>');return}
  const chunks=[];for await(const chunk of req)chunks.push(chunk);const headers=new Headers(req.headers);headers.set('oai-authenticated-user-id','local_qa_reviewer');headers.set('oai-authenticated-user-email','local-reviewer@sites.test');
  const request=new Request('http://127.0.0.1:'+server.address().port+req.url,{method:req.method,headers,body:['GET','HEAD'].includes(req.method)?undefined:Buffer.concat(chunks)});const response=await worker.fetch(request,env);res.writeHead(response.status,Object.fromEntries(response.headers));res.end(Buffer.from(await response.arrayBuffer()))
 }catch(e){res.writeHead(500);res.end(String(e))}});
 await new Promise(resolve=>server.listen(port,'127.0.0.1',resolve));return{server,DB,url:'http://127.0.0.1:'+server.address().port,close:()=>new Promise(resolve=>server.close(()=>{DB.close();resolve()}))};
}
if(process.argv[1]===fileURLToPath(import.meta.url)){const s=await serve({port:Number(process.argv[2]||0),dbFile:process.argv[3]||':memory:',migrations:process.argv[4]!=='existing'});console.log(s.url);process.on('SIGTERM',()=>s.close().then(()=>process.exit()))}
