(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.AUDOrientations=factory()})(typeof globalThis!=='undefined'?globalThis:this,()=>{
'use strict';
const labels={ic:'IC',especializacao:'Especialização',mestrado:'Mestrado',doutorado:'Doutorado',outras:'Outras',tcc:'TCC graduação',it:'IT'};
const focusKinds=['ic','especializacao','mestrado','doutorado'],visibleKinds=['ic','especializacao','mestrado','doutorado','outras','tcc'];
function defaults(){return{person:'',status:'concluida',role:'principal',start:null,end:null,kinds:[...visibleKinds],sort:'name',direction:'asc'}}
function criteria(person,records){
 const complete=person.secao_orientacoes,done=records.filter(r=>r.situacao==='concluida'),main=done.filter(r=>r.papel==='principal'&&!r.possivel_duplicidade),capes=main.filter(r=>['tcc','ic'].includes(r.modalidade)).length;
 const uncertainCapes=done.some(r=>['tcc','ic'].includes(r.modalidade)&&(r.papel==='nao_informada'||r.possivel_duplicidade));
 const capesStatus=capes>=4?'Evidências preliminares suficientes':!complete||uncertainCapes?'Dados insuficientes para avaliar':'Evidências preliminares insuficientes';
 const validUfg=r=>['especializacao','mestrado','doutorado'].includes(r.modalidade)&&!!r.instituicao||['ic','it'].includes(r.modalidade)&&r.institucional_ufg;
 const ufg=main.filter(validUfg).length;
 const uncertainUfg=done.some(r=>['ic','it','especializacao','mestrado','doutorado'].includes(r.modalidade)&&(r.possivel_duplicidade||r.papel==='nao_informada'||r.papel==='coorientacao'||!r.instituicao||(['ic','it'].includes(r.modalidade)&&r.instituicao_ufg&&!r.programa_institucional)));
 const experience=Object.fromEntries(focusKinds.map(k=>['experiencia_'+k,complete?main.filter(r=>r.modalidade===k).length:null]));
 return{...experience,experiencia_agregada:complete?main.filter(r=>focusKinds.includes(r.modalidade)).length:null,capes,capesStatus,ufg,ufgStatus:ufg>0?'Evidência preliminar identificada':!complete||uncertainUfg?'Informação pendente de verificação':'Sem evidência elegível identificada',coorientacoes:done.filter(r=>r.papel==='coorientacao').length};
}
function analyze(d,filters={}){
 const f={...defaults(),...filters};if(f.start!==null&&!Number.isInteger(f.start)||f.end!==null&&!Number.isInteger(f.end)||f.start!==null&&f.end!==null&&f.start>f.end)throw Error('Informe um intervalo de anos válido.');
 const persons=d.people.filter(p=>!f.person||p.id_lattes===f.person),details=[],rows=[];
 for(const person of persons){
  const own=d.records.filter(r=>r.docente_id===person.id_lattes),selected=own.filter(r=>(f.status==='all'||r.situacao===f.status)&&(f.role==='all'||r.papel===f.role)&&f.kinds.includes(r.modalidade)&&(f.start===null&&f.end===null||r.ano!==null&&(f.start===null||r.ano>=f.start)&&(f.end===null||r.ano<=f.end)));
  const row={id:person.id_lattes,name:person.nome,focusTotal:person.secao_orientacoes?selected.filter(r=>focusKinds.includes(r.modalidade)).length:null,total:person.secao_orientacoes?selected.length:null,principal:selected.filter(r=>r.papel==='principal').length,coorientacao:selected.filter(r=>r.papel==='coorientacao').length,ambiguas:selected.filter(r=>r.pendencias.length||r.possivel_duplicidade).length,...Object.fromEntries(Object.keys(labels).map(k=>[k,person.secao_orientacoes?selected.filter(r=>r.modalidade===k).length:null])),...criteria(person,own)};
  rows.push(row);details.push(...selected);
 }
 rows.sort((a,b)=>{if(a[f.sort]===null)return b[f.sort]===null?0:1;if(b[f.sort]===null)return-1;const v=typeof a[f.sort]==='number'?a[f.sort]-b[f.sort]:String(a[f.sort]).localeCompare(String(b[f.sort]),'pt-BR');return(f.direction==='desc'?-v:v)||a.name.localeCompare(b.name,'pt-BR')});
 details.sort((a,b)=>a.docente.localeCompare(b.docente,'pt-BR')||(b.ano||0)-(a.ano||0)||a.orientando.localeCompare(b.orientando,'pt-BR'));
 const cohortCriteria=d.people.map(p=>criteria(p,d.records.filter(r=>r.docente_id===p.id_lattes)));
 const yes=cohortCriteria.filter(r=>r.ufg>0).length,unknown=cohortCriteria.filter(r=>r.ufgStatus==='Informação pendente de verificação').length,n=cohortCriteria.length,required=Math.ceil(n*.75);
 return{filters:f,rows,details,persons,ufg:{yes,unknown,n,required,percent:n?100*yes/n:null,maximum:n?100*(yes+unknown)/n:null,status:n===0?'Selecione docentes no painel':yes>=required&&n?'Referência preliminar de 75% alcançada':yes+unknown>=required&&n?'Dados pendentes podem alterar o resultado':'Referência preliminar de 75% não alcançada'},totals:{selected:details.length,completed:d.records.filter(r=>persons.some(p=>p.id_lattes===r.docente_id)&&r.situacao==='concluida').length,ongoing:d.records.filter(r=>persons.some(p=>p.id_lattes===r.docente_id)&&r.situacao==='andamento').length,withCompleted:persons.filter(p=>d.records.some(r=>r.docente_id===p.id_lattes&&r.situacao==='concluida')).length,withOngoing:persons.filter(p=>d.records.some(r=>r.docente_id===p.id_lattes&&r.situacao==='andamento')).length,unknown:rows.filter(r=>r.capesStatus==='Dados insuficientes para avaliar').length}};
}
return{labels,focusKinds,visibleKinds,defaults,criteria,analyze};
});
