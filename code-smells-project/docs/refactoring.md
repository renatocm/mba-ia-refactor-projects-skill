# PHASE 3 — Resultado da refatoração

Escopo: somente `code-smells-project`, findings F001–F015. O relatório original foi
salvo sem atualizar suas evidências históricas em `../../reports/audit-project-1.md`.
A documentação abaixo é separada para preservar exatamente o relatório solicitado.
Não houve commit, modificação da skill ou dos outros projetos.

## Antes e depois

Antes:

```text
code-smells-project/
├── app.py
├── controllers.py
├── database.py
├── models.py
├── requirements.txt
└── README.md
```

Depois (omitidos `.venv` e caches):

```text
code-smells-project/
├── .gitignore
├── app.py
├── requirements.txt
├── README.md
├── loja/
│   ├── __init__.py
│   ├── auth.py
│   ├── bootstrap.py
│   ├── cli.py
│   ├── config.py
│   ├── database.py
│   ├── errors.py
│   ├── presenters.py
│   ├── routes.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── products.py
│   │   ├── users.py
│   │   ├── orders.py
│   │   └── system.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── policy.py
│   │   ├── products.py
│   │   ├── users.py
│   │   ├── orders.py
│   │   ├── reports.py
│   │   └── system.py
│   └── models/
│       ├── __init__.py
│       ├── repositories.py
│       ├── validation.py
│       └── schema.sql
├── tests/
│   ├── test_api.py
│   └── smoke_http.py
└── docs/
    ├── refactoring.md
    └── http-validation.json
```

`app.py` é o entry point WSGI. A factory compõe config, lifecycle, autenticação,
Blueprint, handlers e CLI. Rotas registram transporte e proteção; controllers adaptam
HTTP; services aplicam política/regras/transações; models contêm invariantes e SQL
parametrizado; presenters implementam as views JSON. Não foi adicionado ORM.

| Antes | Depois |
|---|---|
| SQL público e concatenado | Administração HTTP removida; bind em todo valor externo |
| Senhas em texto puro e nos DTOs | scrypt com salt; DTO público explícito |
| Login sem identidade persistente | Bearer assinado com expiração; identidade/papel verificados |
| Conexão global compartilhada | Conexão por contexto com fechamento garantido |
| Estoque vulnerável e falhas parciais | Quantidades agregadas; transações e rollback; cancelamento idempotente |
| N+1 por pedido/item | Duas consultas de dados por página não vazia |
| Debug público e chave fixa | Debug desligado; host local; segredo externo obrigatório |
| Boot cria schema e contas padrão | CLI explícita sem seed; migração não destrutiva |

## Contratos preservados e alterados

Preservados: métodos e caminhos das 17 operações legítimas; campos básicos
`dados`/`sucesso`/`mensagem`, IDs e campos públicos de produtos/pedidos; HTTP 201 para
criações e 200 para consultas/alterações bem-sucedidas; filtros existentes; PUT de
produto continua exigindo `nome`, `preco`, `estoque`; defaults `descricao=""` e
`categoria="geral"`; relatório mantém faixas e definição prévia de faturamento.

Alterações justificadas:

- `/admin/query` e `/admin/reset-db`: removidos (404).
- Operações sensíveis exigem Bearer; ausência/token inválido retorna 401, falta de
  permissão retorna 403. Usuário só pode acessar seus dados/pedidos, salvo admin.
- Cadastro ignora papel informado e cria cliente. `create-admin` é CLI local.
- Login acrescenta token, tipo e expiração; não usa cookies. Email é normalizado;
  duplicação retorna 409. Novas senhas têm mínimo de 8 caracteres.
- Listas de usuários e detalhe não retornam senha/hash. Health mantém status,
  database e versão; remove segredo, caminho, debug, ambiente e contagens internas.
- Listagens paginadas: padrão 50, máximo 100. `total` da busca representa a página.
- Valores inválidos retornam 400; conteúdo não JSON, 415; corpo excessivo, 413;
  inexistência, 404; conflitos de integridade/transição, 409; falhas inesperadas,
  500 com referência sem detalhes internos; banco não preparado, 503.
- Produto em histórico de pedido não pode ser excluído (409).
- Quantidades devem ser inteiras positivas; itens repetidos são agregados.
- Status obedece transições; repetição é idempotente; cancelamento anterior ao
  envio recompõe estoque; cancelado/entregue não reabrem. Pedido inexistente: 404.
- Nenhuma notificação externa é anunciada sem integração real.

## Evidência e status por finding

Todos os findings estão **resolvidos no código deste escopo**. Nenhum está parcialmente
resolvido ou pendente. Isso não significa implantação em produção ou reconciliação de
um banco histórico não fornecido.

| ID | Status | Evidência da correção | Validação |
|---|---|---|---|
| F001 | Resolvido | `loja/routes.py` não registra SQL/reset | Ambas as rotas retornam 404 para anônimo/admin; dados preservados |
| F002 | Resolvido | `models/repositories.py` usa placeholders; identificadores dinâmicos só de constantes internas | Aspas, payloads SQL, busca e IDs malformados |
| F003 | Resolvido | `services/users.py` scrypt; `presenters.py` allowlist; `bootstrap.py` migra texto puro | Hashes diferentes para mesma senha, verificação positiva/negativa e ausência em DTO |
| F004 | Resolvido | `auth.py`, `services/policy.py`, `routes.py` | Matriz 401/403/200, propriedade, token adulterado/expirado, mudança de papel |
| F005 | Resolvido | `models/validation.py` e `services/orders.py` | Negativos, bool, frações, repetidos, insuficiência e corrida entre pedidos |
| F006 | Resolvido | `database.py` request-local, teardown, `transaction` | Rollback após débito e restauração; conexões fechadas; concorrência |
| F007 | Resolvido | `app.py`, `config.py`: host local, debug=False | Boot real e log `Debug mode: off` |
| F008 | Resolvido | `services/orders.py` máquina de estados e compensação transacional | Transições, inexistência, repetição e cancelamentos concorrentes |
| F009 | Resolvido | Config externa obrigatória; health reduzido | Factory recusa segredo ausente; respostas sem segredo/path |
| F010 | Resolvido | Factory/routes/controllers/services/models/config/errors/presenters | Revisão das dependências entre módulos e regressão de contratos |
| F011 | Resolvido | Validação compartilhada de criação/PUT e parsing seguro | Tipos incorretos, null, NaN/Infinity, limites e JSON inválido |
| F012 | Resolvido | `models/schema.sql`: FK, UNIQUE, CHECK; exclusão restrita | Órfãos/duplicatas rejeitados, foreign_key_check vazio, migração segura |
| F013 | Resolvido | `Orders.list`: pais paginados + JOIN de itens em lote | 2 SELECT de pedidos/itens (+1 de identidade) para página com múltiplos pedidos |
| F014 | Resolvido | `errors.py`: handlers centrais, mensagens controladas | Erro induzido retorna 500 genérico sem exceção/SQL; entrada inválida retorna 4xx |
| F015 | Resolvido | `presenters.py` centraliza DTOs | Catálogo, busca, detalhe e pedidos usam os mesmos presenters |

## Validação executada

Data: 2026-09-22. Ambiente virtual local, Python 3.14. Dependências instaladas:
Flask 3.1.1, Flask-CORS 5.0.1, Werkzeug 3.1.8 e ItsDangerous 2.2.0, mais transitivas.
Werkzeug e ItsDangerous, já dependências do Flask, foram declaradas diretamente por
serem usadas para hashing/tokens. Testes usam `unittest`, sem novo framework.

| Comando | Resultado |
|---|---|
| `.venv/bin/python -m pip install --no-cache-dir -r requirements.txt` | Dependências instaladas no venv local |
| `.venv/bin/python -m pip check` | Sem dependências incompatíveis |
| `.venv/bin/python -m unittest discover -s tests -v` | 19 testes passaram, incluindo subcasos |
| `.venv/bin/python tests/smoke_http.py` | Boot real; 34 requisições HTTP passaram; debug desligado |

Os erros RuntimeError registrados durante a suíte são injeções deliberadas para
verificar rollback e respostas 500 seguras. Houve um ajuste de expectativa de teste:
email de ataque contendo espaços era corretamente rejeitado com 400; o caso foi
substituído por entrada sintaticamente válida para exercitar também o caminho SQL.

O teste HTTP cria banco temporário e admin por CLI, sobe `python app.py`, aguarda
`/health`, percorre endpoints, verifica estoque/estado/foreign keys no SQLite, encerra
servidor e remove o banco temporário. Resultados: [http-validation.json](http-validation.json).

| Endpoint | Status observados por HTTP real |
|---|---|
| GET `/` | 200 |
| GET `/health` | 200 |
| GET `/produtos` | 200 |
| GET `/produtos/busca` | 200 |
| GET `/produtos/<id>` | 200, 404 |
| POST `/produtos` | 201, 403 |
| PUT `/produtos/<id>` | 200, 400 |
| DELETE `/produtos/<id>` | 200, 404, 409 |
| GET `/usuarios` | 200, 401 |
| GET `/usuarios/<id>` | 200, 403, 404 |
| POST `/usuarios` | 201 |
| POST `/login` | 200, 401 |
| POST `/pedidos` | 201 |
| GET `/pedidos` | 200 |
| GET `/pedidos/usuario/<id>` | 200, 403 |
| PUT `/pedidos/<id>/status` | 200, 404, 409 |
| GET `/relatorios/vendas` | 200 |
| POST `/admin/query` | 404 |
| POST `/admin/reset-db` | 404 |

A suíte Flask test client acrescenta entrada inválida, inexistência, autorização,
injeção, token expirado, rollback, concorrência e migração; os status acima são apenas
os observados no teste de rede, não uma alegação de todos os cenários possíveis.

## Limitações operacionais

Nenhum banco real foi fornecido ou migrado; foi validada a migração de fixtures legadas,
inclusive recusa de dados inválidos com origem intacta. A adoção requer revisar dados,
substituir credenciais anteriormente expostas/de exemplo e reconciliar saldos históricos.
Nenhum servidor foi deixado ativo. Não foi realizada implantação, teste de carga ou
auditoria completa de dependências transitivas. A API não implementa pagamentos,
notificações externas nem revogação individual de token; essas capacidades não existiam
no contrato auditado. O relatório de faturamento conserva a semântica anterior.

Fontes oficiais consultadas para as APIs utilizadas:
[Flask application factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/),
[Werkzeug password hashing](https://werkzeug.palletsprojects.com/en/stable/utils/#werkzeug.security.generate_password_hash),
[ItsDangerous timestamps](https://itsdangerous.palletsprojects.com/en/stable/timed/).
