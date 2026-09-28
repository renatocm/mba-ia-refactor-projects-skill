# Desafio — Skill `refactor-arch` com OpenAI Codex

## 1. Visão Geral

Este desafio consiste em criar e validar uma skill capaz de analisar, auditar e refatorar projetos legados para uma arquitetura MVC adaptada à tecnologia encontrada. O trabalho foi executado com o OpenAI Codex, usando uma skill local em `.agents/skills/refactor-arch/` e referências Markdown especializadas.

A skill foi aplicada a três projetos com níveis diferentes de organização: uma API Flask monolítica, uma API Node.js/Express monolítica e uma API Flask que já possuía `models`, `routes`, `services` e `utils`. O objetivo foi verificar que a skill detecta a stack em vez de presumir Python ou Flask, produz auditorias rastreáveis e refatora de maneira incremental quando já existem componentes úteis.

| Projeto | Stack | Arquitetura inicial | Findings Phase 2 | Resultado Phase 3 |
|---|---|---|---:|---|
| `code-smells-project` | Python / Flask / SQLite | Monolítica, com `app.py`, `controllers.py` e `models.py` concentrando responsabilidades | 15 — 2 CRITICAL, 6 HIGH, 6 MEDIUM, 1 LOW | MVC em `loja/`; F001–F015 resolvidos; 19 testes e 34 requisições HTTP |
| `ecommerce-api-legacy` | JavaScript / Node.js / Express / SQLite | Monolítica, concentrada em `AppManager.js` | 13 — 5 HIGH, 7 MEDIUM, 1 LOW | MVC incremental; F001–F013 resolvidos; 17 testes e 28 requisições HTTP |
| `task-manager-api` | Python / Flask / Flask-SQLAlchemy / SQLite | Parcialmente organizada em models, routes, services e utils | 12 — 4 HIGH, 7 MEDIUM, 1 LOW | Arquitetura preservada e ampliada; 9 findings resolvidos e 3 parcialmente resolvidos; 15 testes e 13 cenários HTTP reais |

As auditorias da PHASE 2 foram preservadas em [`reports/`](reports/). Os detalhes de implementação e validação da PHASE 3 estão nos documentos `docs/refactoring.md` disponíveis nos projetos. A reexecução do `task-manager-api` está registrada em [`reports/audit-project-3.md`](reports/audit-project-3.md#phase-3--reexecução-direcionada-de-f004).

## 2. Estrutura do Repositório

```text
.
├── .agents/
│   └── skills/
│       └── refactor-arch/
├── code-smells-project/
├── ecommerce-api-legacy/
├── task-manager-api/
├── reports/
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
└── README.md
```

A mesma skill foi testada nos três projetos. Como o desafio exigia que a skill fosse distribuída junto aos projetos, cópias compatíveis também foram mantidas nas áreas locais correspondentes. A fonte de referência usada nesta documentação é `.agents/skills/refactor-arch/` na raiz.

## 3. Análise Manual

### 3.1 `code-smells-project`

**Stack e domínio.** Python/Flask, com SQLite e uma API de e-commerce para produtos, usuários, pedidos, estoque e relatórios. A arquitetura inicial era monolítica: banco, rotas, regras e serialização estavam concentrados em poucos arquivos.

| Finding manual | Severidade | Evidência | Justificativa |
|---|---|---|---|
| Administração HTTP permitia SQL arbitrário e reset integral | CRITICAL | `app.py`, `controllers.py` e rotas administrativas descritas em `reports/audit-project-1.md` | Exposição de dados, alteração destrutiva e bypass do modelo de autorização |
| Entrada externa era concatenada em SQL | CRITICAL | `models.py`/fluxos de consulta documentados no relatório | Permitia alterar a semântica da consulta por payload externo |
| Senhas eram armazenadas e retornadas em texto puro | HIGH | `models.py` e serializadores originais | Comprometia credenciais e expunha dados diretamente na API |
| Login não estabelecia identidade e não havia autorização por recurso | HIGH | Rotas de usuários, pedidos e administração | Qualquer cliente podia alcançar operações de outros usuários |
| Quantidades inválidas e itens repetidos corrompiam estoque e total | HIGH | Fluxo de criação/cancelamento de pedidos | Afetava invariantes financeiras e de estoque |
| Conexão global e ausência de rollback | HIGH | Módulo de banco e operações de pedido | Permitiria estados parciais e interferência entre requisições |
| Validação divergente entre criação e atualização | MEDIUM | Controllers e validações duplicadas | A mesma entidade aceitava regras diferentes conforme o endpoint |
| Schema sem proteção suficiente para relações e unicidade | MEDIUM | Schema SQLite original | Permitiria órfãos e usuários duplicados |
| Listagem de pedidos com N+1 e sem paginação | MEDIUM | Controller de pedidos | O custo crescia linearmente por pedido/item |
| Exceções internas retornadas ao cliente | MEDIUM | Handlers originais | Vazava detalhes de implementação e produzia respostas instáveis |
| Serialização de produtos duplicada | LOW | `models.py:12–21, 31–40, 304–313` | Aumentava o risco de divergência entre as representações do mesmo produto |
| Magic numbers nas regras de desconto | LOW | `models.py:256–262` | Espalhava valores de negócio sem nome e dificultava manutenção consistente |

O relatório completo contém 15 findings: 2 CRITICAL, 6 HIGH, 6 MEDIUM e 1 LOW. Não foi confirmada chamada de API deprecated no código inspecionado.

### 3.2 `ecommerce-api-legacy`

**Stack e domínio.** JavaScript, Node.js, Express 4 e SQLite em memória. O domínio é um LMS demonstrativo com usuários, cursos, matrículas, pagamentos e relatório financeiro. A aplicação inicial concentrava bootstrap, schema, seed, rotas, persistência, checkout e relatórios em `src/AppManager.js`.

| Finding manual | Severidade | Evidência | Justificativa |
|---|---|---|---|
| Operações sensíveis e identidade do checkout sem autorização | HIGH | `src/AppManager.js` e rotas originais | Email sozinho podia representar identidade e operações administrativas eram públicas |
| Transformação de senha sem proteção criptográfica adequada | HIGH | `src/utils.js` | Base64/truncamento não protege senha contra ataques offline |
| Tipos não validados antes do fluxo de banco | HIGH | Checkout em `src/AppManager.js` | Entradas incompatíveis podiam provocar exceções e respostas incorretas |
| Matrícula, pagamento e auditoria sem atomicidade | HIGH | Operações sequenciais de checkout | Falhas intermediárias deixavam estado parcial |
| Cartão completo registrado em logs | HIGH | Fluxo de checkout | Exposição direta de dado sensível em saída operacional |
| Pagamento aprovado por regra de prefixo | MEDIUM | Regra demonstrativa do checkout | Não representa confirmação de um provedor real; precisava ser isolada como simulação |
| `AppManager` concentrava responsabilidades independentes | MEDIUM | `src/AppManager.js:4–138` | Dificultava testes e mudanças isoladas |
| Schema permitia órfãos e duplicados | MEDIUM | Schema e exclusão de usuários | Não havia constraints suficientes para identidade e matrículas |
| Relatório financeiro com N+1 e carga integral em memória | MEDIUM | Relatório financeiro | O custo crescia com cursos e matrículas |
| Erros de banco eram ignorados ou convertidos em sucesso | MEDIUM | Callbacks de persistência | Produzia falsos sucessos e falhas mal classificadas |
| Cache global sem limite e sem consumidor | MEDIUM | `src/utils.js` | Retinha memória e não participava de um caso de uso real |
| Cadeia de dependências com pacotes deprecated | MEDIUM | `package-lock.json` | Aumentava risco de manutenção e build |
| Nomes pouco descritivos (`u`, `e`, `p`, `cid`, `cc`, `enr`) | LOW | `src/AppManager.js:29–35, 52–54, 89–106` | Reduziam a clareza do fluxo de cadastro, checkout e relatório |
| `totalRevenue` declarado/exportado/importado mas nunca utilizado | LOW | `src/utils.js:10,25`; `src/AppManager.js:2` | Indicava responsabilidade inexistente e confundia a leitura da arquitetura |

O relatório não classificou nenhum finding como CRITICAL: a aplicação era um demonstrador em memória e não havia evidência suficiente de operação financeira real. A auditoria separou APIs legacy de pacotes deprecated; `express.json()`, rotas Express e APIs do driver SQLite não foram declaradas deprecated sem fonte aplicável.

### 3.3 `task-manager-api`

**Stack e domínio.** Python/Flask, Flask-SQLAlchemy, SQLAlchemy e SQLite. O domínio cobre usuários, papéis, tarefas, categorias, status, prioridade e relatórios. A arquitetura inicial já possuía camadas parciais, que foram preservadas em vez de substituídas integralmente.

| Finding manual | Severidade | Evidência | Justificativa |
|---|---|---|---|
| Autenticação e autorização ausentes | HIGH | `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py` | Rotas sensíveis eram públicas e o token de login não era validado |
| Senhas com MD5 e expostas nas respostas | HIGH | `models/user.py:11,16–32`; login | Hash rápido e inclusão do hash em `to_dict()` comprometiam credenciais |
| Credenciais SMTP e `SECRET_KEY` hardcoded | HIGH | `services/notification_service.py:7–10`; `app.py:11–13` | Impedia rotação segura e podia expor integração externa |
| Rotas concentravam HTTP, regras, ORM e serialização | HIGH | `routes/task_routes.py`, `user_routes.py`, `report_routes.py` | A separação nominal de pastas não correspondia à separação de responsabilidades |
| Consultas N+1 | MEDIUM | Rotas de tarefas, usuários, relatórios e categorias | Acesso relacionado dentro de loops elevava custo com o volume |
| Validação inconsistente | MEDIUM | Rotas e `utils/helpers.py` | Tipos, tags, cores e atualizações tinham regras divergentes |
| Tratamento de erros genérico | MEDIUM | `except:` e respostas 500 distribuídas | Dificultava diagnóstico e podia vazar detalhes |
| `datetime.utcnow()` e datas ingênuas | MEDIUM | models, routes, seed e helpers | Podia gerar inconsistência temporal; `utcnow()` é deprecated em Python 3.12+ |
| `Query.get()` deprecated no SQLAlchemy 2.x | MEDIUM | Rotas de tarefas, usuários e relatórios | API legada deveria ser substituída por `Session.get()` |
| Import com efeitos colaterais e seed destrutivo | MEDIUM | `app.py:30–31`; `seed.py:11–14` | Importar criava tabelas e seed apagava todos os dados |
| Integridade relacional dependente de loops manuais | MEDIUM | models e rotas de exclusão | Foreign keys/cascade não estavam definidos de forma suficiente |
| Constantes/regras duplicadas entre models, routes e helpers | LOW | `models/task.py`, `routes/task_routes.py`, `utils/helpers.py` | Aumentava divergência e exigia correções em múltiplos pontos |
| Imports sem uso | LOW | `app.py`, `models/task.py`, `routes/task_routes.py`, `utils/helpers.py` | Adicionava ruído e sugeria dependências que não participavam do fluxo |

O relatório contém 4 HIGH, 7 MEDIUM e 1 LOW. Esta distribuição é a evidência disponível para este projeto; não foi acrescentado finding apenas para alterar a contagem.

## 4. Construção da Skill

### 4.1 Estrutura da Skill

```text
.agents/skills/refactor-arch/
├── SKILL.md
└── references/
    ├── project-analysis.md
    ├── anti-patterns.md
    ├── audit-report-template.md
    ├── mvc-guidelines.md
    └── refactoring-playbook.md
```

### 4.2 Decisões de Design

`SKILL.md` funciona como orquestrador. Ele define as fases, as restrições de leitura e escrita, a necessidade de preservar evidências, a pausa entre auditoria e refatoração e os requisitos de validação.

As referências são carregadas conforme a fase e a necessidade: análise de projeto para detectar stack e arquitetura; catálogo de anti-patterns para a auditoria; template para padronizar findings; guidelines para adaptar MVC; e playbook para aplicar transformações concretas.

A separação em três fases reduz risco operacional:

1. **PHASE 1 — Project Analysis:** leitura e mapeamento, sem modificar arquivos.
2. **PHASE 2 — Architecture Audit:** findings com severidade, arquivo e linhas, ainda sem escrita.
3. **PHASE 3 — Refactoring:** somente após confirmação explícita, com validação de boot e interfaces.

A skill usa heurísticas e evidências de fluxo em vez de nomes fixos de arquivos ou regras exclusivas de uma linguagem. Também orienta uma refatoração incremental: se já existem blueprints, models, services ou repositories úteis, eles são preservados e corrigidos, em vez de uma reescrita automática.

### 4.3 Catálogo de Anti-patterns

O catálogo possui **16 padrões** com sinais, impacto, severidade padrão e recomendações. Os principais são:

- SQL Injection / queries inseguras;
- hardcoded credentials/secrets;
- insecure password storage;
- missing authentication/authorization;
- God Class / God Method;
- business logic in controllers/routes;
- global/shared mutable state;
- missing transactions;
- N+1 queries;
- missing input validation;
- duplicated code;
- magic numbers/strings;
- deprecated APIs;
- error handling espalhado/inadequado;
- nomes opacos/código morto;
- integração simulada no fluxo real.

A severidade é ajustada pela evidência e pelo contexto. Por exemplo, uma simulação de pagamento em um demonstrador pode ser MEDIUM se estiver claramente documentada, enquanto uma integração que anuncia pagamento real sem confirmação pode ser HIGH. Pacote antigo, API legacy e API deprecated também são distinguidos.

### 4.4 Playbook de Refatoração

O playbook possui **13 padrões de transformação**. Entre os exemplos documentados:

| Problema | Transformação |
|---|---|
| SQL inseguro | Bind de valores e allowlist de identificadores |
| Password inseguro | Argon2id/scrypt ou mecanismo adequado, com salt e DTO sem hash |
| God Class | Composition root, controllers, services e repositories separados |
| Route/controller pesado | Schema/validator, controller fino e service para o caso de uso |
| Conexão global | Contexto por requisição, pool ou unidade de trabalho com lifecycle |
| Operações múltiplas | Transação local com rollback e compensação para efeitos remotos |
| N+1 | JOIN, eager loading, batch ou agregação |
| Validação duplicada | Validator/schema compartilhado, distinguindo create e update |
| Configuração hardcoded | Ambiente ou secret store validado no bootstrap |
| Deprecated API | Equivalente moderno documentado para a versão detectada |
| Error handling espalhado | Erros tipados e handler centralizado |
| Acesso irrestrito | Identidade verificável e política por recurso |
| Literais/código duplicado | Policies, presenters e constantes apenas quando agregam valor |

### 4.5 Como a Skill se mantém agnóstica

Nos três testes, a skill adaptou a análise ao projeto:

- no `code-smells-project`, encontrou um Flask monolítico com SQL e regras misturados;
- no `ecommerce-api-legacy`, detectou JavaScript/Node/Express e avaliou callbacks, SQLite, checkout e dependências do `package-lock.json`;
- no `task-manager-api`, reconheceu Python/Flask, mas preservou a separação parcial existente e apontou que routes ainda continham responsabilidades de controller, serviço e acesso a dados.

Portanto, MVC foi usado como distribuição de responsabilidades, não como uma árvore obrigatória de diretórios. Em uma API JSON, presenters/serializers podem cumprir o papel de view; em Flask, blueprints podem ser preservados; em Express, routers e controllers podem ser separados sem impor nomes de arquivos Python.

## 5. Resultados

### 5.1 `code-smells-project`

- **Findings:** 15 — 2 CRITICAL, 6 HIGH, 6 MEDIUM, 1 LOW.
- **Antes:** aplicação monolítica em poucos arquivos, com SQL, autenticação, pedidos, estoque e serialização misturados.
- **Depois:** `loja/` com config, bootstrap, auth, errors, routes, controllers, services, models/repositories e presenters.
- **Principais correções:** remoção de SQL administrativo exposto, queries parametrizadas, scrypt, Bearer assinado, autorização, transações, rollback, estoque seguro, constraints, paginação, N+1, handlers centrais e configuração externa.
- **Testes:** 19 testes automatizados passaram.
- **HTTP:** 34 requisições reais passaram, incluindo sucesso, 401/403/404/409, rollback, autorização e endpoints administrativos removidos.
- **Findings:** F001–F015 resolvidos.
- **Observação:** os endpoints `/admin/query` e `/admin/reset-db` foram removidos por segurança e retornam 404; isso está documentado como mudança necessária de contrato.

### 5.2 `ecommerce-api-legacy`

- **Findings:** 13 — 5 HIGH, 7 MEDIUM, 1 LOW.
- **Antes:** `AppManager.js` criava banco, schema, seed, rotas, checkout, pagamentos, relatórios e exclusões.
- **Depois:** factory, routes, controllers, services, repositories, models/validation, middleware, presenters, config, segurança, pagamentos de demonstração e database.
- **Principais correções:** autorização real, scrypt, validação de tipos, transações de checkout, logs sem cartão, constraints, paginação, correção de N+1, remoção de cache global, tratamento de erros, isolamento da simulação de pagamento e revisão de dependências.
- **Testes:** 17 testes automatizados passaram.
- **HTTP:** 28 requisições reais passaram, cobrindo checkout, cadastro/login, relatório, exclusão, autorização, erros e logs.
- **Findings:** F001–F013 resolvidos.
- **Trade-off:** `sqlite3` foi substituído por `node:sqlite`, eliminando a cadeia de pacotes deprecated. Isso exige Node 24.15+ da série 24; `node:sqlite` era release candidate no runtime validado e as operações são síncronas. O trade-off está documentado em [`ecommerce-api-legacy/docs/refactoring.md`](ecommerce-api-legacy/docs/refactoring.md).

### 5.3 `task-manager-api`

- **Findings:** 12 — 4 HIGH, 7 MEDIUM, 1 LOW; resultado atualizado: **9 resolvidos e 3 parcialmente resolvidos**.
- **Antes da reexecução:** algumas routes já delegavam a services, mas relatórios, categorias e outros handlers ainda misturavam HTTP, ORM, regras e persistência.
- **Depois:** os 20 handlers foram revisados; `report_routes.py`, `task_routes.py` e `user_routes.py` ficam finas e delegam para services, preservando modelos, tabelas, blueprints, caminhos, métodos e decorators de autorização.
- **Services criados:** `report_service.py` e `category_service.py`.
- **Services ampliados:** `task_service.py` e `user_service.py`.
- **Suporte:** `services/transactions.py`, `services/exceptions.py` e `errors.py` concentram transações e tradução de erros.
- **Testes:** **15 testes passaram**, incluindo os dois existentes; novo `test_route_contracts.py` e fixture compartilhada em `conftest.py`.
- **HTTP:** **13 cenários HTTP reais passaram**, com banco temporário, cobrindo summary report, relatório por usuário, CRUD de categorias, tarefas, usuários, autenticação, erros e rollback.
- **Busca residual:** zero ocorrências em `routes/` de `.query`, `db.session`, `session.get`, `session.add`, `session.delete`, `session.commit` e `session.rollback`; nenhum import de models/SQLAlchemy. `git diff --check` passou.
- **Resolvidos:** F001, F002, F003, **F004**, F005, F006, F008, F009 e F010.
- **Parcialmente resolvidos:** **F007, F011 e F012**. F004 foi revalidado nesta execução; os demais status resolvidos foram mantidos no consolidado.
- **Resíduos confirmados:** F007 ainda retorna 500 para `due_date` numérico; F011 apresentou `foreign_keys=0` e duas referências órfãs após exclusões em banco isolado; F012 mantém regras repetidas, helpers/imports sem uso e notificações não integradas fora das routes.
- **Ajuste de contrato:** cadastro sem senha retorna 400 com “Senha é obrigatória”, substituindo o tratamento inadequado como conflito.

## 6. Comparação Antes e Depois

### `code-smells-project`

| Aspecto | Antes | Depois |
|---|---|---|
| Autenticação | Login sem identidade/autorização consistente | Bearer assinado, expiração e políticas por recurso |
| Senha | Texto puro/hash exposto | scrypt com salt e DTO público sem credencial |
| Arquitetura | Monólito com controllers/modelos sobrecarregados | routes → controllers → services → models/repositories → presenters |
| Transações | Commits e falhas parciais | Unidade transacional, rollback e concorrência validada |
| Consultas | SQL concatenado e N+1 | Placeholders, joins/batches e paginação |
| Configuração | Chave/debug e comportamento operacional acoplados | Configuração externa e boot explícito |
| Erros | Exceções devolvidas | Handlers centrais e mensagens controladas |
| APIs deprecated | Nenhuma chamada confirmada | Nenhuma chamada confirmada no resultado |
| Validação | Duplicada e incompleta | Schemas, invariantes e limites centrais |

### `ecommerce-api-legacy`

| Aspecto | Antes | Depois |
|---|---|---|
| Autenticação | Email identificava usuário; admin público | Sessões Bearer, senha verificada e papel atual consultado |
| Senha | Base64/truncamento | scrypt com salt e sem hash em DTO |
| Arquitetura | `AppManager` God Class | Factory, controllers, services, repositories e presenters |
| Transações | Matrícula/pagamento/auditoria independentes | Checkout atômico com rollback |
| Consultas | N+1 no relatório | Consultas agregadas/batch e paginação |
| Configuração | Valores e símbolos sem uso | Config validada por ambiente; pagamento explicitamente demo |
| Erros | Callbacks ignoravam falhas | Middleware central, JSON seguro e códigos coerentes |
| Deprecated/dependências | Cadeia de `sqlite3` com 9 pacotes deprecated | `node:sqlite`; Node 24.15+; sem atualização major do Express |
| Validação | Tipos e limites incompletos | Schemas, limites, conteúdo e autorização validados |

### `task-manager-api`

| Aspecto | Antes | Depois |
|---|---|---|
| Autenticação | Rotas públicas e token falso | Token assinado/expirável e autorização por papel |
| Senha | MD5 e hash nas respostas | Hashing seguro e resposta sem senha |
| Arquitetura | Camadas parciais com routes sobrecarregadas | 20 handlers revisados; routes finas → services → models/ORM; F004 RESOLVED |
| Transações | Commits distribuídos e seed destrutivo | Commit/rollback nos services via `transactions.py`; reset do seed opt-in preservado |
| Consultas | N+1 | `joinedload`, `selectinload` e agregação de categorias |
| Configuração | SMTP e secret hardcoded | Variáveis de ambiente e fallback não sensível |
| Erros | `except:` e mensagens inconsistentes | Tradução central de erros esperados; F007 PARTIAL por entradas inválidas ainda retornarem 500 |
| Deprecated APIs | `Query.get()` e `datetime.utcnow()` | `Session.get()` e helper UTC |
| Validação | Regras repetidas em rotas/helpers | Validators compartilhados; 15 testes e 13 cenários HTTP reais passaram; F012 ainda PARTIAL |
| ORM nas routes | Queries, mutações e agregações nos handlers | Zero ocorrências nos sete padrões buscados; nenhum import de models/SQLAlchemy |
| Integridade relacional | Exclusões dependentes de lógica manual | F011 PARTIAL: `SET NULL` declarado, mas enforcement SQLite não ativo na validação |

## 7. Checklist de Validação

### `code-smells-project`

#### PHASE 1

- [x] Linguagem detectada corretamente: Python.
- [x] Framework detectado corretamente: Flask.
- [x] Domínio descrito corretamente: e-commerce.
- [x] Arquivos analisados contabilizados no relatório.

#### PHASE 2

- [x] Relatório estruturado conforme o template.
- [x] Findings com arquivo e linhas exatos quando disponíveis.
- [x] Findings ordenados por severidade.
- [x] Mais de 5 findings.
- [x] APIs deprecated verificadas e ausência não confirmada documentada.
- [x] Pausa antes da PHASE 3.

#### PHASE 3

- [x] Estrutura MVC criada.
- [x] Configuração extraída.
- [x] Models/repositories e invariantes separados.
- [x] Routes/views preservadas e separadas.
- [x] Controllers e services criados.
- [x] Error handling centralizado.
- [x] Entry point claro.
- [x] Boot real sem erros.
- [x] Endpoints originais validados por HTTP.

### `ecommerce-api-legacy`

#### PHASE 1

- [x] JavaScript/Node.js/Express detectados.
- [x] Domínio LMS/checkout descrito.
- [x] Dependências e lockfile analisados.
- [x] Arquivos e limitações registrados.

#### PHASE 2

- [x] Template estruturado utilizado.
- [x] Findings com localização exata no código/lockfile.
- [x] Ordenação HIGH → MEDIUM → LOW.
- [x] Mais de 5 findings.
- [x] Pacotes deprecated separados de APIs deprecated.
- [x] Pausa antes da PHASE 3.

#### PHASE 3

- [x] Arquitetura MVC adaptada ao Express.
- [x] Configuração, models/validation, routes/views e controllers separados.
- [x] Services, repositories, middleware e presenters criados.
- [x] Error handling centralizado.
- [x] Entry point/factory claro.
- [x] Aplicação iniciou sem erros.
- [x] Endpoints originais validados por HTTP.
- [x] Trade-off de `node:sqlite` e Node 24.15+ documentado.

### `task-manager-api`

#### PHASE 1

- [x] Python/Flask/Flask-SQLAlchemy detectados.
- [x] Domínio de tarefas, usuários, categorias e relatórios descrito.
- [x] Arquitetura parcial existente mapeada.
- [x] Arquivos analisados e limitações registrados.

#### PHASE 2

- [x] Template estruturado utilizado.
- [x] Findings com caminhos e linhas.
- [x] Ordenação HIGH → MEDIUM → LOW.
- [x] Mais de 5 findings.
- [x] `Query.get()` e `datetime.utcnow()` identificados como APIs legadas/deprecated.
- [x] Pausa antes da PHASE 3.

#### PHASE 3

- [x] Refatoração incremental executada.
- [x] Configuração, auth, validation e error handling extraídos.
- [x] Models e routes existentes preservados.
- [x] Services de tarefas/usuários ampliados; services de relatórios/categorias criados.
- [x] F004 RESOLVED: todos os 20 handlers revisados e routes finas, sem persistência ou regra comercial direta.
- [x] Busca final pelos sete padrões ORM/persistência sem ocorrências em `routes/`.
- [x] Nenhum import de models/SQLAlchemy nas routes.
- [x] Caminhos, métodos, blueprints e decorators de autorização preservados.
- [x] 15 testes passaram; fixture compartilhada em `conftest.py`.
- [x] 13 cenários HTTP reais passaram, incluindo relatórios, categorias, tarefas e usuários.
- [x] `git diff --check` passou.
- [x] Entry point e boot validados.
- [x] Endpoints originais exercitados por HTTP real.
- [ ] Todos os findings completamente resolvidos: 9 resolvidos; F007, F011 e F012 permanecem parciais e estão documentados.

## 8. Como Executar

### Pré-requisitos

- OpenAI Codex instalado e configurado;
- Python compatível com cada projeto Python;
- Node.js 24.15+ da série 24 para `ecommerce-api-legacy` após a refatoração;
- dependências instaladas conforme o README de cada projeto;
- ambiente de teste isolado, sem credenciais ou dados de produção.

A skill segue a convenção `.agents/skills`, usada pelo Codex. Não é necessário inventar um comando `/refactor-arch`; a invocação pode ser feita por linguagem natural:

```text
Use a skill refactor-arch para analisar este projeto.
```

O pedido deve ser feito a partir da raiz do projeto que será analisado. Para uma auditoria somente leitura, explicite:

```text
Execute somente PHASE 1 e PHASE 2. Não altere arquivos. Pare antes da PHASE 3.
```

Para continuar, forneça confirmação explícita depois de revisar o relatório:

```text
Confirme a execução da PHASE 3 para este projeto e escopo.
```

### Fluxo operacional

1. **PHASE 1:** o Codex detecta linguagem, framework, dependências, banco, domínio, entry point, arquitetura e arquivos efetivamente analisados.
2. **PHASE 2:** o Codex inspeciona anti-patterns, produz findings ordenados por severidade, com arquivos/linhas e verifica APIs deprecated.
3. **Confirmação humana:** o relatório é revisado e a escrita permanece bloqueada até uma confirmação explícita.
4. **PHASE 3:** o Codex lê as guidelines/playbook pertinentes, aplica refatoração incremental, valida boot, testes, endpoints e efeitos persistidos.

### Execução por projeto

```bash
cd code-smells-project
# instalar dependências conforme code-smells-project/README.md
# pedir ao Codex: "Use a skill refactor-arch para analisar este projeto."
```

```bash
cd ecommerce-api-legacy
npm ci
# pedir ao Codex: "Use a skill refactor-arch para analisar este projeto."
```

```bash
cd task-manager-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# pedir ao Codex: "Use a skill refactor-arch para analisar este projeto."
```

Os comandos de validação reais são específicos de cada projeto e estão documentados em seus READMEs e `docs/refactoring.md`. Não se deve executar seed destrutivo, iniciar serviço de produção ou usar credenciais reais durante a auditoria.

## 9. Lições e Desafios

- **Severidade depende do contexto.** Uma regra de pagamento por prefixo é um problema sério se apresentada como cobrança real, mas foi classificada como MEDIUM no LMS demonstrativo porque o comportamento era explicitamente simulado.
- **Código antigo não é automaticamente deprecated.** `Query.get()` e `datetime.utcnow()` tinham evidência documental; callbacks, CommonJS e APIs Express usadas pelos projetos não foram classificados como deprecated sem fonte aplicável.
- **A skill deve detectar padrões, não nomes de arquivos.** `AppManager.js`, `routes/` e `models/` foram avaliados pelas responsabilidades e pelo fluxo, não pelo nome da pasta.
- **A refatoração incremental foi essencial no `task-manager-api`.** Models, blueprints e o objeto de extensão SQLAlchemy eram úteis e foram preservados; services e validações foram extraídos onde havia acoplamento real.
- **Segurança pode exigir mudança legítima de contrato.** Remover SQL administrativo, exigir Bearer, ignorar papel enviado no cadastro e retirar hashes das respostas altera contratos vulneráveis, mas evita preservar comportamento inseguro.
- **Validação real foi essencial.** Testes unitários isolados não bastaram: os projetos também foram iniciados e exercitados por HTTP, com verificação de status, autorização, efeitos persistidos e rollback quando aplicável.
- **Limitações precisam permanecer visíveis.** O `task-manager-api` tem 9 findings resolvidos e três parciais (F007, F011 e F012); declarar todos os problemas resolvidos teria contrariado os documentos de resultado.

## 10. Conclusão

A skill `refactor-arch` funcionou nos três projetos, em Python/Flask e JavaScript/Node.js/Express. Ela detectou stacks e arquiteturas diferentes, gerou auditorias estruturadas com severidade e localização, verificou APIs e dependências deprecated quando aplicável, pausou antes de modificar código e executou refatorações somente após confirmação.

Os resultados também mostram a importância de adaptar MVC à tecnologia e ao estado real da aplicação. O primeiro projeto exigiu uma separação ampla; o segundo exigiu decompor uma God Class e revisar o runtime; o terceiro exigiu preservar componentes adequados e reorganizar apenas as responsabilidades sobrecarregadas. A validação final combinou testes automatizados, boot e requisições HTTP, mantendo documentadas as mudanças de contrato, os trade-offs e os findings parciais.
