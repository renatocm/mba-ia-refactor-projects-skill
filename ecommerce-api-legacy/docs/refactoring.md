# PHASE 3 — ecommerce-api-legacy

Escopo: F001–F013 da auditoria. O relatório original foi preservado literalmente em
`../../reports/audit-project-2.md`; o resultado está neste documento separado para não
reescrever suas evidências históricas. Sem commit, sem mudanças na skill ou nos projetos
`code-smells-project` e `task-manager-api`.

## Antes e depois

Antes:

```text
ecommerce-api-legacy/
├── src/
│   ├── app.js
│   ├── AppManager.js
│   └── utils.js
├── package.json
├── package-lock.json
├── api.http
└── README.md
```

Depois (sem node_modules):

```text
ecommerce-api-legacy/
├── .gitignore
├── .nvmrc
├── package.json
├── package-lock.json
├── README.md
├── api.http
├── src/
│   ├── app.js
│   ├── create-app.js
│   ├── config/index.js
│   ├── controllers/index.js
│   ├── routes/index.js
│   ├── services/
│   │   ├── auth.js
│   │   ├── checkout.js
│   │   ├── policy.js
│   │   ├── reports.js
│   │   └── users.js
│   ├── repositories/
│   │   ├── checkout.js
│   │   ├── reports.js
│   │   ├── sessions.js
│   │   └── users.js
│   ├── models/
│   │   ├── errors.js
│   │   └── validation.js
│   ├── middleware/
│   │   ├── auth.js
│   │   └── errors.js
│   ├── presenters/index.js
│   ├── security/passwords.js
│   ├── payments/demo.js
│   └── database/
│       ├── index.js
│       ├── schema.sql
│       └── seed.js
├── test/services.test.js
├── scripts/smoke-http.js
└── docs/
    ├── refactoring.md
    └── http-validation.json
```

| Antes | Depois |
|---|---|
| AppManager reúne bootstrap, SQL, HTTP e negócio | Factory e componentes por responsabilidade |
| Base64 truncado/senha padrão | scrypt assíncrono com salt; sem fallback |
| Email identifica usuário sem comprovação | Checkout verifica senha; admin usa sessão Bearer |
| Gravações independentes | Transação para cadastro novo, matrícula, pagamento e auditoria |
| Cartão e chave nos logs | Logs públicos controlados; sem dados de pagamento |
| Pagamento aparenta integração | Adaptador Demo explícito, sem rede e bloqueado em modo production |
| 1 + C + 2E consultas no relatório | 2 consultas de dados por página não vazia |
| Órfãos e duplicados | FK, UNIQUE, CHECK e política de exclusão restrita |
| Cache global sem consumidor | Removido |
| 9 pacotes deprecated no lockfile | 0 pacotes marcados deprecated; Express major preservado |

## Contratos

Mantidos os três métodos/caminhos originais:

- `POST /api/checkout`: mesmos nomes `usr`, `eml`, `pwd`, `c_id`, `card`; HTTP 200 de
  sucesso com `msg` e `enrollment_id`; curso ausente/inativo continua 404.
- `GET /api/admin/financial-report`: array com `course`, `revenue`, `students`,
  `student`, `paid`, incluindo cursos sem matrícula. Receita soma somente PAID.
- `DELETE /api/users/:id`: HTTP 200 com texto na exclusão bem-sucedida.

Mudanças necessárias, com justificativa:

1. **Identidade e autorização (F001):** relatório e exclusão exigem Bearer de admin;
   401 sem credencial válida e 403 sem papel. Checkout de usuário existente exige
   senha correta (401 caso contrário). Novo cadastro público só cria student.
2. **Rotas de suporte à identidade:** `/api/auth/register` (201) permite cadastro sem
   checkout; `/api/auth/login` (200) emite token opaco com expiração. Login novo revoga
   sessão anterior; exclusão de conta também revoga. Papel é lido do banco a cada uso.
3. **Senha (F002):** obrigatória, 8 caracteres a 1024 bytes; scrypt N=32768/r=8/p=3,
   salt aleatório de 16 bytes e comparação em tempo constante. Nenhum hash é exposto.
4. **Validação (F003):** tipos e limites explícitos; c_id inteiro positivo; card string
   de teste com 13–19 dígitos. Entrada inválida retorna 400 antes das consultas do
   checkout, Content-Type incorreto 415 e corpo acima de 16 KiB 413.
5. **Atomicidade (F004):** checkout recusado/falho não deixa novo usuário, matrícula,
   pagamento ou auditoria parcial. Hashing ocorre antes do BEGIN; dentro da transação
   não há await, evitando intercalamento na conexão compartilhada. Email é rechecado
   após o hashing para resolver corrida com outro cadastro.
6. **Demonstração (F005/F006):** sem logs/armazenamento do cartão; regra de prefixo
   mantida apenas no adaptador Demo. Resposta de checkout acrescenta payment_mode;
   todas as respostas têm X-Payment-Mode: demo. NODE_ENV=production e modo de pagamento
   diferente de demo impedem inicialização. Não se anuncia cobrança real.
7. **Integridade (F008):** um email por usuário e uma matrícula por usuário/curso;
   repetição retorna 409. Um pagamento por matrícula. Excluir usuário com matrícula
   retorna 409, inexistente 404, ID inválido 400. Autoexclusão de admin retorna 409.
8. **Paginação (F009):** cursos page/per_page (padrões 1/20, máximo 100); alunos por
   curso student_page/students_per_page (1/50, máximo 100). Headers informam a página;
   formato do array permanece. Receita é integral por curso; alunos podem estar
   paginados. Ordem por IDs é determinística.
9. **Erros (F010):** corpos de erro passam a JSON; falhas inesperadas são 500 genérico
   com referência. Não se devolvem SQL, stack traces, segredos ou mensagens internas.
10. **Bootstrap:** seed mantém os dois cursos, mas elimina conta/senha padrão e
    matrícula/pagamento inicial fictício. Admin é criado somente por configuração
    externa. Banco em memória e reinicialização a cada boot permanecem.
11. **Runtime (F012):** Node 24.15+ da série 24 é agora requisito declarado. Express
    permanece 4.22.1, igual à resolução auditada; não houve migração para Express 5.

## Decisão sobre dependências

O pacote sqlite3 5.1.7 trazia prebuild-install, tar e a cadeia opcional de node-gyp com
nove registros deprecated. Substituí-lo por `node:sqlite` elimina essa cadeia nativa
externa. Os binds e transações SQLite foram reimplementados e testados; nenhuma
atualização major transitiva foi forçada. O lockfile novo tem 68 pacotes, sem metadados
deprecated. A dependência direta restante é Express 4.22.1.

**Trade-off:** `node:sqlite` é release candidate (estabilidade 1.2) no Node 24.15.0,
não uma API classificada como estável. As consultas são síncronas; o escopo é um
LMS demonstrativo em memória, com respostas paginadas. A escolha não constitui teste
de carga nem recomendação de implantação financeira em produção. Para outro runtime
ou uso de produção, reavaliar o adaptador de dados e o gateway.

Fontes oficiais consultadas:
[SQLite no Node 24.15.0](https://nodejs.org/download/release/v24.15.0/docs/api/sqlite.html),
[scrypt](https://nodejs.org/docs/latest-v24.x/api/crypto.html#cryptoscryptpassword-salt-keylen-options-callback),
[Express 4](https://expressjs.com/en/4x/api/).

## Status dos findings

| ID | Status | Evidência da correção | Validação |
|---|---|---|---|
| F001 | Resolvido | services/auth.js, services/policy.js, middleware/auth.js, services/checkout.js | Senha incorreta 401; admin/student/anônimo; token inválido e papel atualizado |
| F002 | Resolvido | security/passwords.js, seed sem credenciais padrão | Salt diferente; senha correta/incorreta; recusa de pseudo-hash legado; DTO sem hash |
| F003 | Resolvido | models/validation.js, middleware/errors.js | Tipos inválidos rejeitados antes de leitura; JSON inválido sem encerrar servidor |
| F004 | Resolvido | database/index.js, services/checkout.js | Falha após cada INSERT reverte tudo; requisições concorrentes não misturam transações |
| F005 | Resolvido | Adaptador sem log de cartão; logger central redigido | Saída real do servidor sem senha, token, email ou cartão de teste |
| F006 | Resolvido | payments/demo.js, config/index.js | Aprovação/recusa explícitas; payment_mode=demo; modo production recusado |
| F007 | Resolvido | routes/controllers/services/repositories/models/config/middleware/presenters | Revisão da direção de dependências; testes por serviço e HTTP |
| F008 | Resolvido | database/schema.sql, services/users.js | FK/UNIQUE/CHECK; concorrência por email; exclusão protegida; foreign_key_check vazio |
| F009 | Resolvido | repositories/reports.js | 2 consultas para múltiplos cursos/alunos; receita correta e curso vazio preservado |
| F010 | Resolvido | middleware/errors.js, asyncHandler, prontidão após bootstrap | Erro interno redigido; rollback de auditoria; 404/409; servidor inicia/encerra |
| F011 | Resolvido | utils.js e cache removidos | Nenhuma referência a globalCache/logAndCache na aplicação |
| F012 | Resolvido | package.json/package-lock.json, adaptador node:sqlite | Instalação limpa, npm ls, zero metadados deprecated, regressão funcional |
| F013 | Resolvido | Configuração usa apenas valores consumidos | Removidos dbUser/dbPass/smtpUser/totalRevenue e chave fictícia |

Não há findings parcialmente resolvidos ou pendentes no código. Isso não significa
migração de dados externos, implantação ou remoção de riscos próprios de software
demonstrativo; os limites acima continuam explícitos.

## Validação executada

Data: 2026-09-22. Node 24.15.0, npm 11.12.1, SQLite 3.51.3 do runtime.

- `npm ci --ignore-scripts --no-audit --no-fund`: instalação reproduzível pelo lockfile;
  nenhum pacote instalado exige script de build.
- `npm ls --depth=0`: Express 4.22.1 instalado, sem dependência inválida.
- `npm test`: **17 testes passaram** com bancos isolados em memória.
- `node scripts/smoke-http.js`: inicia `node src/app.js`, aguarda prontidão em porta
  efêmera, faz **28 requisições HTTP reais**, verifica contratos e encerra por SIGTERM.
- Inspeção do lockfile: **68 pacotes; 0 com metadados deprecated**. Não foi executada
  auditoria completa de CVEs; ausência de deprecated não é prova de ausência de CVEs.

A suíte cobre scrypt, identidade, validação antes de dados, transações com falha após
cada gravação, concorrência de emails iguais/diferentes, sessões expiradas/adulteradas,
revogação, exclusão, constraints, N+1, receita, configuração e erros redigidos.

| Endpoint original | Status HTTP realmente observados |
|---|---|
| POST /api/checkout | 200, 400, 401, 404, 409 |
| GET /api/admin/financial-report | 200, 400, 401, 403 |
| DELETE /api/users/:id | 200, 400, 401, 403, 404, 409 |

| Endpoint adicional | Status HTTP realmente observados |
|---|---|
| POST /api/auth/register | 201, 409 |
| POST /api/auth/login | 200, 401 |

Resultados individuais em [http-validation.json](http-validation.json). O relatório
HTTP verifica receita/alunos após checkout, ausência de conta após pagamento recusado,
matrícula repetida, histórico preservado após exclusão recusada e remoção da conta sem
histórico. O servidor continua respondendo após JSON/tipos malformados. Logs são
inspecionados quanto aos valores sensíveis enviados. Nenhum servidor fica ativo.

## Dados e limites

O original usa exclusivamente SQLite em memória: nenhum arquivo real foi migrado ou
apagado. Não há preservação possível entre reinícios no contrato anterior ou atual.
Exportações externas, se existirem fora do escopo, precisam de plano próprio, revisão
de dados e redefinição de senhas, pois badCrypto perdeu informação. Nenhuma integração
real foi substituída por simulação; não havia integração real no projeto auditado.
