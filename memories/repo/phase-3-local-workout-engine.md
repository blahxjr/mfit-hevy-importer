# Fase 3 — Engine local de execução

- Migration: `20260911_0006_workout_engine.py`.
- Entidades: `Workout`, `WorkoutExercise` e `WorkoutSetLog`.
- Estados: `planned`, `in_progress`, `completed`, `aborted`, com transições validadas.
- Séries são idempotentes por exercício e índice; RPE aceito de 1 a 10.
- Imports MFIT criam planos locais e resolvem exercícios no catálogo próprio, com fallback `custom`.
- A rotina Hevy é somente cache local; não há novas escritas na API Hevy.
- UI: `/workouts` para histórico e `/workouts/:workoutId` para execução.
- IA externa e Strava não foram alterados ou chamados.