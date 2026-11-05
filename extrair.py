import contextlib,io,json,re,sys,csv,hashlib,argparse,os,unicodedata
from datetime import datetime,timezone
from pathlib import Path
from collections import Counter,defaultdict
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter
sys.path.insert(0,os.environ.get('SCRIPTLATTES_ROOT','/workspace/scriptLattes'))
try:
 from scriptLattes.parserLattes import ParserLattes
except ImportError:
 ParserLattes=None
PROJECT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description='Processa HTMLs Lattes e recompõe dashboard, CSVs e XLSX.')
ap.add_argument('--cache',type=Path,default=Path('/workspace/analise-lattes/cache'))
ap.add_argument('--cadastro',type=Path,default=PROJECT/'docentes.csv')
ap.add_argument('--saida',type=Path,default=PROJECT/'dist')
ap.add_argument('--fim',type=int,default=datetime.now().year)
ap.add_argument('--inicio',type=int)
args=ap.parse_args();fim=args.fim;inicio=args.inicio if args.inicio is not None else fim-4
if not 1900<=inicio<=fim<=2100:ap.error('Intervalo inválido')
OUT=args.saida;OUT.mkdir(parents=True,exist_ok=True)
people=sorted(csv.DictReader(args.cadastro.open()),key=lambda p: ''.join(c for c in unicodedata.normalize('NFKD',p['nome'].casefold()) if not unicodedata.combining(c)))
if len({p['id_lattes'] for p in people})!=len(people):raise ValueError('IDs duplicados no cadastro')
previous=json.loads((OUT/'dados.json').read_text()) if (OUT/'dados.json').exists() else None

def norm(s):return re.sub(r'\W','',str(s).casefold())
rows=[];audit=[]
for person in people:
 lid=person['id_lattes'];source=args.cache/lid
 if not source.exists():
  person.update(status_coleta='pendente',coletado_em='',atualizacao_cv='')
  audit.append({'id_lattes':lid,'nome':person['nome'],'status':'pendente','coletado_em':'','atualizacao_cv':'','sha256_html':'','registros':None});continue
 document=source.read_text()
 source_meta=json.loads(source.with_suffix('.meta.json').read_text()) if source.with_suffix('.meta.json').exists() else {'coletado_em':'7–8/10/2026','observacao':'Coleta original de 7–8/10/2026'}
 if lid not in document:raise ValueError('ID esperado ausente: '+lid)

 with contextlib.redirect_stdout(io.StringIO()):parser=ParserLattes(lid,document) if ParserLattes else None
 indexed=defaultdict(list)
 for key,items in (vars(parser) if parser else {}).items():
  if not key.startswith('lista') or not isinstance(items,list):continue
  for item in items:
   if hasattr(item,'__dict__') and getattr(item,'item',None):indexed[norm(item.item)].append(vars(item))
 soup=BeautifulSoup(document,'html.parser')
 cv_name=soup.select_one('h2.nome')
 if not cv_name:raise ValueError('HTML não é currículo completo: '+lid)
 person['nome']=cv_name.get_text(' ',strip=True)
 updated=re.search(r'Última atualização do currículo em\s*(\d{2}/\d{2}/\d{4})',soup.get_text(' ',strip=True))
 person.update(status_coleta='coletado',coletado_em=source_meta['coletado_em'],atualizacao_cv=updated.group(1) if updated else '')
 section=next((x for x in soup.select('.title-wrapper') if x.h1 and x.h1.get_text(strip=True)=='Produções'),None)
 if section is None:raise ValueError('Seção Produções ausente: '+lid)
 group=kind='';num=0
 for el in section.select('.inst_back,.cita-artigos,.layout-cell-11'):
  classes=el.get('class',[])
  if 'inst_back' in classes:group=el.get_text(' ',strip=True);continue
  if 'cita-artigos' in classes:kind=el.get_text(' ',strip=True);continue
  # Only rendered reference text: remove hidden sorting and citation metadata.
  clone=BeautifulSoup(str(el),'html.parser')
  for hidden in clone.select('.informacao-artigo,script,.citacoes,.citado'):hidden.decompose()
  reference=re.sub(r'\s+',' ',clone.get_text(' ',strip=True)).strip()
  matched=indexed.get(norm(reference),[])
  if not matched:
   matched=[d for key,ds in indexed.items() if key and (key in norm(reference) or norm(reference) in key) for d in ds]
  d=matched[0] if len(matched)==1 else {}
  year=str(d.get('ano',''))
  origin='parser + HTML' if d else ''
  if not re.fullmatch(r'(?:19|20)\d{2}',year):
   marker=el.select_one('[data-tipo-ordenacao="ano"]')
   terminal=re.search(r'\.\s*((?:19|20)\d{2})\s*\.(?:\s*\([^)]*\)\.?)?\s*$',reference)
   ys=[terminal.group(1)] if terminal else re.findall(r'\b(?:19|20)\d{2}\b',marker.get_text() if marker else reference)
   unique=list(dict.fromkeys(ys))
   year=unique[0] if len(unique)==1 else ''
   origin='ano explícito único no HTML' if year else 'revisar ano'
  num+=1
  rows.append({'id':f'{lid}-{num:04d}','id_lattes_docente':lid,'docente':person['nome'],'grupo':group,'tipo':kind,'ano':int(year) if year else None,'titulo':str(d.get('titulo','')),'autores':str(d.get('autores','')),'referencia_original':reference,'metodo_ano':origin,'fonte':f'https://lattes.cnpq.br/{lid}','doi':'; '.join(a['href'] for a in el.select('a[href]') if re.match(r'https?://(?:dx\.)?doi.org/',a['href']))})
 audit.append({'id_lattes':lid,'nome':person['nome'],'status':'coletado','coletado_em':person['coletado_em'],'atualizacao_cv':person['atualizacao_cv'],'sha256_html':hashlib.sha256(document.encode()).hexdigest(),'registros':num})
groups=['Produção bibliográfica','Produção técnica','Produção artística/cultural']
type_groups={r['tipo']:r['grupo'] for r in rows}
types=sorted(set(r['tipo'] for r in rows),key=lambda t:(groups.index(type_groups[t]),t.casefold()))
selected=[r for r in rows if r['ano'] and inicio<=r['ano']<=fim]
summary=[]
for p in people:
 rr=[r for r in selected if r['id_lattes_docente']==p['id_lattes']];c=Counter(r['tipo'] for r in rr)
 summary.append({'Docente':p['nome'],**{label:sum(r['grupo']==group for r in rr) if p['status_coleta']=='coletado' else None for label,group in [('Bibliográfica','Produção bibliográfica'),('Técnica/tecnológica','Produção técnica'),('Artístico-cultural','Produção artística/cultural')]},'Total':len(rr) if p['status_coleta']=='coletado' else None,**{t:c[t] if p['status_coleta']=='coletado' else None for t in types},'Status da coleta':p['status_coleta'],'Sem ano (fora do total)':sum(r['ano'] is None for r in rows if r['id_lattes_docente']==p['id_lattes'])})
meta={'inicio':inicio,'fim':fim,'processado_em':datetime.now(timezone.utc).isoformat(),'coleta':'Datas individuais na seção Fontes','nota':'Contagens por currículo, sem deduplicação entre docentes. Ano em curso parcial. Zero significa nenhum registro identificado na categoria e período no HTML coletado. Registros sem ano ficam fora dos totais. Apresentações mantidas no grupo bibliográfico como no Lattes. Não inclui bancas, orientações, participação em eventos ou projetos. Extração automática sujeita a conferência.','people':people,'groups':groups,'types':types,'type_groups':type_groups,'records':rows,'audit':audit}
if previous:
  version_dir=PROJECT/'historico'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');version_dir.mkdir(parents=True,exist_ok=True)
  (version_dir/'dados.json').write_text(json.dumps(previous,ensure_ascii=False,indent=2))
changes=[]
for p in people:
 old=[r for r in (previous or {}).get('records',[]) if r['id_lattes_docente']==p['id_lattes']]
 new=[r for r in rows if r['id_lattes_docente']==p['id_lattes']]
 a={norm(r['referencia_original']) for r in old};b={norm(r['referencia_original']) for r in new}
 changes.append({'docente':p['nome'],'id_lattes':p['id_lattes'],'status':p['status_coleta'],'registros_anteriores':len(old),'registros_atuais':len(new) if p['status_coleta']=='coletado' else None,'referencias_adicionadas':len(b-a),'referencias_removidas':len(a-b)})
payload=json.dumps(meta,ensure_ascii=False,indent=2)
tmp=OUT/'dados.json.tmp';tmp.write_text(payload);tmp.replace(OUT/'dados.json')
(PROJECT/'ultima-atualizacao.json').write_text(json.dumps({'processado_em':meta['processado_em'],'inicio':inicio,'fim':fim,'docentes':changes},ensure_ascii=False,indent=2))
from classificacao.motor import build as build_qualification
qualification=build_qualification(meta,OUT,args.cache,PROJECT/'historico/cache-classificacao.json')
from orientacoes import build as build_orientations
orientations=build_orientations(people,args.cache,OUT)
(OUT/'catalogo-capes.json').write_text(json.dumps(qualification.get('catalogo',{}),ensure_ascii=False,indent=2))
template=(PROJECT/'index.template.html').read_text()
(OUT/'index.html').write_text(template.replace('__ORIENTATION_DATA__',json.dumps(orientations,ensure_ascii=False).replace('<','\\u003c')).replace('__QUAL_DATA__',json.dumps(qualification,ensure_ascii=False).replace('<','\\u003c')).replace('__DATA__',json.dumps(meta,ensure_ascii=False).replace('<','\\u003c')).replace('__INICIO__',str(inicio)).replace('__FIM__',str(fim)))
for filename,data in [(f'tabela-{inicio}-{fim}.csv',summary),(f'referencias-{inicio}-{fim}.csv',selected)]:
 with (OUT/filename).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(data[0] if data else rows[0]),lineterminator="\n");w.writeheader();w.writerows(data)
w=Workbook();w.remove(w.active)
for name,data in [(f'Quantitativos {inicio}-{fim}',summary),(f'Referências {inicio}-{fim}',selected),('Sem ano - conferir',[r for r in rows if r['ano'] is None]),('Fontes',audit)]:
 ws=w.create_sheet(name)
 if not data:continue
 ws.append(list(data[0]))
 for r in data:ws.append(list(r.values()))
 ws.freeze_panes='B2';ws.auto_filter.ref=ws.dimensions
 for cell in ws[1]:cell.font=Font(color='FFFFFF',bold=True);cell.fill=PatternFill('solid',fgColor='183E3A');cell.alignment=Alignment(wrap_text=True,vertical='center')
 for cell in ws[1]:
  if cell.value in type_groups:
   cell.fill=PatternFill('solid',fgColor={'Produção bibliográfica':'E5EEE8','Produção técnica':'F6EAD7','Produção artística/cultural':'EEE8F5'}[type_groups[cell.value]]);cell.font=Font(color='67736C',bold=False)
  if cell.value in ['Bibliográfica','Técnica/tecnológica','Artístico-cultural','Total']:
   is_total=cell.value=='Total';cell.fill=PatternFill('solid',fgColor='174D40' if is_total else 'E5EEE8');cell.font=Font(color='FFFFFF' if is_total else '173D37',bold=True,size=12)
   for body_cell in list(ws.columns)[cell.column-1][1:]:body_cell.fill=PatternFill('solid',fgColor='174D40' if is_total else 'F0F4EE');body_cell.font=Font(color='FFFFFF' if is_total else '173D37',bold=True,size=12)
 ws.row_dimensions[1].height=65
 for col in ws.columns:
  title=str(col[0].value);width=52 if title in ['Docente','docente','referencia_original','titulo','autores'] else 25
  ws.column_dimensions[get_column_letter(col[0].column)].width=width
 ws.sheet_properties.pageSetUpPr.fitToPage=True
 ws.page_setup.orientation='landscape';ws.page_setup.paperSize=ws.PAPERSIZE_A3;ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=0
ws=w.create_sheet('Como ler');ws.append(['Período',f'{inicio}–{fim} (inclusive)']);ws.append(['Coleta',meta['coleta']]);ws.append(['Critério',meta['nota']]);ws.column_dimensions['A'].width=20;ws.column_dimensions['B'].width=110;ws['B3'].alignment=Alignment(wrap_text=True);ws.row_dimensions[3].height=100
w.save(OUT/f'producao-docente-{inicio}-{fim}.xlsx')
print('TOTAL HISTÓRICO',len(rows),'PERÍODO',len(selected),'SEM ANO',sum(r['ano'] is None for r in rows),'METODOS',Counter(r['metodo_ano'] for r in rows))
print('GRUPOS',Counter(r['grupo'] for r in selected));print('PENDÊNCIAS',[(r['docente'],r['tipo'],r['referencia_original'][:200]) for r in rows if r['ano'] is None])
print('TABELA')
for p in people:
 rr=[r for r in selected if r['id_lattes_docente']==p['id_lattes']];print(p['nome'],*[sum(r['grupo']==g for r in rr) if p['status_coleta']=='coletado' else 'PENDENTE' for g in groups],len(rr) if p['status_coleta']=='coletado' else 'PENDENTE')
