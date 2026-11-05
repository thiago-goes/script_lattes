import copy,json,unittest
from pathlib import Path
from classificacao.motor import classify,consolidate,POT,INC,NONE
from classificacao.revisao import load_reviews,review_key
RULES=json.loads((Path(__file__).resolve().parents[1]/'classificacao/regras.json').read_text())
def record(id='r1',owner='p1',kind='Artigos completos publicados em periódicos',group='Produção bibliográfica',title='Pesquisa sobre arquitetura e território',year=2024,reference=None,authors='SILVA, A.; SOUZA, B.',doi=''):
 return {'id':id,'id_lattes_docente':owner,'docente':owner,'tipo':kind,'grupo':group,'titulo':title,'ano':year,'autores':authors,'doi':doi,'fonte':'https://lattes.cnpq.br/'+owner,'referencia_original':reference or f'{authors}. {title}. Revista de Arquitetura, v. 2, p. 10-20, {year}.'}
class ClassificationTests(unittest.TestCase):
 def test_article_has_preliminary_state_without_qualis(self):
  d=classify(record(),RULES);self.assertEqual((d['tipo_bibliografico'],d['estado']),('artigo',POT));self.assertTrue(d['necessita_conferencia']);self.assertNotIn('qualis',d)
 def test_artifact_nature_does_not_depend_only_on_lattes_heading(self):
  r=record(group='Produção técnica',kind='Trabalhos técnicos',title='Projeto arquitetônico do museu da cidade',reference='SILVA, A.. Projeto arquitetônico do museu da cidade. 2024. Projeto executado e exposto em acervo público.')
  d=classify(r,RULES);self.assertEqual(d['grande_categoria'],'artistica');self.assertEqual(d['estado'],POT)
 def test_type_alone_is_not_enough(self):
  r=record();r['autores']='';self.assertEqual(classify(r,RULES)['estado'],INC)
 def test_book_and_chapter(self):
  for kind,key,ref in [('Livros publicados/organizados ou edições','livro','SILVA, A.. Pesquisa sobre arquitetura e território. 1. ed. Goiânia: Editora UFG, 2024.'),('Capítulos de livros publicados','capitulo','SILVA, A.. Pesquisa sobre arquitetura e território. In: SOUZA, B. Livro de Arquitetura. Goiânia: UFG, 2024.')]:
   d=classify(record(kind=kind,reference=ref),RULES);self.assertEqual((d['tipo_bibliografico'],d['estado']),(key,POT))
 def test_complete_anais_is_distinct_from_abstracts_and_presentation(self):
  d=classify(record(kind='Trabalhos completos publicados em anais de congressos',reference='SILVA, A.. Pesquisa sobre arquitetura e território. In: Congresso AUD, 2024. Anais do Congresso. p. 1-10.'),RULES);self.assertEqual((d['tipo_bibliografico'],d['estado']),('anais',POT))
  for typ in ['Resumos publicados em anais de congressos','Resumos expandidos publicados em anais de congressos','Apresentações de Trabalho']:
   d=classify(record(kind=typ),RULES);self.assertNotEqual(d['tipo_bibliografico'],'anais');self.assertEqual(d['estado'],NONE)
 def test_guide_duplicate_across_lattes_subcategories(self):
  a=record(kind='Trabalhos técnicos',group='Produção técnica',title='Guia de manutenção das edificações públicas',reference='SILVA, A.; SOUZA, B.. Guia de manutenção das edificações públicas. Editora UFG, 2024. Manual técnico.')
  b={**a,'id':'r2','tipo':'Desenvolvimento de material didático ou instrucional','referencia_original':a['referencia_original']+' (Material instrucional).'}
  original=copy.deepcopy([a,b]);p,_,_=consolidate([a,b],RULES);self.assertEqual(len(p),1);self.assertEqual(len(p[0]['participacoes']),1);self.assertEqual(p[0]['duplicatas_internas'],1);self.assertEqual([a,b],original)
 def test_coauthor_participation_is_preserved(self):
  a=record(doi='https://doi.org/10.1234/abc');b={**a,'id':'r2','docente':'p2','id_lattes_docente':'p2'}
  p,_,_=consolidate([a,b],RULES);self.assertEqual(len(p),1);self.assertEqual(len(p[0]['participacoes']),2)
 def test_course_is_not_organized_event(self):
  d=classify(record(group='Produção técnica',kind='Demais tipos de produção técnica',title='Curso de extensão em arquitetura hospitalar',reference='SILVA, A.. Curso de extensão em arquitetura hospitalar. 2024. Curso ministrado.'),RULES);self.assertEqual(d['estado'],INC);self.assertNotEqual(d['tipo_capes'],'Evento Organizado')
 def test_music_without_adherence_is_uncertain(self):
  d=classify(record(group='Produção artística/cultural',kind='Música',title='Concerto de violão',reference='SILVA, A.. Concerto de violão. 2024. Música.'),RULES);self.assertEqual(d['estado'],INC)
 def test_manual_and_teaching_material_not_automatic_technical_bibliography(self):
  for title in ['Guia de manutenção das edificações públicas','Material didático para o ensino de urbanismo']:
   d=classify(record(group='Produção técnica',kind='Demais tipos de produção técnica',title=title),RULES);self.assertEqual(d['estado'],INC)
 def test_consultancy_and_portfolio_are_not_automatically_qualified(self):
  for title in ['Consultoria para um escritório de arquitetura','Portfólio de projetos arquitetônicos']:
   self.assertEqual(classify(record(group='Produção técnica',kind='Trabalhos técnicos',title=title),RULES)['estado'],INC)
 def test_distinct_publication_contexts_are_not_merged_by_title(self):
  a=record();b={**a,'id':'r2','referencia_original':a['referencia_original'].replace('Revista de Arquitetura','Revista de Urbanismo')};p,_,_=consolidate([a,b],RULES);self.assertEqual(len(p),2);self.assertTrue(all(x['possivel_duplicidade'] for x in p))
 def test_unchanged_record_reuses_classification_despite_number_change(self):
  a=record();_,cache,_=consolidate([a],RULES);_,_,stats=consolidate([{**a,'id':'r99'}],RULES,cache=cache);self.assertEqual(stats['classificacoes_reutilizadas'],1)
 def test_conflicting_years_require_review(self):
  a=record(doi='10.1234/abc');b={**a,'id':'r2','ano':2025};p,_,_=consolidate([a,b],RULES);self.assertEqual(p[0]['estado'],INC);self.assertIsNone(p[0]['ano'])
 def test_accepted_article_is_uncertain(self):self.assertEqual(classify(record(kind='Artigos aceitos para publicação'),RULES)['estado'],INC)

class ReviewCacheTests(unittest.TestCase):
 def test_intellectual_property_need_not_be_a_patent(self):
  r=record(group='Produção técnica',kind='Produtos tecnológicos',title='Registro de marca do laboratório de urbanismo',reference='AUTOR FICTÍCIO, A.. Registro de marca do laboratório de urbanismo. INPI, registro nº de exemplo. 2024.')
  d=classify(r,RULES);self.assertEqual(d['tipo_capes'],'Ativos de Propriedade Intelectual');self.assertEqual(d['estado'],POT)
 def test_changing_one_review_invalidates_only_that_cached_decision(self):
  a=record();b={**a,'id':'b','titulo':'Outro estudo arquitetônico fictício'}
  _,cache,_=consolidate([a,b],RULES,reviews={})
  p,_,stats=consolidate([a,b],RULES,cache=cache,reviews={review_key(a):{'justificativa':'Decisão fictícia revista'}})
  self.assertEqual(stats['classificacoes_reutilizadas'],1);self.assertEqual(stats['classificacoes_recalculadas'],1)
if __name__=='__main__':unittest.main()
