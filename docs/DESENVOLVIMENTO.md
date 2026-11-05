# Desenvolvimento e operação

## Organização

| Camada | Arquivos principais |
| --- | --- |
| Dados e cadastro | Cadastro local, `examples/demo-data.json`, JSONs gerados em `dist/` |
| Extração/atualização | `extrair.py`, `atualizar.py`, `orientacoes.py` |
| Coleta do ambiente original | `coletar_navegador.py`, `scripts/navegar-lattes.py` |
| Classificação | `classificacao/motor.py`, `criterios.py`, `regras.json`, `catalogo.json` |
| Interface | `index.template.html`, `dist/app.js`, `qual-*.js`, `orientation-*.js`, `review-*.js`, `cohort.js` |
| Exportações | `dist/table-exports.js`, geração Python em `extrair.py` |
| Servidor hospedado | `worker/index.mjs` |
| Esquema D1 | `db/schema.ts`, `drizzle/` |
| Desenvolvimento local | `tests/local-server.mjs` |

`dist/index.html` incorpora o retrato JSON usado na interface. Os JSONs também são distribuídos separadamente para integração. Alterar apenas um JSON não recompõe o conteúdo já incorporado no HTML; use o processamento ou uma regeneração deliberada do template.

## Ambiente local

Use Node 24+ para `node:sqlite`. Execute `npm ci` e `npm run dev`; o servidor atende apenas em `127.0.0.1` e informa a URL. A prévia contém uma identidade de desenvolvimento para testar a revisão manual e não deve ser exposta como servidor de produção.

Para SQLite persistente, na primeira execução:

```sh
mkdir -p .local
node tests/local-server.mjs 5173 .local/revisoes.sqlite
```

Nas próximas execuções com esse mesmo banco, acrescente `existing` para não reaplicar a criação inicial de tabelas:

```sh
node tests/local-server.mjs 5173 .local/revisoes.sqlite existing
```

Mantenha esse arquivo local fora do Git. O modo padrão de `npm run dev` usa banco em memória.

## Testes

```sh
python -m venv .venv
# Ative a venv correspondente ao seu sistema operacional.
python -m pip install -r requirements.txt
python scripts/verificar.py
```

Há testes de classificação, deduplicação, orientação, seleção de docentes, indicadores, decisões manuais e API. Nenhum desses testes unitários precisa consultar o CNPq.

Para os testes de navegador, instale Chrome/Chromium e ChromeDriver compatíveis. Os scripts detectam executáveis no PATH ou usam as variáveis `CHROME_BIN` e `CHROMEDRIVER`. Se não forem informados, o Selenium poderá tentar sua descoberta/gerenciamento padrão. Os artefatos de QA ficam em `.local/browser` ou no caminho indicado em `ATLAS_TEST_WORK`.

```sh
python tests/test_browser_demo.py
```

## Reprocessar HTMLs salvos

O pacote público inclui somente exemplos fictícios, sem dados ou HTMLs brutos de pessoas reais. Use uma pasta local de cache; cada currículo completo deve estar em um arquivo com o ID Lattes de 16 dígitos, sem extensão. O importador confere nome, ID e seção de produções antes de armazenar.

Exemplo de importação para uma saída de trabalho:

```sh
python atualizar.py --cadastro .local/docentes.csv --cache ./html-cache --saida ./outputs/importacao --importar /caminho/curriculo.html --id SEU_ID_LATTES_16_DIGITOS --inicio 2022 --fim 2026
```

Durante a preparação do cache, a saída separada evita substituir o retrato distribuído em `dist/`. Docentes sem HTML ficam com coleta pendente. Para reproduzir o grupo completo, disponibilize os HTMLs dos docentes correspondentes ao cadastro.

Depois de montar o cache, processe em uma pasta de trabalho:

```sh
python atualizar.py --cadastro .local/docentes.csv --cache ./html-cache --saida ./outputs/processado --inicio 2022 --fim 2026
```

Confira fontes, datas, metadados e diferenças antes de substituir a base da interface.

## Parser bibliográfico externo

O projeto original usou o scriptLattes de https://github.com/jpmenachalco/scriptLattes, no commit `fb713a1b77eb954910cee48bd275e714267f61cd`. Ele é uma dependência externa, não foi incorporado a este repositório.

Para habilitar o enriquecimento com o mesmo parser, obtenha esse checkout e suas dependências e configure `SCRIPTLATTES_ROOT` com o diretório que contém o pacote `scriptLattes`. Exemplo Linux/macOS:

```sh
git clone https://github.com/jpmenachalco/scriptLattes.git .local/scriptLattes
git -C .local/scriptLattes checkout fb713a1b77eb954910cee48bd275e714267f61cd
python -m pip install -r .local/scriptLattes/requirements.txt
export SCRIPTLATTES_ROOT="$PWD/.local/scriptLattes"
```

Sem o parser, o fallback preserva referências e anos inequívocos, mas pode deixar títulos/autores/metadados incompletos. Não presuma reprodução idêntica da classificação depois de um processamento sem essa dependência e sem as mesmas fontes.

## Coleta online

O coletor original navega pelo resumo público do CNPq e usa o botão Abrir currículo, valida a identidade e preserva versões anteriores. Ele depende dos caminhos, Docker, Chromium e certificados do ambiente original do ChatGPT. Os detalhes estão em `docs/AMBIENTE_ORIGINAL.md`.

Não é um coletor portátil pronto para qualquer máquina. O cadastro nominal real não é distribuído; prepare-o localmente e preserve sua autorização de uso. Para outro ambiente, adapte as dependências ou use a importação de HTMLs completos. CAPTCHA interativo deve ser resolvido pelo fluxo normal do CNPq; uma coleta pendente não deve substituir silenciosamente um HTML válido.

## Publicação e autenticação

O Worker usa `ASSETS` para a interface e `DB` para D1. As migrações em `drizzle/` são de esquema e não semeiam dados nem decisões reais. Não modifique uma migração já aplicada; gere uma nova com `npm run db:generate` quando houver mudança de esquema.

O exemplo `.openai/hosting.example.json` contém apenas os bindings lógicos. Para um novo Site, registre sua própria identidade e crie a configuração local `.openai/hosting.json`; ela está ignorada no Git desta cópia. O script `scripts/build-hosted.py` espera essa configuração e gera um pacote fora do checkout.

Na hospedagem original, o Sites injeta identidade autenticada. A variável de servidor `REVIEW_OWNER_EMAIL` autoriza alterações nas decisões, enquanto o ID autenticado é registrado no histórico. Valores de produção e credenciais não estão no Git.

Se o projeto for incorporado a outro provedor ou aplicação, substitua a autenticação por uma integração confiável desse ambiente. Não aceite cabeçalhos `oai-authenticated-user-*` diretamente de clientes como prova de identidade. O servidor local de QA é exclusivamente de desenvolvimento e não implementa autenticação de produção.
