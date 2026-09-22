# ARCHITECTURE AUDIT REPORT

**PHASE 1 e PHASE 2 concluídas para `ecommerce-api-legacy`. Nenhum arquivo foi modificado; a skill permaneceu intacta.**

A stack identificada é **JavaScript / Node.js / Express / SQLite**, com domínio de **LMS e comercialização de cursos**. Foram identificados **13 findings**, sendo **5 HIGH, 7 MEDIUM e 1 LOW**. Não há evidência suficiente para classificar algum como CRITICAL neste escopo demonstrativo.

## PHASE 1 — PROJECT ANALYSIS

| Campo | Identificação e evidência |
|---|---|
| Projeto | `ecommerce-api-legacy`, exclusivamente |
| Raiz | `/Users/renatoalencar/Developer/Personal/MBA-IA/mba-ia-refactor-projects-skill/ecommerce-api-legacy` |
| Revisão | `2e3b874f4997deb34326a3b05083e270edddeff9` |
| Estado local | `git status --short` sem alterações |
| Linguagem | **JavaScript**, módulos **CommonJS** (`require` / `module.exports`) |
| Runtime | **Node.js**; versão do projeto não declarada |
| Framework | **Express**: declarado `^4.18.2`; resolvido **4.22.1** |
| Dependência de banco | **sqlite3**: declarado `^5.1.6`; resolvido **5.1.7** |
| Gerenciador | **npm**, com `package-lock.json`, formato 3 |
| Banco | **SQLite em memória**, criado por `new sqlite3.Database(':memory:')` |
| ORM | Nenhum; acesso direto por `db.get`, `db.all` e `db.run` |
| Domínio | Usuários, cursos, matrículas, pagamentos e registros de auditoria |
| Arquitetura | Monólito concentrado em uma classe, com callbacks aninhados e responsabilidades misturadas |
| Entry point | `npm start` → `node src/app.js`, conforme `package.json:5–7` |
| Cobertura | **3 arquivos de código integralmente analisados; 4 auxiliares consultados** |

As versões resolvidas constam em `package-lock.json:641–642` e `2021–2022`. Não são afirmações sobre pacotes efetivamente instalados.

### Inventário analisado

| Arquivo | Cobertura e responsabilidade |
|---|---|
| `src/app.js:1–14` | Integral: criação do Express, middleware JSON, inicialização e servidor |
| `src/AppManager.js:1–141` | Integral: banco, schema, seeds, rotas, checkout, relatório e exclusão |
| `src/utils.js:1–25` | Integral: configuração, cache global e transformação de senha |
| `package.json:1–13` | Integral: manifesto e comando de execução |
| `package-lock.json` | Consulta direcionada a versões, relações de dependência e todos os registros `deprecated` encontrados |
| `README.md:1–14` | Integral: domínio e operação documentada |
| `api.http:1–31` | Integral: exemplos de checkout, relatório e exclusão |

Total de código integralmente lido: **180 linhas em 3 arquivos únicos**. A skill e suas três referências de análise/auditoria foram consultadas separadamente.

Não foram encontrados testes, migrações, configuração externa de autenticação ou infraestrutura no diretório. Os outros projetos ficaram fora do escopo.

### Domínio e arquitetura efetiva

Apesar do nome `ecommerce-api-legacy`, as entidades e os fluxos mostram um **LMS com checkout de cursos**, confirmado pelo README.

```text
src/app.js
    ├── Express + parser JSON + servidor
    └── AppManager
          ├── SQLite em memória
          ├── criação de tabelas e seeds
          ├── checkout e cadastro de usuário
          ├── decisão simulada de pagamento
          ├── matrícula, pagamento e auditoria
          ├── relatório financeiro
          └── exclusão de usuário
                    │
                    └── utils: configuração, senha e cache
```

Não existe separação efetiva em MVC. Os handlers HTTP contêm regras comerciais, consultas e montagem de respostas; a mesma classe controla a inicialização do banco.

### Rotas e contratos observados

| Método e caminho | Entrada | Comportamento e resposta |
|---|---|---|
| `POST /api/checkout` | JSON: `usr`, `eml`, `pwd`, `c_id`, `card` | Busca curso ativo e usuário; cria usuário quando necessário; simula pagamento; grava matrícula, pagamento e auditoria. Sucesso: HTTP 200 com `msg` e `enrollment_id` |
| `GET /api/admin/financial-report` | Sem parâmetros previstos | Lista cursos com `course`, `revenue` e `students`; resposta JSON |
| `DELETE /api/users/:id` | ID na URL | Exclui usuário e retorna texto; não verifica existência nem resultado da exclusão |

**Nenhuma das três rotas implementa autenticação ou autorização.** Não há integração externa real de pagamento ou email.

### Método e limitações

Inspeção estática, rastreamento de entradas até consultas, callbacks e respostas, com consulta à documentação oficial.

Não houve instalação, importação da aplicação, boot, execução de seeds, testes ou gravação de relatório. A implantação e eventuais proteções externas não estão disponíveis. Como o projeto é apresentado como boilerplate demonstrativo, essa condição foi considerada nas severidades.

## PHASE 2 — ARCHITECTURE AUDIT

### Resumo

| Severidade | Quantidade |
|---|---:|
| CRITICAL | 0 |
| HIGH | 5 |
| MEDIUM | 7 |
| LOW | 1 |
| **Total** | **13** |

Os IDs abaixo pertencem exclusivamente à auditoria de `ecommerce-api-legacy`.

### F001 — [HIGH] Operações sensíveis e identidade do checkout não têm autorização

- **Padrão:** AP04.
- **Arquivos/linhas:** `src/app.js:5–10`; `src/AppManager.js:28–40, 66–80, 131–135`.
- **Descrição/evidência:** qualquer cliente pode consultar o relatório financeiro ou excluir um usuário. No checkout, encontrar um email existente é suficiente para utilizar seu ID; a senha recebida não é verificada nesse caminho.
- **Impacto:** exclusão não autorizada, exposição de informações financeiras e associação de matrículas à identidade de terceiros.
- **Recomendação:** autenticação verificável; autorização administrativa para relatório/exclusão; no checkout de usuário existente, vincular a operação à identidade autenticada. Separar cadastro de identificação por email.

### F002 — [HIGH] Transformação de senha não oferece proteção criptográfica adequada

- **Padrão:** AP03.
- **Arquivos/linhas:** `src/utils.js:17–22`; `src/AppManager.js:18, 66–69`.
- **Descrição/evidência:** `badCrypto()` repete os dois primeiros caracteres da representação Base64 e devolve somente dez caracteres. A informação do restante da senha é descartada; não há salt nem KDF apropriada. O seed grava senha em texto puro, e o cadastro aceita uma senha padrão quando `pwd` está ausente.
- **Impacto:** colisões triviais entre senhas, proteção insuficiente dos registros e armazenamento inconsistente. As 10 mil iterações não corrigem a perda de informação e ainda consomem CPU síncrona.
- **Recomendação:** usar scrypt ou Argon2id com salt gerenciado pela biblioteca; exigir senha válida no cadastro; remover fallback e credenciais padrão. Os valores produzidos por `badCrypto()` não permitem recuperar a senha original para migração: prever redefinição.

### F003 — [HIGH] Tipos não validados podem provocar exceções fora do fluxo de erros HTTP

- **Padrões:** AP10, AP14.
- **Arquivos/linhas:** `src/AppManager.js:29–46, 66–71`; `src/utils.js:17–20`.
- **Descrição/evidência:** o checkout valida apenas valores truthy. Um `card` numérico não zero passa pela validação e chega a `cc.startsWith()` dentro de um callback do banco. Com curso ativo e email existente, esse caminho não depende da criação de usuário. Para novo usuário, um `pwd` truthy de tipo incompatível pode falhar em `Buffer.from()`.
- **Impacto:** exceção assíncrona sem tratamento, com possibilidade de encerramento do processo e indisponibilidade de todas as rotas.
- **Recomendação:** validar estrutura, tipos, tamanhos e formatos antes do primeiro acesso ao banco. Encaminhar falhas de callbacks a `next(err)` e centralizar o tratamento de erros.

A documentação do Express diferencia erros síncronos dos erros provenientes de callbacks, que precisam ser encaminhados explicitamente. [Tratamento de erros do Express](https://expressjs.com/en/guide/error-handling/#working-with-callback-apis).

### F004 — [HIGH] Matrícula, pagamento e auditoria são gravados sem atomicidade

- **Padrão:** AP08.
- **Arquivo/linhas:** `src/AppManager.js:50–61, 68–71`.
- **Descrição/evidência:** as gravações são encadeadas por callbacks, sem `BEGIN`, `COMMIT` ou `ROLLBACK`. Se a inserção de pagamento falhar, a matrícula anterior permanece. O cadastro de usuário também precede a decisão de pagamento.
- **Impacto:** matrícula sem pagamento correspondente e inconsistência entre conclusão do checkout e registros persistidos.
- **Recomendação:** definir uma unidade transacional para as gravações relacionadas. Decidir explicitamente se o cadastro deve sobreviver a um checkout recusado. Ao usar uma conexão compartilhada, impedir intercalamento de unidades transacionais de requisições distintas.

O `serialize()` presente na inicialização não transforma o checkout em uma transação.

### F005 — [HIGH] Checkout registra o número completo do cartão em logs

- **Padrão:** AP02 — exposição de dados sensíveis.
- **Arquivo/linhas:** `src/AppManager.js:33, 43–46`.
- **Descrição/evidência:** o valor recebido em `card` é interpolado integralmente em `console.log`, junto ao valor configurado como chave do gateway.
- **Impacto:** se dados reais forem enviados, o número completo do cartão ficará disponível a quem acessa os logs e seus destinos de armazenamento.
- **Recomendação:** não registrar cartão completo; preferir tokenização pelo provedor e identificadores de operação. Aplicar redação aos logs e não registrar credenciais de integração.

A validade e a natureza secreta do literal denominado `paymentGatewayKey` não foram comprovadas. A severidade se apoia na exposição direta do cartão, não em presumir uma credencial real.

### F006 — [MEDIUM] Pagamento é declarado aprovado por uma regra de prefixo

- **Padrão:** AP16.
- **Arquivo/linhas:** `src/AppManager.js:45–54, 59–60`.
- **Descrição/evidência:** qualquer string de cartão iniciada por `"4"` produz `PAID`; não existe chamada a provedor, confirmação de cobrança ou identificador externo.
- **Impacto:** o estado de pagamento representa uma simulação, não uma cobrança verificável.
- **Severidade:** MEDIUM porque README e exemplos apresentam um boilerplate demonstrativo. Não há evidência de operação financeira real que justifique elevar este finding.
- **Recomendação:** encapsular a simulação em um adaptador explicitamente de demonstração/teste. Para uso real, exigir uma integração definida e confirmação verificável antes de marcar pagamento como concluído.

### F007 — [MEDIUM] `AppManager` concentra responsabilidades independentes

- **Padrões:** AP05, AP06.
- **Arquivos/linhas:** `src/AppManager.js:4–138`; `src/app.js:8–10`; `src/utils.js:1–25`.
- **Descrição/evidência:** a classe cria banco, define schema, executa seeds, registra rotas, decide pagamento, cadastra usuários, matricula, calcula relatórios e exclui registros. `utils.js` agrupa configuração, cache e senha.
- **Impacto:** alterações comerciais afetam transporte e persistência; testes isolados ficam difíceis; callbacks aninhados tornam falhas e conclusão das operações menos claras.
- **Recomendação:** separar composition root, routers/controllers Express, serviços de checkout/relatório, acesso a dados, configuração e apresentação JSON. Criar uma fronteira explícita para pagamento.

A severidade considera o tamanho reduzido do projeto; a evidência é a mistura de responsabilidades, não apenas o número de linhas.

### F008 — [MEDIUM] Schema e exclusão permitem registros órfãos e duplicados

- **Padrão:** integridade de dados / AP10.
- **Arquivo/linhas:** `src/AppManager.js:12–15, 40, 50–54, 69, 131–135`.
- **Descrição/evidência:** não há foreign keys entre usuários, matrículas e pagamentos; email não é único. A exclusão remove apenas o usuário. Duas requisições podem consultar a ausência do mesmo email antes das respectivas inserções.
- **Impacto:** matrículas órfãs, dados de identidade ambíguos e concorrência produzindo duplicações. O relatório já contém fallback `Unknown` para usuário inexistente.
- **Recomendação:** definir constraints, habilitar foreign keys e estabelecer política de exclusão compatível com o histórico financeiro. Garantir unicidade de email e tratar conflitos concorrentes; definir a política de matrícula repetida.

### F009 — [MEDIUM] Relatório financeiro executa N+1 e carrega tudo em memória

- **Padrão:** AP09.
- **Arquivo/linhas:** `src/AppManager.js:80–127`.
- **Descrição/evidência:** uma consulta busca cursos; cada curso gera uma consulta de matrículas; cada matrícula gera duas consultas adicionais, para usuário e pagamento.
- **Impacto:** **1 + C + 2E consultas**, sendo C o número de cursos e E o total de matrículas percorridas. Não há paginação ou limite de volume.
- **Recomendação:** consultas agregadas/JOIN ou carregamento em lote, com paginação. Preservar cursos sem matrícula e evitar multiplicar receitas caso existam múltiplos pagamentos por matrícula.

### F010 — [MEDIUM] Erros de banco são ignorados ou convertidos em sucesso

- **Padrão:** AP14.
- **Arquivo/linhas:** `src/AppManager.js:12–21, 37–38, 57–60, 92–94, 104–115, 131–135`.
- **Descrição/evidência:** falha ao gravar auditoria ainda leva a HTTP 200; exclusão ignora `err` e não verifica linhas afetadas. O relatório acessa `enrollments.length` sem tratar a falha da consulta. A busca de curso mistura erro de banco e inexistência em uma resposta 404.
- **Impacto:** sucesso falso, erros classificados incorretamente, relatório incompleto ou exceções secundárias. Falhas de inicialização também não recebem tratamento explícito nos comandos de schema/seed.
- **Recomendação:** verificar cada erro e resultado, encaminhar falhas ao handler central e distinguir 404, conflito e erro interno. Só anunciar prontidão após inicialização bem-sucedida.

Este finding trata falhas de persistência e respostas; F003 trata entradas malformadas que alcançam operações incompatíveis.

### F011 — [MEDIUM] Cache global cresce sem limite e não possui consumidor

- **Padrão:** AP07.
- **Arquivos/linhas:** `src/utils.js:9, 12–15, 25`; `src/AppManager.js:59`.
- **Descrição/evidência:** cada checkout concluído grava uma chave por usuário em `globalCache`. Não há TTL, limite, remoção na exclusão de usuário ou leitura desse cache no código analisado.
- **Impacto:** retenção desnecessária de memória conforme novos usuários realizam checkout; entradas de usuários excluídos continuam presentes.
- **Recomendação:** remover o cache se não houver caso de uso. Se necessário, definir consumidores, limites, expiração e invalidação.

Não se classificou a conexão compartilhada de `node-sqlite3`, isoladamente, como equivalente à conexão Python com uso inseguro entre threads.

### F012 — [MEDIUM] Cadeia de dependências contém pacotes deprecated e sem manutenção

- **Padrão:** AP13 — dependências, não chamadas de API.
- **Arquivo/linhas:** `package-lock.json:33–42, 160–169, 763–778, 827–840, 1074–1084, 1478–1489, 1569–1587, 1718–1726, 2027–2034, 2113–2125`.
- **Descrição/evidência:** o lockfile registra nove pacotes/versões com metadados `deprecated`. `sqlite3` depende diretamente de `prebuild-install` e `tar`; sua cadeia opcional de `node-gyp` inclui outros componentes descontinuados.
- **Impacto:** manutenção e compatibilidade da instalação/build ficam dependentes de componentes sem suporte. Isso não demonstra automaticamente uma vulnerabilidade HTTP alcançável.
- **Recomendação:** revisar a cadeia do driver e sua compatibilidade com o Node escolhido; atualizar ou substituir componentes por meio das dependências responsáveis. Evitar overrides de versões major sem testes.

### F013 — [LOW] Configurações e símbolos sem uso confundem o comportamento real

- **Padrão:** AP15.
- **Arquivos/linhas:** `src/utils.js:2–6, 10, 25`; `src/AppManager.js:2`.
- **Descrição/evidência:** `dbUser`, `dbPass` e `smtpUser` não são consumidos. `totalRevenue` é exportado e importado, mas não participa do cálculo do relatório.
- **Impacto:** sugere autenticação de banco, envio de email e controle global de receita inexistentes, dificultando compreender a arquitetura.
- **Recomendação:** remover símbolos comprovadamente ociosos e manter configuração próxima de seus consumidores. Externalizar valores de implantação quando realmente utilizados.

Não foi afirmado vazamento de credencial de banco válida: o banco efetivo é SQLite em memória e não utiliza esses campos.

## APIs deprecated, APIs legacy e pacotes descontinuados

**Não foi confirmada chamada deprecated no código da aplicação.** Foram identificadas depreciações de dependências transitivas.

| Item | Arquivo/linhas | Situação e fonte | Ação |
|---|---|---|---|
| `Buffer.from()` | `src/utils.js:20` | API suportada; não é o construtor antigo `new Buffer()`. [Node.js Buffer](https://nodejs.org/api/buffer.html) | Corrigir o algoritmo de senha, não substituir por suposta depreciação |
| `express.json()`, rotas e respostas | `src/app.js:5–6`; `src/AppManager.js:28–135` | Não identificadas como deprecated para Express 4. [Express 4](https://expressjs.com/en/4x/api/) | Preservar APIs adequadas e corrigir organização/tratamento de erros |
| `sqlite3.verbose()`, `Database`, `serialize`, `get/all/run` | `src/AppManager.js:1–133` | Interfaces documentadas do driver; callbacks não são, por si, deprecated. [API node-sqlite3](https://github.com/TryGhost/node-sqlite3/wiki/API) | Modernização opcional com cuidado com `this.lastID` |
| `prebuild-install@7.1.3` | `package-lock.json:1569–1573` | Deprecated no lockfile e no [repositório oficial](https://github.com/prebuild/prebuild-install) | Rever o componente de instalação via dependência responsável |
| `rimraf@3.0.2` | `package-lock.json:1718–1722` | Versões anteriores à 4 sem suporte, confirmado no [registro oficial npm](https://registry.npmjs.org/rimraf/3.0.2) | Atualizar a cadeia que o exige |
| `npmlog@6.0.2` | `package-lock.json:1478–1482` | Deprecated no lockfile; [repositório oficial arquivado](https://github.com/npm/npmlog) | Rever cadeia de build |
| `are-we-there-yet@3.0.1` | `package-lock.json:160–164` | Deprecated no lockfile; [repositório oficial](https://github.com/npm/are-we-there-yet) | Rever dependências de logging/build |
| `gauge@4.0.4` | `package-lock.json:763–767` | Deprecated no lockfile; [repositório oficial](https://github.com/npm/gauge) | Rever dependências de logging/build |
| `@npmcli/move-file@1.1.2` | `package-lock.json:33–37` | Lockfile informa migração da funcionalidade para `@npmcli/fs`; [repositório oficial](https://github.com/npm/move-file) | Atualizar dependência responsável |
| `glob@7.2.3` | `package-lock.json:827–831` | Deprecated registrado no lockfile; reconfirmação externa da versão bloqueada nesta consulta | Revisar atualização da cadeia |
| `inflight@1.0.6` | `package-lock.json:1074–1078` | Lockfile informa ausência de suporte e vazamento de memória; reconfirmação externa bloqueada | Remover pela atualização/substituição da dependência responsável |
| `tar@6.2.1` | `package-lock.json:2113–2117` | Deprecated registrado no lockfile; reconfirmação externa da versão bloqueada nesta consulta | Revisar atualização da cadeia do driver |

**Distinções importantes:**

- Express 4 não foi classificado como deprecated apenas por existir Express 5.
- CommonJS e callbacks são escolhas de organização/API; não comprovam depreciação.
- Não foi executado `npm audit`; não se atribuiu CVE ou exploração concreta com base apenas nos avisos do lockfile.
- Não foi comprovada descontinuação das duas dependências diretas.

## Evidências que não sustentam novos findings

- **SQL Injection:** os valores externos nas consultas examinadas usam placeholders `?`. Não há executor público de SQL arbitrário.
- **Persistência em memória:** é comportamento explicitamente documentado do demonstrador, não perda acidental de um banco em arquivo.
- **Credenciais aparentes:** nomes ou prefixos sugestivos não provam que os literais configurados sejam segredos reais utilizáveis.
- **Pagamento:** a simulação foi identificada, mas não tratada como uma integração real defeituosa.
- **Testes:** os exemplos de `api.http` não equivalem a testes automatizados executados.

## Escopo proposto para eventual PHASE 3

Somente `ecommerce-api-legacy`, cobrindo **F001–F013**: separar rotas/controllers Express, serviços de checkout e relatório, acesso a dados, configuração, erros e apresentação; corrigir identidade, senhas, logs, integridade e transações; reduzir consultas do relatório; revisar dependências.

Mudanças de contrato necessárias deverão ser explicitadas antes da implementação: proteção das operações administrativas, verificação de identidade no checkout, validação de entrada, política de exclusão, paginação e distinção entre pagamento demonstrativo e real.

**Destino do relatório:** somente esta conversa.  
**Status:** `AWAITING EXPLICIT CONFIRMATION`.  
**Arquivos alterados nesta execução:** nenhum.

**Você confirma a execução da PHASE 3 — REFACTORING para `ecommerce-api-legacy`, no escopo F001–F013 deste relatório?**

A [skill refactor-arch](/Users/renatoalencar/Developer/Personal/MBA-IA/mba-ia-refactor-projects-skill/.agents/skills/refactor-arch/SKILL.md) exige: “Ao final desta fase, pause obrigatoriamente e encerre a execução.” Conforme essa regra e sua instrução, parei após a PHASE 2.
