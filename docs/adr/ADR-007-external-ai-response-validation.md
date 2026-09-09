# ADR-007: Validação da Resposta de IA Externa

## Status

Accepted

## Contexto

O usuário pode devolver manualmente um JSON produzido por uma IA externa. Esse conteúdo não é confiável por padrão e deve ser comparado integralmente com o import MFIT original antes de qualquer persistência.

## Decisão

Usar schemas Pydantic v2 estritos, com `extra="forbid"`, para validar a forma da resposta. Em seguida, comparar importação, nome do arquivo, treinos, ordens, exercícios, IDs e nomes com os registros locais. Somente uma resposta integralmente consistente pode persistir dados derivados em `ExerciseCanonicalization`.

## Validação estrita

- Limite de 5 MB e UTF-8 obrigatório.
- JSON e schema obrigatórios.
- Campos extras e campos de escrita são rejeitados.
- A quantidade e a identidade dos treinos e exercícios devem coincidir exatamente.
- O nome do arquivo deve coincidir com `Import.filename`.
- `needs_review` é sempre forçado para `true`.

## Transação atômica

Todos os upserts usam uma transação controlada pelo agente. Erros de estrutura não persistem nada; erros de banco provocam rollback. Relatórios sanitizados podem ser registrados em `AuditEvent` sem salvar o payload integral.

## Idempotência

O `ExerciseCanonicalizationRepository` atualiza pelo `source_exercise_id`, mantendo uma única canonicalização por exercício. Reimportar o mesmo JSON não cria duplicatas.

## Segurança

- Nenhuma IA externa é chamada.
- Nenhuma API Hevy ou endpoint `/write` é chamado.
- Dados MFIT originais, normalização e mapeamentos não são alterados.
- Não são aceitos IDs do Hevy, credenciais, tokens ou ações de escrita.
- A resposta sanitizada armazena somente campos de canonicalização permitidos e é limitada em tamanho.
- A revisão humana continua obrigatória.

## Alternativas rejeitadas

- Aceitar JSON livre sem schema.
- Persistir parcialmente uma resposta inconsistente.
- Sobrescrever `SourceExercise` ou `NormalizedExercise`.
- Confirmar automaticamente `ExerciseMapping`.
- Enviar a resposta diretamente para a API Hevy.

## Nenhuma escrita no Hevy

Esta etapa apenas valida e persiste sugestões locais. Nenhuma rotina Hevy é criada, atualizada ou removida.