# ADR-003: Contratos da API Hevy

## Status
Draft (será atualizado após Fase 0)

## Context

A API Hevy é crítica para o projeto, pois será o destino final de todas as importações. Precisamos validar:
- Endpoints disponíveis e seus contratos
- Campos obrigatórios vs. opcionais
- Limites de rate limit e tratamento de erros
- Estrutura real das respostas

Referência oficial: https://www.hevyapp.com/api/docs

## Decision

Fase 0 executa validação estruturada da API Hevy usando `scripts/prova_hevy_api.py`.

### Endpoints Validados

#### 1. GET /v1/exercise_templates
**Objetivo:** Listar templates de exercícios disponíveis

**Response esperada:**
```json
{
  "data": [
    {
      "id": "string (UUID)",
      "title": "string",
      "category": "strength|cardio|stretching|plyometrics",
      "muscle_groups": ["string"],
      "equipment": ["string"]
    }
  ]
}
```

**Necessário para:** Mapeamento de exercícios do MFIT

#### 2. GET /v1/routine_folders
**Objetivo:** Listar pastas/coleções de rotinas

**Response esperada:**
```json
{
  "data": [
    {
      "id": "string (UUID)",
      "name": "string"
    }
  ]
}
```

**Necessário para:** Organização de rotinas criadas

#### 3. GET /v1/routines
**Objetivo:** Listar rotinas existentes

**Response esperada:**
```json
{
  "data": [
    {
      "id": "string (UUID)",
      "name": "string",
      "folder_id": "string (UUID or null)",
      "exercises": [...]
    }
  ]
}
```

**Necessário para:** Detecção de duplicatas e reexecução idempotente

#### 4. POST /v1/routines
**Objetivo:** Criar nova rotina

**Request esperado:**
```json
{
  "name": "string (obrigatório)",
  "folder_id": "string (opcional)",
  "exercises": [
    {
      "template_id": "string (obrigatório)",
      "notes": "string (opcional)",
      "sets": [
        {
          "reps": "integer (opcional)",
          "weight": "number (opcional)",
          "weight_unit": "kg|lb (opcional)",
          "duration": "integer em segundos (opcional)",
          "rest": "integer em segundos (opcional)"
        }
      ]
    }
  ]
}
```

**Resposta esperada:** Nova rotina com ID

#### 5. PUT /v1/routines/{routineId}
**Objetivo:** Atualizar rotina existente

**Request:** Mesma estrutura de POST

### Tratamento de Erros

| Status | Significado | Ação |
|--------|------------|------|
| 200 | Sucesso | Prosseguir |
| 400 | Erro de validação | Logar schema, não retry |
| 401 | Não autenticado | Verificar API key e Hevy Pro |
| 403 | Não autorizado | Verificar permissões no Hevy |
| 404 | Recurso não encontrado | Verificar IDs |
| 409 | Conflito (duplicata, etc) | Verificar estado remoto antes de retry |
| 429 | Rate limit | Respeitar Retry-After, backoff exponencial |
| 5xx | Erro servidor | Retry com backoff limitado (max 3x) |

### Rate Limits

**Observar em Fase 0:**
- [ ] Limite de requisições por minuto
- [ ] Header `Retry-After` quando 429
- [ ] Header `X-RateLimit-Remaining`
- [ ] Impacto de múltiplos templates (paginação?)

### Segurança

- API key sempre em variável de ambiente (`.env`)
- Nunca logar a chave completa (usar mask: `****...XXXX`)
- Responses sanitizadas antes de salvar em logs
- Não commitar dados com IDs de usuário real

## Consequences

✅ **Validação antes de implementação:** Evita surpresas integrando depois  
✅ **Documentação de contratos:** Base para implementação confiável  
✅ **Mocks capturados:** Testes rápidos sem chamar API  
✅ **Detecção de incompatibilidades:** Rate limits, schemas diferentes  

⚠️ **Requer API key real:** Não pode ser feito 100% sem Hevy Pro  
⚠️ **Pode descobrir limitações:** Endpoint/campo não existentes ou documentação desatualizada  

## Implementation

Fase 0 executa:

1. `python backend/scripts/prova_hevy_api.py`
2. Testa cada endpoint GET
3. Salva responses em `docs/flows/hevy-api-prova-01.json`
4. Documenta achados em `docs/flows/hevy-api-prova-01.txt`
5. Atualiza mocks em `backend/tests/fixtures/hevy_api_mocks.py`
6. Valida schemas contra esperado em `docs/schemas/hevy-api-schemas.json`

Fase 1 implementa:

1. Cliente Hevy em `backend/src/hevy/hevy_client.py`
2. Testes com mocks (não API real)
3. Retry logic baseado em status code
4. Pydantic models alinhados com contratos reais

## Related ADRs

- ADR-001: 10 Agentes Especializados
- ADR-002: Estado Imutável JSON

## References

- [Documentação oficial Hevy API](https://www.hevyapp.com/api/docs)
- [Fase 0 — Validação de Contratos](../ORQUESTRAÇAO_PRÓXIMO_PASSO.md)
