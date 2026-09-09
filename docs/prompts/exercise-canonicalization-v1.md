# Canonicalização de exercícios MFIT → Hevy — v1

## Objetivo

Transforme os nomes de exercícios em português extraídos do MFIT em nomes canônicos em inglês técnico de musculação. O objetivo é melhorar uma busca textual futura no catálogo do Hevy. Você está apenas sugerindo termos de busca: não está escolhendo, confirmando ou criando nenhum exercício no Hevy.

## Restrições de segurança

- Não chame APIs, ferramentas, navegadores ou serviços externos.
- Não crie, edite ou exclua rotinas.
- Não crie exercícios customizados.
- Não invente IDs.
- Não afirme que um exercício existe no Hevy.
- Não selecione nem retorne `template_id`, `hevy_template_id`, `routine_id` ou qualquer outro ID remoto.
- Não altere `source_exercise_id`.
- Não altere `source_exercise_order`.
- Não altere `source_workout_order`.
- Não altere `source_name_pt`.
- Não altere séries.
- Não altere repetições.
- Não altere carga.
- Não altere percentual.
- Não converta percentual em kg ou lb.
- Não altere descanso.
- Não altere observações.
- Não altere técnicas.
- Não altere `group_id`.
- Não retorne Markdown, explicações ou texto fora do JSON final.
- Não inclua chaves, tokens, senhas, dados de autenticação ou dados pessoais.

## Regras de canonicalização

1. Preserve qualquer equipamento explícito: máquina, cabo, halter, barra, smith, peso corporal, kettlebell, faixa, anilha e outros.
2. Preserve a pegada, o lado, a posição e a variação quando estiverem explícitos no nome ou nas notas fornecidas.
3. Gere termos em inglês técnico de musculação, usando capitalização legível e específica.
4. Gere de 1 a 5 aliases em inglês que sejam úteis para uma busca textual.
5. Não invente detalhes que não estejam no nome ou no contexto do exercício.
6. Quando houver ambiguidade, use `confidence` baixa, preencha `review_reason` e defina `needs_review` como `true`.
7. Nunca selecione um template real do Hevy e nunca diga que um template existe.
8. Mantenha `needs_review` como `true` por padrão, mesmo quando a confiança parecer alta.
9. Trate somente o nome e o contexto do exercício. Não transforme nem interprete dados de carga, volume, séries, repetições, descanso, percentual, técnicas ou grupos.
10. Copie exatamente os campos de origem exigidos pelo schema, sem reordenar, corrigir ou normalizar seus valores.

## Schema obrigatório

A resposta deve obedecer exatamente ao contrato abaixo. Todos os objetos devem usar somente as propriedades previstas e devem conter os campos obrigatórios.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MFIT External AI Canonicalization Response",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "import_id", "source_filename", "generated_by", "workouts"],
  "properties": {
    "schema_version": { "const": "1.0" },
    "import_id": { "type": "string", "minLength": 1 },
    "source_filename": { "type": "string", "minLength": 1 },
    "generated_by": {
      "type": "object",
      "additionalProperties": false,
      "required": ["provider"],
      "properties": {
        "provider": { "enum": ["chatgpt", "perplexity", "copilot", "grok", "deepseek", "gemini", "claude", "ollama", "other"] },
        "model": { "type": "string" },
        "generated_at": { "type": "string", "format": "date-time" }
      }
    },
    "workouts": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["source_workout_order", "source_workout_name_pt", "exercises"],
        "properties": {
          "source_workout_order": { "type": "integer", "minimum": 0 },
          "source_workout_name_pt": { "type": "string", "minLength": 1 },
          "exercises": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": ["source_exercise_id", "source_exercise_order", "source_name_pt", "canonical_name_en", "search_aliases_en", "movement_pattern", "equipment_hint", "primary_muscle_hint", "secondary_muscles_hint", "confidence", "needs_review", "review_reason", "notes_for_hevy_search"],
              "properties": {
                "source_exercise_id": { "type": "integer", "exclusiveMinimum": 0 },
                "source_exercise_order": { "type": "integer", "minimum": 0 },
                "source_name_pt": { "type": "string", "minLength": 1 },
                "canonical_name_en": { "type": ["string", "null"] },
                "search_aliases_en": { "type": "array", "maxItems": 5, "items": { "type": "string" } },
                "movement_pattern": { "type": ["string", "null"], "enum": ["horizontal_push", "vertical_push", "horizontal_pull", "vertical_pull", "squat", "hip_hinge", "lunge", "knee_extension", "knee_flexion", "calf_raise", "core", "cardio", "mobility", "other", null] },
                "equipment_hint": { "type": ["string", "null"], "enum": ["barbell", "dumbbell", "cable", "machine", "bodyweight", "smith_machine", "kettlebell", "resistance_band", "plate", "other", null] },
                "primary_muscle_hint": { "type": ["string", "null"] },
                "secondary_muscles_hint": { "type": "array", "maxItems": 8, "items": { "type": "string" } },
                "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
                "needs_review": { "type": "boolean" },
                "review_reason": { "type": ["string", "null"] },
                "notes_for_hevy_search": { "type": ["string", "null"] }
              }
            }
          }
        }
      }
    }
  }
}
```

## Contexto de entrada

Use exclusivamente o contexto JSON abaixo. Ele contém dados necessários para a canonicalização e não deve ser enriquecido com informações externas:

{{MFIT_AI_CONTEXT_JSON}}

## Saída obrigatória

Retorne **apenas JSON válido**, sem Markdown, sem cercas de código, sem comentários e sem qualquer explicação antes ou depois do objeto JSON. A resposta deve ser validável pelo schema `docs/schemas/ai-external-response.schema.json`.
