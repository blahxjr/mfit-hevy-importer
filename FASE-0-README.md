# 🚀 Fase 0 — Validação de Contratos

**Status:** ⏳ Pronto para execução  
**Início Recomendado:** Imediatamente após estrutura inicial  
**Duração Estimada:** 1-2 horas  

---

## O Que É Fase 0?

Fase 0 valida os contratos e a disponibilidade da API Hevy ANTES de implementar qualquer parsing ou mapeamento. Sem essa validação, investir em implementação pode ser inútil.

## Por Que Fase 0?

- 🎯 Confirma que API key funciona
- 🎯 Captura schemas reais vs. esperados
- 🎯 Identifica rate limits e limitações
- 🎯 Prepara base para testes em Fase 1
- 🎯 Documenta decisões arquiteturais

## Instruções Imediatas

### 1️⃣ Confirmar Hevy Pro

Acessar https://www.hevyapp.com/account e verificar que tem:
- ✅ Assinatura **Hevy Pro** ativa
- ✅ Sem suspensão ou débito pendente

### 2️⃣ Obter API Key

1. Ir para https://www.hevyapp.com/settings?developer
2. Copiar a API key
3. **Manter segura** (não expor em git/logs)

### 3️⃣ Configurar .env

```bash
cd backend

# Copiar template
cp ../.env.example .env

# Abrir .env e preencher HEVY_API_KEY com a chave obtida
# Salvar sem commitar
```

### 4️⃣ Executar Prova

```bash
# Ativar venv
source venv/bin/activate  # Linux/Mac: venv\Scripts\activate # Windows

# Instalar dependências (se não feito)
pip install -r requirements-dev.txt

# Rodar prova da API
python scripts/prova_hevy_api.py
```

**Esperado:**
- ✅ 4 testes (templates, folders, routines, user)
- ✅ Todos com status 200
- ✅ Arquivos salvos em `docs/flows/hevy-api-prova-01.json` e `.txt`

**Se der erro:**
- 401 → Verificar API key e Hevy Pro
- 429 → Rate limit (documentar e prosseguir)
- 5xx → Problema servidor Hevy (tentar depois)

### 5️⃣ Analisar Resultados

```bash
# Ver resumo
cat docs/flows/hevy-api-prova-01.txt

# Ver dados completos
cat docs/flows/hevy-api-prova-01.json | less
```

### 6️⃣ Atualizar Documentação

- [ ] `docs/schemas/hevy-api-real.json` com respostas reais
- [ ] `backend/tests/fixtures/hevy_api_mocks.py` com exemplos
- [ ] `docs/adr/ADR-003-hevy-api-contracts.md` com achados

### 7️⃣ Adicionar PDF MFIT

- Copiar um PDF real do MFIT para `backend/tests/fixtures/mfit_sample_01.pdf`
- Documentar conteúdo esperado em `backend/tests/fixtures/README.md`

---

## Arquivos Relacionados

| Arquivo | Descrição |
|---------|-----------|
| `backend/scripts/prova_hevy_api.py` | Script principal da Fase 0 |
| `backend/scripts/README.md` | Documentação do script |
| `backend/tests/fixtures/hevy_api_mocks.py` | Mocks para testes |
| `docs/adr/ADR-003-hevy-api-contracts.md` | Decisão sobre contratos |
| `docs/flows/hevy-api-prova-01.*` | Resultados (JSON + TXT) |

---

## Checklist de Conclusão

Fase 0 concluída quando:

- [ ] `python scripts/prova_hevy_api.py` executa sem erro 401
- [ ] Todos os 4 testes retornam status 200
- [ ] Arquivos salvos em `docs/flows/`
- [ ] `docs/schemas/hevy-api-real.json` criado
- [ ] `docs/adr/ADR-003-hevy-api-contracts.md` completo
- [ ] `backend/tests/fixtures/mfit_sample_01.pdf` copiado
- [ ] Documentação atualizada com resultados

**Quando tudo ✅ → Pronto para Fase 1**

---

## Próxima Fase

Com Fase 0 concluída:
1. Iniciar implementação de Database Layer (SQLAlchemy)
2. Implementar MFIT Parser Agent
3. Implementar demais agentes em paralelo

Ver [IMPLEMENTATION-GUIDE.md](IMPLEMENTATION-GUIDE.md) para detalhes de Fase 1.

---

## Referências

- [IMPLEMENTATION-GUIDE.md](IMPLEMENTATION-GUIDE.md) — Roteiro completo
- [ORQUESTRAÇAO_PRÓXIMO_PASSO.md](ORQUESTRAÇAO_PRÓXIMO_PASSO.md) — Orquestração
- [Documentação oficial Hevy API](https://www.hevyapp.com/api/docs)
- [ADR-003: Contratos Hevy API](docs/adr/ADR-003-hevy-api-contracts.md)

---

**🔔 Lembrete:** Fase 0 é bloqueante. Não prosseguir para Fase 1 sem todos os itens ✅
