# ADR-013 — Engine local de execução e histórico de treinos

- **Status:** aceito
- **Data:** 2026-09-11

## Decisão

O MagicMusculo mantém treinos executáveis localmente em três entidades: `Workout`, `WorkoutExercise` e `WorkoutSetLog`. O plano guarda snapshots de séries, repetições, carga, tempo e distância; a execução registra valores reais, RPE e horário de conclusão por série. A rotina Hevy sincronizada preserva seu plano em `Routine.exercise_plan` e pode ser materializada no treino local.

O estado segue transições explícitas:

```text
planned → in_progress → completed
planned → aborted
in_progress → aborted
```

O log de uma série é idempotente por `(workout_exercise_id, set_index)`, permitindo reenvio seguro da mesma série pelo cliente.

## Origens

- Imports MFIT geram um treino local com os exercícios resolvidos no catálogo próprio.
- Ausência de correspondência cria um exercício `custom` local, sem alterar Hevy.
- Rotinas Hevy são usadas somente do cache local já sincronizado; o plano e os exercícios são materializados localmente, e o vínculo `hevy_routine_id` fica preparado para futura sincronização.

## Limites

- Nenhum endpoint de escrita Hevy foi chamado ou criado.
- Nenhuma API Strava foi chamada.
- Contratos e prompts de IA externa permaneceram inalterados.
- A migration é reversível e compatível com SQLite.