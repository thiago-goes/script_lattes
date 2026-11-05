"""Worker de coleta por navegação pública; executado em contêiner descartável."""
import json,os,re,tempfile,time
from datetime import datetime,timezone
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sys
sys.path.insert(0,'/app')
from atualizar import validate
people=json.loads(Path('/input.json').read_text());output=Path('/output');statuses=[]
os.environ['NO_PROXY']='localhost,127.0.0.1,'+os.environ.get('NO_PROXY','')
options=webdriver.ChromeOptions();options.binary_location='/workspace/tools/chromium/usr/lib/chromium/chromium'
for f in ['--headless=new','--no-sandbox','--disable-dev-shm-usage','--user-data-dir='+tempfile.mkdtemp(prefix='lattes-')]:options.add_argument(f)
proxy=os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
if proxy:options.add_argument('--proxy-server='+proxy)
with webdriver.Chrome(service=Service('/workspace/tools/chromium/usr/bin/chromedriver'),options=options) as driver:
 driver.set_page_load_timeout(45);wait=WebDriverWait(driver,35)
 for i,person in enumerate(people):
  lid=person['id_lattes'];name=person['nome'];print('COLETANDO',name,flush=True)
  try:
   handles=driver.window_handles
   for handle in handles[1:]:driver.switch_to.window(handle);driver.close()
   driver.switch_to.window(handles[0]);driver.switch_to.default_content()
   driver.get('https://buscatextual.cnpq.br/buscatextual/preview.do?metodo=apresentar&id='+person['id_interno'])
   if driver.title=='Privacy error':raise RuntimeError('Falha de confiança TLS no navegador isolado')
   summary_name=driver.find_element(By.TAG_NAME,'body').text
   # The subsequent full curriculum must pass both the name and Lattes-ID checks.
   wait.until(lambda d:d.execute_script("return typeof abreCV === 'function' && typeof grecaptcha !== 'undefined'"))
   button=wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a[onclick="abreCV()"]')));button.click()
   wait.until(lambda d:len(d.window_handles)>1);driver.switch_to.window(driver.window_handles[-1])
   wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'h2.nome')))
   document=driver.page_source;validate(document,person)
   path=output/(lid+'.html');path.write_text(document,encoding='utf-8');path.chmod(0o644)
   statuses.append({'id_lattes':lid,'nome':name,'status':'atualizado','coletado_em':datetime.now(timezone.utc).isoformat()})
   print('COLETADO',name,len(document),'caracteres',flush=True)
  except Exception as exc:
   text=driver.find_element(By.TAG_NAME,'body').text.casefold() if driver.window_handles else ''
   reason='CNPq solicitou verificação de segurança; intervenção necessária' if 'código de segurança' in text else type(exc).__name__+': coleta pelo navegador não concluída'
   statuses.append({'id_lattes':lid,'nome':name,'status':'pendente','motivo':reason});print('PENDENTE',name,reason,flush=True)
  finally:
   status=output/'status.json';status.write_text(json.dumps(statuses,ensure_ascii=False,indent=2));status.chmod(0o644)
  if i+1<len(people):time.sleep(2)
