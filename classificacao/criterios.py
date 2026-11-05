"""Salvaguardas de natureza/evidência: prevalecem sobre a leitura assistida antiga."""
import copy,re
from .motor import norm,POT,INC

def refine(record,decision,catalog=None):
 d=copy.deepcopy(decision);full=norm(record.get('referencia_original'));title=norm(record.get('titulo') or record.get('referencia_original'))
 project=bool(re.search(r'projeto|reforma|ampliacao|maquete|levantamento (?:cadastral|arquitetonico)|representacao espacial',title)) or d.get('subtipo_capes') in ('project','model')
 circulation=bool(re.search(r'projeto (?:premiado|selecionado)|premiad|bienal|expost[oa]|exibid|apresentad.{0,60}(?:exposicao|mostra|evento artistico)|selecionad.{0,60}(?:mostra|exposicao|concurso)|catalogo curatorial',full))
 creative=bool(re.search(r'investigacao (?:artistica|projetual)|projeto experimental|experimentacao (?:artistica|projetual)|processo criativo de pesquisa',full))
 research=bool(re.search(r'pesquisa|investigacao|experimental|cientific',full))
 d['evidencias_avaliadas']={'natureza_projetual':project,'circulacao_artistica_explicita':circulation,'investigacao_criativa_explicita':creative,'pesquisa_mencionada':research,'documentacao_integra':'Não consultada; referência do Lattes apenas'}
 def revise(kind,reason,rule,category=None):
  d['sugestao_anterior']={k:d.get(k) for k in ['estado','grande_categoria','tipo_capes','regra']}
  d.update(estado=INC,tipo_capes=kind,regra=rule,justificativa=reason,necessita_conferencia=True)
  if category:d['grande_categoria']=category
  d['pendencias']=list(dict.fromkeys(d.get('pendencias',[])+['Conferir entrega, autoria, vínculo com pesquisa e documentação; palavras no título não demonstram qualidade']))
 if record.get('grupo')=='Produção técnica' and d['grande_categoria']=='artistica' and d.get('subtipo_capes') in ('project','model'):
  if re.search(r'laudo tecnico|parecer tecnico|relatorio tecnico',title):
   revise('Relatório Técnico Conclusivo','Laudo/parecer profissional identificado na referência. A leitura assistida anterior sugeria natureza artística inadequada; corrigida para candidato técnico conclusivo, sujeito à conferência da íntegra e resultados.','T-CORRECAO-NATUREZA','tecnica');d['estado']=POT
   d['fontes']=list(dict.fromkeys(d.get('fontes',[])+['tecnico2019']));d['pendencias']=['Qualidade, impacto e aderência às linhas/projetos não verificados','Conferir íntegra do documento técnico, resultados, conclusões e autoria']
  elif re.search(r'responsavel tecnico execucao|rt execucao',title) and not re.search(r'projeto',title):
   revise('Serviço técnico / responsabilidade profissional','Responsabilidade por execução não demonstra produto artístico ou entrega intelectual autônoma. Corrigida a sugestão assistida anterior, preservando o serviço no panorama geral.','T-EXECUCAO-SEM-PRODUTO','tecnica')
 if d['grande_categoria']=='artistica' and project:
  d['natureza_projetual']='Investigação/criação documentada na referência' if creative else 'Circulação ou reconhecimento mencionado' if circulation else 'Projeto técnico com menção a pesquisa' if research else 'Projeto profissional ou representação convencional; caráter artístico não demonstrado'
  if not (circulation or creative):
   revise('Projeto/representação — enquadramento artístico-cultural não demonstrado','A referência identifica projeto ou representação, mas não demonstra criação/investigação artístico-cultural ou circulação pertinente. Projeto residencial, estrutural, executivo, reforma, levantamento e maquete não se tornam produção artística qualificada por sua simples existência. Verificar eventual produto técnico documentado, mantendo a referência original.','AC-PROJETO-INCERTO')
   d['enquadramento_alternativo']='Projeto técnico resultante de pesquisa/assessoria, caso haja entrega e evidências; não equivale automaticamente a Relatório Técnico Conclusivo.'
  else:
   d.update(estado=POT,regra='AC-PROJETO-INDICIOS',justificativa='A referência apresenta indício explícito de circulação/reconhecimento artístico ou investigação criativa. Candidato a análise artístico-cultural; prêmio/seleção/apresentação não comprova qualidade ou aderência à APCN. Conferir autoria, documentação e contexto.')
 if d['grande_categoria']=='tecnica':
  if d.get('tipo_capes')=='Tecnologia Social' and not re.search(r'participativ|socialmente construid|construcao coletiva|apropriacao comunitaria|reaplicad',full):
   revise('Tecnologia Social — processo participativo a comprovar','Finalidade social e proposta metodológica não comprovam, isoladamente, tecnologia social. Faltam indícios de construção participativa, aplicação/apropriação e resultados.','T-SOCIAL-INCERTO')
  if d.get('tipo_capes')=='Produto de Comunicação' and record.get('tipo')=='Redes sociais, websites e blogs':
   revise('Produto de Comunicação — estrutura e autoria a comprovar','Uma conta, página ou site tem potencial de divulgação, mas o registro não documenta uma produção estruturada nem distingue gestão do canal de criação de conteúdo técnico-científico. Conferir série, conteúdos, autoria, circulação e pesquisa.','T-CANAL-INCERTO')
  if d.get('tipo_capes')=='Relatório Técnico Conclusivo':
   explicit=bool(re.search(r'laudo|parecer tecnico|relatorio tecnico|relatorio final|relatorio de (?:pesquisa|viabilidade)|estudo tecnico|avaliacao pos ocupacional|analise d[oe] (?:desempenho|conforto|rtq)|diagnostic',full))
   consultancy=record.get('tipo')=='Assessoria e consultoria'
   regular=bool(re.search(r'relatorio.{0,140}(?:pibic|paep|edital universal|finalizacao regular|prestacao de contas)',full))
   generic=bool(re.fullmatch(r'relatorio final(?: de (?:pesquisa|extensao))?',title))
   if regular or generic or not explicit or (consultancy and not re.search(r'laudo|parecer tecnico|relatorio|estudo tecnico',full)):
    revise('Relatório Técnico Conclusivo — entrega a comprovar','Tema, assessoria ou diagnóstico como atividade não demonstra por si um documento conclusivo. Solicitar entrega técnica identificável, resultados e conclusões; não converter serviço em relatório por inferência.','T-ENTREGA-INCERTA')
    if regular:d['justificativa']='Relatório regular de finalização/prestação de contas de projeto ou programa financiado não é automaticamente RTC. O GT Produção Técnica 2019, §10, p. 52, exclui relatórios regulares desse tipo; verificar se existe um produto técnico autônomo distinto.'
 if catalog and d.get('tipo_capes') in catalog:d['catalogo_id']=d['tipo_capes']
 d['versao_criterios']='aud-3.0.0';return d
