# ADR-011 — Catálogo local com ExerciseDB

- **Status:** aceito
- **Data:** 2026-09-11

## Decisão

Manter uma entidade local `Exercise`, independente de `ExerciseTemplate`, com origem, metadados, instruções e referências de mídia. A ExerciseDB é consultada somente por GET através de cliente configurável por `EXERCISEDB_API_BASE_URL`, `EXERCISEDB_API_KEY` e timeout.

O sincronismo é incremental por `exercisedb_id`; o enriquecimento com Hevy usa somente templates já armazenados localmente e RapidFuzz. O vínculo é uma sugestão persistida no catálogo, não uma confirmação de mapeamento MFIT.

## Limites

- Nenhuma escrita é adicionada à API Hevy.
- Nenhum scraping ou download automático de mídia é realizado.
- A canonicalização de IA externa não foi alterada.
- A revisão humana continua obrigatória antes de qualquer aprovação.

## Compatibilidade

O schema aceita campos públicos v2 (`exerciseId`, `imageUrl`, listas) e campos legados (`id`, `gifUrl`) sem acoplar a UI ao formato externo.