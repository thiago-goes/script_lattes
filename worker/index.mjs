/* Shared GT records behind the current Sites access policy.
 * Visitor identity is supplied by Sites, never by browser form fields.
 * Reading follows Site visibility; writing is restricted to its responsible owner.
 */
const json=(body,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
export function signature(p){return JSON.stringify(p.registros_origem.map(r=>[r.docente_id,r.categoria_lattes,r.subcategoria_lattes,r.ano,r.referencia_original]).sort((a,b)=>JSON.stringify(a)<JSON.stringify(b)?-1:JSON.stringify(a)>JSON.stringify(b)?1:0))}
function decode(row){return row?{...row,source_snapshot:JSON.parse(row.source_snapshot)}:null}
async function staticJson(env,request,path){const url=new URL(path,request.url);const response=await env.ASSETS.fetch(new Request(url));if(!response.ok)throw Error('Dados da publicação indisponíveis');return response.json()}
export default{
 async fetch(request,env){
  const url=new URL(request.url);
  if(!url.pathname.startsWith('/api/'))return env.ASSETS.fetch(request);
  if(url.pathname!='/api/reviews')return json({error:'Recurso não encontrado'},404);
  if(!env.DB)return json({error:'Armazenamento de revisões indisponível; nenhuma decisão foi salva.'},503);
  try{
   const canReview=!!request.headers.get('oai-authenticated-user-id')&&!!env.REVIEW_OWNER_EMAIL&&request.headers.get('oai-authenticated-user-email')?.toLowerCase()===env.REVIEW_OWNER_EMAIL.toLowerCase();
   if(request.method==='GET'){
    const result=await env.DB.prepare('SELECT * FROM production_reviews ORDER BY product_id').all();
    const history=url.searchParams.get('history')==='1'?await env.DB.prepare('SELECT * FROM production_review_history ORDER BY created_at,product_id,revision').all():null;
    return json({reviews:Object.fromEntries(result.results.map(r=>[r.product_id,decode(r)])),history:history?.results||null,can_review:canReview});
   }
   if(request.method!=='POST')return json({error:'Método não permitido'},405);
   if(!request.headers.get('oai-authenticated-user-id'))return json({error:'Entre no Site com sua conta para salvar uma revisão.'},401);
   if(!canReview)return json({error:'Somente o responsável pelo dashboard pode alterar as decisões do GT.'},403);
   if(request.headers.get('origin')&&request.headers.get('origin')!==url.origin)return json({error:'Origem não permitida'},403);
   if(request.headers.get('sec-fetch-site')==='cross-site')return json({error:'Abra a revisão dentro do dashboard.'},403);
   const text=await request.text();if(text.length>180000)return json({error:'Decisão excede o tamanho permitido.'},413);
   let input;try{input=JSON.parse(text)}catch{return json({error:'JSON inválido'},400)}
   const {product_id,action,category,kind,notes,evidence,source_signature,expected_revision}=input;
   if(!/^prod-[a-f0-9]{20}$/.test(product_id||'')||!['confirmed','pending','rejected','reverted'].includes(action)||!Number.isInteger(expected_revision)||expected_revision<0||typeof notes!=='string'||notes.length>12000||typeof evidence!=='string'||evidence.length>6000||typeof source_signature!=='string')return json({error:'Revise os campos da decisão.'},400);
   if(action!=='reverted'&&!notes.trim())return json({error:'Registre uma observação que fundamente a decisão.'},400);
   const [catalog,data]=await Promise.all([staticJson(env,request,'/catalogo-capes.json'),staticJson(env,request,'/qualificacao.json')]);
   if(!catalog[kind]||catalog[kind].grupo!==category)return json({error:'Categoria e tipo devem corresponder ao catálogo.'},400);
   const product=data.produtos.find(p=>p.produto_id===product_id);if(!product)return json({error:'O produto mudou ou não está na base publicada. Atualize a página.'},409);
   if(signature(product)!==source_signature)return json({error:'A fonte foi atualizada. Consulte o registro atual antes de decidir.'},409);
   const prior=await env.DB.prepare('SELECT revision FROM production_reviews WHERE product_id=?').bind(product_id).first();
   if(expected_revision!==(prior?.revision||0))return json({error:'A decisão foi alterada. Recarregue a revisão antes de salvar.'},409);
   const revision=expected_revision+1,stamp=new Date().toISOString(),actor=request.headers.get('oai-authenticated-user-id'),event=crypto.randomUUID();
   const snapshot=JSON.stringify({titulo:product.titulo_original,ano:product.ano,participacoes:product.participacoes,registros_origem:product.registros_origem.map(r=>({registro_id:r.registro_id,docente_id:r.docente_id,referencia_original:r.referencia_original,categoria_lattes:r.categoria_lattes,subcategoria_lattes:r.subcategoria_lattes}))});
   const payload=JSON.stringify({product_id,action,category,kind,notes:notes.trim(),evidence,source_signature,revision,source_snapshot:JSON.parse(snapshot),updated_at:stamp,actor});
   const results=await env.DB.batch([
    env.DB.prepare('INSERT INTO production_reviews (product_id,action,category,kind,notes,evidence,source_signature,source_snapshot,revision,updated_at,actor,event_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(product_id) DO UPDATE SET action=excluded.action,category=excluded.category,kind=excluded.kind,notes=excluded.notes,evidence=excluded.evidence,source_signature=excluded.source_signature,source_snapshot=excluded.source_snapshot,revision=excluded.revision,updated_at=excluded.updated_at,actor=excluded.actor,event_id=excluded.event_id WHERE production_reviews.revision=?').bind(product_id,action,category,kind,notes.trim(),evidence,source_signature,snapshot,revision,stamp,actor,event,expected_revision),
    env.DB.prepare('INSERT INTO production_review_history (product_id,revision,payload,created_at,actor) SELECT product_id,revision,?,?,actor FROM production_reviews WHERE product_id=? AND event_id=?').bind(payload,stamp,product_id,event)
   ]);
   if(!results[0].meta.changes)return json({error:'Outra decisão foi salva antes desta. Recarregue a revisão para comparar.'},409);
   return json({review:decode(await env.DB.prepare('SELECT * FROM production_reviews WHERE product_id=?').bind(product_id).first())});
  }catch{return json({error:'Não foi possível acessar as revisões. Nenhuma alteração deve ser considerada salva; tente novamente.'},503)}
 }
};
