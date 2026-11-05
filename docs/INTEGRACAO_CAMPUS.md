# Integração com o levantamento de produção do campus

## Começar pelo modelo de dados e pelos exemplos

O repositório distribui somente exemplos fictícios em `examples/demo-data.json`. `npm run dev` gera os JSONs correspondentes em `dist/`. Para dados reais, utilize arquivos locais autorizados; eles não foram publicados no GitHub. O modelo de dados abaixo também se aplica a essas fontes locais.

```python
import json
from pathlib import Path

base = json.loads(Path('dist/dados.json').read_text(encoding='utf-8'))
docentes = base['people']
producoes = base['records']

orientacoes = json.loads(
    Path('dist/orientacoes.json').read_text(encoding='utf-8')
)['records']
```

Mantenha identificadores Lattes como **strings**. O nome é um atributo de exibição; o identificador é mais adequado para relacionar docentes entre sistemas.

## Modelos de dados

### Produção original — `dist/dados.json`

`people`: `id_lattes`, `nome`, `status_coleta`, `coletado_em`, `atualizacao_cv` e metadados do cadastro.

`records`: `id`, `id_lattes_docente`, `docente`, `grupo`, `tipo`, `ano`, `titulo`, `autores`, `referencia_original`, `fonte`, `doi` e `metodo_ano`.

Os grupos são `Produção bibliográfica`, `Produção técnica` e `Produção artística/cultural`. O campo `tipo` preserva a seção Lattes. Valores ausentes não devem ser preenchidos como se fossem informação confirmada.

O `id` original inclui posição na extração e pode mudar quando o currículo é reordenado. Não o use sozinho como chave permanente de um produto. Preserve o ID docente e a referência original para conferência.

### Produtos classificados — `dist/qualificacao.json`

`produtos` contém `produto_id`, ano, título, referência, natureza CAPES, tipo sugerido, estado, regra, justificativa, fontes e pendências. Cada produto guarda `participacoes` por docente e `registros_origem` com os registros que o sustentam.

Os estados são `Potencialmente qualificada`, `Enquadramento incerto` e `Sem enquadramento identificado`. São sugestões automáticas/assistidas. Uma decisão humana do GT é uma camada separada, persistida no D1.

O mesmo produto pode contar uma vez para cada docente coautor e uma vez no total coletivo de produtos únicos. Por isso, a contagem de `records`, a de participações e a de produtos únicos têm significados diferentes. Não elimine coautorias nem some novamente registros repetidos dentro do mesmo currículo.

O ID consolidado se apoia em DOI, referência ou combinação de metadados. Alterações relevantes e novas fusões podem mudar a identidade; preserve a rastreabilidade, detecte conflitos e não aplique uma decisão antiga a um texto diferente automaticamente.

### Orientações — `dist/orientacoes.json`

`records` guarda `id`, `docente_id`, `orientando`, `titulo`, `modalidade`, `ano`, `ano_inicio`, `ano_conclusao`, `situacao`, `papel`, `instituicao`, `curso_programa`, `programa_institucional`, indicadores de vínculo UFG, referência, fonte e pendências.

Modalidades: `ic`, `it`, `tcc`, `especializacao`, `mestrado`, `doutorado` e `outras`. Situação: `concluida` ou `andamento`. Papéis incluem `principal`, `coorientacao`, `supervisao` e `nao_informada`.

O ID deriva do conteúdo; um texto alterado pode receber novo ID. Repetições exatas são consolidadas; coincidências ambíguas são sinalizadas. Um registro com vários orientandos não é multiplicado automaticamente.

## Indicadores e cuidados de integração

- A produção geral contabiliza registros Lattes; não é uma certificação de produção qualificada.
- A classificação técnica/artística exige natureza e evidências. Projeto profissional convencional não é automaticamente produção artística qualificada.
- Manuais e outros tipos da lista geral AUD não são automaticamente equiparados aos dez tipos específicos de AU.
- A soma principal de orientação reúne IC, especialização, mestrado e doutorado. TCC está separado.
- O critério UFG de 75% não equivale à existência de qualquer IC: é necessário verificar o programa institucional UFG para IC/IT. O critério CAPES de quatro TCC/IC é independente.
- O histórico de orientação não é limitado automaticamente à janela recente da produção intelectual.
- Seção ausente, coleta pendente, ano sem cobertura e produção zero são situações distintas.
- A seleção no painel é uma preferência de análise do navegador; não representa exclusão do docente na base original.

## Adaptar para mais docentes

1. Prepare um cadastro local autorizado, fora do Git público, com IDs Lattes e nomes conferidos. `id_interno` é usado pelo coletor original de resumo público.
2. Separe o armazenamento dos HTMLs brutos do banco processado e registre datas e hashes das fontes.
3. Use extração, normalização, deduplicação, sugestão CAPES e revisão humana como etapas separadas.
4. Conserve versões e decisões humanas; sinalize novos registros, fontes alteradas e conflitos.
5. Defina o grupo analisado explicitamente ao calcular percentuais e coautorias.
6. Preserve as referências originais e os motivos de cada enquadramento.

O cadastro atual é um recorte de Arquitetura e Urbanismo. O catálogo CAPES está orientado à Área 29/subárea AU; não deve ser aplicado como regra universal de qualificação de todas as áreas do campus.

## Revisões humanas e publicação

`db/schema.ts` e `drizzle/` descrevem duas tabelas: decisão atual e histórico. A API e a lógica de aplicação da revisão ficam em `worker/index.mjs` e `dist/review-core.js`. A assinatura das fontes e a versão da decisão impedem sobrescritas silenciosas.

Para incorporar as decisões da aplicação hospedada, combine com o responsável a exportação do backup JSON pelo painel. Esta cópia Git não contém o banco de produção nem credenciais de acesso a ele.

O GitHub é uma cópia de colaboração da versão entregue. Alterações aqui não publicam automaticamente no Site existente. Combine a integração e a publicação com o responsável antes de substituir versões ou migrar dados.
