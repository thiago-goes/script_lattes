import unittest,json
from pathlib import Path
from classificacao.motor import classify,consolidate,POT,INC
from classificacao.criterios import refine
from test_classificacao import record,RULES
class EvidenceTests(unittest.TestCase):
 def decision(self,title,ref=None,group='Produção artística/cultural'):
  r=record(group=group,kind='Artes visuais',title=title,reference=ref);return refine(r,classify(r,RULES))
 def test_conventional_projects_do_not_enter_artistic_total(self):
  for title in ['Projeto de reforma residencial','Projeto arquitetônico de residência','Projeto executivo de ampliação de edifício','Projeto de instalações e adequação de ambientes','Projeto urbanístico convencional','Maquete de residência']:
   d=self.decision(title);self.assertEqual(d['estado'],INC,title);self.assertIn('não demonstrado',d['tipo_capes'])
 def test_selection_and_award_are_only_preliminary_candidates(self):
  for evidence in ['Projeto selecionado para exposição pública de arquitetura','Projeto premiado em concurso de arquitetura','Investigação projetual experimental apresentada em exposição']:
   d=self.decision('Projeto arquitetônico experimental do museu','SILVA, A.. Projeto arquitetônico experimental do museu. 2024. '+evidence+'.');self.assertEqual(d['estado'],POT);self.assertTrue(d['necessita_conferencia']);self.assertIn('não comprova',d['justificativa'])
 def test_technical_project_does_not_automatically_become_art(self):
  d=self.decision('Projeto técnico de reforma de residência',group='Produção técnica');self.assertFalse(d['grande_categoria']=='artistica' and d['estado']==POT)
 def test_social_purpose_alone_is_not_technology_social(self):
  r=record(group='Produção técnica',title='Método de melhorias habitacionais');d=refine(r,{'grande_categoria':'tecnica','tipo_capes':'Tecnologia Social','estado':POT,'pendencias':[]});self.assertEqual(d['estado'],INC)
 def test_consultancy_without_document_is_not_report(self):
  r=record(group='Produção técnica',kind='Assessoria e consultoria',title='Assessoria para diagnóstico de imóvel tombado');d=refine(r,{'grande_categoria':'tecnica','tipo_capes':'Relatório Técnico Conclusivo','estado':POT,'pendencias':[]});self.assertEqual(d['estado'],INC)
 def test_assisted_project_decision_does_not_override_evidence_guard(self):
  from classificacao.revisao import review_key
  r=record(group='Produção técnica',kind='Trabalhos técnicos',title='Projeto convencional residencial fictício')
  reviewed={review_key(r):{'grande_categoria':'artistica','subtipo_capes':'project','tipo_capes':'Projeto arquitetônico','estado':POT}}
  p,_,_=consolidate([r],RULES,reviews=reviewed)
  self.assertEqual(p[0]['estado'],INC);self.assertIn('sugestao_anterior',p[0])
if __name__=='__main__':unittest.main()
