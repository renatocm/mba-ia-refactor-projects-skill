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

Direção preferida: entrada → controller → serviço/model; persistência e integrações cumprem contratos necessários ao caso de uso. Em fluxos simples, um controller pode usar diretamente um model ORM de acordo com a stack; introduza camadas extras somente para isolar responsabilidades concretas.

Defina transação por unidade de trabalho e lifecycle conforme runtime: conexão/sessão por contexto, pool gerenciado quando suportado, teardown garantido. Não confunda objeto de extensão/factory global com sessão/conexão mutável compartilhada. Operação remota não participa automaticamente da transação local.

Preserve métodos, caminhos, payloads, status, ordenação e efeitos legítimos; registre exceções necessárias para corrigir vulnerabilidades e dados inválidos. Mudanças de schema precisam de migração e estratégia para dados existentes. Defina um contrato de erro compatível, com mensagem pública segura e diagnóstico interno. Mantenha regras comerciais testáveis sem subir o servidor e valide integração HTTP/persistência separadamente.
