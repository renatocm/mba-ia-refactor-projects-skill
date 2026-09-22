# Heurísticas de análise

Inspecione a raiz solicitada e instruções locais; inventarie com busca de arquivos, excluindo dependências vendorizadas, builds, caches, código gerado e metadados de VCS. Leia manifestos e configuração antes de seguir os fluxos de negócio. Não execute código para descobrir arquitetura nas fases somente leitura.

| Aspecto | Evidências e interpretação |
|---|---|
| Linguagem | Extensões, imports, compiladores e manifestos. Registre stacks mistas; não derive versão de runtime apenas da sintaxe. |
| Framework | Dependências mais imports, inicialização e configuração efetivamente usados. Diferencie dependência declarada de uso real. |
| Package/dependency manager | Manifesto, lockfile e scripts: pyproject/requirements e uv/Poetry/pip; package.json e npm/pnpm/Yarn; pom/Gradle; csproj/NuGet; go.mod; Cargo.toml; Gemfile; composer.json. Havendo múltiplos lockfiles, registre ambiguidade. |
| Versões | Separe restrição declarada, versão resolvida no lockfile e runtime instalado. Não afirme a terceira sem evidência. |
| Banco de dados | Drivers, DSNs, SQL, migrações, inicialização, containers e chamadas de persistência. Distinga memória, arquivo e serviço externo; omita credenciais. |
| ORM | Mapeamentos, entidades, sessões/unidades de trabalho e consultas; SQL direto pode coexistir com ORM. |
| Entry point | Scripts de execução, main, bootstrap, servidores, comandos CLI e registro de módulos. Observe efeitos colaterais de importação. |
| Rotas / Views | Registro de endpoints, routers, decorators/annotations, handlers, templates e serializadores. Enumere método, caminho, entrada, saída e proteção. |
| Models | Entidades, invariantes, relacionamentos, persistência e representação do domínio. Não considere todo arquivo chamado model uma entidade de domínio. |
| Controllers | Adaptação de entrada e coordenação de casos de uso; localize SQL, loops de negócio e integrações indevidamente concentrados. |
| Services | Casos de uso, transações, regras entre entidades e gateways externos. Verifique se são usados ou apenas existem no diretório. |
| Domínio | Nomes de entidades, rotas, regras e fluxos reais: compra, matrícula, tarefa, cobrança etc. Confirme README com código. |
| Arquitetura existente | Trace entrada → regra → dados/integração → saída. Classifique monólito procedural, camadas, MVC parcial, modular ou outra organização com evidências de dependências. Não imponha rótulo por nomes de pastas. |

Mantenha um inventário de arquivos únicos lidos com seus papéis. Conte código de aplicação, testes e scripts relevantes explicitando a composição; conte manifestos/documentos separadamente. Informe módulos não cobertos em projetos grandes. Gere um mapa sucinto de componentes e uma lista de contratos existentes para orientar a auditoria e a futura validação.

Registre incertezas: autenticação pode estar em middleware, gateway ou infraestrutura fora do escopo; uma biblioteca pode ser opcional; o README pode estar desatualizado. Procure a configuração correspondente antes de afirmar ausência. Arquivos de exemplo não provam uso em produção.
