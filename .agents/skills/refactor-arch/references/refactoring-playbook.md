# Playbook de transformações

Use somente os padrões associados aos findings autorizados. Exemplos curtos são ilustrativos: adapte APIs, placeholders e lifecycle ao driver/framework e versão encontrados. Fragmentos com `repository`, `unit_of_work`, `validate` ou `hasher` representam contratos a implementar, não bibliotecas presumidas. Não execute exemplos nas fases 1 e 2.

## P01 — SQL inseguro → parametrizado (AP01)
- **Problema:** input altera a estrutura do SQL.
- **Objetivo:** separar instrução de valores.
- **Estratégia:** bind nativo do driver; allowlist para identificadores que não aceitam bind.
- **Before:** Python/SQLite `db.execute("SELECT * FROM users WHERE email='" + email + "'")`.
- **After:** Python/SQLite `db.execute("SELECT * FROM users WHERE email = ?", (email,))`.
- **Before:** JavaScript/PostgreSQL ``client.query(`SELECT * FROM users WHERE email='${email}'`)``.
- **After:** JavaScript/PostgreSQL `client.query('SELECT * FROM users WHERE email = $1', [email])`.
- **Validação:** aspas e payloads de injeção são tratados como dados; filtros e resultados legítimos continuam corretos.

## P02 — Password inseguro → hashing adequado (AP03)
- **Problema:** texto puro, encoding ou hash rápido usado como proteção de senha.
- **Objetivo:** armazenar somente hash resistente a ataques offline.
- **Estratégia:** biblioteca mantida para Argon2id/scrypt ou mecanismo nativo adequado; salt automático; migração por reset ou rehash após autenticação válida. Remover senha/hash de DTOs.
- **Before:** Python `stored = hashlib.md5(password.encode()).hexdigest()`; JS `stored = Buffer.from(password).toString('base64')`.
- **After:** Python, com `argon2-cffi`: `stored = hasher.hash(password)` e `hasher.verify(stored, candidate)`; tratar a exceção de senha incorreta como falha de autenticação. JS, com `argon2`: `stored = await argon2.hash(password, {type: argon2.argon2id})` e `await argon2.verify(stored, candidate)`.
- **Validação:** mesma senha produz hashes distintos; correta autentica, incorreta falha sem 500; respostas não contêm credenciais; hashes legados seguem a migração definida.

## P03 — God Class → componentes separados (AP05)
- **Problema:** bootstrap, HTTP, negócio e banco no mesmo objeto.
- **Objetivo:** separar razões de mudança.
- **Estratégia:** extrair casos de uso, persistência e apresentação; injetar dependências no composition root.
- **Before:** `Manager.init_db(); Manager.routes(); Manager.charge(); Manager.report()`.
- **After:** `repository = Repository(pool); service = CheckoutService(repository, gateway); controller = CheckoutController(service); register_routes(router, controller)`.
- **Validação:** regra de checkout testável com gateway falso isolado; integração real preservada; rotas mantêm contratos. Nenhum novo componente acumula todas as responsabilidades.

## P04 — Heavy Route/Controller → Thin Route + Service (AP06)
- **Problema:** handler calcula total, verifica estoque, persiste e monta resposta.
- **Objetivo:** deixar transporte e caso de uso independentes.
- **Estratégia:** schema valida entrada; serviço aplica regras e retorna resultado/erro de domínio; controller traduz HTTP.
- **Before:** JS `router.post('/orders', async (req, res) => { /* validar, SQL, estoque, total, pagamento */ })`.
- **After:** JS `router.post('/orders', adaptAsync(controller.create))`; controller chama `await service.create(validate(req.body), req.user)` e entrega DTO/status. `adaptAsync` encaminha rejeições ao mecanismo de erro da versão do framework.
- **Validação:** testes do serviço cobrem invariantes sem request/response; testes de rota verificam payload, status, identidade e erros.
- **Critério de conclusão — ANTES:** route faz HTTP + ORM + regra + commit.
- **Critério de conclusão — DEPOIS:** route apenas parseia/valida entrada HTTP, obtém identidade/contexto, chama service e retorna presenter/response; erros seguem o mecanismo centralizado. Service coordena regra de negócio, chama repositories/models e define a unidade transacional. Repository/data access concentra queries quando a complexidade justificar.
- **Validação pós-refatoração obrigatória:** busque em todos os diretórios de routes/controllers por `.query`, `db.session`, `session.get`, `session.add`, `session.delete`, `session.commit`, `session.rollback` e chamadas ORM equivalentes da stack detectada, incluindo aliases. Inspecione também handlers definidos fora desses diretórios. Faça a busca final em toda a codebase do projeto para identificar ocorrências residuais ou responsabilidades apenas deslocadas.
- **Revisão dos resultados:** a presença desses padrões não é automaticamente erro; examine cada correspondência e registre a conclusão. Se representar persistência ou regra de negócio direta no handler, o finding não pode ser RESOLVED. Verifique TODAS as rotas do módulo auditado, não só endpoints inicialmente alterados; registre cobertura e resíduos como PARTIAL ou OPEN conforme a PHASE 3.

## P05 — Global DB connection → lifecycle apropriado (AP07)
- **Problema:** requisições compartilham conexão/sessão mutável sem isolamento.
- **Objetivo:** escopo e liberação previsíveis.
- **Estratégia:** usar contexto/unidade de trabalho ou pool gerenciado, incluindo rollback e fechamento em falhas.
- **Before:** Python `connection = connect(...)` no módulo, reutilizada por todos os handlers.
- **After:** pseudocódigo Python `with connection_scope() as connection: repository.save(connection, x)`; `connection_scope` adquire conexão do contexto/pool e garante rollback/liberação ao sair.
- **Before:** JS guarda cliente transacional em variável global.
- **After:** JS `const client = await pool.connect(); try { await executeUnit(client); } finally { client.release(); }`; `executeUnit` controla commit/rollback.
- **Validação:** requisições simultâneas não confirmam alterações umas das outras; erro libera recurso; conexões não crescem indefinidamente. Confira semântica do context manager: nem todo `with` fecha conexão.

## P06 — Operações múltiplas → transação (AP08)
- **Problema:** gravações relacionadas sobrevivem parcialmente a erros.
- **Objetivo:** atomicidade local.
- **Estratégia:** transação abrangendo invariantes, gravações e estoque; rollback em qualquer falha. Efeitos remotos exigem idempotência/compensação própria.
- **Before:** `save_order(); commit(); save_items(); commit(); decrement_stock(); commit()`.
- **After:** pseudocódigo `with unit_of_work.transaction(): save_order(); save_items(); decrement_stock_conditionally()`.
- **Validação:** falha induzida em cada etapa não deixa estado parcial; concorrência não permite estoque negativo; repetição idempotente não duplica cobrança/matrícula quando exigida pelo contrato.

## P07 — N+1 → query agregada/join/batch (AP09)
- **Problema:** uma busca por pai/filho dentro de loop.
- **Objetivo:** limitar round-trips e dados carregados.
- **Estratégia:** agregar no banco ou carregar relações em lote; paginar pais antes de carregar filhos.
- **Before:** `for user in users: count = query_tasks(user.id).count()`.
- **After:** `SELECT user_id, COUNT(*) AS total FROM tasks GROUP BY user_id`; associar resultados aos usuários e preencher zero para ausentes. Para detalhe, buscar filhos por conjunto de IDs ou eager loading equivalente.
- **Validação:** contagem de queries não cresce linearmente por pai dentro da página; resultados preservam zeros, cardinalidade, ordenação e totais, sem duplicação por joins.

## P08 — Validação duplicada → schema compartilhado (AP10/AP11)
- **Problema:** criação/edição repetem regras com divergências e não validam tipos.
- **Objetivo:** uma fonte de regras com semântica própria para cada operação.
- **Estratégia:** compartilhar campos, enums e limites; separar campos obrigatórios na criação dos opcionais na atualização e distinguir ausente de null.
- **Before:** Python/JS repetem `if priority < 1 ...` em cada handler.
- **After:** pseudocódigo `CreateInput = schema(fields, required=['title']); UpdateInput = schema(fields, partial=True); input = validate(operationSchema, body)`; domínio mantém invariantes como quantidade inteira positiva.
- **Validação:** testar null, ausente, strings, booleanos em campos numéricos, limites, enums e atualizações parciais; inputs inválidos retornam 4xx sem gravações parciais.

## P09 — Hardcoded config → environment/config (AP02)
- **Problema:** valores de implantação e segredos misturados ao código.
- **Objetivo:** configuração validada centralmente, sem vazamento.
- **Estratégia:** ler ambiente/secret store no bootstrap; validar obrigatórios; fornecer defaults somente para valores não sensíveis. Não versionar arquivo contendo segredo real.
- **Before:** `gateway_key = 'literal-secret'`.
- **After:** Python `gateway_key = os.environ['PAYMENT_GATEWAY_KEY']`; JS `const gatewayKey = requireEnv('PAYMENT_GATEWAY_KEY')`, com `requireEnv` rejeitando valor ausente/vazio; injetar configuração no gateway.
- **Validação:** segredo ausente impede inicialização com mensagem segura; ambiente válido inicia; logs/respostas não exibem valores; rotação de credencial real é coordenada sem presumir acesso externo.

## P10 — Deprecated API → equivalente moderno (AP13)
- **Problema:** chamada legada incompatível com estratégia de atualização.
- **Objetivo:** usar API suportada preservando semântica.
- **Estratégia:** conferir documentação oficial da versão detectada, assinatura, retorno e tratamento de erro antes de trocar.
- **Before:** Python/SQLAlchemy `user = User.query.get(user_id)`.
- **After:** `user = db.session.get(User, user_id)`; manter retorno 404 quando não existir.
- **Before:** Python `datetime.utcnow()`.
- **After:** `datetime.now(timezone.utc)`, após definir persistência e conversão de datas antigas; não comparar diretamente datas naive com aware.
- **Before:** JavaScript/Node `new Buffer(text, 'utf8')`.
- **After:** `Buffer.from(text, 'utf8')`; para alocação numérica, usar `Buffer.alloc(size)` e conferir limites.
- **Validação:** casos equivalentes, timezone, entrada/retorno e ausência dos avisos alvo. Não trocar API somente por ser antiga; documentar fonte e versões.

## P11 — Error handling espalhado → handler central (AP14)
- **Problema:** cada rota transforma exceções em respostas inconsistentes ou vaza detalhes.
- **Objetivo:** erros previsíveis e diagnóstico seguro.
- **Estratégia:** erros de domínio tipados; adaptador central traduz validação/not-found/conflito; erro inesperado gera 500 genérico e log interno redigido. Mantenha rollback no lifecycle transacional.
- **Before:** Python `except Exception as e: return {'error': str(e)}, 500`; JS callback ignora `err`.
- **After:** handlers específicos retornam 4xx; handler de inesperados registra erro com identificador e devolve corpo seguro. JS callbacks fazem `if (err) return next(err)`; promessas são encaminhadas conforme versão do framework.
- **Validação:** malformed input, registro inexistente, conflito e falha de banco têm status/corpo adequados; erro assíncrono não encerra processo; logs não contêm segredos.

## P12 — Acesso irrestrito → identidade e política (AP04)
- **Problema:** usuário controla ID/papel sem verificação de identidade ou propriedade.
- **Objetivo:** limitar cada ação ao principal autorizado.
- **Estratégia:** middleware verifica sessão/token; caso de uso verifica permissão sobre recurso; operações administrativas exigem papel apropriado atribuído por fluxo confiável.
- **Before:** `delete_user(request.params.id)` disponível anonimamente.
- **After:** pseudocódigo `principal = authenticate(request); policy.require(principal, 'delete', target); service.delete(target)`.
- **Validação:** anônimo recebe 401; autenticado sem permissão recebe 403 ou 404 conforme contrato; autorizado executa; token adulterado e troca de ID não contornam política. Documentar a mudança necessária nos contratos antes abertos.

## P13 — Literais/duplicação de apresentação → política/presenter (AP11/AP12/AP15)
- **Problema:** DTOs copiados, limites repetidos e nomes obscuros.
- **Objetivo:** manutenção localizada sem criar abstrações artificiais.
- **Estratégia:** nomear constantes de domínio, centralizar apenas representações equivalentes e remover símbolos comprovadamente sem uso.
- **Before:** múltiplos handlers montam o mesmo dicionário; `if p > 5` repetido.
- **After:** `presenter.to_public_dto(entity)` e validação com `MAX_PRIORITY`, definidos em componentes apropriados.
- **Validação:** comparar campos públicos, nulls e valores padrão; verificar referências antes de remover export; garantir que o presenter não inclua senha/hash.
