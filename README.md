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

## Licença

MIT
