# ADR-005: Persistência de Canonicalização de Exercícios

## Status

Accepted

## Contexto

A canonicalização produzida manualmente por uma IA externa precisa ser guardada localmente para auditoria, reprocessamento e melhoria futura do matching. Esses dados são sugestões e não podem sobrescrever a ficha MFIT original nem confirmar um mapeamento no catálogo Hevy.

## Decisão

Criar a tabela `exercise_canonicalizations` com uma relação 1:1 com `SourceExercise`, usando `source_exercise_id` como chave estrangeira única. A tabela armazenará o nome original para auditoria, a sugestão canônica, aliases, dicas semânticas, confiança, necessidade de revisão, metadados do provedor e a resposta sanitizada.

A canonicalização será persistida como dado derivado. O `SourceExercise` continuará sendo a fonte imutável dos dados MFIT, e nenhuma linha de `NormalizedExercise` ou `ExerciseMapping` será alterada por esta etapa.

## Consequências

- Mantém histórico local e rastreabilidade da sugestão.
- Permite reprocessar uma canonicalização sem criar duplicatas.
- Garante idempotência por `source_exercise_id`.
- Permite ordenar e consultar canonicalizações por importação.
- Mantém a revisão humana antes de qualquer matching confirmado ou escrita futura.

## Segurança

- Nunca guardar API keys, tokens, senhas ou payloads não sanitizados.
- Não confirmar mapeamentos automaticamente.
- Não alterar dados originais do MFIT.
- Não criar ou atualizar `ExerciseMapping`.
- Não chamar IA externa, API Hevy ou endpoint `/write` nesta etapa.
- `raw_response_sanitized` só deve receber conteúdo previamente sanitizado.

## Alternativas rejeitadas

- **Sobrescrever `SourceExercise`:** rejeitada porque destruiria a distinção entre dado original e sugestão derivada.
- **Salvar somente em JSON solto:** rejeitada por dificultar integridade referencial, consultas por importação, idempotência e auditoria transacional.
- **Adicionar todos os campos diretamente em `ExerciseMapping`:** rejeitada porque mistura sugestão de linguagem com confirmação de matching e acopla etapas que devem permanecer independentes.
