# Fixtures e Mocks para Testes

Este diretório contém dados de teste e mocks para validação da API Hevy sem chamar endpoints reais.

## Estrutura

### `hevy_api_mocks.py`
Mocks das respostas da API Hevy capturadas durante Fase 0.

**Uso em testes:**
```python
from tests.fixtures.hevy_api_mocks import get_mock_templates, get_mock_folders

def test_with_mock():
    templates = get_mock_templates()
    assert len(templates["data"]) > 0
```

### `mfit_sample_*.pdf`
Arquivos PDF de referência do MFIT para testar parser.

**Criado em:** Fase 0 (após confirmar exemplo real)
**Conteúdo esperado:**
- Pelo menos uma ficha de treino
- Exercícios com séries, repetições, carga
- Observações e técnicas avançadas

## Capturando Dados Reais (Fase 0)

Após executar `scripts/prova_hevy_api.py`:

1. Respostas salvas em `docs/flows/hevy-api-prova-01.json`
2. Copiar exemplos para `hevy_api_mocks.py`
3. Remover dados sensíveis (IDs de usuário, etc.)
4. Commitar no Git (sem exposição de chaves)

## Mocks vs. API Real

| Aspecto | Mock | Real |
|---------|------|------|
| Velocidade | Imediato | ~100-200ms |
| Rate limit | N/A | Limitado |
| Dados | Exemplos | Seu account |
| CI/CD | ✅ Sim | ❌ Requer chave |
| Desenvolvimento | ✅ Preferido | ❌ Apenas validação |

## Adicionando Novos Mocks

1. Executar prova_hevy_api.py
2. Copiar response de `hevy-api-prova-01.json`
3. Remover campos desnecessários
4. Adicionar função `get_mock_*()` em `hevy_api_mocks.py`
5. Documentar em docstring

Exemplo:
```python
def get_mock_workout_history():
    """Mock de histórico de treinos"""
    return {
        "data": [
            {
                "id": "history-001",
                "routine_id": "routine-001",
                "date": "2026-08-31",
                ...
            }
        ]
    }
```

## Fase 0 Entregáveis

- [x] `hevy_api_mocks.py` com templates, folders, routines
- [ ] `mfit_sample_01.pdf` (PDF real do MFIT)
- [ ] Documentação em `docs/flows/hevy-api-prova-01.txt`
- [ ] Schemas reais em `docs/schemas/hevy-api-real.json`
