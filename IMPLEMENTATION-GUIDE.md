# Guia de Implementação - MFIT → Hevy

## Estrutura Criada

✅ Diretórios base organizados por arquitetura hexagonal  
✅ Configuração Python com Pydantic v2, FastAPI, SQLAlchemy  
✅ Docker Compose para desenvolvimento  
✅ Schemas Pydantic iniciais com estado orquestrado  
✅ Endpoint FastAPI básico  
✅ ADRs documentando decisões arquiteturais  
✅ Schemas JSON para API Hevy e MFIT  
✅ Fluxo de orquestração documentado  
✅ Alembic para migrations  
✅ Testes (conftest.py)  

## Próximos Passos - Fase 0 (CRÍTICA)

⚠️ **Fase 0 DEVE ser completada antes de Fase 1**. Sem validação de API, implementação de parsing/mapping será inútil.

### 1. Setup inicial (30 min)

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements-dev.txt
```

**Validar:**
```bash
python --version        # deve ser 3.12+
python -c "import fastapi; print(fastapi.__version__)"
python -c "import pydantic; print(pydantic.__version__)"
```

### 2. Configurar Hevy Pro e API Key (OBRIGATÓRIO)

**Pré-requisitos:**
- Ter assinatura **Hevy Pro** (API só disponível para Pro)
- Acessar https://www.hevyapp.com/settings?developer

**Como fazer:**

```bash
# 1. Copiar template de .env
cd backend
cp ../.env.example .env

# 2. Editar .env com sua API key (usar editor ou comando abaixo)
# No Windows PowerShell:
(Get-Content .env) -replace 'HEVY_API_KEY=.*', 'HEVY_API_KEY=sua_chave_aqui' | Set-Content .env

# 3. Verificar que .env não vai ser commitado
grep ".env" ../.gitignore  # Deve estar em .gitignore
```

**Validar `.env`:**
```bash
cat .env | grep HEVY_API
# Esperado: HEVY_API_KEY=sua_chave_aqui (não vazio)
```

### 3. Executar Prova da API Hevy (CRÍTICA)

**Script:** `backend/scripts/prova_hevy_api.py`  
**Objetivo:** Validar contratos e capturar schemas reais

```bash
cd backend
python scripts/prova_hevy_api.py
```

**Esperado na saída:**
```
PROVA DE CONCEITO — API HEVY
========================================================================

🔍 Testando: GET /v1/exercise_templates
   Status: 200 ✅
   Items: 147

🔍 Testando: GET /v1/routine_folders
   Status: 200 ✅
   Items: 3

🔍 Testando: GET /v1/routines
   Status: 200 ✅
   Items: 5

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

**Se der erro 401 (Não autenticado):**
- Verificar API key no `.env`
- Confirmar que tem Hevy Pro

**Se der erro 429 (Rate limit):**
- Documentar o limite observado
- Implementar backoff em Fase 1

**Arquivos gerados:**
- `docs/flows/hevy-api-prova-01.json` — responses brutas
- `docs/flows/hevy-api-prova-01.txt` — resumo legível

### 4. Ajustar Schemas com Dados Reais

**Arquivo:** `docs/schemas/hevy-api-real.json`

Após rodar prova_hevy_api.py:

```bash
# Copiar o JSON gerado para schemas
cp docs/flows/hevy-api-prova-01.json docs/schemas/hevy-api-real.json

# Comparar com schemas esperados
diff docs/schemas/hevy-api-schemas.json docs/schemas/hevy-api-real.json

# Anotar discrepâncias em ADR-003
```

### 5. Criar arquivo MFIT de referência

**O que fazer:**
- Selecionar ou exportar uma ficha real do MFIT
- Salvar em `backend/tests/fixtures/mfit_sample_01.pdf`
- Documentar conteúdo em `backend/tests/fixtures/README.md`

**Por que:**
Precisamos de um exemplo concreto para validar parser e testes em Fase 1.

**Output esperado:**
- `backend/tests/fixtures/mfit_sample_01.pdf` (arquivo binário)
- Documentação dos exercícios esperados na ficha

## Próximos Passos - Fase 1 (MVP)

### 4. Database Layer (1-2 dias)

**O que implementar:**
- Entidades SQLAlchemy em `backend/src/infrastructure/models.py`:
  - `Project`, `Import`, `SourceWorkout`, `SourceExercise`
  - `HevyExerciseTemplate`, `HevyFolder`, `ExerciseMapping`
  - `Decision`, `AuditEvent`, `ImportState`

- Migrations Alembic em `backend/alembic/versions/`
  - 001_create_initial_schema.py

- Repositórios em `backend/src/repositories/`:
  - `import_repository.py`
  - `mapping_repository.py`
  - `hevy_catalog_repository.py`

### 5. MFIT Parser Agent (2-3 dias)

**O que implementar:**
- `backend/src/parsers/mfit_parser.py`
  - Usar PyMuPDF ou pdfplumber
  - Extrair fichas, exercícios, séries, reps, carga
  - Preservar texto original e localização
  - Retornar JSON validado contra schema

- `backend/tests/unit/test_mfit_parser.py`
  - Testar com `data/sample_mfit.pdf`
  - Validar todos os campos

### 6. Normalizer Agent (1-2 dias)

**O que implementar:**
- `backend/src/application/normalizer.py`
  - Converter unidades (kg, lb)
  - Padronizar reps (range, fixed, time)
  - Técnicas (dropset, rest-pause, 8x8, superséries)
  - Preservar `raw_value` em tudo

- `backend/tests/unit/test_normalizer.py`

### 7. Hevy Catalog Agent (1 dia)

**O que implementar:**
- `backend/src/hevy/hevy_client.py`
  - Classe `HevyClient` com método `get_templates()`, `get_folders()`, etc
  - Cache com TTL
  - Tratamento de erros HTTP
  - Sem expor API key em logs

- `backend/tests/unit/test_hevy_client.py`
  - Mock das respostas

### 8. Mapping Agent (1-2 dias)

**O que implementar:**
- `backend/src/application/exercise_mapper.py`
  - Ordem: memória > exato > alias > fuzzy > manual
  - RapidFuzz para similaridade
  - Limiares configuráveis

- `backend/tests/unit/test_exercise_mapper.py`

### 9. Payload Builder Agent (1 dia)

**O que implementar:**
- `backend/src/application/payload_builder.py`
  - Validar contra schema Hevy
  - Modo dry-run

### 10. Review Agent (1 dia)

**O que implementar:**
- `backend/src/application/review_generator.py`
  - Gerar HTML/JSON legível para usuário

### 11. Upload & UI Initial (1-2 dias)

**O que implementar:**
- `backend/src/api/imports.py`
  - POST `/imports/upload`
  - GET `/imports/{id}`
  - POST `/imports/{id}/approve`

- Frontend básico em React
  - Upload
  - Exibir estado
  - Formulário de revisão

### 12. Write Agent (1 dia)

**O que implementar:**
- `backend/src/hevy/hevy_writer.py`
  - Executa operações aprovadas
  - Idempotência
  - Retry com backoff

### 13. QA Agent (1 dia)

**O que implementar:**
- `backend/src/application/qa_validator.py`
  - Validações pós-escrita

## Estrutura de Testes

```
backend/tests/
├── conftest.py                    (fixtures globais)
├── unit/
│   ├── test_mfit_parser.py       (parser)
│   ├── test_normalizer.py        (normalizador)
│   ├── test_exercise_mapper.py   (mapeador)
│   ├── test_hevy_client.py       (cliente Hevy)
│   ├── test_payload_builder.py   (payload)
│   └── test_qa_validator.py      (QA)
└── integration/
    ├── test_full_flow.py         (fluxo completo com mock)
    └── test_hevy_api.py          (teste com API real - opcional)
```

## Comandos Úteis

```bash
# Desenvolvimento
uvicorn src.api.main:app --reload

# Testes
pytest                              # Todos
pytest backend/tests/unit/          # Apenas unit
pytest -v --cov=src --cov-report=html

# Migrations
alembic init alembic
alembic revision --autogenerate -m "Create initial schema"
alembic upgrade head
alembic downgrade -1

# Linting
black src/
isort src/
flake8 src/

# Docker
docker-compose up -d
docker-compose logs -f api
```

## Checklist de Aceite da Fase 0

A Fase 0 está completa quando TODOS os itens abaixo são ✅:

- [ ] **Hevy Pro confirmado**: Assinatura ativa em https://www.hevyapp.com/account
- [ ] **API key obtida**: Key copiada de https://www.hevyapp.com/settings?developer
- [ ] **`.env` preenchido**: `backend/.env` tem `HEVY_API_KEY` válida
- [ ] **Script de prova roda**: `python backend/scripts/prova_hevy_api.py` executa sem erro de autenticação
- [ ] **Endpoints GET validados**: Todos retornam 200 para templates, folders, routines
- [ ] **Arquivos salvos**: 
  - [ ] `docs/flows/hevy-api-prova-01.json`
  - [ ] `docs/flows/hevy-api-prova-01.txt`
- [ ] **Schemas atualizados**: 
  - [ ] `docs/schemas/hevy-api-real.json` com respostas reais
  - [ ] `backend/tests/fixtures/hevy_api_mocks.py` com exemplos
- [ ] **ADR-003 completo**: `docs/adr/ADR-003-hevy-api-contracts.md` documentado
- [ ] **PDF MFIT selecionado**: 
  - [ ] `backend/tests/fixtures/mfit_sample_01.pdf` copiado
  - [ ] Conteúdo documentado em `backend/tests/fixtures/README.md`
- [ ] **Documentação atualizada**: 
  - [ ] `IMPLEMENTATION-GUIDE.md` com results
  - [ ] `docs/flows/hevy-api-prova-01.txt` salvo e reviewado

**Status de Aceite:** ⏳ Aguardando execução de Fase 0

### Critérios de Sucesso

✅ **Sucesso:** Todos os endpoints GET retornam 200 com estrutura esperada  
⚠️ **Parcial:** Alguns endpoints retornam 429 (rate limit) — documentar e prosseguir  
❌ **Falha:** Erro 401 (auth), 403 (permissão) ou 5xx persistente — não prosseguir sem resolver

---

## Checklist de Aceite do MVP (Fase 1)

Com Fase 0 concluída, Fase 1 entrega o MVP com:

- [ ] Database layer completo (SQLAlchemy + migrations)
- [ ] MFIT Parser Agent funcional (extrai PDF)
- [ ] Workout Normalizer Agent (padroniza dados)
- [ ] Hevy Catalog Agent com cache
- [ ] Exercise Mapping Agent (exato + manual + fuzzy)
- [ ] Payload Builder Agent (valida contra schema)
- [ ] Review Agent (UI legível)
- [ ] Hevy Write Agent (dry-run + aprovação)
- [ ] QA Agent (validações pós-escrita)
- [ ] Tela de revisão interativa no frontend
- [ ] Uma rotina criada com sucesso no Hevy (end-to-end)
- [ ] Reprocessar mesmo arquivo não cria duplicata
- [ ] API key nunca aparece em logs/UI/commits
- [ ] Todos os testes passam com coverage >= 80%

## Referências

- [Documento principal](../MFIT_Hevy_Orquestrador_Prompts.md)
- [Fluxo de orquestração](flows/orchestration-flow.md)
- [ADRs](adr/)
- [Schemas](schemas/)

---

**Próximo passo recomendado:**  
Comece com **Fase 0, item 2**: Verificar a API Hevy e capturar schemas reais.
