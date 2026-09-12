# Fase 2 — ExerciseDB e catálogo local

- Migration: `20260911_0005_exercise_model.py`.
- A entidade `Exercise` é independente de `ExerciseTemplate` e pode ser ligada opcionalmente a um template Hevy.
- Cliente ExerciseDB realiza somente GET, usa configuração segura e suporta respostas v1/v2.
- A tela `/exercises` lista, filtra por nome/origem e abre detalhes com instruções/mídia.
- A `ReviewPage` oferece navegação aditiva para explorar o catálogo próprio usando o nome canonicalizado.
- Não houve alteração no fluxo de IA externa nem novas escritas Hevy.