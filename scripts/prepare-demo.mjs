/* Only synthetic fixtures are distributed. User-supplied local data are preserved. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),dist=path.join(root,'dist');
try{
 const existing=JSON.parse(await fs.readFile(path.join(dist,'dados.json'),'utf8'));
 if(existing.dataset_kind!=='demo_ficticio'){
  console.log('Usando a base local existente. A demonstração não substituiu seus dados.');process.exit(0);
 }
}catch(e){if(e.code!=='ENOENT')throw e}
const fixture=JSON.parse(await fs.readFile(path.join(root,'examples/demo-data.json'),'utf8'));
const load=async name=>JSON.parse(await fs.readFile(path.join(root,'classificacao',name+'.json'),'utf8'));
const {data,qualification,orientations}=fixture;
Object.assign(qualification,{catalogo:await load('catalogo'),fontes:await load('fontes'),regras:await load('regras')});
const serialized=v=>JSON.stringify(v).replaceAll('<','\u003c');
let template=await fs.readFile(path.join(root,'index.template.html'),'utf8');
template=template.replace('__DATA__',serialized(data)).replace('__QUAL_DATA__',serialized(qualification)).replace('__ORIENTATION_DATA__',serialized(orientations)).replaceAll('__INICIO__',String(data.inicio)).replaceAll('__FIM__',String(data.fim));
template=template.replace('<main>','<main><div class="note"><strong>DEMONSTRAÇÃO — TODOS OS DADOS SÃO FICTÍCIOS.</strong> Nenhum nome, trabalho ou orientação nesta base representa uma pessoa ou produção real.</div>');
await fs.mkdir(dist,{recursive:true});
for(const [file,value]of Object.entries({'dados.json':data,'qualificacao.json':qualification,'orientacoes.json':orientations,'catalogo-capes.json':qualification.catalogo}))await fs.writeFile(path.join(dist,file),JSON.stringify(value,null,2));
await fs.writeFile(path.join(dist,'index.html'),template);
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const page=(title,content)=>'<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><body style="font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px"><a href="./">Voltar</a><h1>'+title+'</h1>'+content+'</body></html>';
await fs.writeFile(path.join(dist,'implementacao-classificacao.html'),page('Implementação e critérios','<pre style="white-space:pre-wrap">'+escape(await fs.readFile(path.join(root,'classificacao/IMPLEMENTACAO.md'),'utf8'))+'</pre>'));
await fs.writeFile(path.join(dist,'revisao-tecnica.html'),page('Exemplos fictícios de classificação','<p>Este repositório não distribui produtos ou decisões de docentes reais. Consulte os exemplos sintéticos no dashboard.</p>'));
await fs.writeFile(path.join(dist,'guia-atualizacao.html'),page('Atualização da base local','<p>Comece pelo README e por docs/DESENVOLVIMENTO.md. A demonstração não coleta o CNPq; importações reais precisam de fontes e cadastro locais autorizados.</p>'));
console.log('Demonstração gerada com nomes, produtos e orientações totalmente fictícios.');
