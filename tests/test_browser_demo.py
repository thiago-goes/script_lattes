"""Integração de navegação, filtros e downloads reais, inclusive em iframe restrito."""
import json,os,shutil,tempfile,threading,time,zipfile,xml.etree.ElementTree as ET,csv,subprocess
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
ROOT=Path(__file__).resolve().parents[1];WORK=Path(os.environ.get('ATLAS_TEST_WORK',str(ROOT/'.local/browser')));WORK.mkdir(parents=True,exist_ok=True);DL=WORK/'downloads';DL.mkdir(exist_ok=True)
os.environ['XDG_CONFIG_HOME']=str(WORK/'config');os.environ['XDG_CACHE_HOME']=str(WORK/'cache');os.environ['NO_PROXY']='localhost,127.0.0.1,'+os.environ.get('NO_PROXY','')
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/embedded':
   self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<iframe style="width:1400px;height:1000px" src="/?view=qualified" sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox"></iframe>')
  else:super().do_GET()
preview=subprocess.Popen(['node',str(ROOT/'tests/local-server.mjs')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,cwd=ROOT);base_url=preview.stdout.readline().strip();assert base_url.startswith('http://127.0.0.1:'),base_url
o=webdriver.ChromeOptions();browser_binary=os.environ.get('CHROME_BIN') or shutil.which('chromium') or shutil.which('google-chrome')
if browser_binary:o.binary_location=browser_binary
driver_path=os.environ.get('CHROMEDRIVER') or shutil.which('chromedriver')
for f in ['--headless=new','--no-sandbox','--disable-dev-shm-usage','--user-data-dir='+tempfile.mkdtemp(dir=WORK)]:o.add_argument(f)
o.add_experimental_option('prefs',{'download.default_directory':str(DL),'download.prompt_for_download':False});o.set_capability('goog:loggingPrefs',{'browser':'ALL'})
try:
 with webdriver.Chrome(service=(Service(driver_path) if driver_path else Service()),options=o) as d:
  d.set_window_size(1450,1000);d.execute_cdp_cmd('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(DL)});wait=WebDriverWait(d,20)
  d.get(base_url+'/');wait.until(lambda _:d.execute_script('return window.AtlasReview&&AtlasReview.ready()'));assert 'TODOS OS DADOS SÃO FICTÍCIOS' in d.find_element(By.TAG_NAME,'body').text
  assert len(d.find_elements(By.CSS_SELECTOR,'#summary tbody tr'))==3
  d.find_element(By.ID,'cohort-toggle').click();wait.until(lambda _:d.execute_script("return document.getElementById('cohort-panel').getAnimations().every(a=>a.playState==='finished')"));d.find_element(By.ID,'cohort-none').click()
  for lid in ['demo-a','demo-b']:d.find_element(By.CSS_SELECTOR,'#cohort-list input[value="'+lid+'"]').click()
  d.find_element(By.ID,'cohort-apply').click();assert len(d.find_elements(By.CSS_SELECTOR,'#summary tbody tr'))==2
  d.find_element(By.ID,'tab-qualified').click();assert len(d.find_elements(By.CSS_SELECTOR,'#qa-summary tbody tr'))==2
  d.execute_script('AtlasCohort.set(["demo-a","demo-b","demo-c"])');product=d.execute_script("return AUDDiagnostic.data.produtos.find(p=>p.titulo_original.includes('residencial')).produto_id")
  d.execute_script('AtlasReview.open(arguments[0])',product);d.execute_script("document.getElementById('review-kind').value='Projeto arquitetônico, urbanístico, paisagístico, gráfico ou de produto';document.getElementById('review-notes').value='Revisão de exemplo totalmente fictícia para teste local.'")
  d.find_element(By.ID,'review-save').click();wait.until(lambda _:'Decisão salva no servidor' in d.find_element(By.ID,'review-save-status').text);d.find_element(By.CSS_SELECTOR,'[data-close="review-dialog"]').click()
  d.find_element(By.ID,'tab-orientations').click();headers=[h.text for h in d.find_elements(By.CSS_SELECTOR,'#or-summary th')];assert headers[1:5]==['IC','Especialização','Mestrado','Doutorado'];assert headers[-1]=='TCC graduação';assert 'IT' not in headers
  assert d.execute_script('return AtlasOrientations.analysis().rows.find(r=>r.id==="demo-c").experiencia_agregada')==0
  assert d.execute_script('return AtlasOrientations.analysis().rows.find(r=>r.id==="demo-c").capes')==4
  for file in DL.iterdir():file.unlink()
  d.find_element(By.ID,'or-word').click();time.sleep(.5)
  with zipfile.ZipFile(next(DL.glob('*.docx'))) as z:assert z.testzip() is None;ET.fromstring(z.read('word/document.xml'))
  d.set_window_size(430,900);assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth')
  assert not [e for e in d.get_log('browser') if e['level']=='SEVERE' and 'favicon.ico' not in e['message']]
  print('PASS: demonstração fictícia, seleção do grupo, revisão manual local, orientações e Word/celular.',flush=True)
finally:preview.terminate();preview.wait(timeout=15)
