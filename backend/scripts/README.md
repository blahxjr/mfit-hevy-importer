# Scripts — MFIT → Hevy

Utilitários e ferramentas para desenvolvimento e validação do projeto.

## prova_hevy_api.py

**Objetivo:** Validar a API Hevy e capturar schemas reais.  
**Fase:** 0 (Pré-requisito antes de Fase 1)  
**Autenticação:** Requer API key do Hevy Pro

### Como usar

#### 1. Pré-requisitos

```bash
# Ter Hevy Pro ativo
# Ter venv ativado
# Ter .env preenchido com HEVY_API_KEY

cd backend
pip install -r requirements-dev.txt  # Se não instalado ainda
```

#### 2. Obter API Key

1. Acessar https://www.hevyapp.com/settings?developer
2. Copiar API key
3. Preencher em `.env`:
   ```ini
   HEVY_API_KEY=sua_chave_aqui
   ```

#### 3. Executar

```bash
python scripts/prova_hevy_api.py
```

#### 4. Validar Saída

Esperado:
```
PROVA DE CONCEITO — API HEVY
========================================================================

🔍 Testando: GET /v1/exercise_templates
   Status: 200 ✅
   Items: 147

🔍 Testando: GET /v1/routine_folders
   Status: 200 ✅
   Items: 3

... (outros endpoints)

========================================================================
RESUMO DOS RESULTADOS
========================================================================
Total de testes: 4
Sucessos: 4 ✅
Falhas: 0 ❌

✅ Todos os testes passaram!

✅ Resultados salvos em: docs/flows/hevy-api-prova-01.json
✅ Resumo TXT salvo em: docs/flows/hevy-api-prova-01.txt
```

### Arquivos de Saída

| Arquivo | Formato | Uso |
|---------|---------|-----|
| `docs/flows/hevy-api-prova-01.json` | JSON | Dados estruturados para análise |
| `docs/flows/hevy-api-prova-01.txt` | Texto | Resumo legível |

### Tratamento de Erros

#### Erro 401 — Não Autenticado

```
❌ ERRO: Erro de Autenticação: 401 Client Error
```

**Causa:** API key inválida, expirada ou não é Hevy Pro  
**Solução:**
1. Verificar API key em https://www.hevyapp.com/settings?developer
2. Confirmar Hevy Pro em https://www.hevyapp.com/account
3. Atualizar `.env` e tentar novamente

#### Erro 429 — Rate Limit

```
Status: 429 ❌
Erro: 429 Client Error: Too Many Requests
```

**Causa:** Atingiu limite de requisições por minuto  
**Solução:**
- Documentar limite observado
- Implementar backoff exponencial em Fase 1
- Aguardar e tentar novamente

#### Erro 5xx — Servidor

```
Status: 500+ ❌
Erro: 5xx Server Error
```

**Causa:** Problema no servidor Hevy (raro)  
**Solução:**
- Verificar status em https://status.hevyapp.com
- Tentar mais tarde
- Contatar suporte se persistir

### O que o script faz

1. Lê `HEVY_API_KEY` do `.env`
2. Testa cada endpoint GET principais:
   - `/v1/exercise_templates`
   - `/v1/routine_folders`
   - `/v1/routines`
   - `/v1/user` (validação de auth)
3. Captura status HTTP, contagem de items, amostra de dados
4. Salva responses em JSON e TXT
5. Exibe resumo com sucessos e falhas

### Endpoints Testados

| Endpoint | Descrição | Essencial |
|----------|-----------|-----------|
| GET /v1/exercise_templates | Templates de exercícios | ✅ Sim |
| GET /v1/routine_folders | Pastas de rotinas | ✅ Sim |
| GET /v1/routines | Rotinas existentes | ✅ Sim |
| GET /v1/user | Dados do usuário | ⚠️ Validação |

### Segurança

✅ **API key:**
- Lida de variável de ambiente (nunca hardcoded)
- Mascarada em output (apenas últimos 4 caracteres mostrados)

✅ **Responses:**
- Não incluem dados sensíveis de usuário
- Sanitizadas antes de salvar em arquivo

✅ **Logs:**
- Sem exposição de chaves completas
- Erro messages genéricas quando apropriado

### Fase 0 — Checklist

- [ ] Script executa sem erro 401
- [ ] Todos os endpoints retornam 200 (ou 429 com backoff)
- [ ] Arquivos gerados em `docs/flows/`
- [ ] Schemas analisados e documentados
- [ ] ADR-003 atualizado com achados

Quando tudo OK → Prosseguir para Fase 1

### Referências

- [ADR-003: Contratos da API Hevy](../../docs/adr/ADR-003-hevy-api-contracts.md)
- [IMPLEMENTATION-GUIDE.md](../../IMPLEMENTATION-GUIDE.md)
- [Documentação oficial Hevy API](https://www.hevyapp.com/api/docs)
