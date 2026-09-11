# Mídia por exercício e PDF — decisões verificadas

- Branch da implementação: `feature/external-ai-canonicalization`.
- PDF original salvo em `backend/data/imports/<import_id>/original.pdf` e servido inline por GET validado por UUID.
- `WorkoutExerciseMedia` é local e específico de uma ocorrência; `ExerciseTemplateMedia` permanece global; biblioteca genérica é fallback opcional.
- Prioridade visual: `local_manual` verificada/não verificada, `generic_library`, placeholder.
- Upload não chama Hevy, não altera mapeamento e valida PNG/JPEG/WEBP por extensão, MIME, assinatura e limite de 3 MB.
- A biblioteca só retorna mídia se o arquivo mapeado existir localmente; não há scraping nem URLs inventadas.