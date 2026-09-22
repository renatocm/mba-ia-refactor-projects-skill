# code-smells-project

API de e-commerce em Python/Flask: produtos, usuários, pedidos, estoque e relatórios.
A refatoração preserva os caminhos legítimos e o formato básico `dados` / `sucesso`.
As alterações necessárias de segurança e comportamento estão em [docs/refactoring.md](docs/refactoring.md).

## Ambiente e execução

Python 3.9+ (validação executada com Python 3.14). Na raiz deste projeto:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export DATABASE_PATH="$PWD/loja.db"
python -m flask --app app init-db
python -m flask --app app create-admin
python app.py
```

`create-admin` solicita nome, email e senha com confirmação; não há credencial padrão.
`init-db` cria um banco vazio e **recusa sobrescrever um arquivo existente**. Importar ou
iniciar a aplicação não cria tabelas nem executa seed. `/health` retorna 503 se o banco
não foi preparado ou ainda tem schema legado. Use o mesmo `SECRET_KEY` em todos os
processos; armazene-o externamente com segurança. A geração acima serve ao ambiente local.

O servidor local escuta `127.0.0.1:5000`, sem debug ou reloader. Para implantação,
carregue o objeto WSGI `app:app` com o servidor WSGI da infraestrutura, atrás de HTTPS;
`python app.py` é apenas o comando de desenvolvimento, não um servidor de produção.

| Configuração | Valor padrão / regra |
|---|---|
| `SECRET_KEY` | Obrigatória, sem fallback; pelo menos 32 caracteres aleatórios |
| `DATABASE_PATH` | `loja.db` na raiz deste projeto; diretório pai deve existir |
| `TOKEN_TTL` | 3600 segundos; permitido de 1 a 86400 |
| `HOST` / `PORT` | `127.0.0.1` / `5000` para o comando local |
| `CORS_ORIGINS` | Vazio (CORS desabilitado); origens explícitas separadas por vírgula |

## Autenticação

`POST /usuarios` registra sempre um cliente, independentemente de `tipo` no JSON.
Nome, email e senha são obrigatórios; novas senhas precisam de 8 a 1024 caracteres.
Email é normalizado para minúsculas e não pode se repetir. Senhas são armazenadas
somente como hashes scrypt com salt; nunca são retornadas pela API.

`POST /login` continua aceitando `email` e `senha`, preserva `dados`, `sucesso` e
`mensagem` e acrescenta `token`, `token_type: "Bearer"` e `expires_in`. Envie:

```text
Authorization: Bearer <token retornado pelo login>
```

O token assinado tem expiração; o usuário e seu papel são consultados no banco em
cada requisição. Usuário excluído deixa de autenticar e mudança de papel tem efeito
imediato. Não há endpoint de logout/revogação individual nesta API; expiração e rotação
da chave invalidam acesso (rotação invalida todos os tokens). Não envie tokens na URL.

| Superfície | Permissão |
|---|---|
| GET `/`, `/health`, `/produtos`, `/produtos/busca`, `/produtos/<id>` | Pública |
| POST `/usuarios`, `/login` | Pública |
| POST/PUT/DELETE de produtos | Admin |
| GET `/usuarios` | Admin |
| GET `/usuarios/<id>` | Próprio usuário ou admin |
| POST `/pedidos` | Próprio usuário; admin pode informar outro usuário existente |
| GET `/pedidos` | Admin |
| GET `/pedidos/usuario/<id>` | Próprio usuário ou admin |
| PUT `/pedidos/<id>/status`, GET `/relatorios/vendas` | Admin |
| POST `/admin/query`, `/admin/reset-db` | Removidos: 404, inclusive para admin |

Listagens aceitam `page` (padrão 1) e `per_page` (padrão 50, máximo 100), com ordenação
por ID. Os campos `page` e `per_page` são adicionais; `dados` continua uma lista.
Na busca de produtos, `total` conta os resultados **da página**, não todo o catálogo.

## Pedidos e integridade

O corpo de criação mantém `usuario_id` e `itens`, com `produto_id` e `quantidade`.
IDs e quantidades devem ser inteiros; quantidade positiva, até 1.000.000 por produto,
em no máximo 100 linhas. Linhas repetidas são agregadas antes da checagem de estoque.
Estoque e pedido são gravados em uma única transação `BEGIN IMMEDIATE`, com rollback.

Transições: `pendente → aprovado → enviado → entregue`; cancelamento permitido a
partir de `pendente` ou `aprovado`. Repetir o status atual é idempotente. Cancelar
recompõe estoque exatamente uma vez. `cancelado` e `entregue` são terminais.
Não há integração de pagamento: `aprovado` é um status operacional atribuído por admin.

Produto referenciado por pedido não pode ser excluído (409). Pedidos/itens têm foreign
keys; email é único. O relatório mantém a definição anterior de faturamento, que inclui
todos os status e aplica as mesmas faixas de desconto. Notificações fictícias foram
retiradas; a API não promete entrega de email/SMS/push.

## Banco legado

Interrompa escritas no banco antigo e mantenha backup protegido antes da troca.
A migração **não sobrescreve a origem nem um destino existente**:

```sh
python -m flask --app app migrate-legacy --source /caminho/loja-antiga.db --destination /caminho/loja-migrada.db
```

O comando copia IDs, timestamps, sequências e registros para o schema com constraints,
converte cada senha legada de texto puro em scrypt e normaliza emails. Duplicatas,
órfãos, campos nulos proibidos e violações de constraints abortam a operação; o arquivo
novo incompleto é removido e a origem fica intacta. Corrija esses dados de forma
controlada antes de tentar novamente. Após revisar o resultado, configure
`DATABASE_PATH` para o destino e inicie a aplicação.

Não se tenta adivinhar ou corrigir saldos históricos de cancelamentos antigos. Eles
precisam de reconciliação com dados do negócio. As senhas antigas, inclusive as curtas,
continuam autenticando após a migração; contas de exemplo e credenciais previamente
expostas precisam ser substituídas no processo de adoção. O banco de origem ainda
contém texto puro: proteja sua retenção e descarte conforme a política local.

## Validação

```sh
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/smoke_http.py
```

A suíte usa apenas bancos temporários. O teste HTTP inicia `python app.py`, aguarda
prontidão, verifica os endpoints e efeitos persistidos e encerra o processo em `finally`.
Ele precisa de permissão para abrir uma porta local. Senhas e tokens não são impressos.

Consulte [resultado da refatoração](docs/refactoring.md) e
[auditoria original](../reports/audit-project-1.md).
