# Decisão de mídia visual local para templates Hevy

- Política: priorizar imagem oficial quando presente no contrato validado; caso contrário usar imagem local manual e, se não existir, fallback visual gerado localmente.
- Restrições: não fazer scraping, não inventar URLs de imagem, não escrever no Hevy, não assumir que uma visual confirma o mapeamento.
- Local: `exercise_template_media` + serviço `ExerciseVisualService` + rota `/catalog/templates/{template_id}/media`.
- Segurança: upload validado por extensão, MIME, tamanho e path traversal; arquivos servidos pelo app local.
- UX: a UI da revisão usa `TemplateVisualDescriptor` para mostrar card visual com `placeholder` quando não há mídia oficial/local.
- Auditoria: cada item guarda `source`, `image_url`, `local_file_name`, `alt_text`, `attribution`, `is_verified` e timestamps.
