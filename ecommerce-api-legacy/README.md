# ecommerce-api-legacy

LMS demonstrativo com checkout em **Node.js / Express 4 / SQLite em memória**.
Pagamento é **somente simulação**, nunca uma cobrança real. Não envie cartões reais.

## Instalação e execução

Requer **Node 24.15+ da série 24** e npm; `.nvmrc` registra o runtime validado.

```sh
npm ci
export ADMIN_EMAIL='admin@example.test'
read -rs 'ADMIN_PASSWORD?Senha do administrador (mínimo 8 caracteres): '
export ADMIN_PASSWORD
npm start
```

O exemplo de leitura de senha acima usa zsh. Em outros shells, defina a variável por
mecanismo equivalente de entrada oculta. A senha não é escrita em arquivo ou argumento
de processo. O servidor escuta `127.0.0.1:3000` e só anuncia prontidão depois de concluir
schema, seed dos dois cursos e hashing do administrador. Sem as variáveis de admin,
inicia sem administrador; não há credenciais padrão. Importar módulos não inicia servidor.

| Variável | Regra |
|---|---|
| `HOST` | `127.0.0.1` por padrão |
| `PORT` | `3000` por padrão; `0` permite porta efêmera para testes |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Opcionais, mas fornecidas juntas; criam admin no boot |
| `SESSION_TTL_SECONDS` | 3600 por padrão; permitido de 60 a 86400 |
| `PAYMENT_MODE` | Apenas `demo` |
| `NODE_ENV` | `production` é recusado: não há gateway real |

O banco permanece em memória, como no projeto original. Reiniciar remove contas,
sessões e operações; o seed recria apenas os cursos e, se configurado, o admin.
Os antigos usuário/senha padrão, matrícula e pagamento fictício pré-gravados foram
retirados. Não há arquivo de banco legado para migrar. `badCrypto` não é aceito como
hash; se houver exportação externa dos dados antigos, a adoção exige redefinição das
senhas, revisão de duplicatas/órfãos e uma migração específica antes de importação.

## Endpoints e contratos

### POST /api/checkout

Mantém `usr`, `eml`, `pwd`, `c_id`, `card`. `usr` deve ter 2–200 caracteres; `eml` é
normalizado e validado; `pwd` é obrigatório, com mínimo de 8 caracteres e máximo de
1024 bytes; `c_id` é inteiro positivo; `card` é string de 13–19 dígitos **de teste**.
Usuário existente precisa fornecer sua senha correta; email sozinho não estabelece
identidade. Novo usuário é cadastrado apenas se o checkout inteiro concluir.

O adaptador `DemoPaymentGateway` mantém a regra demonstrativa de prefixo: `4` aprova,
outros prefixos recusam. Não faz rede, não usa chave de provedor, não registra nem
armazena cartão. A resposta 200 preserva `msg` e `enrollment_id`, acrescentando
`payment_mode: "demo"`. Todas as respostas incluem `X-Payment-Mode: demo`.

Usuário novo, matrícula, pagamento e auditoria são uma transação. Recusa/falha não
persiste alterações parciais. Senhas usam scrypt assíncrono com salt; o KDF ocorre fora
da transação. A seção transacional SQLite é síncrona, curta e não cede o event loop,
impedindo intercalamento de operações na mesma conexão. Matrícula repetida retorna 409.

### POST /api/auth/register (novo)

Aceita `usr`, `eml`, `pwd`; cria sempre `student`, ignorando papel enviado pelo cliente.
Retorna 201 com `user: {id,name,email,role}`. Email duplicado retorna 409. Permite criar
uma conta sem fazer checkout; não existe criação pública de administradores.

### POST /api/auth/login (novo)

Aceita `eml`, `pwd`; retorna `user`, `token`, `token_type: "Bearer"`, `expires_in`.
Token opaco aleatório de 256 bits; somente seu SHA-256 é armazenado. A senha usa scrypt,
não SHA-256. Login substitui a sessão anterior da conta. Sessões expiram, consultam o
papel atual e são removidas ao excluir o usuário. Restart também as invalida.
Não há chave de assinatura compartilhada nem segredo hardcoded.

### GET /api/admin/financial-report

Exige `Authorization: Bearer <token de admin>`. Preserva o array de cursos com
`course`, `revenue` e `students: [{student,paid}]`, incluindo cursos sem matrículas.
São duas consultas de dados por página não vazia, independentemente do número de
cursos/alunos retornados; autenticação faz uma consulta adicional.

Paginação de cursos: `page=1`, `per_page=20` (máximo 100). Paginação de alunos **por
curso**: `student_page=1`, `students_per_page=50` (máximo 100). Receita considera todos
os pagamentos `PAID` do curso, mesmo quando a lista de alunos está paginada. A ordem
agora é determinística, por IDs. Headers `X-Page`, `X-Per-Page`, `X-Student-Page` e
`X-Students-Per-Page` informam os parâmetros aplicados. Página vazia retorna `[]`.

### DELETE /api/users/:id

Exige admin. Usuário sem matrícula é excluído e recebe HTTP 200, texto `Usuário deletado.`.
Usuário com histórico retorna 409; inexistente, 404; ID inválido, 400. Admin não pode
excluir a própria conta. Não há exclusão silenciosa de histórico financeiro.

### Erros

Erros retornam JSON `{error: mensagem}`. Falha inesperada: 500 com mensagem genérica
e referência; logs têm somente evento, referência e classe do erro. Não incluem corpo,
headers, SQL, senha, cartão ou token. JSON inválido retorna 400; formato não JSON, 415;
corpo acima de 16 KiB, 413; credencial ausente/inválida, 401; permissão insuficiente, 403.

## Dependências e arquitetura

Express permanece **4.22.1**, sem atualização major. O driver `sqlite3` foi substituído
por `node:sqlite` do runtime: isso remove a cadeia de nove pacotes deprecated, sem
forçar versões transitivas incompatíveis. O lockfile preserva versões da cadeia Express.
Node 24.15.0 classifica `node:sqlite` como **release candidate (1.2)**. Essa limitação e
o novo requisito de runtime são explícitos; o banco continua SQLite, sem ORM.
As operações síncronas são adequadas ao demonstrador, não uma validação de escala.

Fluxo: routes → controllers → services → repositories → SQLite. `models` contém
validação/invariantes; `presenters` monta DTOs; `middleware` trata identidade e erros;
`config` lê ambiente; `payments` isola simulação; factory/entry point compõem e iniciam.

## Validação

```sh
npm test
npm run test:http
```

`npm test` usa `node:test` e bancos em memória isolados. O teste HTTP inicia o entry
point real em porta efêmera, percorre os três endpoints originais e os dois de
identidade, verifica respostas/efeitos/logs e encerra o servidor em `finally`.
Ele precisa de permissão para abrir uma porta local.

Veja [resultado da refatoração](docs/refactoring.md), [requisições de exemplo](api.http)
e [auditoria original](../reports/audit-project-2.md).
