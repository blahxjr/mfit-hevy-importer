# 📚 Navegação — Fase 0

**Bem-vindo à Fase 0 do projeto MFIT → Hevy!**

Esta é a fase crítica de validação antes de qualquer implementação. Todos os documentos abaixo têm um propósito específico.

---

## 🎯 Se você é novo no projeto

**Comece aqui:**

1. Leia [README.md](README.md) — Visão geral do projeto
2. Leia [FASE-0-README.md](FASE-0-README.md) — Guia visual de Fase 0 (⭐ COMECE AQUI)
3. Execute os 7 passos documentados em FASE-0-README.md
4. Quando terminar, volte para este arquivo

---

## 📖 Documentação por Tipo

### Para Começar (Visual e Direto)
- **[FASE-0-README.md](FASE-0-README.md)** — Guia visual com checklist
- **[FASE-0-SUMARIO-EXECUTIVO.md](FASE-0-SUMARIO-EXECUTIVO.md)** — Resumo de tudo que foi criado

### Para Entender a Infraestrutura
- **[backend/scripts/README.md](backend/scripts/README.md)** — Como usar o script prova_hevy_api.py
- **[backend/tests/fixtures/README.md](backend/tests/fixtures/README.md)** — Como funciona o sistema de mocks
- **[docs/adr/ADR-003-hevy-api-contracts.md](docs/adr/ADR-003-hevy-api-contracts.md)** — Decisão técnica sobre contratos

### Para Implementação Futura
- **[IMPLEMENTATION-GUIDE.md](IMPLEMENTATION-GUIDE.md)** — Roteiro de Fase 1, 2, 3, 4
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** — Estrutura de pastas e arquivos

### Documentação Original do Projeto
- **[MFIT_Hevy_Orquestrador_Prompts.md](MFIT_Hevy_Orquestrador_Prompts.md)** — Especificação completa dos 10 agentes
- **[ORQUESTRAÇAO_PRÓXIMO_PASSO.md](ORQUESTRAÇAO_PRÓXIMO_PASSO.md)** — Orquestração que levou a Fase 0

---

## 🔧 Arquivos Técnicos (Não Editar Manualmente)

Esses arquivos são criados pela Fase 0 e NÃO devem ser editados manualmente:

- `docs/flows/hevy-api-prova-01.json` — Resultado bruto da API (criado após rodar script)
- `docs/flows/hevy-api-prova-01.txt` — Resumo legível (criado após rodar script)
- `docs/schemas/hevy-api-real.json` — Será atualizado com schemas reais

---

## 📋 Checklist Rápido (7 Passos)

```bash
# Passo 1-2: Verificar Hevy Pro e obter API key
# → https://www.hevyapp.com/account
# → https://www.hevyapp.com/settings?developer

# Passo 3: Configurar .env
cd backend
cp ../.env.example .env
# → Editar .env e preencher HEVY_API_KEY

# Passo 4: Executar prova
python scripts/prova_hevy_api.py

# Passo 5: Analisar resultados
cat docs/flows/hevy-api-prova-01.txt

# Passo 6: Copiar schemas reais
cp docs/flows/hevy-api-prova-01.json ../docs/schemas/hevy-api-real.json

# Passo 7: Adicionar PDF MFIT
cp /seu/ficha_mfit.pdf tests/fixtures/mfit_sample_01.pdf
```

**Quando todos os 7 passos ✅ → Fase 0 concluída!**

---

## 💾 Memória Persistente Criada

A memória está organizada em 3 escopos (ver [Skills em VS Code](c:\Users\Junior\AppData\Local\Programs\Microsoft%20VS%20Code%20Insiders\5c91732763\resources\app\extensions\copilot\assets\prompts\skills)):

### /memories/repo/ (Persistente no Projeto)
- `projeto-structure.md` — Stack e arquitetura
- `fase-0-validation.md` — Status e objetivos de Fase 0
- `fase-0-decisions.md` — Decisões arquiteturais de Fase 0
- `fase-0-artifacts.md` — Inventário de arquivos criados

### /memories/session/ (Sessão Atual)
- `fase-0-execution-plan.md` — Plano detalhado de execução

---

## 🚀 O Que Acontece Depois

### Quando Fase 0 Terminar (✅ Todos os 7 passos)

Avise (sim, é importante!) e eu orquestro:

1. **Fase 1 — MVP** (2-3 semanas)
   - Database layer com SQLAlchemy
   - 10 agentes implementados
   - Tela de revisão interativa
   - End-to-end: PDF → Rotina no Hevy

2. **Fase 2 — Memória** (1-2 semanas)
   - Mapeamentos aprendidos
   - Histórico de importações

3. **Fases 3-4**
   - Técnicas avançadas, OCR, Docker, logs, métricas

Ver [IMPLEMENTATION-GUIDE.md](IMPLEMENTATION-GUIDE.md) para detalhes completos.

---

## ⚠️ Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| 401 — Auth Error | API key inválida/expirada | Renovar em https://www.hevyapp.com/settings?developer |
| 403 — Permission | Não tem Hevy Pro | Ativar Pro em https://www.hevyapp.com/account |
| 429 — Rate Limit | Muitas requisições | Aguardar 1-2 min e tentar novamente |
| ModuleNotFoundError | Falta `pip install` | `pip install -r requirements-dev.txt` |

---

## 🔐 Segurança

✅ Nunca commitar `.env` (está em `.gitignore`)  
✅ API key NUNCA em logs ou output  
✅ Script mascara a chave (mostra apenas `****...XXXX`)  
✅ Responses sanitizadas antes de salvar  

---

## 📞 Se Tiver Dúvidas

1. Verifique [FASE-0-README.md](FASE-0-README.md)
2. Verifique [backend/scripts/README.md](backend/scripts/README.md)
3. Verifique [docs/adr/ADR-003-hevy-api-contracts.md](docs/adr/ADR-003-hevy-api-contracts.md)
4. Verifique erros comuns acima

---

## 📂 Estrutura de Pasta Rápida

```
c:\dev\Treinoimport\
├── FASE-0-README.md                    ⭐ COMECE AQUI
├── FASE-0-SUMARIO-EXECUTIVO.md         (Resumo)
├── FASE-0-NAVEGACAO.md                 ⭐ ESSE ARQUIVO
├── IMPLEMENTATION-GUIDE.md             (Roadmap completo)
│
├── backend/
│   ├── .env.example                    (Template)
│   ├── .env                            (Criar e preencher)
│   ├── scripts/
│   │   └── prova_hevy_api.py           ⭐ Script principal
│   └── tests/fixtures/
│       └── hevy_api_mocks.py           (Mocks para testes)
│
├── docs/
│   ├── adr/
│   │   └── ADR-003-hevy-api-contracts.md  (Decisão)
│   ├── flows/
│   │   ├── hevy-api-prova-01.json      (Resultado da prova)
│   │   └── hevy-api-prova-01.txt       (Resultado legível)
│   └── schemas/
│       └── hevy-api-real.json          (Será criado)
```

---

## ✅ Resumo

| O Quê | Arquivo | Status |
|-------|---------|--------|
| Comece aqui | FASE-0-README.md | ⭐ Novo |
| Script de prova | backend/scripts/prova_hevy_api.py | ✅ Pronto |
| Mocks de API | backend/tests/fixtures/hevy_api_mocks.py | ✅ Pronto |
| Documentação | IMPLEMENTATION-GUIDE.md | ✅ Atualizado |
| Decisão técnica | docs/adr/ADR-003-hevy-api-contracts.md | ✅ Novo |
| Memória persistente | /memories/repo/fase-0-*.md | ✅ Novo |

---

**🎯 Próximo passo:** Abra [FASE-0-README.md](FASE-0-README.md) e siga os 7 passos.
