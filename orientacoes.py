"""Orientações extraídas do HTML local, independentes da produção intelectual."""
import hashlib,json,re,unicodedata
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup

def norm(value):
 return re.sub(r'[^a-z0-9]+',' ',' '.join(''.join(c for c in unicodedata.normalize('NFKD',str(value or '').lower()) if not unicodedata.combining(c)).split())).strip()
def identity(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]
KINDS={'ic':'Iniciação científica','it':'Iniciação tecnológica','tcc':'TCC de graduação','especializacao':'Especialização / lato sensu','mestrado':'Mestrado','doutorado':'Doutorado','outras':'Outras orientações e supervisões'}
def parse_reference(reference,heading,status,person):
 text=' '.join(reference.split());n=norm(text);h=norm(heading)
 category='outras'
 if 'doutorado' in h and 'pos doutorado' not in h:category='doutorado'
 elif 'mestrado' in h:category='mestrado'
 elif 'especializacao' in h or 'aperfeicoamento' in h:category='especializacao'
 elif 'graduacao' in h and 'conclusao' in h:category='tcc'
 elif 'iniciacao tecnologica' in h or re.search(r'\bpibiti\b|iniciacao tecnologica',n):category='it'
 elif 'iniciacao cientifica' in h or re.search(r'\b(?:pibic|pivic)\b',n):category='ic'
 role='coorientacao' if re.search(r'co[ -]?orientador',text,re.I) else 'principal' if re.search(r'(?<!co)\borientador(?:a)?\b',text,re.I) else 'supervisao' if re.search(r'supervisor|supervisao',norm(text+' '+heading)) else 'nao_informada'
 start=re.search(r'In[ií]cio:\s*((?:19|20)\d{2})',text,re.I)
 years=list(re.finditer(r'\.\s*((?:19|20)\d{2})\s*\.\s',text)) if not start else []
 marker=start if start else years[-1] if years else None
 year=int(marker.group(1)) if marker else None
 lead=text[:marker.start()].strip('. ') if marker else text
 name,sep,title=lead.partition('. ')
 if not sep:name=lead;title=''
 course='';institution=''
 match=re.search(r'\(([^()]*)\)\s*-\s*(.*)',text,re.I)
 if match:
  course=match.group(1).strip();tail=re.split(r'\.(?:\s*(?:Co[ -]?)?Orientador|\s*Supervisor)|\s*\((?:Co[ -]?)?Orientador',match.group(2),flags=re.I)[0]
  institution=tail.split(',')[0].strip(' .,')
 elif marker:
  tail=re.split(r'\.(?:\s*(?:Co[ -]?)?Orientador|\s*Supervisor)|\s*\((?:Co[ -]?)?Orientador',text[marker.end():],flags=re.I)[0]
  if ' - ' in tail:institution=tail.partition(' - ')[2].split(',')[0].strip(' .,')
  elif 'pos doutorado' in h:institution=tail.split('. ')[0].strip(' .,')
 programs=re.findall(r'\b(?:PIBIC|PIVIC|PIBITI|PIVITI|PIBIC-AF|PIBIC-EM)\b',text,re.I)
 institutional=bool(programs or re.search(r'programa institucional|iniciacao cientifica institucional|institucional de iniciacao',n))
 ufg=bool(re.match(r'^(?:universidade federal de goias|ufg)(?: |$)',norm(institution)))
 pending=[]
 if not year:pending.append('Ano não identificado')
 if not institution:pending.append('Instituição não identificada')
 if role=='nao_informada':pending.append('Papel de orientação não identificado')
 if category in ('ic','it') and not institutional:pending.append('Programa institucional não identificado; IC/IT na UFG não comprova automaticamente programa institucional')
 if category=='outras':pending.append('Modalidade não incluída automaticamente nos critérios específicos')
 record={'docente_id':person['id_lattes'],'docente':person['nome'],'orientando':name,'titulo':title,'ano_conclusao':year if status=='concluida' else None,'ano_inicio':year if status=='andamento' else None,'ano':year,'modalidade':category,'modalidade_lattes':heading,'situacao':status,'papel':role,'curso_programa':course,'instituicao':institution,'programa_institucional':'; '.join(dict.fromkeys(p.upper() for p in programs)) if programs else 'Programa institucional indicado' if institutional else '', 'instituicao_ufg':ufg,'institucional_ufg':bool(ufg and institutional),'referencia_original':text,'fonte':'https://lattes.cnpq.br/'+person['id_lattes'],'pendencias':pending}
 record['id']='ori-'+identity([person['id_lattes'],heading,status,n]);record['chave_trabalho']=identity([person['id_lattes'],norm(name),norm(title),category,year,status,role]);return record

def extract(document,person):
 soup=BeautifulSoup(document,'html.parser');section=next((x for x in soup.select('.title-wrapper') if x.h1 and x.h1.get_text(strip=True)=='Orientações'),None)
 if section is None:return [],False
 status='';heading='';rows=[]
 for e in section.select('.inst_back,.cita-artigos,.layout-cell-11'):
  classes=e.get('class',[]);text=' '.join(e.get_text(' ',strip=True).split())
  if 'inst_back' in classes:status='concluida' if 'conclu' in norm(text) else 'andamento' if 'andamento' in norm(text) else '';heading=''
  elif 'cita-artigos' in classes:heading=text
  elif status:
   clone=BeautifulSoup(str(e),'html.parser')
   for hidden in clone.select('script,.informacao-artigo'):hidden.decompose()
   rows.append(parse_reference(clone.get_text(' ',strip=True),heading,status,person))
 return rows,True

def build(people,cache,out):
 records=[];coverage=[]
 for p in people:
  path=cache/p['id_lattes'];rows,found=extract(path.read_text(),p) if path.exists() else ([],False)
  records.extend(rows);coverage.append({**p,'secao_orientacoes':found,'registros_brutos':len(rows)})
 unique={}
 for r in records:
  if r['id'] in unique:unique[r['id']]['repeticoes']+=1
  else:unique[r['id']]={**r,'repeticoes':0,'possivel_duplicidade':False}
 groups=Counter(r['chave_trabalho'] for r in unique.values())
 for r in unique.values():r['possivel_duplicidade']=groups[r['chave_trabalho']]>1
 data={'versao':'orientacoes-1.0','people':coverage,'modalidades':KINDS,'records':list(unique.values()),'registros_brutos':len(records),'duplicatas_exatas':len(records)-len(unique),'nota':'Retrato dos HTMLs locais; seção ausente não equivale a zero. Concluída é a situação declarada no Lattes, não comprovação documental de defesa com êxito. Critérios normativos calculados no histórico completo e separados dos filtros da tabela.'}
 (out/'orientacoes.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));return data
