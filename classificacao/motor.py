"""Camada de análise preliminar, sem alterar registros Lattes originais."""
import copy,hashlib,json,re,unicodedata,inspect,html
from collections import defaultdict,Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
HERE=Path(__file__).resolve().parent
POT='Potencialmente qualificada';INC='Enquadramento incerto';NONE='Sem enquadramento identificado'
def norm(value):
 value=''.join(c for c in unicodedata.normalize('NFKD',str(value or '').casefold()) if not unicodedata.combining(c))
 return re.sub(r'[^a-z0-9]+',' ',value).strip()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def author_keys(value):
 out=set()
 for author in str(value or '').split(';'):
  parts=author.strip().split(',',1)
  if len(parts)==2:
   surname=norm(parts[0]);initial=norm(parts[1])[:1]
  else:
   words=norm(author).split();surname=words[-1] if words else '';initial=words[0][:1] if words else ''
  if surname and initial:out.add(surname+':'+initial)
 return sorted(out)
def doi(value):
 match=re.search(r'10\.\d{4,9}/[^\s;<>]+',str(value or ''),re.I)
 return match.group().rstrip('.,').casefold() if match else ''
def enrich(raw,cache):
 """Somente metadados efetivamente existentes em exportações/HTMLs locais."""
 lookup={};legacy=Path('/workspace/analise-lattes/publicacoes/publicacoes.json')
 if legacy.exists():
  for r in json.loads(legacy.read_text()):lookup[(r['id_lattes_docente'],norm(r['referencia_original']))]=r
 links={};ids={r['id_lattes_docente'] for r in raw}
 for lid in ids:
  path=cache/lid
  if not path.exists():continue
  soup=BeautifulSoup(path.read_text(),'html.parser')
  for block in soup.select('div.layout-cell-11'):
   coauthors=set()
   for a in block.select('a[href]'):
    match=re.search(r'lattes\.cnpq\.br/(\d{16})',a['href'])
    if match:coauthors.add(match.group(1))
   if not coauthors:continue
   for el in block.select('.informacao-artigo,script,.citacoes,.citado'):el.decompose()
   links[(lid,norm(block.get_text(' ',strip=True)))]=sorted(coauthors)
 result={}
 for r in raw:
  key=(r['id_lattes_docente'],norm(r['referencia_original']));old=lookup.get(key,{})
  result[r['id']]={k:old.get(k,r.get(k,'')) for k in ['issn','isbn','revista','evento','editora','livro','volume','paginas']}
  for code in ['issn','isbn']:
   match=re.search(r'\b'+code+r'(?:-1[03])?\s*:?\s*([0-9Xx-]{8,20})',r.get('referencia_original',''),re.I)
   if not result[r['id']][code] and match:result[r['id']][code]=match.group(1)
  result[r['id']]['coautores_ids']=sorted(set(links.get(key,[]))|{p['id_lattes'] for p in old.get('coautores_com_id_lattes',[])})
 return result

def classify(r,rules,extra=None):
 extra=extra or {};text=norm(r.get('titulo') or r.get('referencia_original'));full=norm(r.get('referencia_original'));typ=r.get('tipo','');group=r.get('grupo','')
 result={'grande_categoria':'bibliografica' if group=='Produção bibliográfica' else 'artistica' if 'artística' in group else 'tecnica','tipo_capes':'','subtipo_capes':'','tipo_bibliografico':None,'estado':INC,'regra':'','justificativa':'','fontes':['apcn2026','area2025'],'escopo_documental':'especifico_au','necessita_conferencia':True,'pendencias':['Qualidade e impacto não verificados','Aderência às linhas e aos projetos da APCN não verificada']}
 def assign(state,kind,rule,reason):
  result.update(estado=state,tipo_capes=kind,regra=rule,justificativa=reason);return result
 if result['grande_categoria']=='bibliografica':
  item=rules['bibliografica'].get(typ,{'chave':'outro','tipo':'Outro registro bibliográfico','familia':'outro','candidato':False});result['tipo_bibliografico']=item['chave']
  if typ=='Artigos aceitos para publicação':return assign(INC,item['tipo'],'B-ACEITO','Há aceite registrado, mas a publicação efetiva deve ser confirmada. Não integra automaticamente o indicador de publicados.')
  if not item['candidato']:return assign(NONE,item['tipo'],'B-OUTROS','Natureza bibliográfica preservada; não foi identificada regra que incorpore automaticamente este subtipo ao indicador principal de candidatos.')
  title=norm(r.get('titulo'));authors=norm(r.get('autores'));reference=norm(r.get('referencia_original'))
  evidence=bool(title and len(title)>=8 and authors and title in reference and len(reference)>len(title)+25 and r.get('ano'))
  if item['chave']=='artigo':evidence=evidence and bool(extra.get('revista') or re.search(r'\bv\b|\bp\b|\bn\b|doi|revista|journal|caderno',reference))
  if item['chave']=='livro':evidence=evidence and bool(extra.get('editora') or re.search(r'\bed\b|isbn|editora|editorial',reference))
  if item['chave']=='capitulo':evidence=evidence and bool(re.search(r'\bin\b',reference) or extra.get('livro'))
  if item['chave']=='anais':evidence=evidence and bool(re.search(r'anais|proceedings|actas|atas|\bin\b',reference))
  return assign(POT if evidence else INC,item['tipo'],'B-'+item['chave'].upper(),'Tipo reconhecido pela Área, com título, autoria, ano e indícios editoriais na referência. Candidato à análise qualitativa; sem atribuição de Qualis ou aprovação.' if evidence else 'Tipo bibliográfico elegível em tese, porém a referência extraída não oferece todos os indícios mínimos adotados pela heurística (título, autoria, ano e contexto editorial). Conferir o original.')
 # A project or curatorial artifact can be recorded under a technical Lattes heading.
 if result['grande_categoria']=='tecnica' and re.search(r'projeto arquitetonic|projeto urbanistic|projeto paisagistic|museograf|curadoria',text):
  result['grande_categoria']='artistica'
 if result['grande_categoria']=='artistica':
  result['fontes']+=['artistico2019']
  subtype=next((t['tipo'] for t in rules['arte'] if re.search(t['padrao'],text)), 'Produção artístico-cultural; subtipo a confirmar')
  result['subtipo_capes']=subtype
  if 'portfolio' in text:return assign(INC,subtype,'A-PORTFOLIO','O título de portfólio não comprova um produto qualificado nem sua aderência à proposta.')
  if typ=='Música' and not re.search(r'pesquisa em arquitetura|paisagem sonora|patrimonio sonoro|memoria urbana',full):return assign(INC,'Produção musical','A-MUSICA','A relação desta produção musical com AUD e com os projetos da proposta não está demonstrada no registro disponível.')
  area=bool(re.search(rules['aderencia_au'],full));artifact=subtype!='Produção artístico-cultural; subtipo a confirmar'
  eligible=area and artifact and bool(r.get('ano'))
  if group=='Produção técnica' and not re.search(r'executad|construid|implantad|apresentad|exposicao|publicad|premiad|concurso|acervo',full):eligible=False
  return assign(POT if eligible else INC,subtype,'A-INDICIOS','Há produto artístico/projetual identificável e sinais textuais de relação com AUD. A relação com pesquisa, alcance e proposta deve ser conferida.' if eligible else 'Há registro artístico-cultural, mas os dados não permitem confirmar simultaneamente o subtipo e a aderência a AUD. Mantido fora do total principal.')
 # Technical/technological: strong matching + corroborating information, never category alone.
 result['fontes']+=['tecnico2019']
 if re.search(r'parecerista|participacao em banca|avaliacao de (trabalho|resumo|projeto)|comissao julgadora|parecer.*(conpeex|congresso|periodico|revista|artigo|resumo|edital|selecao)',text):return assign(NONE,'Atividade de avaliação/parecer','T-AVALIACAO','Atividade acadêmica de avaliação identificada; não há produto final correspondente à tipologia AU suficientemente documentado neste registro.')
 if re.search(r'curso|oficina|minicurso',text) and not re.search(r'organizacao de (evento|congresso|seminario|exposicao|encontro)|evento organizado',text):
  result['escopo_documental']='lista_geral_nao_equiparada';return assign(INC,'Curso/atividade formativa','T-CURSO','Curso ministrado não equivale a Evento Organizado. Eventual enquadramento na lista geral exige análise do recorte AU e documentação adicional.')
 for rule in rules['tecnica']:
  if not re.search(rule['padrao'],text):continue
  if rule['id']=='T02' and re.search(r'sem registro|sem patente|nao registrad',full):continue
  corroborated=bool(re.search(rule['evidencia'],full))
  # Interviews alone, consultation alone, or a product title are insufficient.
  if typ.startswith('Entrevistas') and not re.search(r'producao|roteiro|criacao|direcao',full):corroborated=False
  if typ=='Assessoria e consultoria' and not re.search(r'relatorio|mapa|acervo|base de dados|publicacao',full):corroborated=False
  return assign(POT if corroborated and r.get('ano') else INC,rule['tipo'],rule['id'],'Correspondência plausível com a lista específica AU, apoiada em sinais de natureza e documentação na referência. Requer validação do produto, uso, qualidade e aderência.' if corroborated else 'Há indício de correspondência com a lista específica AU, mas o produto ou sua documentação não está suficientemente caracterizado.')
 for item in rules['tipos_gerais_nao_equiparados']:
  if re.search(item['padrao'],text):
   result['escopo_documental']='lista_geral_nao_equiparada';return assign(INC,item['tipo'],'T-GERAL','Tipo ou atividade encontrado na lista geral/contexto técnico. Não foi equiparado automaticamente aos dez tipos específicos de AU; verificar o produto resultante e o recorte da subárea.')
 return assign(INC,'Produto técnico/tecnológico a esclarecer','T-INDETERMINADO','A categoria Lattes ou o título não bastam para identificar um dos tipos específicos AU. É necessária documentação do produto, finalidade e resultado.')

def consolidate(raw,rules,metadata=None,cache=None,reviews=None):
 from .revisao import load_reviews,review_key,apply_review
 from .criterios import refine
 catalog=json.loads((HERE/'catalogo.json').read_text()) if (HERE/'catalogo.json').exists() else {}
 reviews=load_reviews(HERE/'revisao_tecnica.json') if reviews is None else reviews
 metadata=metadata or {};cache=cache if cache is not None else {};new_cache={};entries=[];reused=0
 rules_hash=digest([rules,inspect.getsource(classify),inspect.getsource(norm),inspect.getsource(refine),catalog])
 for r in raw:
  extra=metadata.get(r['id'],{});content={k:v for k,v in r.items() if k!='id'};review=reviews.get(review_key(r));fingerprint=digest([rules_hash,content,extra,review,inspect.getsource(apply_review)]);old=cache.get(fingerprint)
  decision=copy.deepcopy(old) if old else refine(r,apply_review(r,classify(r,rules,extra),review),catalog)
  if old:reused+=1
  new_cache[fingerprint]=copy.deepcopy(decision)
  title=r.get('titulo','');family=rules['bibliografica'].get(r.get('tipo'),{}).get('familia',r.get('tipo')) if decision['grande_categoria']=='bibliografica' else decision['grande_categoria']
  pub_context=norm(r.get('referencia_original','')).partition(norm(title))[2] if norm(title) else ''
  entries.append({'contexto_publicacao':pub_context,'registro_id':r['id'],'docente_id':r['id_lattes_docente'],'docente':r['docente'],'ano':r.get('ano'),'titulo_original':title,'titulo_normalizado':norm(title),'autores':r.get('autores',''),'autores_normalizados':author_keys(r.get('autores')),'doi':doi(r.get('doi')),'issn':extra.get('issn',''),'isbn':extra.get('isbn',''),'metadados_editoriais':{k:extra.get(k,'') for k in ['revista','evento','livro','editora','volume','paginas']},'identificadores_adicionais':{k:r[k] for k in ['issn','isbn','registro_inpi'] if r.get(k)},'categoria_lattes':r.get('grupo'),'subcategoria_lattes':r.get('tipo'),'referencia_original':r.get('referencia_original',''),'fonte_registro':r.get('fonte',''),'coautores_ids':extra.get('coautores_ids',[]),'familia':family,'fingerprint':fingerprint,**decision})
 parent=list(range(len(entries)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b):
  a,b=find(a),find(b)
  if a!=b:parent[max(a,b)]=min(a,b)
 strong=defaultdict(list);weak=defaultdict(list);possible=defaultdict(set)
 for i,e in enumerate(entries):
  if e.get('identidade_revisada'):strong[('review',e['identidade_revisada'],e['ano'],e['docente_id'],e['familia'])].append(i)
  if e['doi']:strong[('doi',e['doi'],e['familia'])].append(i)
  title=e['titulo_normalizado'];year=e['ano']
  if title and year:
   weak[(title,year)].append(i)
   if len(title)>=24 and len(title.split())>=4:strong[('title',title,year,e['familia'])].append(i)
  # Exact repeated reference inside a curriculum is unambiguous even without a parsed title.
  strong[('reference',e['familia'],norm(e['referencia_original']))].append(i)
 for key,indices in strong.items():
  for j,i in enumerate(indices):
   for k in indices[:j]:
    a,b=entries[i],entries[k]
    if key[0]=='title' and (a['grande_categoria']=='artistica' or (a['grande_categoria']=='bibliografica' and (not a['contexto_publicacao'] or a['contexto_publicacao']!=b['contexto_publicacao']))):continue
    if key[0] in ('doi','reference','review') or (not(a['doi'] and b['doi'] and a['doi']!=b['doi']) and (set(a['autores_normalizados']) & set(b['autores_normalizados']) or a['autores_normalizados']==b['autores_normalizados']!=[])):
     union(i,k)
 for indices in weak.values():
  for j,i in enumerate(indices):
   for k in indices[:j]:
    if find(i)!=find(k):possible[i].add(k);possible[k].add(i)
 clusters=defaultdict(list)
 for i,e in enumerate(entries):clusters[find(i)].append((i,e))
 products=[]
 for members in clusters.values():
  candidates=[e for _,e in members];best=sorted(candidates,key=lambda e:(0 if e['estado']==POT else 1 if e['estado']==INC else 2,not bool(e['titulo_original']),e['registro_id']))[0]
  years={e['ano'] for e in candidates if e['ano'] is not None};conflicting=len(years)>1
  specific=bool(best['grande_categoria']!='artistica' and len(best['titulo_normalizado'])>=24 and len(best['titulo_normalizado'].split())>=4 and best['autores_normalizados'])
  canonical=['doi',best['doi'],best['familia']] if best['doi'] else ['title' if specific else 'reference',best['titulo_normalizado'] if specific else norm(best['referencia_original']),best['ano'],best['familia'],best['autores_normalizados'],best['contexto_publicacao'] if best['grande_categoria']=='bibliografica' else '']
  pid='prod-'+digest(canonical)[:20];counts=Counter(e['docente_id'] for e in candidates);participants=[]
  if best.get('identidade_revisada'):pid='prod-'+digest(['review',best['identidade_revisada'],best['ano'],best['familia']])[:20]
  for person_id in sorted(counts):
   own=[e for e in candidates if e['docente_id']==person_id];participants.append({'docente_id':person_id,'docente':own[0]['docente'],'registro_ids':[e['registro_id'] for e in own],'duplicatas_internas':len(own)-1})
  p={k:v for k,v in best.items() if k not in ['docente_id','docente','registro_id','fingerprint','coautores_ids']}
  p.update(produto_id=pid,ano=next(iter(years)) if len(years)==1 else None,participacoes=participants,registros_origem=candidates,possivel_duplicidade=any(i in possible for i,_ in members),possiveis_registros_duplicados=sorted({entries[j]['registro_id'] for i,_ in members for j in possible.get(i,set())}),duplicatas_internas=sum(n-1 for n in counts.values()),coautores_ids=sorted(set(e['docente_id'] for e in candidates)|{lid for e in candidates for lid in e['coautores_ids']}),decisao_deduplicacao='D01 — DOI compatível ou título/ano/natureza/autoria; originais preservados',conflito_ano=conflicting)
  if conflicting:p.update(estado=INC,justificativa=p['justificativa']+' Anos divergentes entre registros; ano não escolhido automaticamente.')
  if best.get('identidade_revisada'):p['decisao_deduplicacao']='D02 — Identidade examinada na revisão interpretativa; variações de título e seções do mesmo produto consolidadas, mantendo os originais'
  if p['possivel_duplicidade']:p['pendencias']=list(dict.fromkeys(p['pendencias']+['Possível duplicidade com natureza/autoria a conferir; sem fusão automática']))
  products.append(p)
 # Extremely unlikely IDs collisions are made explicit instead of silently overwriting a product.
 assert len({p['produto_id'] for p in products})==len(products),'Colisão de identidade de produtos exige conferência'
 technical=[e for e in entries if e['categoria_lattes']=='Produção técnica']
 return products,new_cache,{'registros_originais':len(raw),'produtos_unicos':len(products),'participacoes_deduplicadas':sum(len(p['participacoes']) for p in products),'duplicatas_internas':sum(p['duplicatas_internas'] for p in products),'classificacoes_reutilizadas':reused,'classificacoes_recalculadas':len(raw)-reused,'registros_tecnicos':len(technical),'registros_tecnicos_revisados':sum(bool(e.get('chave_revisao')) for e in technical),'registros_tecnicos_sem_revisao':sum(not e.get('chave_revisao') for e in technical)}

def build(base,out,html_cache,classification_cache=None):
 rules=json.loads((HERE/'regras.json').read_text());sources=json.loads((HERE/'fontes.json').read_text());config=json.loads((HERE/'config.json').read_text())
 prior=json.loads(classification_cache.read_text()) if classification_cache and classification_cache.exists() else {}
 products,next_cache,stats=consolidate(base['records'],rules,enrich(base['records'],html_cache),prior)
 current=datetime.now(ZoneInfo('America/Sao_Paulo'));years=[r['ano'] for r in base['records'] if r.get('ano')];start=min(years) if years else current.year
 people=[]
 for p in base['people']:
  date=p.get('coletado_em','');match=re.search(r'\b(20\d{2})\b',date);until=int(match.group(1)) if match else None
  update_match=re.search(r'(20\d{2})$',p.get('atualizacao_cv',''));update_year=int(update_match.group(1)) if update_match else None
  if until and update_year:until=min(until,update_year)
  people.append({**p,'cobertura_inicio':start if p.get('status_coleta')=='coletado' else None,'cobertura_fim':until,'categoria_na_proposta':p.get('categoria_na_proposta','Não informada')})
 config['ano_submissao_padrao']=config['ano_submissao_padrao'] or current.year;config['ano_referencia_recente']=config['ano_referencia_recente'] or current.year
 payload={'catalogo':json.loads((HERE/'catalogo.json').read_text()) if (HERE/'catalogo.json').exists() else {},'versao_regras':rules['versao'],'hash_regras':digest(rules),'hash_revisao':hashlib.sha256((HERE/'revisao_tecnica.json').read_bytes()).hexdigest() if (HERE/'revisao_tecnica.json').exists() else None,'hash_motor':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'processado_em':current.isoformat(),'ano_atual':current.year,'config':config,'fontes':sources,'regras':rules,'people':people,'produtos':products,'estatisticas':stats,'cobertura':{'inicio':start,'fim':max((p['cobertura_fim'] or start for p in people),default=current.year)},'avisos':['Classificação preliminar, sujeita à conferência humana. Todos os candidatos exigem avaliação de qualidade e aderência à proposta.','O modo restrito é um cenário interno do GT; não afirma exclusão normativa de trabalhos completos em anais.','A base contempla as seções de produção extraídas. Organização de eventos fora dessas seções, orientações, bancas e projetos não foram adicionados nem classificados por inferência.','A categoria de docente permanente e a base comparativa de programas nota 3 não foram informadas. Não se conclui atendimento institucional.','Coautoria por correspondência conservadora de registros e IDs Lattes; abreviações de nomes isoladas não criam automaticamente participações.']}
 out.mkdir(parents=True,exist_ok=True);(out/'qualificacao.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
 reviewed=[e for p in products for e in p['registros_origem'] if e['categoria_lattes']=='Produção técnica']
 reviewed.sort(key=lambda e:(norm(e['docente']),-(e['ano'] or 0),norm(e['titulo_original'] or e['referencia_original'])))
 esc=lambda value:html.escape(str(value or ''))
 style='body{font:16px system-ui;line-height:1.65;max-width:1100px;margin:40px auto;padding:20px;color:#173d37;background:#f4f3ed}article{background:white;border:1px solid #ccc;padding:22px;margin:20px 0;overflow-wrap:anywhere}a{color:inherit}small{font-size:14px}'
 report='<html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Revisão da produção técnica</title><style>'+style+'</style><a href="./?view=qualified">← Voltar ao dashboard</a><h1>Revisão interpretativa da produção técnica</h1><p>Histórico completo, sem filtro temporal: '+str(stats['registros_tecnicos_revisados'])+' de '+str(stats['registros_tecnicos'])+' registros examinados. As repetições aparecem aqui para auditoria; não são contagens de produtos únicos. Use o dashboard para o recorte temporal e os totais deduplicados.</p><p>Leitura assistida das referências do Lattes, sem análise das íntegras e sem validação do GT/docente. Manuais/materiais técnicos e software com recorte AU pendente aparecem como potenciais a confirmar, dentro dos incertos e fora do total principal. Propriedade intelectual abrange diferentes ativos; RRT/ART não é evidência suficiente de patente ou de registro INPI.</p>'
 for e in reviewed:
  report+='<article><small>'+esc(e['docente'])+' · '+esc(e['ano'])+' · '+esc(e['registro_id'])+'</small><h2>'+esc(e['titulo_original'] or e['referencia_original'])+'</h2><p><strong>'+esc(e['estado'])+'</strong> · '+esc(e['tipo_capes'])+'</p><p>'+esc(e['referencia_original'])+'</p><p>'+esc(e['justificativa'])+'</p><p>'+esc(e.get('enquadramento_alternativo'))+'</p><p><strong>Pendências:</strong> '+esc('; '.join(e['pendencias']))+'</p><small>Regra '+esc(e['regra'])+' · '+esc(e.get('revisao_interpretativa'))+' · '+esc(e.get('revisao_em'))+'</small><p>Fontes: '+('; '.join('<a href="'+esc(sources[k]['url'])+'">'+esc(sources[k]['titulo'])+'</a> — '+esc(sources[k]['localizacao']) for k in e['fontes']))+'</p></article>'
 (out/'revisao-tecnica.html').write_text('<!doctype html>'+report+'</html>')
 document=HERE/'IMPLEMENTACAO.md'
 if document.exists():
  links='<ul>'+''.join('<li><a href="'+html.escape(s['url'],quote=True)+'">'+html.escape(s['titulo'])+'</a> — '+html.escape(s['localizacao'])+'</li>' for s in sources.values())+'</ul>'
  (out/'implementacao-classificacao.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Implementação da análise preliminar — Área 29</title><style>body{font:16px system-ui;line-height:1.7;max-width:1050px;margin:40px auto;padding:20px;color:#173d37;background:#f4f3ed}pre{white-space:pre-wrap}a{color:inherit}</style><a href="./?view=qualified">← Voltar à análise preliminar</a><h1>Regras, fontes, testes e limitações</h1>'+links+'<pre>'+html.escape(document.read_text())+'</pre></html>')
 if classification_cache:
  classification_cache.parent.mkdir(parents=True,exist_ok=True);tmp=classification_cache.with_suffix('.tmp');tmp.write_text(json.dumps(next_cache,ensure_ascii=False));tmp.replace(classification_cache)
 return payload
