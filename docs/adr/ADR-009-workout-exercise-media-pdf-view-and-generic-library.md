# ADR-009 — PDF original, mídia por exercício e biblioteca genérica

## Status

Aceito — 2026-09-10.

## Decisão

O PDF original é copiado para `backend/data/imports/<import_id>/original.pdf` durante o parse e servido apenas como `GET /imports/{import_id}/pdf`, com validação UUID, existência do import e resposta inline. A mídia carregada pelo usuário é vinculada a `(import_id, exercise_index)` na tabela `workout_exercise_media`; o índice é global e determinístico dentro da importação para que o endpoint não precise expor dados adicionais do treino.

O descritor visual segue a prioridade `local_manual` (verificada ou não), `generic_library` e `placeholder`. `ExerciseTemplateMedia` continua sendo mídia global do template; `WorkoutExerciseMedia` é específica de uma ocorrência do exercício importado; `GenericMovementLibrary` é uma referência opcional por padrão de movimento.

## Segurança e escopo

- Uploads aceitam somente PNG, JPEG e WEBP com extensão, MIME e assinatura coerentes, até 3 MB, em nomes gerados pelo servidor.
- SVG, path traversal, listagem de diretórios e armazenamento de binários no banco são proibidos.
- A mídia não confirma canonicalização/mapeamento e não altera templates globais.
- Não há endpoints de exclusão nem chamadas de escrita à API Hevy nesta funcionalidade.
- A biblioteca local não usa scraping, URLs inventadas ou imagens sem licença; arquivos devem ser próprios ou licenciados pelo responsável pela instalação.

## Consequências

O frontend consegue revisar o PDF e corrigir uma referência visual sem tocar no plano ou no catálogo Hevy. A biblioteca genérica só é ativada para arquivos que realmente foram instalados em `backend/data/generic-movement-library`, evitando imagens quebradas por padrão.