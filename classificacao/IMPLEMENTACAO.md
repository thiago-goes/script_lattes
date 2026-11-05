# Classificação preliminar, revisão humana e orientações

Esta distribuição pública contém código e exemplos sintéticos, sem currículos ou dados pessoais reais.

## Camadas

Lattes HTML → extração → normalização → deduplicação → sugestão CAPES → revisão humana → indicadores e relatórios. A base original, a sugestão automática e a decisão humana são preservadas separadamente.

- motor.py: classificação, consolidação, coautoria, cobertura e cache.
- criterios.py: salvaguardas de natureza/evidência.
- regras.json e catalogo.json: tipos, hipóteses e ajuda contextual.
- fontes.json: referências oficiais e sua hierarquia.
- revisao.py: aplicação de decisões assistidas vinculadas ao conteúdo exato. O arquivo distribuído de revisões é vazio.
- dist/review-core.js e worker/index.mjs: aplicação e persistência da revisão humana, com versão, assinatura da fonte e histórico.
- orientacoes.py e dist/orientation-core.js: extração e critérios de experiência de orientação.

## Produção

Artigos, livros, capítulos e trabalhos completos em anais são examinados por natureza e evidências bibliográficas. Resumos e apresentações não equivalem a artigos/anais completos. O cenário sem anais é filtro interno, não uma proibição normativa da CAPES. Não há Qualis, notas ou seleção automática de destaques.

Projetos convencionais, reformas, execução, instalações, levantamento e maquetes não se qualificam automaticamente como produção artístico-cultural. Indícios de investigação criativa, circulação, seleção ou reconhecimento sustentam candidatos, sujeitos a conferência. Um prêmio não substitui avaliação de qualidade e aderência.

Laudo ou parecer técnico profissional é distinto de avaliação acadêmica. Serviço de consultoria sem entrega identificável não vira relatório conclusivo. Finalidade social isolada não comprova tecnologia social; conta/site não comprova produto de comunicação estruturado; curso não comprova organização de evento. Relatórios regulares de finalização de projetos financiados não são automaticamente RTC.

Tipos da lista geral AUD, como Manual/Protocolo e Material Didático, não equivalem automaticamente aos dez tipos específicos AU. O catálogo diferencia os escopos. Confirmar uma tipologia geral no GT não resolve, por si, o enquadramento específico AU.

## Estados, identidade e revisão

Os estados são Potencialmente qualificada, Enquadramento incerto e Sem enquadramento identificado. Todos preservam justificativas, referências e fontes. A decisão humana pode confirmar/alterar, deixar pendente, rejeitar e reverter, sem apagar a sugestão automática ou o histórico.

A assinatura do conteúdo identifica alterações da fonte; decisões conflitantes são preservadas mas não reaplicadas silenciosamente. Repetições internas e coautorias têm tratamento distinto. Registros de naturezas diferentes não são fundidos somente por título. IDs posicionais da extração não devem ser usados isoladamente como identidade permanente.

No servidor, D1 mantém a decisão atual e o histórico. Escritas exigem a identidade autenticada do responsável. A implementação original depende do mecanismo de identidade do Sites; outra hospedagem exige autenticação confiável própria.

## Orientações e grupo docente

Orientações concluídas/em andamento, modalidade e papel são extraídos de seções próprias do HTML; bancas não viram orientações. Nome, título, anos, instituição e programa são preservados quando identificáveis. Ausências e ambiguidades não são inventadas ou tratadas como certeza.

O agregado principal soma IC, especialização, mestrado e doutorado. TCC permanece separado. A referência UFG de 75% exige observar programas institucionais IC/IT da UFG e pós-graduação; ela não é simplesmente a presença de qualquer IC. A referência CAPES de quatro TCC/IC concluídos é independente. Coorientações e andamento não substituem automaticamente orientação principal concluída.

Os critérios usam o histórico completo, sem receber a janela recente da produção por inferência. O percentual do grupo usa os docentes marcados no painel; inspecionar um docente não muda esse denominador. Preferências de seleção no navegador não apagam fontes ou decisões do servidor.

## Fontes e limites

APCN 2026 da Área 29, Documento de Área AUD 2025–2028, PRPG/UFG e GTs CAPES 2019 são documentados no catálogo e em fontes.json. Tipologias operacionais, exemplos e heurísticas são identificados como apoio, não novas normas.

Referências Lattes não substituem íntegras, evidências de autoria/uso/circulação, comprovação documental de orientação, qualidade ou aderência à proposta. Seção ausente, ano sem cobertura e produção zero são distintos. O catálogo AU não deve ser aplicado como regra universal a todas as áreas do campus.
