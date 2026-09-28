# MVC adaptado à tecnologia

MVC define responsabilidades, não uma árvore universal. Preserve convenções e componentes úteis do framework: routers/Blueprints, controllers anotados, módulos, handlers ou templates podem cumprir papéis equivalentes. Uma API JSON tem apresentação por DTO/serializer; não precisa criar telas ou pastas vazias de views. Em CLI ou workers, adapte entrada/saída aos mesmos limites de responsabilidade.

| Componente | Responsabilidade | Limite |
|---|---|---|
| Model | Entidades, relacionamentos e invariantes do domínio; mapeamento ORM conforme convenção. | Não depende de request/response HTTP nem expõe senha/hash na saída pública. |
| View / Routes | Registrar entradas, selecionar handler, serializar DTOs ou renderizar templates. | Sem SQL, cálculo comercial ou transação espalhada na apresentação. |
| Controller | Adaptar entrada, chamar o caso de uso e selecionar resposta/status. | Mantém-se pequeno; validação sintática pode ser delegada a schema. |
| Service, quando necessário | Coordenar caso de uso, regras entre entidades, transação e integrações. | Sem dependência de objetos HTTP; não criar um serviço gigante substituindo a antiga God Class. |
| Repository / Data Access, quando necessário | Consultas, persistência e otimização de acesso a dados. | Não devolver respostas HTTP; não criar wrappers sem valor sobre cada chamada ORM. |
| Config | Ler ambiente/secret store, validar configuração e oferecer valores tipados. | Sem segredos no código/logs; valores sensíveis obrigatórios não recebem fallback inseguro. |
| Middleware / Error handling | Autenticação transversal, contexto, tradução central de erros e logs. | Autorização por recurso permanece próxima do caso de uso; erros internos não vazam para cliente. |
| Composition root / Entry point | Construir aplicação, conectar dependências, registrar rotas e lifecycle. | Não contém regras comerciais nem executa seeds destrutivos ao importar/iniciar. |

Direção preferida: entrada → controller → service/use case → models/repositories; persistência e integrações cumprem contratos necessários ao caso de uso. O service pode usar models ORM sem repository intermediário quando a complexidade não justificar essa camada.

## Thin route / thin controller

Uma route/controller HTTP deve se limitar, preferencialmente, a:

- Receber e parsear parâmetros HTTP, delegando validação sintática a schemas quando adequado.
- Obter identidade/contexto da requisição.
- Delegar para service/use case.
- Converter resultado para resposta HTTP/presenter.
- Mapear erros por meio do mecanismo centralizado.

Uma route/controller NÃO deve conter diretamente queries ORM; `db.session.get/query/filter/filter_by`; `db.session.add/delete/commit/rollback`; SQL; agregações de relatório; regras comerciais; loops de persistência; ou transações. Isso inclui APIs equivalentes da stack detectada. Essas responsabilidades pertencem aos services e, quando útil, a repositories/data access; o service define a unidade transacional e o domínio mantém suas invariantes. Obter a identidade HTTP não equivale a decidir regras de autorização comercial, que pertencem ao caso de uso.

Esse limite vale para TODAS as rotas do módulo auditado, inclusive leitura, exclusão e relatórios, não somente para endpoints alterados inicialmente.

Defina transação por unidade de trabalho e lifecycle conforme runtime: conexão/sessão por contexto, pool gerenciado quando suportado, teardown garantido. Não confunda objeto de extensão/factory global com sessão/conexão mutável compartilhada. Operação remota não participa automaticamente da transação local.

Preserve métodos, caminhos, payloads, status, ordenação e efeitos legítimos; registre exceções necessárias para corrigir vulnerabilidades e dados inválidos. Mudanças de schema precisam de migração e estratégia para dados existentes. Defina um contrato de erro compatível, com mensagem pública segura e diagnóstico interno. Mantenha regras comerciais testáveis sem subir o servidor e valide integração HTTP/persistência separadamente.
