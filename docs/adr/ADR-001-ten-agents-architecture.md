# ADR-001: Uso de 10 Agentes Especializados

## Status
Accepted

## Context
O projeto MFIT → Hevy requer coordenação complexa entre extração de dados, normalização, mapeamento, validação e escrita segura em API externa.

## Decision
Usar arquitetura de 10 agentes especializados, cada um com responsabilidade clara e contrato bem definido:

1. **Orchestrator Agent**: Coordena fluxo, lê memória, valida, encaminha tarefas
2. **Project Memory Agent**: Lê/grava memória persistente, consulta histórico
3. **MFIT Parser Agent**: Extrai dados de PDF/imagem preservando original
4. **Workout Normalizer Agent**: Padroniza unidades, formatos, técnicas
5. **Hevy Catalog Agent**: Consulta e cache do catálogo Hevy
6. **Exercise Mapping Agent**: Mapeia exercícios com múltiplos métodos
7. **Payload Builder Agent**: Constrói JSON exato para API Hevy
8. **Review Agent**: Apresenta revisão legível ao usuário
9. **Hevy Write Agent**: Executa operações aprovadas com idempotência
10. **QA Agent**: Valida resultado pós-escrita

## Consequences
- ✅ Cada agente tem responsabilidade clara
- ✅ Fácil testar e debugar individualmente
- ✅ Fácil substituir ou melhorar um agente
- ✅ Facilita integração com IA/LLM se necessário no futuro
- ⚠️ Requer coordenação forte do Orchestrator
- ⚠️ Mais arquivos e módulos inicialmente

## Alternatives Considered
1. Monolith com tudo em uma classe
2. 3-4 agentes maiores
3. Pipeline simples sem orquestração
