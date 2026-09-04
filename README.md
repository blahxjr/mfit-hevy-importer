# MFIT → Hevy: Importador de Fichas de Treino

Sistema seguro para importar fichas de treino do MFIT e criar/atualizar rotinas no Hevy via API.

## Objetivo

Automatizar a transferência de planos de treino do MFIT para a plataforma Hevy, com:
- Extração confiável de PDFs
- Normalização e padronização de dados
- Mapeamento inteligente de exercícios
- Revisão e aprovação humana obrigatória
- Escrita segura e idempotente na API do Hevy
- Rastreabilidade completa e memória persistente

## Arquitetura

### Componentes

- **10 Agentes Especializados**: Orquestrador, Parser MFIT, Normalizador, Catálogo Hevy, Mapeador, Payload Builder, Revisão, Escrita, QA, Memória
- **Memória Persistente**: SQLite com histórico imutável
- **API Segura**: FastAPI com validação Pydantic
- **Interface**: React + TypeScript + Bootstrap

### Estrutura de Pasta

```
backend/
  src/
    agents/         # Implementação dos 10 agentes
    api/            # Endpoints FastAPI
    application/    # Casos de uso e orquestração
    domain/         # Modelos de negócio
    infrastructure/ # Config, DB, cache, HTTP
    parsers/        # Extração MFIT
    hevy/           # Cliente da API Hevy
    repositories/   # Acesso a dados (SQLAlchemy)
    schemas/        # Pydantic models
  tests/
    unit/           # Testes unitários
    integration/    # Testes de integração

frontend/
  src/
    components/     # Componentes React reutilizáveis
    pages/          # Páginas da aplicação
    services/       # Chamadas à API
    types/          # TypeScript interfaces

docs/
  adr/              # Architectural Decision Records
  schemas/          # Schemas de API e dados
  flows/            # Diagramas de fluxo
```

## Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic
- **Frontend**: React + TypeScript, Bootstrap
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Extração**: PyMuPDF, pdfplumber
- **Matching**: RapidFuzz
- **Containerização**: Docker Compose

## Roadmap

### Fase 0 — Contratos e Prova de API
- [ ] Confirmar conta Hevy Pro e API key
- [ ] Testar endpoints de leitura da API Hevy
- [ ] Definir schemas reais e contratos de agentes
- [ ] Escolher PDF MFIT de referência

### Fase 1 — MVP Seguro
- [ ] Upload e armazenamento de PDF
- [ ] Parser MFIT determinístico
- [ ] Normalização de dados
- [ ] Cache do catálogo Hevy
- [ ] Matching exato e manual
- [ ] Tela de revisão interativa
- [ ] Dry-run e criação de rotina no Hevy

### Fase 2 — Memória e Idempotência
- [ ] Mapeamentos aprendidos
- [ ] Histórico de importações
- [ ] Hash de arquivos e detecção de duplicidade
- [ ] IDs remotos e reexecução segura

### Fase 3 — Técnicas Avançadas
- [ ] Dropsets, superséries, tempos, observações
- [ ] OCR para imagens
- [ ] Matching semântico (com revisão obrigatória)

### Fase 4 — Operação
- [ ] Autenticação de usuários
- [ ] PostgreSQL
- [ ] Docker production-ready
- [ ] Logs estruturados e métricas
- [ ] Backup da memória

## Requisitos

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (opcional)

## Desenvolvimento

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest
uvicorn src.api.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

### Docker

```bash
docker-compose up -d
```

## Princípios

1. **Segurança**: API keys nunca em logs, commits ou interface
2. **Rastreabilidade**: Auditoria completa de cada decisão e operação
3. **Confiabilidade**: Nenhuma escrita sem aprovação do usuário
4. **Idempotência**: Operações repetíveis sem criar duplicatas
5. **Memória**: Aprendizagem entre importações, histórico imutável
6. **Especialização**: Cada agente tem responsabilidade clara e contrato bem definido

## Documentação

- [Orquestrador e Prompts](MFIT_Hevy_Orquestrador_Prompts.md)
- [ADRs](docs/adr/)
- [Schemas](docs/schemas/)
- [Fluxos](docs/flows/)

## Segredos

Para usar com a API do Hevy:

1. Obter API key em https://www.hevyapp.com/developer
2. Salvar em variável de ambiente:
   ```bash
   export HEVY_API_KEY="sua-chave-aqui"
   ```
3. Nunca commitar a chave ou expô-la em logs

## Primeira escrita controlada no Hevy

> **Segurança:** o projeto não cria ou atualiza nenhuma rotina até que o usuário confirme cada mapeamento e todos os valores ambíguos sejam resolvidos.

O fluxo de validação é deliberadamente dividido em etapas:

1. Sincronize o catálogo local com `python scripts/sync_catalog.py`.
2. Faça parsing, normalização e mapeamento do PDF.
3. Abra `/review/{importId}` e confirme manualmente cada exercício e suas alternativas.
4. Para cargas prescritas em percentual (por exemplo, `65-75%`), informe uma carga real em kg/lb antes de liberar a escrita.
5. Aprove o plano apenas quando a revisão não tiver pendências.
6. Gere e confira o dry-run com `python scripts/build_payload.py <import_id>`.
7. Execute **somente uma rotina revisada**, informando sua ordem e a confirmação explícita: `python scripts/execute_plan.py <import_id> <ordem_treino> --confirm-write`. A rotina A tem ordem `0`.
8. Consulte `POST /write/{import_id}/qa` e valide a rotina criada no Hevy.

O primeiro import local preparado nesta etapa tem ID `b92e4581-0860-4ee7-8ff4-2d88999d1d30`. Ele contém 36 exercícios e permanece com status `parsed`: há 36 mapeamentos a confirmar, 10 sem correspondência automática e cargas percentuais que exigem decisão humana. Portanto, **nenhuma escrita foi realizada**.

## Plano da Fase 2 — OCR de imagens

| Incremento | Objetivo | Critério de aceite |
|---|---|---|
| 2.1 — Upload de imagem | Aceitar JPEG, PNG e HEIC com limites de tamanho e checksum | Arquivo validado, armazenado temporariamente e auditável |
| 2.2 — Extração OCR | Adicionar adaptador para Tesseract local e opção de provedor externo | Texto por página/bloco, confiança por trecho e sem segredos em logs |
| 2.3 — Pré-processamento | Corrigir rotação, contraste, recorte e ruído | Melhoria mensurável em um conjunto de fichas de teste |
| 2.4 — Parser unificado | Reutilizar o `MFITParser` para texto de PDF e OCR | Mesmo contrato de `ParsedMfitPDF`, com origem e confiança preservadas |
| 2.5 — Revisão reforçada | Destacar campos originados por OCR e baixa confiança | Nenhum campo OCR ambíguo é escrito sem confirmação humana |
| 2.6 — Privacidade e operação | Definir retenção, exclusão e escolha de provedor | Imagens removidas após processamento ou guardadas apenas com consentimento |

O OCR será introduzido atrás de uma interface de adaptador para permitir testes com mocks e evitar acoplamento a um provedor. PDF com texto continuará usando PyMuPDF, pois é mais confiável e barato que OCR.

## Licença

MIT
