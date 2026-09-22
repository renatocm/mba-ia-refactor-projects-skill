# Relatório de auditoria — task-manager-api

Execução realizada conforme a skill `refactor-arch`, somente nas PHASE 1 e PHASE 2.

Nenhum arquivo foi modificado. Não foram executados testes, instalação de dependências, seed ou inicialização da aplicação.

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
