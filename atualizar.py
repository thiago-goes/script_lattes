"""Atualização assistida com HTML validado, histórico e processamento em staging."""
import argparse,csv,json,shutil,subprocess,sys,tempfile,unicodedata,re,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import build_opener,HTTPCookieProcessor,Request
from http.cookiejar import CookieJar
from bs4 import BeautifulSoup
PROJECT=Path(__file__).resolve().parent

def norm(text):return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if c.isalnum())
def validate(document,person):
 soup=BeautifulSoup(document,'html.parser');name=soup.select_one('h2.nome')
 if not name:
  if 'código de segurança' in soup.get_text(' ',strip=True).casefold() or soup.select('[name="tokenCaptchar"],.g-recaptcha'):
   raise ValueError('CNPq solicitou verificação de segurança. Abra o currículo no navegador, conclua a verificação e importe o HTML salvo.')
  raise ValueError('A resposta não contém um currículo HTML completo.')
 if norm(name.get_text())!=norm(person['nome']):raise ValueError('Nome não coincide com o cadastro.')
 ident=next((x for x in soup.select('.title-wrapper') if x.h1 and x.h1.get_text(strip=True)=='Identificação'),None)
 if not ident or person['id_lattes'] not in ident.get_text(' ',strip=True):raise ValueError('ID Lattes não confirmado na seção Identificação.')
 if not any(x.h1 and x.h1.get_text(strip=True)=='Produções' for x in soup.select('.title-wrapper')):raise ValueError('Seção Produções ausente; arquivo não será incorporado.')
 return soup

def store(document,person,cache,method):
 validate(document,person);lid=person['id_lattes'];cache.mkdir(parents=True,exist_ok=True);target=cache/lid;stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 if target.exists():
  backup=PROJECT/'historico'/'html'/stamp;backup.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup/lid)
  if target.with_suffix('.meta.json').exists():shutil.copy2(target.with_suffix('.meta.json'),backup/(lid+'.meta.json'))
 meta={'id_lattes':lid,'nome':person['nome'],'coletado_em':datetime.now(timezone.utc).isoformat(),'url':'https://lattes.cnpq.br/'+lid,'metodo':method}
 temp=target.with_suffix('.tmp');temp.write_text(document,encoding='utf-8');temp.replace(target)
 target.with_suffix('.meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache',type=Path,default=Path('/workspace/analise-lattes/cache'));ap.add_argument('--cadastro',type=Path,default=PROJECT/'docentes.csv');ap.add_argument('--id',help='ID de um docente; omita para processar o grupo.');ap.add_argument('--importar',type=Path,help='HTML salvo após abrir o currículo completo.');ap.add_argument('--coletar',action='store_true',help='Coletar por navegador no fluxo público resumo → Abrir currículo.');ap.add_argument('--fim',type=int,default=datetime.now().year);ap.add_argument('--inicio',type=int);ap.add_argument('--saida',type=Path,default=PROJECT/'dist');args=ap.parse_args()
 people=list(csv.DictReader(args.cadastro.open()));selected=[p for p in people if not args.id or p['id_lattes']==args.id]
 if not selected:ap.error('ID não cadastrado')
 if args.importar and (not args.id or args.coletar):ap.error('--importar exige --id e não pode ser combinado com --coletar')
 statuses=[]
 if args.importar:
  raw=args.importar.read_bytes()
  try:document=raw.decode('utf-8-sig')
  except UnicodeDecodeError:document=raw.decode('latin-1')
  store(document,selected[0],args.cache,'HTML completo salvo pelo usuário; nome e ID validados')
  print('IMPORTADO',selected[0]['nome'],flush=True)
 if args.coletar:
  from coletar_navegador import collect
  statuses=collect(selected,args.cache)
 if statuses:(PROJECT/'status-coleta.json').write_text(json.dumps({'tentativa_em':datetime.now(timezone.utc).isoformat(),'docentes':statuses},ensure_ascii=False,indent=2))
 # All output is built before replacing the published source files.
 staging=Path(tempfile.mkdtemp(prefix='lattes-build-'))
 try:
  if (args.saida/'dados.json').exists():shutil.copy2(args.saida/'dados.json',staging/'dados.json')
  command=[sys.executable,str(PROJECT/'extrair.py'),'--cache',str(args.cache),'--cadastro',str(args.cadastro),'--saida',str(staging),'--fim',str(args.fim)]
  if args.inicio is not None:command+=['--inicio',str(args.inicio)]
  subprocess.run(command,check=True)
  d=json.loads((staging/'dados.json').read_text());assert len(d['people'])==len(people)
  for generated in staging.iterdir():
   if generated.is_file():args.saida.mkdir(parents=True,exist_ok=True);shutil.copy2(generated,args.saida/generated.name)
 finally:shutil.rmtree(staging,ignore_errors=True)
 print('BASE PROCESSADA. Revise ultima-atualizacao.json e os status das fontes antes de publicar.',flush=True)
 if any(s['status']=='pendente' for s in statuses):print('Há coletas pendentes. Os HTMLs anteriores foram preservados; não são dados atualizados.',flush=True)
if __name__=='__main__':main()
