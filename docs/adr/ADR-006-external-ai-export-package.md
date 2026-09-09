# ADR-006: Pacote de Exportação para IA Externa

## Status

Accepted

## Contexto

Após a definição dos contratos e da persistência local de canonicalizações, o usuário precisa obter os dados necessários para uma interação manual com uma IA externa. O MVP não deve integrar provedores de IA nem enviar dados automaticamente.

## Decisão

Criar um `AIExportAgent` que monta, a partir de uma importação local, um contexto JSON sanitizado e um prompt Markdown baseado no contrato da Etapa 1. Os artefatos são gravados somente em `backend/data/exports/<import_id>/` e disponibilizados por endpoints locais de geração e download.

Estrutura de arquivos:

- `mfit_ai_context_<import_id>.json` — contexto MFIT mínimo para canonicalização.
- `mfit_ai_prompt_<import_id>.md` — instruções e contexto incorporado para copiar em uma IA externa.

O pacote retorna somente nomes e caminhos relativos, contagens e hashes de auditoria. A geração é determinística e pode substituir arquivos existentes com o mesmo conteúdo lógico, sem timestamps ou nomes aleatórios.

## Segurança

- Nenhuma IA externa é chamada.
- Nenhuma API Hevy é chamada.
- Nenhum endpoint `/write` é chamado.
- Nenhuma rotina é criada, atualizada ou apagada.
- O contexto não inclui API keys, tokens, senhas, URLs privadas, dados pessoais, IDs do Hevy, mapeamentos, canonicalizações ou logs internos.
- O agente não altera `SourceExercise`, `NormalizedExercise`, `ExerciseMapping` ou `ExerciseCanonicalization`.
- O `AuditEvent` registra somente hashes, contagens e nomes de arquivos.
- `import_id` é validado antes de ser usado em caminhos.

## Idempotência

O nome dos arquivos depende apenas do `import_id`. A mesma importação gera os mesmos bytes e a segunda execução informa `regenerated: true`, sem criar arquivos extras.

## Alternativas rejeitadas

- Integração direta com APIs de IA.
- Exportação de dados completos do catálogo Hevy.
- Inclusão de IDs remotos ou credenciais no pacote.
- Upload automático da resposta da IA.
- Gravação de conteúdo integral do prompt ou contexto em auditoria.

## Consequências

- O usuário mantém controle explícito sobre o provedor externo.
- O pacote pode ser baixado e auditado antes de ser compartilhado.
- A futura importação da resposta permanece separada e validável.
- O diretório de exportação local precisa ser protegido e não deve ser versionado.