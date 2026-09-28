# Template de relatório

Preencha os campos com evidências, removendo instruções e marcadores não aplicáveis. Prepare na conversa na fase 2; nenhum arquivo deve ser salvo antes da confirmação. Use caminhos relativos à raiz auditada e linhas da revisão analisada. Não inclua segredos ou dados pessoais desnecessários.

```markdown
# ARCHITECTURE AUDIT REPORT

Project: <nome e raiz>
Revision: <commit se disponível; alterações locais relevantes>
Stack: <linguagens, runtimes conhecidos, frameworks, dependências, banco e ORM>
Domain: <entidades e casos de uso>
Architecture: <organização real e fluxo entre componentes>
Files analyzed: <N arquivos de código; M auxiliares; cobertura e exclusões>
Method: <inspeção estática; fontes consultadas; limitações; nenhum teste presumido>

## Summary

| Severity | Count |
|---|---:|
| CRITICAL | <n> |
| HIGH | <n> |
| MEDIUM | <n> |
| LOW | <n> |

Total findings: <soma>

## Findings

### F001 — [<CRITICAL/HIGH/MEDIUM/LOW>] <título concreto>

- Pattern: <APxx>
- File: <caminho relativo>
- Lines: <linha ou início–fim; demais locais se necessários>
- Description: <problema e evidência; fluxo alcançável/condições>
- Impact: <consequência e justificativa da severidade>
- Recommendation: <mudança concreta adaptada à stack>
- Evidence: <trecho curto sem segredo ou explicação verificável>

<Repetir bloco por finding, ordenado por severidade.>

## Deprecated APIs

| API ou dependência | File / Lines | Versão aplicável / situação | Fonte oficial | Substituto / ação |
|---|---|---|---|---|
| <item> | <local> | <deprecated, legacy, pacote descontinuado ou não confirmado> | <URL> | <ação> |

<Se nenhuma chamada deprecated for encontrada, declarar isso no escopo inspecionado.>

## Escopo proposto para refatoração

<Findings abrangidos, componentes afetados e mudanças de contrato necessárias.>
Report destination: <caminho solicitado, a salvar após aprovação; ou somente conversa>
Status: AWAITING EXPLICIT CONFIRMATION

Você confirma a execução da PHASE 3 — REFACTORING para este escopo?
Esta skill exige confirmação após a auditoria; nenhum arquivo foi alterado nesta execução.
```

Após refatoração autorizada, acrescente uma seção de resultado sem reescrever evidências da revisão original: estrutura antes/depois, alterações contratuais, comandos/resultados de boot e testes de endpoints, limitações e a tabela abaixo. Não marque como resolvido um finding apenas por ter movido seu código de arquivo ou corrigido alguns exemplos.

| Finding ID | Status | Evidência da correção | Validação de ausência residual |
|---|---|---|---|
| <ID original> | <RESOLVED / PARTIAL / OPEN / N/A> | <mudança e locais na revisão final; testes/resultados> | <escopo reinspecionado após a mudança; buscas/comandos; resultados e revisão das correspondências; resíduos e limitações> |

Para findings arquiteturais, exija evidência de que a codebase foi verificada novamente após a mudança. Para HIGH/CRITICAL de separação arquitetural, registre cobertura completa dos componentes/handlers abrangidos, sem amostragem. Nos padrões sujeitos à busca final obrigatória da PHASE 3, documente a busca em toda a codebase do projeto. Correspondências descartadas precisam de justificativa; ausência textual isolada não prova resolução. Qualquer ocorrência relevante restante no escopo auditado, cobertura incompleta ou validação inconclusiva impede RESOLVED: use PARTIAL ou OPEN conforme a correção efetiva e liste as pendências.
