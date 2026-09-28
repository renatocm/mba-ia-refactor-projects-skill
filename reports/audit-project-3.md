# Relatório de auditoria — task-manager-api

**Resultado consolidado após a reexecução:** 9 findings resolvidos e 3 parcialmente resolvidos. F004 está **RESOLVED**; F007, F011 e F012 permanecem **PARTIAL**. Validação final: 15 testes passaram, 13 cenários HTTP reais passaram e 20 handlers revisados.

As seções PHASE 1 e PHASE 2 abaixo preservam a auditoria original, inclusive caminhos e linhas daquela revisão. Naquela etapa somente leitura, nenhum arquivo foi modificado e não foram executados testes, instalação de dependências, seed ou inicialização. Os resultados posteriores estão na seção de reexecução ao final deste relatório.

## PHASE 1 — Project Analysis

| Item | Resultado |
|---|---|
| Linguagem | Python |
| Framework | Flask 3.0.0 |
| ORM | Flask-SQLAlchemy 3.1.1 / SQLAlchemy |
| Banco | SQLite (`tasks.db`) |
| Dependências | Flask, Flask-SQLAlchemy, Flask-CORS, Marshmallow, Requests, python-dotenv |
| Domínio | Gerenciamento de tarefas, usuários, categorias, prioridades, status, relatórios e produtividade |
| Entry points | `app.py` para servidor; `seed.py` para carga inicial |
| Arquitetura atual | MVC parcial: models, routes, services e utils |
| Arquivos analisados | 15 arquivos Python + `requirements.txt` + `README.md` |
| Testes | Nenhum teste identificado |
| Lockfile | Não existe |

A organização existente deve ser preservada parcialmente: models, routes, database.py, services e utils. O principal problema é que as rotas concentram HTTP, validação, regras de negócio, acesso ao banco, transações e serialização.

## PHASE 2 — Architecture Audit

Resumo por severidade: CRITICAL 0; HIGH 4; MEDIUM 7; LOW 1.

### F001 — HIGH — Autenticação e autorização ausentes

Arquivos: `routes/task_routes.py:11-299`, `routes/user_routes.py:10-211`, `routes/report_routes.py:12-223`, `routes/user_routes.py:185-211`.

Todos os endpoints são públicos. O login retorna token falso que não é validado. O cliente também controla `role` e `active` em `routes/user_routes.py:52`, `71-78` e `119-125`. Impacto: acesso e alteração de dados sem autorização.

### F002 — HIGH — Senhas armazenadas com MD5 e expostas

Arquivos: `models/user.py:11`, `16-24`, `27-32`; `routes/user_routes.py:201-210`; `seed.py:19`, `26`, `33`.

`set_password()` usa MD5 sem salt; `to_dict()` inclui o hash e o login o retorna. Impacto: hashes podem ser expostos e quebrados.

### F003 — HIGH — Credenciais SMTP hardcoded

Arquivos: `services/notification_service.py:7-10`; `app.py:11-13`.

Host, usuário, senha SMTP e SECRET_KEY estão no código. Impacto: comprometimento de credenciais e configuração insegura.

### F004 — HIGH — Rotas concentram responsabilidades

Arquivos: `routes/task_routes.py:85-223`, `routes/user_routes.py:42-151`, `routes/report_routes.py:12-223`.

As rotas fazem parsing, validação, regras, ORM, commits, serialização, logging e tratamento de exceções. Impacto: acoplamento e baixa testabilidade.

### F005 — MEDIUM — Consultas N+1

Arquivos: `routes/task_routes.py:14-16`, `42`, `51`; `routes/user_routes.py:12`, `22`; `routes/report_routes.py:53-56`, `159-163`.

Loops executam consultas adicionais por item. Impacto: degradação com o volume de dados.

### F006 — MEDIUM — Validação inconsistente

Arquivos: `routes/task_routes.py:85-144`, `156-215`; `routes/user_routes.py:42-78`, `92-125`; `routes/report_routes.py:167-207`; `utils/helpers.py:57-108`.

Há validação parcial de tipos, tags, cores, corpos nulos e regras duplicadas.

### F007 — MEDIUM — Tratamento de erros genérico

Arquivos: `routes/task_routes.py:62-63`, `151-154`, `221-223`; `routes/user_routes.py:87-90`, `128-132`; `routes/report_routes.py:180-188`, `203-209`, `215-223`; `utils/helpers.py:36-41`; `services/notification_service.py:23-24`.

Há `except:` genérico, respostas 500 inconsistentes e possível vazamento de detalhes.

### F008 — MEDIUM — Datetime ingênuo e API depreciada

Arquivos: `app.py:24`; models; routes; `seed.py`; `services/notification_service.py`; `utils/helpers.py`.

O projeto usa `datetime.utcnow()` e `datetime.now()` sem timezone. `datetime.utcnow()` é deprecated desde Python 3.12; recomenda-se `datetime.now(timezone.utc)`.

### F009 — MEDIUM — `Query.get()` depreciado

Arquivos: `routes/task_routes.py:67`, `117`, `158`, `188`, `227`; `routes/user_routes.py:29`, `94`, `136`, `155`; `routes/report_routes.py:105`, `192`, `213`.

A API foi deprecated no SQLAlchemy 2.0; deve ser substituída por `Session.get()`.

### F010 — MEDIUM — Efeitos colaterais e seed destrutivo

Arquivos: `app.py:30-31`; `seed.py:11-14`, `16-37`, `39-92`.

Importar a aplicação cria tabelas e o seed exclui todos os dados antes de inserir exemplos.

### F011 — MEDIUM — Integridade relacional dependente de lógica manual

Arquivos: `models/task.py:13-14`; `routes/user_routes.py:138-146`; `routes/report_routes.py:211-223`.

Não há política explícita de cascade e exclusões dependem de loops manuais.

### F012 — LOW — Regras duplicadas e código não utilizado

Arquivos: `utils/helpers.py:110-116`; imports de routes/models; `services/notification_service.py:4-43`.

Constantes são repetidas nas rotas e o serviço de notificações não está integrado.

## Escopo incremental proposto

Preservar blueprints, endpoints, modelos, tabelas e `database.py`; extrair configuração, autenticação, services, repositories, validação, presenters e error handlers; otimizar consultas; corrigir segurança, timezone e transações; tornar o seed explícito e não destrutivo por padrão.


## PHASE 3 — Reexecução direcionada de F004

A devolutiva da avaliação identificou correção incompleta de F004: embora `create_task` e `update_task` já delegassem parte do trabalho, outros handlers ainda acessavam ORM e executavam regras. A reanálise cobriu todos os arquivos de `routes/` e os **20 handlers**. O escopo principal foi F004, com reavaliação de F007, F011 e F012.

### Comparação arquitetural

| Aspecto | Antes da reexecução | Depois |
|---|---|---|
| Relatórios | `summary_report` e `user_report` consultavam ORM e calculavam agregações nas routes | `report_routes.py` delega para `report_service.py` |
| Categorias | Listagem agregada, criação, edição e exclusão faziam ORM/commit/rollback no handler | Mesmo blueprint e endpoints; persistência e regras em `category_service.py` |
| Tarefas | Exclusão, busca e estatísticas ainda acessavam ORM; rollback nas routes | `task_service.py` ampliado; handlers finos |
| Usuários | Queries, relações ORM, política de cadastro, autorização comercial e login nas routes | `user_service.py` ampliado; routes recebem entrada/identidade e devolvem resposta |
| Transações e erros | Controle distribuído em handlers | `services/transactions.py`, `services/exceptions.py` e `errors.py` |
| Contratos | Endpoints e blueprints existentes | Caminhos, métodos, decorators de autorização, blueprints, modelos e tabelas preservados |

**Routes modificadas:** `routes/report_routes.py`, `routes/task_routes.py` e `routes/user_routes.py`.

**Services criados:** `services/report_service.py` e `services/category_service.py`. **Ampliados:** `services/task_service.py` e `services/user_service.py`.

**Testes:** novo `tests/test_route_contracts.py`; fixture compartilhada em `tests/conftest.py`, mantendo os testes existentes em `tests/test_api.py`.

**Ajuste pontual de contrato:** cadastro sem senha retorna HTTP 400 com “Senha é obrigatória”, substituindo o tratamento inadequado como conflito.

### Validação final executada

- **15 testes passaram**, incluindo os dois existentes.
- **13 cenários HTTP reais passaram**, em `127.0.0.1` com SQLite temporário e encerramento dos servidores.
- Cobertura HTTP: summary report, relatório por usuário, CRUD de categorias, tarefas, usuários, login/autorização, erros e rollback.
- **20 handlers revisados** em todos os arquivos de routes; caminhos, métodos e decorators de autorização preservados.
- Nenhum import de models/SQLAlchemy nas routes; revisão também cobriu acessos a relacionamentos capazes de disparar queries.
- **`git diff --check` passou.**

Comandos executados na validação final, a partir da raiz do repositório:

```bash
PYTHONDONTWRITEBYTECODE=1 /tmp/task-manager-f004-venv/bin/python -m pytest -q -p no:cacheprovider task-manager-api/tests
PYTHONDONTWRITEBYTECODE=1 TASK_API_LIVE_HTTP=1 /tmp/task-manager-f004-venv/bin/python -m pytest -q -p no:cacheprovider task-manager-api/tests/test_route_contracts.py
rg -n '\.query|db\.session|session\.get|session\.add|session\.delete|session\.commit|session\.rollback' task-manager-api/routes
git diff --check
```

O ambiente em `/tmp` foi temporário. Os 13 cenários HTTP não representam uma contagem de requisições individuais.

| Padrão buscado em `routes/` | Ocorrências residuais |
|---|---:|
| `.query` | 0 |
| `db.session` | 0 |
| `session.get` | 0 |
| `session.add` | 0 |
| `session.delete` | 0 |
| `session.commit` | 0 |
| `session.rollback` | 0 |

A revisão da codebase distinguiu a persistência nos services, a consulta de identidade no middleware `auth.py` e os acessos de seed/testes de persistência direta nos handlers HTTP. Não restou ocorrência relevante de F004 nas routes.

### Status consolidado e evidências da reexecução

A contagem passou de **8 resolvidos / 4 parciais** para **9 resolvidos / 3 parciais**.

- **Resolvidos:** F001, F002, F003, F004, F005, F006, F008, F009 e F010.
- **Parciais:** F007, F011 e F012.

Os status dos oito findings resolvidos fora do foco desta reexecução foram mantidos no consolidado; não se atribui a eles uma nova auditoria completa nesta etapa.

| Finding ID | Status | Evidência da correção | Validação de ausência residual |
|---|---|---|---|
| F004 | **RESOLVED** | Três módulos de routes delegam para services; consultas, regras e transações fora dos handlers | Reinspeção de todos os arquivos de routes e 20 handlers; zero ocorrências dos sete padrões e nenhum import de models/SQLAlchemy; testes e HTTP passaram |
| F007 | **PARTIAL** | Erros esperados centralizados; rollback nos services; cadastro sem senha retorna 400 | Resíduo confirmado: `due_date` numérico ainda retorna 500 com `Erro interno` |
| F011 | **PARTIAL** | Modelos já declaram `SET NULL`; nenhuma alteração de modelo/tabela nesta reexecução | Banco isolado com `PRAGMA foreign_keys=0`; exclusões de usuário/categoria deixaram duas referências órfãs, confirmadas por `foreign_key_check` |
| F012 | **PARTIAL** | Imports ociosos removidos das routes | Reinspeção encontrou regras repetidas, helpers/imports sem uso e serviço de notificações não integrado fora das routes |

Os testes aprovados não eliminam os resíduos documentados de F007, F011 e F012. Não foi feito commit na reexecução.
