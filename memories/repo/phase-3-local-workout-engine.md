# Fase 3 — Engine local de execução

- Migrations: `20260911_0006_workout_engine.py` e `20260911_0007_routine_exercise_plan.py`.
- Entidades: `Workout`, `WorkoutExercise` e `WorkoutSetLog`.
- Estados: `planned`, `in_progress`, `completed`, `aborted`, com transições validadas.
- Séries são idempotentes por exercício e índice; RPE aceito de 1 a 10.
- Imports MFIT criam planos locais e resolvem exercícios no catálogo próprio, com fallback `custom`.
- A rotina Hevy preserva seu `exercise_plan` no cache e materializa exercícios locais; não há novas escritas na API Hevy.
- UI: `/workouts` para histórico e `/workouts/:workoutId` para execução.
- IA externa e Strava não foram alterados ou chamados.