import unittest
from orientacoes import parse_reference,extract
P={'id_lattes':'1234567890123456','nome':'Docente Exemplo'}
class OrientationTests(unittest.TestCase):
 def row(self,heading='Iniciação científica',state='concluida',tail='Iniciação Científica (Graduando em Arquitetura) - Universidade Federal de Goiás. Orientador: Docente Exemplo.',year='2020'):
  return parse_reference('Estudante Exemplo. Pesquisa do ambiente construído. '+year+'. '+tail,heading,state,P)
 def test_ic_concluida_and_historical_year(self):
  r=self.row();self.assertEqual((r['modalidade'],r['ano_conclusao'],r['papel']),('ic',2020,'principal'));self.assertTrue(r['instituicao_ufg']);self.assertFalse(r['institucional_ufg'])
 def test_ic_ongoing_has_start_not_completion(self):
  r=parse_reference('Estudante. Estudo urbano. Início: 2026. Iniciação científica (Graduando em Arquitetura) - Universidade Federal de Goiás. (Orientador).','Iniciação científica','andamento',P);self.assertEqual((r['ano_inicio'],r['ano_conclusao'],r['situacao']),(2026,None,'andamento'))
 def test_pibiti_is_it_and_program_institutional(self):
  r=self.row(tail='PIBITI. Iniciação Tecnológica (Graduando em Arquitetura) - Universidade Federal de Goiás. Orientador: Docente Exemplo.');self.assertEqual(r['modalidade'],'it');self.assertTrue(r['institucional_ufg'])
 def test_modalities_and_coorientation(self):
  for heading,kind in [('Trabalho de conclusão de curso de graduação','tcc'),('Monografia de conclusão de curso de aperfeiçoamento/especialização','especializacao'),('Dissertação de mestrado','mestrado'),('Tese de doutorado','doutorado'),('Orientações de outra natureza','outras')]:self.assertEqual(self.row(heading=heading)['modalidade'],kind)
  self.assertEqual(self.row(tail='Dissertação (Mestrado em Arquitetura) - Universidade de Brasília. Coorientador: Docente Exemplo.')['papel'],'coorientacao')
 def test_missing_year_and_institution_are_not_invented(self):
  r=parse_reference('Estudante. Estudo urbano. Orientador: Docente Exemplo.','Iniciação científica','concluida',P);self.assertIsNone(r['ano']);self.assertFalse(r['instituicao']);self.assertTrue(r['pendencias'])
 def test_institution_without_parenthesized_course(self):
  r=self.row(tail='Iniciação Científica - Universidade Federal de Goiás. Orientador: Docente Exemplo.');self.assertEqual(r['instituicao'],'Universidade Federal de Goiás')
 def test_external_pibic_is_not_ufg(self):
  r=self.row(tail='PIBIC. Iniciação Científica (Graduando em Arquitetura) - Universidade de Brasília. Orientador: Docente Exemplo.');self.assertFalse(r['institucional_ufg'])
 def test_missing_section_is_unknown_and_no_bancas_are_extracted(self):
  r,found=extract('<div class="title-wrapper"><h1>Bancas</h1><div class="layout-cell-11">Pessoa. Trabalho. 2025.</div></div>',P);self.assertFalse(found);self.assertEqual(r,[])
 def test_structural_headings_and_original_reference(self):
  ref='Estudante. Estudo. 2020. Iniciação Científica - Universidade Federal de Goiás. Orientador: Docente.'
  doc='<div class="title-wrapper"><h1>Orientações</h1><div class="inst_back">Orientações e supervisões concluídas</div><div class="cita-artigos">Iniciação científica</div><div class="layout-cell-11">'+ref+'</div></div>'
  r,found=extract(doc,P);self.assertTrue(found);self.assertEqual(r[0]['referencia_original'],ref)
if __name__=='__main__':unittest.main()
