/* Pure diagnostic calculations shared by browser and consistency tests. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.AUDAnalysis=factory()})(typeof globalThis!=='undefined'?globalThis:this,()=>{
'use strict';
const POT='Potencialmente qualificada',INC='Enquadramento incerto',NONE='Sem enquadramento identificado';
const kinds={artigo:'Artigos em periódicos',livro:'Livros',capitulo:'Capítulos',anais:'Trabalhos completos em anais',resumo_expandido:'Resumos expandidos (auditoria)',resumo:'Resumos simples (auditoria)',apresentacao:'Apresentações (auditoria)',outro:'Outros bibliográficos (auditoria)'};
function available(p,year){return p.status_coleta==='coletado'&&Number.isInteger(p.cobertura_inicio)&&Number.isInteger(p.cobertura_fim)&&year>=p.cobertura_inicio&&year<=p.cobertura_fim}
function defaults(d){return{start:d.config.periodo_padrao.inicio,end:d.config.periodo_padrao.fim,personIds:[],category:'',biblioTypes:[...d.config.tipos_bibliograficos_padrao],recentEnd:d.config.ano_referencia_recente,minimum:d.config.minimo_candidatos_gt,concentration:d.config.limite_concentracao_gt_percentual,sort:'name',direction:'asc',reviewMode:'automatic'}}
function inScenario(p,f){return(!f.category||p.grande_categoria===f.category)&&(p.grande_categoria!=='bibliografica'||f.biblioTypes.includes(p.tipo_bibliografico))}
function analyze(d,filters){
 const f={...defaults(d),...filters};
 if(!Number.isInteger(f.start)||!Number.isInteger(f.end)||f.start>f.end||f.start<1900||f.end>2100||!Number.isInteger(f.recentEnd))throw Error('Informe um intervalo de anos válido.');
 const years=Array.from({length:f.end-f.start+1},(_,i)=>f.start+i),recentStart=f.recentEnd-d.config.janela_recente_anos+1;
 const persons=d.people.filter(p=>!f.personIds.length||f.personIds.includes(p.id_lattes)),cohort=new Set(d.people.map(p=>p.id_lattes));
 const candidates=d.produtos.filter(p=>inScenario(p,f)),rows=[],details=[];
 const joint=p=>new Set((p.coautores_ids||p.participacoes.map(x=>x.docente_id)).filter(id=>cohort.has(id))).size>=2;
 for(const p of persons){
  const own=candidates.filter(x=>x.participacoes.some(a=>a.docente_id===p.id_lattes));
  const dated=own.filter(x=>x.ano!==null&&x.ano>=f.start&&x.ano<=f.end&&available(p,x.ano));
  const eligible=dated.filter(x=>x.estado===POT),uncertain=dated.filter(x=>x.estado===INC||!x.estado);
  const annual=Object.fromEntries(years.map(y=>[y,available(p,y)?eligible.filter(x=>x.ano===y).length:null]));
  const complete=years.every(y=>available(p,y)),hasData=years.some(y=>available(p,y)),undated=own.filter(x=>x.ano===null).length;
  const recentCovered=f.start<=recentStart&&f.end>=f.recentEnd&&Array.from({length:d.config.janela_recente_anos},(_,i)=>recentStart+i).every(y=>available(p,y));
  const recent=recentCovered?eligible.filter(x=>x.ano>=recentStart&&x.ano<=f.recentEnd).length:null;
  const alerts=[];
  if(!complete)alerts.push('Dados incompletos no intervalo');
  if(undated)alerts.push(`${undated} produto(s) sem ano, fora dos totais`);
  if(hasData&&!eligible.length)alerts.push('Sem candidatos identificados no cenário');
  const duplicateRisk=dated.filter(x=>x.possivel_duplicidade).length;
  if(duplicateRisk)alerts.push(`${duplicateRisk} possível(is) duplicidade(s) a conferir`);
  if(uncertain.length)alerts.push(`${uncertain.length} enquadramento(s) incerto(s)`);
  if(recent===0)alerts.push(f.recentEnd>=d.ano_atual?'Sem candidatos recentes até a coleta; ano corrente parcial':'Sem candidatos recentes identificados');
  if(recent===null)alerts.push('Dados insuficientes para a janela recente');
  if(f.minimum!==null&&f.minimum!==''&&hasData&&eligible.length<Number(f.minimum))alerts.push(`Abaixo do limiar interno do GT (${f.minimum})`);
  const r={id:p.id_lattes,name:p.nome,bibliografica:hasData?eligible.filter(x=>x.grande_categoria==='bibliografica').length:null,tecnica:hasData?eligible.filter(x=>x.grande_categoria==='tecnica').length:null,artistica:hasData?eligible.filter(x=>x.grande_categoria==='artistica').length:null,total:hasData?eligible.length:null,uncertain:hasData?uncertain.length:null,confirmed:hasData?dated.filter(x=>x.confirmada_gt).length:null,pendingPotential:hasData?uncertain.filter(x=>x.potencial_a_confirmar).length:null,recent,complete,hasData,undated,annual,joint:hasData?eligible.filter(joint).length:null,alerts,share:null,situation:alerts.join(' · ')||'Candidatos identificados; conferir qualidade e aderência'};
  rows.push(r);
  for(const x of dated){const part=x.participacoes.find(a=>a.docente_id===p.id_lattes);details.push({...x,docente_id:p.id_lattes,docente:p.nome,registro_ids:part.registro_ids,duplicatas_internas_docente:part.duplicatas_internas,conjunto_grupo:joint(x)})}
 }
 const sum=key=>rows.reduce((n,r)=>n+(r[key]||0),0),total=sum('total');rows.forEach(r=>r.share=r.total!==null&&total?r.total/total*100:null);
 rows.sort((a,b)=>{const av=a[f.sort],bv=b[f.sort];if(av===null&&bv!==null)return 1;if(bv===null&&av!==null)return-1;const v=typeof av==='number'&&typeof bv==='number'?av-bv:String(av??'').localeCompare(String(bv??''),'pt-BR');return (f.direction==='desc'?-v:v)||a.name.localeCompare(b.name,'pt-BR')});
 details.sort((a,b)=>a.docente.localeCompare(b.docente,'pt-BR')||b.ano-a.ano||String(a.tipo_capes||'').localeCompare(String(b.tipo_capes||''),'pt-BR'));
 const positive=rows.filter(r=>r.total>0),zeros=rows.filter(r=>r.complete&&r.total===0),recentZeros=rows.filter(r=>r.recent===0),coverageComplete=rows.length>0&&rows.every(r=>r.complete);
 const qualified=details.filter(p=>p.estado===POT),uniquePotential=new Set(qualified.map(p=>p.produto_id)).size;
 const yearly=years.map(y=>({year:y,total:rows.some(r=>r.annual[y]===null)?null:rows.reduce((n,r)=>n+r.annual[y],0),known:rows.reduce((n,r)=>n+(r.annual[y]||0),0)}));
 const maxShare=total?Math.max(...rows.map(r=>r.share||0)):null;
 const annualRegular=coverageComplete?rows.filter(r=>years.every(y=>r.annual[y]>=1)).length/rows.length*100:null;
 const jointShare=coverageComplete?rows.filter(r=>r.joint>0).length/rows.length*100:null;
 const notices=[];
 if(years.includes(d.ano_atual))notices.push(`${d.ano_atual} é parcial: contagens refletem somente a coleta disponível.`);
 if(!coverageComplete)notices.push('Há anos ou currículos sem cobertura. Valores com ≥ representam o mínimo observado; — indica informação indisponível, sem equivalência a zero.');
 if(f.start>recentStart||f.end<f.recentEnd)notices.push(`Janela recente independente: ${recentStart}–${f.recentEnd}. O filtro geral não a contém integralmente; indicador recente indisponível.`);
 if(f.concentration!==null&&f.concentration!==''&&maxShare!==null&&maxShare>Number(f.concentration))notices.push(`Maior participação (${maxShare.toFixed(1)}%) supera o limite interno do GT informado (${f.concentration}%).`);
 if(!rows.some(r=>r.hasData))notices.push('Nenhum ano do intervalo está coberto para os docentes selecionados.');
 return{filters:f,years,recentStart,persons,rows,details,yearly,notices,coverageComplete,totals:{bibliografica:sum('bibliografica'),tecnica:sum('tecnica'),artistica:sum('artistica'),total,uncertain:sum('uncertain'),pendingPotential:sum('pendingPotential'),withPotential:positive.length,withoutPotential:zeros.length,withoutRecent:recentZeros.length,unknownRecent:rows.filter(r=>r.recent===null).length,uniquePotential,jointProducts:new Set(qualified.filter(joint).map(p=>p.produto_id)).size,jointParticipants:rows.filter(r=>r.joint>0).length,maxShare,annualRegular,jointShare,duplicates:details.reduce((n,p)=>n+(p.duplicatas_internas_docente||0),0)}};
}
function metadata(d,a){const f=a.filters;return[['Classificação','Preliminar, sujeita à conferência humana; contagens de participações por docente, sem duplicatas internas.'],['Período',`${f.start}–${f.end}`],['Docentes',a.persons.map(p=>p.nome).join('; ')],['Categoria',f.category||'Todas'],['Bibliográfica',f.biblioTypes.map(k=>kinds[k]).join('; ')||'Nenhuma'],['Trabalhos completos em anais',f.biblioTypes.includes('anais')?'Incluídos':'Excluídos — cenário analítico do GT'],['Janela recente',`${a.recentStart}–${f.recentEnd}; independente; dados insuficientes se não contida no filtro geral`],['Cobertura',a.coverageComplete?'Intervalo coberto nas datas das coletas':'Dados incompletos; valores são mínimos observados, não zeros de anos indisponíveis'],['Fontes das coletas',a.persons.map(p=>p.nome+': '+(p.coletado_em||'pendente')).join('; ')],['Potenciais a confirmar','Manuais/materiais técnicos e software identificados, com recorte AU ainda incerto: subconjunto dos incertos, fora do total principal.'],['Cenário de revisão',f.reviewMode==='confirmed'?'Somente confirmadas pelo GT':f.reviewMode==='merged'?'Decisões do GT prevalecem; demais produtos mantêm sugestão automática':'Sugestão automática, sem aplicar decisões humanas'],['Regra',d.versao_regras],['Parâmetros internos GT',`Mínimo: ${f.minimum??'desativado'}; limite de concentração: ${f.concentration??'desativado'}%`],['Limitação institucional','Vínculos permanentes, licenças parentais, aderência às linhas e comparação com programas nota 3 exigem avaliação externa.'],['Processamento',d.processado_em]]}
function diagnosisRows(a){return [['Docente','Bibliográfica','Técnica/tecnológica','Artístico-cultural','Total prévio','Confirmadas GT no recorte','Incertos','Potenciais a confirmar (dentro dos incertos)','Últimos 3 anos','Participação % observada','Produções conjuntas','Cobertura completa','Situação'],...a.rows.map(r=>[r.name,r.bibliografica,r.tecnica,r.artistica,r.total,r.confirmed,r.uncertain,r.pendingPotential,r.recent,r.share===null?null:r.share.toFixed(2),r.joint,r.complete?'Sim':'Não — mínimo observado',r.situation])]}
function detailRows(d,a,items=a.details){return[['Docente','Ano','Título original','Categoria Lattes','Subcategoria Lattes','Grande categoria CAPES','Tipo CAPES sugerido','Estado','Justificativa','Regra heurística','Referências documentais','Possível duplicidade','Duplicatas internas consolidadas','Necessita conferência','Referência original','Produto ID','Registros originais','DOI','ISSN','ISBN','Coautoria no grupo','Metadados editoriais preservados','Escopo documental','Enquadramento alternativo','Potencial a confirmar','Origem da revisão','Data da revisão','Pendências','Revisão GT','Decisão GT','Sugestão automática preservada'],...items.map(p=>[p.docente,p.ano,p.titulo_original||'Título não extraído; conferir referência',p.categoria_lattes,p.subcategoria_lattes,p.grande_categoria,p.tipo_capes,p.estado,p.justificativa,p.regra,p.fontes.map(k=>`${d.fontes[k].titulo} (${d.fontes[k].localizacao}): ${d.fontes[k].url}`).join('; '),p.possivel_duplicidade?'Sim':'Não',p.duplicatas_internas_docente,'Sim',p.referencia_original,p.produto_id,p.registro_ids.join('; '),p.doi,p.issn,p.isbn,p.conjunto_grupo?'Sim':'Não identificada',JSON.stringify(p.metadados_editoriais||{}),p.escopo_documental,p.enquadramento_alternativo||'',p.potencial_a_confirmar?'Sim — fora do total principal':'Não sinalizado',p.revisao_interpretativa||'Heurística automática',p.revisao_em||'',(p.pendencias||[]).join('; '),p.revisao_gt||'Não revisado',JSON.stringify(p.decisao_gt||null),JSON.stringify(p.classificacao_automatica||null)])]}
function annualRows(a){return[['Docente',...a.years.map(String),'Total prévio'],...a.rows.map(r=>[r.name,...a.years.map(y=>r.annual[y]),r.total])]}
return{POT,INC,NONE,kinds,available,defaults,inScenario,analyze,metadata,diagnosisRows,detailRows,annualRows};
});
