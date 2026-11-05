/* Browser-local analysis preference; source data and GT decisions remain intact. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.AtlasCohortCore=factory()})(typeof globalThis!=='undefined'?globalThis:this,()=>{
'use strict';
function ids(people,selection){const valid=new Set(people.map(p=>p.id_lattes));return selection===null?people.map(p=>p.id_lattes):[...new Set(selection)].filter(id=>valid.has(id))}
function scope(data,selection){const chosen=new Set(ids(data.people,selection));return{...data,people:data.people.filter(p=>chosen.has(p.id_lattes))}}
return{ids,scope};
});
if(typeof document!=='undefined'){
 (function(){
 'use strict';
 const people=JSON.parse(document.getElementById('data').textContent).people.sort((a,b)=>a.nome.localeCompare(b.nome,'pt-BR')),key='atlas-ufg-analysis-cohort-v1',$c=id=>document.getElementById(id);let selected=null,persistent=true;
 try{const saved=JSON.parse(localStorage.getItem(key));if(Array.isArray(saved?.ids))selected=saved.ids}catch{persistent=false}
 const query=new URLSearchParams(location.search);if(query.has('cohort'))try{const value=JSON.parse(query.get('cohort'));if(Array.isArray(value))selected=value}catch{}
 selected=AtlasCohortCore.ids(people,selected);let set=new Set(selected);
 function refresh(){
  $c('cohort-count').textContent=selected.length+' de '+people.length+' docentes na análise';$c('cohort-status').textContent=selected.length?'A seleção vale para as três abas e para os arquivos exportados. ':'Nenhum docente selecionado. Marque os participantes para calcular a análise.';$c('cohort-status').textContent+=persistent?' Preferência salva neste navegador.':' A seleção vale nesta sessão; o navegador bloqueou o armazenamento local.';
  $c('cohort-list').querySelectorAll('input').forEach(i=>i.checked=set.has(i.value));
 }
 function choose(value){selected=AtlasCohortCore.ids(people,value);set=new Set(selected);try{localStorage.setItem(key,JSON.stringify({ids:selected}));persistent=true}catch{persistent=false}refresh();window.dispatchEvent(new Event('atlas:cohort'))}
 function syncSelect(select){if(!select)return;const prior=select.value;[...select.options].forEach((o,i)=>{if(i){o.hidden=!set.has(o.value);o.disabled=!set.has(o.value)}});if(prior&&!set.has(prior))select.value=''}
 function addToUrl(url){url.searchParams.set('cohort',JSON.stringify(selected));return url}
 for(const p of people){const l=document.createElement('label'),i=document.createElement('input'),s=document.createElement('span');i.type='checkbox';i.value=p.id_lattes;i.addEventListener('change',()=>choose([...$c('cohort-list').querySelectorAll('input:checked')].map(x=>x.value)));s.textContent=p.nome;l.append(i,s);$c('cohort-list').append(l)}
 $c('cohort-toggle').onclick=()=>{$c('cohort-panel').showModal();$c('cohort-toggle').setAttribute('aria-expanded','true')};$c('cohort-panel').addEventListener('close',()=>$c('cohort-toggle').setAttribute('aria-expanded','false'));$c('cohort-close').onclick=()=>$c('cohort-panel').close();$c('cohort-apply').onclick=()=>$c('cohort-panel').close();$c('cohort-all').onclick=()=>choose(people.map(p=>p.id_lattes));$c('cohort-none').onclick=()=>choose([]);
 $c('cohort-search').oninput=()=>{const text=$c('cohort-search').value.toLocaleLowerCase('pt-BR');$c('cohort-list').querySelectorAll('label').forEach(l=>l.hidden=!l.textContent.toLocaleLowerCase('pt-BR').includes(text))};
 window.AtlasCohort={ids:()=>[...selected],has:id=>set.has(id),people:()=>people.filter(p=>set.has(p.id_lattes)),scope:data=>AtlasCohortCore.scope(data,selected),set:choose,syncSelect,addToUrl,description:()=>people.filter(p=>set.has(p.id_lattes)).map(p=>p.nome).join('; ')||'Nenhum docente'};refresh();
 })();
}
