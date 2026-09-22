---
name: refactor-arch
description: Analise e audite a arquitetura de projetos existentes e, após confirmação explícita do relatório, refatore para MVC conforme a stack detectada. Use para revisão arquitetural, identificação de anti-patterns e modernização de aplicações legadas, inclusive quando somente a análise for solicitada.
---

# Refactor Arch

Execute exatamente as três fases abaixo, em sequência. Em monorepos, delimite o projeto solicitado e mantenha evidências, relatórios e aprovação por escopo. Respeite instruções locais e alterações preexistentes do usuário. Não presuma linguagem, framework ou estrutura de diretórios.

As fases 1 e 2 são somente leitura: não crie nem modifique arquivos, inclusive relatórios, dependências, caches ou bancos. Não importe/inicie aplicações, rode seeds ou comandos com efeitos de escrita nessas fases. Prepare o relatório na conversa. Instalações, migrações e execução pertencem à fase 3, após aprovação. Não exponha valores de segredos no relatório.

## PHASE 1 — PROJECT ANALYSIS

Leia [project-analysis.md](references/project-analysis.md). Inspecione manifestos, lockfiles, configurações e código relevante; siga o fluxo de entrada até persistência e integrações.

Detecte linguagem, framework, dependências relevantes, gerenciador, banco, ORM, entry point e rotas. Identifique domínio e arquitetura efetiva, distinguindo evidência de hipótese. Conte arquivos de código únicos efetivamente analisados; informe separadamente manifestos e documentos consultados, exclusões e limitações. Não confunda arquivos encontrados com arquivos lidos.

Imprima este resumo antes de avançar:

```text
PHASE 1 — PROJECT ANALYSIS
Project: <raiz e escopo>
Language: <linguagens e versões conhecidas>
Framework: <framework e versão declarada/resolvida>
Dependencies: <dependências relevantes; gerenciador; lockfile>
Database / ORM: <tecnologias e evidências>
Domain: <entidades e casos de uso>
Architecture: <componentes, dependências e responsabilidades reais>
Entry points / Routes: <inicialização e superfícies da aplicação>
Files analyzed: <N arquivos de código; M arquivos auxiliares>
Limitations: <não verificado ou não disponível>
```

## PHASE 2 — ARCHITECTURE AUDIT

Leia [anti-patterns.md](references/anti-patterns.md) e [audit-report-template.md](references/audit-report-template.md). Avalie arquitetura, segurança, qualidade e performance; verifique também APIs deprecated contra documentação oficial da versão aplicável.

Para cada finding, registre ID estável, severidade CRITICAL/HIGH/MEDIUM/LOW, caminho relativo, linha ou intervalo exato, descrição, impacto e recomendação. Demonstre o fluxo alcançável e condições do problema; não trate correspondência textual como prova. Separe APIs deprecated, APIs legacy e pacotes descontinuados. Não invente findings para preencher quantidades por severidade. Agrupe ocorrências da mesma causa e ordene CRITICAL → HIGH → MEDIUM → LOW; confira totais.

Prepare o relatório completo na conversa usando o template. Se houver destino solicitado, informe o caminho planejado; salve apenas depois da aprovação. Distingua inspeção estática de testes executados e hipóteses pendentes.

**Ao final desta fase, pause obrigatoriamente e encerre a execução.** Apresente uma pergunta de confirmação explícita para o projeto e findings relatados: “Você confirma a execução da PHASE 3 — REFACTORING para este escopo?” Explique que esta skill exige a confirmação entre auditoria e escrita. Não entre na fase 3, nem altere qualquer arquivo, sem resposta afirmativa explícita ao relatório. Silêncio, pedido inicial de análise ou invocação da skill não são confirmação. Se a resposta limitar o escopo, siga somente o autorizado.

## PHASE 3 — REFACTORING

Somente após confirmação, leia [mvc-guidelines.md](references/mvc-guidelines.md) e as transformações pertinentes de [refactoring-playbook.md](references/refactoring-playbook.md).

1. Planeje mudanças mapeando findings → componentes → validações. Registre árvore anterior, contratos e comandos de execução identificados. Se autorizado, salve o relatório preparado no destino acordado, preservando as referências à revisão anterior.
2. Adapte MVC às convenções da stack: separe Models, Views/Routes e Controllers; adicione Services e Repositories apenas quando separarem responsabilidades reais. Mantenha composition root/entry point claro, configuração externa e tratamento centralizado de erros.
3. Corrija os findings autorizados incrementalmente, preservando contratos e comportamento legítimo sempre que possível. Comportamento vulnerável não é contrato a preservar: explicite alterações necessárias em autenticação, respostas ou validação e suas consequências. Não substitua integrações reais por simulações para fazer testes passarem.
4. Valide no ambiente de teste/desenvolvimento isolado, sem dados ou credenciais de produção. Execute checks adequados à stack e testes relevantes; inicie/boote a aplicação com o comando identificado, verifique prontidão e teste os endpoints existentes (sucesso, entrada inválida, inexistência e autorização quando aplicáveis), incluindo efeitos persistidos. Use banco temporário e encerre processos iniciados. Para aplicações sem HTTP, valide as interfaces equivalentes e marque endpoints como não aplicável.
5. Apresente estrutura antes/depois, contratos preservados/alterados, comandos e resultados da validação, e status por ID: resolvido, parcial, pendente ou não aplicável, com justificativa. Reinspecione o código antes de declarar resolução; se boot ou endpoints não puderem ser verificados, informe a limitação e não declare validação completa.
