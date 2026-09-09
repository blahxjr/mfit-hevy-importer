# Plano — Etapa 1.1: IA Externa para Canonicalização MFIT → Hevy

- **Data:** 2026-09-08
- **Branch:** `feature/external-ai-canonicalization`
- **Objetivo do MVP:** permitir que o sistema exporte um contexto JSON sanitizado e um prompt para o usuário utilizar manualmente uma IA externa na canonicalização de nomes de exercícios MFIT em inglês técnico, sem integração de API e sem escrita no Hevy.
- **Fluxo manual:** parser/normalização local → exportação de prompt + contexto JSON → usuário usa ChatGPT, Perplexity, Copilot, Grok, DeepSeek ou outra IA → usuário salva a resposta JSON → futura importação e validação local → matching melhorado → revisão humana → escrita controlada somente em fase posterior.
- **Fase atual:** Etapa 1 — contratos e documentação.

## Arquivos criados

- `docs/schemas/ai-external-context.schema.json` — contrato do contexto exportado para a IA externa.
- `docs/schemas/ai-external-response.schema.json` — contrato da resposta JSON da IA externa.
- `docs/prompts/exercise-canonicalization-v1.md` — prompt universal em português.
- `docs/adr/ADR-004-external-ai-canonicalization.md` — decisão arquitetural e controles de segurança.
- `memories/repo/fase-1-1-external-ai-plan.md` — registro deste plano e próximas etapas.

## Restrições de segurança

- Nenhuma API de IA é chamada automaticamente.
- Nenhuma chamada ao Hevy é permitida nesta funcionalidade.
- Nenhum endpoint `/write` deve ser chamado.
- Nenhum POST, PUT, PATCH ou DELETE deve ser enviado à API Hevy.
- O contexto não contém API keys, tokens, senhas, IDs de templates, IDs de rotinas ou dados pessoais.
- A resposta não aceita IDs do Hevy, campos de escrita, volumes, cargas ou alterações dos dados de origem.
- Nenhum mapeamento é confirmado automaticamente.
- Revisão humana permanece obrigatória.

## Próximas etapas

1. Criar o `AIExportAgent`.
2. Criar o `AIResponseImportAgent`.
3. Integrar com o `ExerciseMappingAgent`.
4. Criar a interface de download/upload.

## Etapa 2 concluída

- Criada a entidade `ExerciseCanonicalization` na tabela `exercise_canonicalizations`.
- Criada relação 1:1 com `SourceExercise`, com `delete-orphan` para remover o dado derivado junto com o exercício de origem.
- Persistidos nome original para auditoria, nome canônico, aliases, dicas semânticas, confiança, revisão, provedor, modelo, versão do prompt e resposta sanitizada.
- Arrays são armazenados como JSON serializado, com helpers seguros que retornam listas vazias para valores nulos ou inválidos.
- `SourceExercise.source_name`, `NormalizedExercise` e `ExerciseMapping` permanecem preservados e inalterados.
- Criada migration reversível `20260908_0004_exercise_canonicalizations.py`.
- Criado `ExerciseCanonicalizationRepository` com buscas por ID, exercício, importação, upsert idempotente e exclusão filtrada.
- Criados testes unitários para criação, busca, upsert, unicidade, ordenação por importação, serialização, preservação e cascade.
- Nenhuma IA externa, API Hevy ou endpoint `/write` foi chamado.

**Próximo passo:** criar o `AIExportAgent`.

## Etapa 3 concluída

- Criado o `AIExportAgent` para gerar prompt Markdown e contexto JSON sanitizado.
- Arquivos gerados em `backend/data/exports/<import_id>/`, fora do Git.
- Criados os endpoints locais `POST /ai-export/{import_id}`, `GET /ai-export/{import_id}/download/prompt` e `GET /ai-export/{import_id}/download/context`.
- Criado o script `backend/scripts/export_ai_package.py`.
- Adicionado bloco opcional de geração e download na página de importações.
- Adicionados testes de agente e rotas para estrutura, segurança, idempotência, traversal, downloads e erros.
- Exportação não inclui credenciais, dados pessoais, IDs Hevy, mapeamentos ou canonicalizações.
- Nenhuma IA externa, API Hevy ou endpoint `/write` foi chamado.

**Próximo passo:** criar o `AIResponseImportAgent`.

## Etapa 4 concluída

- Criados schemas Pydantic estritos para respostas de IA externa.
- Criado o `AIResponseImportAgent` com limite, validação UTF-8/JSON/schema e conferência integral contra o import local.
- Criados upload `POST /ai-response/import` e relatório `GET /ai-response/{import_id}/validation-report`.
- Criado o script `backend/scripts/import_ai_response.py`.
- Respostas válidas persistem somente em `ExerciseCanonicalization`, com `needs_review=True` e upsert idempotente.
- Inconsistências rejeitam sem persistência parcial; dados MFIT, normalização e mapeamentos permanecem intactos.
- Adicionada interface de upload, relatório resumido e remapeamento local opcional.
- Revisão humana continua obrigatória.
- Nenhuma IA externa, API Hevy, endpoint `/write` ou rotina Hevy foi chamada.

**Próximo passo:** integrar canonicalizações ao `ExerciseMappingAgent`.
