# Atlas Lattes — código para análise de produção e orientações

Código do dashboard desenvolvido para apoiar levantamentos de produção intelectual e experiência de orientação. Inclui extração de HTML Lattes, classificação preliminar CAPES/AU, seleção de docentes, revisão manual e exportações Excel/CSV/Word.

**Repositório:** https://github.com/thiago-goes/script_lattes

**Este repositório público contém somente código e exemplos fictícios.** Não distribui currículos, produção, orientações ou decisões de pessoas reais. Os dados de trabalho da aplicação original não foram publicados aqui.

- [Guia de integração com o projeto do campus](docs/INTEGRACAO_CAMPUS.md)
- [Instalação, extração e hospedagem](docs/DESENVOLVIMENTO.md)
- [Classificação, evidências e limites](classificacao/IMPLEMENTACAO.md)

## Executar a demonstração

Requisito: **Node.js 24 ou superior**.

```sh
git clone https://github.com/thiago-goes/script_lattes.git
cd script_lattes
npm ci
npm run dev
```

Abra **http://127.0.0.1:5173**. O comando prepara uma base com nomes, produtos e orientações inteiramente fictícios. A demonstração não consulta o CNPq e não se conecta ao banco da aplicação original.

O servidor local usa SQLite em memória e uma identidade de desenvolvimento, somente em loopback. As decisões desse modo duram até reiniciar o servidor. O guia explica como usar SQLite local persistente.

## O que o programador encontra

- Produção geral e qualificada, com grupos, totais, filtros e coautorias.
- Classificador CAPES/AU, catálogo de ajuda e evidências de enquadramento.
- Revisão humana separada da sugestão automática, histórico e controle de versão.
- Orientações por modalidade e papel, com critérios CAPES e UFG independentes.
- Painel de seleção do grupo docente e indicadores calculados sobre esse grupo.
- Worker de hospedagem, esquema D1, testes e geração de relatórios.

Os arquivos `dist/*.json` e `dist/index.html` são gerados localmente, não versionados. A amostra sintética fica em `examples/demo-data.json`. O cadastro `docentes.csv` contém somente cabeçalhos; use um cadastro local autorizado para dados reais.

## Verificações

```sh
npm test
```

Para a parte Python, use Python 3.12 e uma venv:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/verificar.py
```

O teste de navegador precisa de Chrome/Chromium e ChromeDriver compatíveis:

```sh
python tests/test_browser_demo.py
```

Os executáveis podem ser indicados por `CHROME_BIN` e `CHROMEDRIVER`.

## Usar outras fontes

A extração atual usa **HTML**, não XML. Dados reais devem ser fornecidos localmente, com cadastro, fontes, datas e autorização adequados ao projeto. O processamento não preenche metadados ausentes como se fossem confirmados.

O coletor online original depende de Docker/Chromium do ambiente gerenciado e pode exigir adaptação em outra máquina. CAPTCHA interativo continua exigindo intervenção. A demonstração não oferece coleta fictícia nem promete acesso automático ao CNPq.

## Publicação e colaboração

Seu colega pode clonar este repositório ou baixar o ZIP pelo botão Code do GitHub. Alterações aqui não publicam automaticamente a aplicação original.

A configuração `.openai/hosting.example.json` tem apenas os bindings lógicos. Não contém ID da implantação existente, credenciais nem variáveis de produção. O banco de revisões da aplicação original não faz parte do repositório.

Para hospedar em outro provedor, configure banco e autenticação próprios. O Worker original utiliza identidade fornecida pelo ChatGPT Sites; em outra infraestrutura, não aceite esses cabeçalhos diretamente de visitantes como prova de identidade.

A classificação é preliminar e específica ao recorte CAPES/AU documentado. Para um levantamento de todo o campus, adapte os critérios às áreas envolvidas. A procedência do código está em `PROVENIENCIA.json`.
