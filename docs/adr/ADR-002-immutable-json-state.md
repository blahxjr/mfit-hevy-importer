# ADR-002: JSON Schema com Versionamento para Contrato de Estado

## Status
Accepted

## Context
Múltiplos agentes precisam comunicar, e o estado precisa ser imutável e rastreável. Versões de schema podem mudar conforme o projeto evolui.

## Decision
- Usar Pydantic v2 para validação rigorosa
- Estado representado como JSON imutável entre agentes
- Cada estado contém: `agent_name`, `agent_version`, `timestamp`, `input_hash`, `output_hash`
- Versionamento de schema no banco de dados
- Historicamente, nunca apagar versões antigas

## Consequences
- ✅ Auditoria completa
- ✅ Rastreabilidade de todas as mudanças
- ✅ Fácil debugging
- ✅ Migrations seguras (sempre forward-compatible)
- ⚠️ Banco cresce com histórico

## Alternatives Considered
1. Overwrite state (não auditável, perde histórico)
2. Usar apenas JSONSchema sem Pydantic
3. Não versionador schema
