"""Coleta reutilizável no ambiente configurado, com confiança TLS isolada por execução."""
import argparse,csv,json,os,shutil,subprocess,tempfile
from pathlib import Path
PROJECT=Path(__file__).resolve().parent
IMAGE='debian:trixie-slim@sha256:f6b08b09a05725f9431502d3b5714f5c4576e82c1a84fa1debe0c24a7e0c3ec4'
def collect(people,cache):
 from atualizar import store
 if not shutil.which('docker'):raise RuntimeError('O coletor por navegador exige o ambiente Docker configurado.')
 for p in people:
  if not p.get('id_interno'):raise ValueError('ID interno do CNPq não confirmado para '+p['nome'])
 work=Path(tempfile.mkdtemp(prefix='coleta-lattes-',dir='/workspace/work'))
 input_file=work/'input.json';input_file.write_text(json.dumps(people,ensure_ascii=False));output=work/'output';output.mkdir()
 mounts=[(PROJECT,'/app',True),(input_file,'/input.json',True),(output,'/output',False),('/usr/lib','/usr/lib',True),('/usr/share','/usr/share',True),('/usr/bin/certutil','/usr/bin/certutil',True),('/workspace/tools/chromium','/workspace/tools/chromium',True),('/workspace/venvs/scriptlattes','/workspace/venvs/scriptlattes',True),('/opt/codex/runtimes/codex-primary-runtime/dependencies/python','/opt/codex/runtimes/codex-primary-runtime/dependencies/python',True),('/usr/local/share/ca-certificates/environment-proxy-ca.crt','/run/proxy-ca.crt',True),('/etc/ssl/certs/ca-certificates.crt','/run/ca-bundle.pem',True)]
 command=['docker','--host=unix:///var/run/docker.sock','run','--rm']
 for source,target,readonly in mounts:
  if not Path(source).exists():raise FileNotFoundError('Recurso do ambiente indisponível: '+str(source))
  command+=['--mount',f'type=bind,src={Path(source).resolve()},dst={target}'+(',readonly' if readonly else '')]
 command+=['-e','SSL_CERT_FILE=/run/ca-bundle.pem',IMAGE,'/bin/sh','/app/scripts/iniciar-coleta.sh']
 env=os.environ.copy()
 for key in ['DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH']:env.pop(key,None)
 result=subprocess.run(command,env=env)
 if result.returncode or not (output/'status.json').exists():raise RuntimeError('O navegador não iniciou ou a coleta foi interrompida; nenhum HTML anterior foi substituído. Diagnóstico: '+str(work))
 statuses=json.loads((output/'status.json').read_text());by_id={p['id_lattes']:p for p in people}
 for status in statuses:
  if status['status']!='atualizado':continue
  path=output/(status['id_lattes']+'.html');document=path.read_text()
  store(document,by_id[status['id_lattes']],cache,'Coleta online por navegador: resumo público e botão Abrir currículo; nome e ID validados')
 print('Resumo da coleta:',sum(s['status']=='atualizado' for s in statuses),'de',len(people),'atualizados.',flush=True)
 return statuses

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--id',action='append');ap.add_argument('--cadastro',type=Path,default=PROJECT/'docentes.csv');ap.add_argument('--cache',type=Path,default=Path('/workspace/analise-lattes/cache'));args=ap.parse_args()
 people=list(csv.DictReader(args.cadastro.open()));selected=[p for p in people if not args.id or p['id_lattes'] in args.id]
 if not selected:ap.error('Nenhum docente selecionado')
 statuses=collect(selected,args.cache)
 if any(s['status']!='atualizado' for s in statuses):raise SystemExit(2)
if __name__=='__main__':main()
