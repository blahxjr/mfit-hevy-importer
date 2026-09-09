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

1. Criar a tabela `ExerciseCanonicalization`.
2. Criar o `AIExportAgent`.
3. Criar o `AIResponseImportAgent`.
4. Integrar com o `ExerciseMappingAgent`.
5. Criar a interface de download/upload.
