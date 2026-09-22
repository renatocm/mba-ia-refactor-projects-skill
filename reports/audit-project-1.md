# ARCHITECTURE AUDIT REPORT

**PHASE 1 e PHASE 2 concluídas. Nenhum arquivo foi alterado. PHASE 3 não iniciada.**

Foram identificados **15 findings**, ordenados por severidade: **2 CRITICAL, 6 HIGH, 6 MEDIUM e 1 LOW**. Nenhuma chamada deprecated foi confirmada no código inspecionado.

## PHASE 1 — PROJECT ANALYSIS

| Campo | Resultado |
|---|---|
| Projeto | `code-smells-project` |
| Raiz | `/Users/renatoalencar/Developer/Personal/MBA-IA/mba-ia-refactor-projects-skill/code-smells-project` |
| Revisão | `6d1ce6248c3e956801010a89d8bdaab48029bf30` |
| Estado local | Sem alterações indicadas no diretório auditado. Há diretórios não rastreados no projeto pai, fora do escopo. |
| Linguagem | **Python**; versão do runtime não declarada nem verificada |
| Framework | **Flask 3.1.1**, conforme `requirements.txt:1` |
| Dependências | Flask-CORS `5.0.1`; `sqlite3` da biblioteca padrão |
| Gerenciador | `pip`, conforme README; sem lockfile de dependências transitivas |
| Banco / ORM | **SQLite**, arquivo relativo `loja.db`; SQL direto, **sem ORM** |
| Domínio | **E-commerce**: catálogo, usuários, login, pedidos, itens, estoque e relatório de vendas |
| Arquitetura | **Monólito procedural com camadas parciais e responsabilidades misturadas** |
| Inicialização | `python app.py`; objeto WSGI `app`; criação de tabelas e seed no primeiro `get_db()` |
| Cobertura | **4 arquivos de código integralmente analisados e 2 auxiliares** |

**Inventário efetivamente lido:**

| Arquivo | Responsabilidade atual |
|---|---|
| `app.py` — 88 linhas | Configuração Flask, registro de rotas, administração com SQL direto e inicialização |
| `controllers.py` — 292 linhas | HTTP, validação, respostas, notificações simuladas e consulta direta ao banco |
| `models.py` — 314 linhas | Persistência, regras de pedidos/estoque, relatório e serialização |
| `database.py` — 86 linhas | Conexão global, criação do schema e seed automático |
| `requirements.txt` | Dependências diretas fixadas |
| `README.md` | Domínio declarado e instruções de execução |

A skill e suas três referências foram consultadas separadamente, sem entrar nessa contagem. Não foram encontrados testes, migrações, templates ou configuração de infraestrutura no diretório auditado.

**Arquitetura observada:**

```text
HTTP → app.py → controllers.py → models.py → database.py → SQLite
          │           │
          └───────────┴────────────────────→ acesso direto ao banco
```

Os nomes dos arquivos sugerem MVC, mas a separação é incompleta. Os “models” são funções que combinam consultas, regras comerciais e montagem de respostas. Os controllers também contêm políticas de validação e lógica de status. Não há camada independente de serviços nem entidades com invariantes. A apresentação é JSON; não existe interface HTML.

### Rotas e contratos atuais

Todas as rotas abaixo estão **sem proteção de autenticação/autorização implementada na aplicação**.

| Métodos | Caminho | Entrada / comportamento / saída |
|---|---|---|
| GET | `/` | Metadados e catálogo parcial de endpoints |
| GET, POST | `/produtos` | Listagem; criação via JSON, retornando ID e HTTP 201 |
| GET | `/produtos/busca` | Filtros `q`, `categoria`, `preco_min`, `preco_max`; resultados e total |
| GET, PUT, DELETE | `/produtos/<int:id>` | Consulta, atualização e exclusão; 404 quando não encontrado |
| GET, POST | `/usuarios` | Listagem; cadastro via nome, email e senha |
| GET | `/usuarios/<int:id>` | Dados do usuário ou 404 |
| POST | `/login` | Email e senha; dados do usuário ou 401; não cria sessão/token |
| GET, POST | `/pedidos` | Listagem; criação via `usuario_id` e itens, retornando ID e total |
| GET | `/pedidos/usuario/<int:usuario_id>` | Pedidos e itens do usuário indicado |
| PUT | `/pedidos/<int:pedido_id>/status` | Status via JSON; resposta de sucesso |
| GET | `/relatorios/vendas` | Contagens, faturamento, descontos e ticket médio |
| GET | `/health` | Consulta ao banco, contagens e configuração |
| POST | `/admin/reset-db` | Exclui os registros das quatro tabelas |
| POST | `/admin/query` | Executa SQL recebido no corpo JSON |

São **19 combinações explícitas de método/caminho**, desconsiderando métodos automáticos do Flask.

## PHASE 2 — ARCHITECTURE AUDIT

**Método:** inspeção estática integral, rastreamento de entradas até SQL e respostas, e consulta à documentação oficial para APIs.

**Limitações:** aplicação não importada nem iniciada; nenhum teste, seed, instalação ou comando de escrita executado. Exploração e concorrência não foram testadas. A exposição externa depende da implantação; não há evidência de gateway ou proteção externa no escopo. O README caracteriza o projeto como exercício, portanto as severidades representam o impacto caso esses caminhos sejam disponibilizados com dados reais.

### Resumo

| Severidade | Quantidade |
|---|---:|
| CRITICAL | 2 |
| HIGH | 6 |
| MEDIUM | 6 |
| LOW | 1 |
| **Total** | **15** |

### F001 — [CRITICAL] Administração pública permite SQL arbitrário e exclusão integral

- **Padrões:** AP01, AP04.
- **Arquivo e linhas:** `app.py:47–78`.
- **Descrição/evidência:** `POST /admin/query` recebe `sql` do JSON e o entrega diretamente a `cursor.execute(query)`. Consultas retornam dados; outras instruções recebem `commit()`. `POST /admin/reset-db` executa quatro exclusões sem verificar identidade ou permissão.
- **Impacto:** qualquer cliente com acesso HTTP pode ler, modificar ou destruir dados. O problema não depende de múltiplas instruções SQL: uma única instrução já permite ações destrutivas.
- **Recomendação:** retirar a execução genérica de SQL da superfície HTTP e mover manutenção/reset para comandos administrativos restritos, com separação de ambiente.

### F002 — [CRITICAL] Entrada externa é concatenada em SQL nos fluxos comuns

- **Padrão:** AP01.
- **Arquivos e linhas:** `controllers.py:111–123, 146–176, 188–203`; `models.py:47–50, 57–61, 109–111, 126–129, 139–165, 289–299`.
- **Descrição/evidência:** email e senha chegam à consulta de login sem parâmetros; termo/categoria da busca entram em SQL concatenado. Cadastro e atualização também interpolam texto. IDs do JSON de pedidos passam por `str()`, que não valida um inteiro.
- **Impacto:** alteração da lógica de consultas, bypass da comparação de credenciais, extração ou alteração indevida de dados, conforme o ponto de entrada. Esses caminhos persistem mesmo que as rotas administrativas sejam removidas.
- **Recomendação:** parametrizar todos os valores com placeholders `?`, validar tipos antes da persistência e manter SQL estrutural separado dos dados.

**Precisão:** IDs provenientes de rotas `<int:...>` e o status validado por enum não foram considerados provas independentes de injeção. O finding se apoia nos parâmetros externos efetivamente livres.

### F003 — [HIGH] Senhas são armazenadas e retornadas em texto puro

- **Padrão:** AP03.
- **Arquivos e linhas:** `models.py:72–103, 105–111, 122–130`; `controllers.py:128–144`; `database.py:75–83`.
- **Descrição/evidência:** o cadastro grava a senha recebida diretamente. Login compara o valor original. Os serializers de usuários incluem o campo `senha`, e os controllers retornam esses objetos.
- **Impacto:** listagem e consulta de usuários expõem credenciais recuperáveis. O seed também cria credenciais literais.
- **Recomendação:** usar hashing próprio para senhas, remover credenciais de todos os DTOs e prever migração/reset de senhas existentes. Não manter contas com credenciais fixas fora de ambiente de demonstração.

### F004 — [HIGH] Login não estabelece identidade e recursos não têm autorização

- **Padrão:** AP04.
- **Arquivos e linhas:** `app.py:11–28`; `controllers.py:167–183, 188–203, 222–252`.
- **Descrição/evidência:** `/login` apenas retorna os dados do usuário; não estabelece sessão ou token. Operações de produtos, consultas de pedidos, atualização de status e relatórios não verificam identidade, papel ou propriedade. O cliente escolhe o `usuario_id` de um pedido.
- **Impacto:** leitura e alteração de recursos de terceiros e execução anônima de operações administrativas de negócio.
- **Recomendação:** implementar identidade verificável, autorização por operação/recurso e obtenção do usuário do contexto autenticado.

Este finding cobre os recursos comuns; as rotas administrativas destrutivas estão agrupadas em F001.

### F005 — [HIGH] Quantidades inválidas e itens repetidos corrompem estoque e total

- **Padrão:** AP10.
- **Arquivos e linhas:** `controllers.py:195–203`; `models.py:139–146, 154–165`.
- **Descrição/evidência:** não há exigência de quantidade inteira positiva. Uma quantidade negativa passa pela comparação de estoque, reduz o total e aumenta o estoque na subtração. Itens repetidos são verificados separadamente contra o saldo anterior às baixas.
- **Impacto:** pedidos com valores inválidos, aumento artificial de estoque e venda acima da disponibilidade. Por exemplo, com saldo 10, duas linhas de quantidade 6 passam individualmente e deixam saldo −2.
- **Recomendação:** validar quantidades, agregar itens por produto e verificar/debitar saldo atomicamente.

### F006 — [HIGH] Conexão global e ausência de rollback comprometem isolamento transacional

- **Padrões:** AP07, AP08.
- **Arquivos e linhas:** `database.py:4–12, 86`; `models.py:148–168`; `controllers.py:218–220`.
- **Descrição/evidência:** todas as requisições reutilizam uma conexão com `check_same_thread=False`. A criação do pedido faz múltiplas gravações e termina com `commit()`, mas não executa rollback em falhas. Uma exceção após uma gravação pode deixar mudanças pendentes para um commit posterior na mesma conexão.
- **Impacto:** persistência parcial após falhas e interferência entre operações concorrentes, inclusive commits envolvendo trabalho de outra requisição.
- **Recomendação:** conexão por requisição/unidade de trabalho, fechamento no teardown e transações com commit/rollback explícitos. Integrar a verificação de estoque à transação.

**Precisão:** existe um commit final; o problema não é “nenhuma transação”, mas a ausência de delimitação e recuperação seguras. A documentação alerta para a necessidade de serializar escritas quando uma conexão é compartilhada entre threads. [Documentação do sqlite3](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect).

### F007 — [HIGH] Inicialização documentada expõe servidor com debug habilitado

- **Padrão:** configuração insegura de execução.
- **Arquivo e linhas:** `app.py:8, 80–88`.
- **Descrição/evidência:** o comando do README chega a `app.run(host="0.0.0.0", ..., debug=True)`, com debug também configurado globalmente.
- **Impacto:** se a porta estiver acessível, erros não capturados podem expor detalhes e o debugger. A possibilidade de execução pelo debugger depende de suas proteções e condições de acesso; não foi assumido bypass do PIN.
- **Recomendação:** configuração por ambiente, debug desligado por padrão e servidor WSGI apropriado em implantação.
- **Fonte:** o Flask documenta que o debugger permite execução de código e não deve ser exposto em produção. [Debugging Application Errors](https://flask.palletsprojects.com/en/stable/debugging/).

### F008 — [HIGH] Cancelamento não recompõe estoque e status ignora transições

- **Padrões:** AP06, AP10.
- **Arquivos e linhas:** `controllers.py:237–252`; `models.py:163–168, 275–283`.
- **Descrição/evidência:** criar pedido debita estoque. Cancelar apenas atualiza o status e imprime uma mensagem sobre devolução; nenhuma devolução ocorre. A atualização não consulta o status anterior e retorna sucesso mesmo quando nenhum pedido corresponde ao ID.
- **Impacto:** estoque permanece indisponível após cancelamento, transições incoerentes são aceitas e recursos inexistentes recebem sucesso.
- **Recomendação:** definir transições permitidas, verificar existência e realizar a compensação de estoque atomicamente e uma única vez.

### F009 — [MEDIUM] Chave de configuração está fixa e é divulgada pelo health

- **Padrão:** AP02.
- **Arquivos e linhas:** `app.py:7`; `controllers.py:285–290`.
- **Descrição/evidência:** a chave configurada no Flask aparece novamente na resposta pública de `/health`.
- **Impacto:** perda de confidencialidade da configuração. A severidade é MEDIUM porque o código atual não utiliza sessões assinadas nem demonstra outro consumidor criptográfico; não há evidência suficiente para afirmar falsificação de sessão já explorável.
- **Recomendação:** remover o segredo da resposta, carregar configuração externa e substituir a chave se utilizada em ambiente real. Restringir o health aos dados operacionais necessários.

### F010 — [MEDIUM] Regras de negócio, transporte e persistência estão acoplados

- **Padrões:** AP05, AP06.
- **Arquivos e linhas:** `app.py:47–78`; `controllers.py:24–96, 237–252, 264–290`; `models.py:133–169, 235–273`; `database.py:7–84`.
- **Descrição/evidência:** SQL aparece em rotas e controllers; regras de estoque e descontos convivem com persistência e serialização; `get_db()` acumula conexão, DDL e seed.
- **Impacto:** mudanças de negócio atravessam múltiplos módulos, validações divergem e testes isolados exigem dependências de HTTP/banco. Classificado como MEDIUM pelo tamanho atual e pela separação parcial já existente.
- **Recomendação:** controllers como adaptadores HTTP, serviços para pedidos e relatórios, persistência separada e bootstrap explícito para schema/seed. Não é necessário introduzir ORM para corrigir a separação.

### F011 — [MEDIUM] Validação é incompleta e diverge entre criação e atualização

- **Padrão:** AP10.
- **Arquivo e linhas:** `controllers.py:28–54, 72–92, 113–126, 148–160`.
- **Descrição/evidência:** criação valida tamanho do nome e categoria, mas atualização ignora essas regras. Comparações numéricas e `len()` são executados sem checar tipos. Filtros de preço são convertidos sem tratamento específico.
- **Impacto:** dados rejeitados no cadastro podem entrar por atualização; tipos incorretos e filtros inválidos provocam HTTP 500.
- **Recomendação:** validação compartilhada de estrutura, tipos, limites e enums; tratamento consistente de entrada inválida com respostas 4xx.

Os problemas financeiros de quantidades estão em F005, sem duplicação de contagem.

### F012 — [MEDIUM] Schema não protege relações e unicidade de usuários

- **Padrão:** integridade de dados / AP10.
- **Arquivos e linhas:** `database.py:26–53`; `models.py:65–69, 122–130, 148–151`; `controllers.py:195–203`.
- **Descrição/evidência:** não existem foreign keys para pedidos/itens nem unicidade de email. Criar pedido não verifica a existência do usuário. Excluir produto remove fisicamente um registro potencialmente referenciado.
- **Impacto:** pedidos órfãos, referências quebradas e contas duplicadas com login ambíguo.
- **Recomendação:** estabelecer constraints e políticas de exclusão, validar referências e unicidade, e habilitar a fiscalização de foreign keys nas conexões SQLite.

### F013 — [MEDIUM] Listagem de pedidos executa N+1 queries sem paginação

- **Padrão:** AP09.
- **Arquivo e linhas:** `models.py:171–201, 203–233`.
- **Descrição/evidência:** após buscar pedidos, faz uma consulta de itens por pedido e uma consulta de nome do produto por item.
- **Impacto:** cada listagem executa **1 + P + I consultas**, sendo P o número de pedidos e I o total de itens retornados. O uso de `fetchall()` e a ausência de paginação ampliam consumo de memória e latência.
- **Recomendação:** paginação e consultas em lote/JOIN para itens e produtos, preservando a estrutura das respostas.

### F014 — [MEDIUM] Exceções internas são devolvidas ao cliente

- **Padrão:** AP14.
- **Arquivos e linhas:** `app.py:77–78`; `controllers.py:10–12, 60–62, 95–96, 125–126, 218–220, 291–292`.
- **Descrição/evidência:** blocos genéricos retornam `str(e)` como conteúdo HTTP. Também convertem falhas de entrada e exceções HTTP de parsing em respostas genéricas 500.
- **Impacto:** divulgação de detalhes internos, classificação incorreta dos erros e contrato inconsistente para consumidores.
- **Recomendação:** erros de domínio tipados, handlers centralizados, mensagens públicas controladas e logs internos com contexto e redação de dados sensíveis.

### F015 — [LOW] Serialização duplicada aumenta risco de divergência

- **Padrão:** AP11.
- **Arquivo e linhas:** `models.py:12–21, 31–40, 304–313, 178–200, 211–232`.
- **Descrição/evidência:** os mesmos campos de produtos são montados em três funções; pedidos e seus itens têm duas implementações praticamente equivalentes.
- **Impacto:** inclusão ou correção de um campo exige múltiplas alterações e pode produzir respostas diferentes para a mesma entidade.
- **Recomendação:** centralizar serializers/presenters, preservando os contratos legítimos das respostas.

### APIs deprecated, APIs legacy e dependências

**Nenhuma chamada deprecated foi confirmada no escopo analisado.** Isso não equivale a uma auditoria de vulnerabilidades de todas as dependências transitivas.

| API / local | Situação verificada | Fonte oficial / ação |
|---|---|---|
| `Flask`, `add_url_rule`, `route`, `jsonify`, `request.get_json` — `app.py:1–60`, `controllers.py` | Não identificadas como deprecated para a série Flask 3.1 | [API Flask 3.1](https://flask.palletsprojects.com/en/stable/api/) e [changelog](https://flask.palletsprojects.com/en/stable/changes/). Nenhuma substituição por depreciação indicada. |
| `app.run` — `app.py:88` | API suportada; o problema é a configuração e o contexto de uso, não depreciação | [API Flask](https://flask.palletsprojects.com/en/stable/api/#flask.Flask.run). Ação em F007. |
| `sqlite3.connect(..., check_same_thread=False)` — `database.py:10` | Não usa a forma posicional deprecated para parâmetros opcionais desde Python 3.13; `check_same_thread` já é nomeado | [sqlite3.connect](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect). Runtime do projeto não declarado. |
| Controle transacional implícito — `database.py:10`; `models.py:168` | Na documentação Python 3.12+, o padrão é chamado **legacy transaction control**; isso não torna `commit()` deprecated | [Controle de transações](https://docs.python.org/3/library/sqlite3.html#transaction-control). Tornar o comportamento explícito conforme o runtime escolhido. |
| `CORS(app)` — `app.py:9` | Nenhuma depreciação confirmada; verificação específica da versão 5.0.1 ficou limitada | A URL versionada estava indisponível; a [documentação acessível](https://flask-cors.readthedocs.io/en/latest/api.html) se identifica como 3.0.10. Não foi tratada como prova da versão 5.0.1. |

**Pacotes descontinuados:** nenhum confirmado. Versão fixada ou antiga, isoladamente, não demonstra descontinuação.

### Observações e hipóteses não promovidas a findings

- Email, SMS e push em `controllers.py:208–210` são apenas `print()`. Como o README descreve um exercício e não promete entrega de notificações, não foi atribuído HIGH por integração simulada.
- O campo `ambiente` do health não comprova implantação em produção.
- O relatório soma todos os pedidos em `models.py:239–254`, inclusive cancelados. A definição comercial de “faturamento” precisa ser confirmada antes de classificar isso como erro.
- Nenhum mecanismo de pagamento foi encontrado; não se inferiu aprovação financeira real.
- O seed depende de o catálogo estar vazio e não possui separação por ambiente (`database.py:56–84`). Deve ser tratado na reorganização do bootstrap.

### Escopo proposto para eventual refatoração

Abranger **F001–F015** nos quatro módulos Python, priorizando proteção dos dados, credenciais, pedidos e transações. A organização proposta separaria rotas/controllers, serviços de negócio, persistência e serialização, com configuração e bootstrap explícitos.

Mudanças contratuais necessárias incluem retirar SQL/reset públicos, exigir autenticação/autorização, eliminar senhas e segredos das respostas, rejeitar entradas inválidas com 4xx e retornar 404 para pedidos inexistentes. Contratos legítimos de catálogo e pedidos devem ser preservados quando compatíveis com essas correções.

**Destino do relatório:** somente esta conversa.  
**Validação executada:** inspeção estática e consulta documental; nenhum teste de execução.  
**Status:** `AWAITING EXPLICIT CONFIRMATION`.

**Você confirma a execução da PHASE 3 — REFACTORING para este escopo?**

A [skill refactor-arch](/Users/renatoalencar/Developer/Personal/MBA-IA/mba-ia-refactor-projects-skill/.agents/skills/refactor-arch/SKILL.md) determina: “Ao final desta fase, pause obrigatoriamente e encerre a execução.” Conforme essa regra e sua instrução, parei após a auditoria, sem alterar arquivos.
