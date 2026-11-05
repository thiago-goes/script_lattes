"""Aplicação de decisões interpretativas, vinculadas ao conteúdo exato do Lattes."""
import copy
from .motor import digest

FIELDS=('id_lattes_docente','grupo','tipo','ano','titulo','autores','referencia_original','doi')
def review_key(record):
 return digest({k:record.get(k,'') for k in FIELDS})

def load_reviews(path):
 if not path.exists():return {}
 import json
 data=json.loads(path.read_text());result={}
 for item in data['itens']:
  key=item['chave_conteudo'];decision=item['decisao']
  if key in result:assert result[key]==decision,'Decisões divergentes para o mesmo conteúdo'
  result[key]=decision
 return result

def apply_review(record,decision,review):
 result=copy.deepcopy(decision)
 if review:
  result.update(copy.deepcopy(review))
  result['revisao_interpretativa']='Leitura assistida do registro Lattes; não validada pelo docente ou pelo GT'
 elif record.get('grupo')=='Produção técnica':
  result['revisao_interpretativa']='Registro novo ou alterado: leitura interpretativa pendente'
 return result
