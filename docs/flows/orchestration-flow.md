# Fluxo de Orquestração - MFIT → Hevy

## Fluxo Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Receber arquivo PDF/Imagem                                  │
│     - Calcular SHA-256                                           │
│     - Verificar duplicidade por hash                             │
│     - Perguntar ao usuário se deve reprocessar                   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Registrar importação                                         │
│     - Criar import_id (UUID)                                     │
│     - Salvar arquivo original                                    │
│     - Definir status: RECEIVED                                   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. MFIT Parser Agent                                           │
│     - Extrair fichas, exercícios, séries, reps, carga, intervalo│
│     - Preservar texto original e localização no documento        │
│     - Status: PARSED                                             │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Workout Normalizer Agent                                    │
│     - Padronizar unidades                                        │
│     - Converter números inequivocamente                          │
│     - Representar técnicas (dropset, rest-pause, 8x8)            │
│     - Status: NORMALIZED                                         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Project Memory Agent                                        │
│     - Consultar mapeamentos confirmados anteriormente            │
│     - Consultar IDs de pastas/rotinas já criadas                 │
│     - Consultar decisões e preferências do usuário               │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. Hevy Catalog Agent                                          │
│     - Consultar templates de exercícios disponíveis              │
│     - Consultar pastas do usuário                                │
│     - Respeitar paginação e limites                              │
│     - Armazenar cache com timestamp                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. Exercise Mapping Agent                                      │
│     - Ordem: memória > exato > alias > fuzzy > manual            │
│     - Nunca confirmar automaticamente se < limiar                │
│     - Status: MAPPED (com confidência)                           │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. Payload Builder Agent (dry-run)                             │
│     - Construir JSON exato para API Hevy                         │
│     - Validar tipos, IDs, séries, reps, pesos                   │
│     - Verificar folder, nome da rotina                           │
│     - Marcar riscos potenciais                                   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  9. Review Agent                                                │
│     - Mostrar arquivo, treinos encontrados                       │
│     - Listar exercícios com mapeamentos                          │
│     - Destacar campos ausentes/alterados                         │
│     - Mostrar operações que serão executadas                     │
│     - Pedir correções e confirmação explícita                    │
│     - Status: AWAITING_REVIEW                                    │
└──────────────────┬──────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   [Rejeitar]          [Aprovar]
   (voltar ou            │
    cancelar)            ▼
        │        ┌─────────────────────────────────────────────────────────────┐
        │        │  10. Revalidar e gerar plano idempotente                   │
        │        │      - Validar que hash = aprovado                          │
        │        │      - Confirmar endpoint, IDs e payload                    │
        │        │      - Gerar idempotency keys                              │
        │        │      - Status: APPROVED                                     │
        │        └────────────────┬────────────────────────────────────────────┘
        │                         │
        │                         ▼
        │        ┌─────────────────────────────────────────────────────────────┐
        │        │  11. Hevy Write Agent                                       │
        │        │      - Validar novo plano contra aprovação                   │
        │        │      - Executar operações na sequência                      │
        │        │      - Usar idempotency key                                 │
        │        │      - Tratar 429, 5xx com backoff/retry                    │
        │        │      - Registrar response sanitizada                        │
        │        │      - Status: WRITING                                      │
        │        └────────────────┬────────────────────────────────────────────┘
        │                         │
        │                         ▼
        │        ┌─────────────────────────────────────────────────────────────┐
        │        │  12. QA Agent                                               │
        │        │      - Validar estrutura de resposta                        │
        │        │      - Conferir contagens e ordem                           │
        │        │      - Validar IDs remotos                                  │
        │        │      - Verificar idempotência                               │
        │        │      - Status: COMPLETED / FAILED                           │
        │        └────────────────┬────────────────────────────────────────────┘
        │                         │
        │                         ▼
        │        ┌─────────────────────────────────────────────────────────────┐
        │        │  13. Persistir resultado                                    │
        │        │      - Gravar IDs remotos                                   │
        │        │      - Gravar decisões em memória                           │
        │        │      - Gravar eventos de auditoria                          │
        └────────┤      - Notificar sucesso                                    │
                 └─────────────────────────────────────────────────────────────┘

```

## Detalhamento do Matching (Exercise Mapping)

```
Para cada exercício MFIT:

1. [Memória confirmada?]
   ├─ SIM: Usar mapeamento confirmado
   └─ NÃO: continuar

2. [Correspondência exata normalizada?]
   ├─ SIM: Usar com alta confiança
   └─ NÃO: continuar

3. [Alias confirmado?]
   ├─ SIM: Usar alias
   └─ NÃO: continuar

4. [Equivalência textual/fuzzy?]
   ├─ SIM + confiança >= 0.92: Sugerir candidato
   ├─ 0.75-0.919: Marcar como "precisa revisão"
   └─ < 0.75: Nenhuma sugestão automática

5. [Equipamento e padrão de movimento?]
   ├─ Match claro: Sugerir
   └─ Ambíguo: Marcar revisão

6. [Manual?]
   └─ Encaminhar para usuário revisar e confirmar
```

## Estados e Transições

```
RECEIVED
   │
   ├─ erro ──────────────┐
   │                     │
   ▼                     │
PARSED                  │
   │                     │
   ├─ erro ──────────────┤
   │                     │
   ▼                     │
NORMALIZED              │
   │                     │
   ├─ erro ──────────────┤
   │                     │
   ▼                     │
MAPPED                  │
   │                     │
   ├─ erro ──────────────┤
   │                     │
   ▼                     │
AWAITING_REVIEW         │
   │                     │
   ├─ REJECTED ─────────┘
   │ (volta para RECEIVED)
   │
   ├─ APPROVED           │
   │     │               │
   │     ├─ erro ───────┤
   │     │               │
   │     ▼               │
   │  WRITING            │
   │     │               │
   │     ├─ erro ───────┤
   │     │               │
   │     ▼               │
   │  COMPLETED          │
   │                     │
   └─────────────────────▼
        FAILED

```

## Idempotência

Cada operação tem uma `idempotency_key` gerada como:
```
hash(import_id + operation_type + exercise_index + timestamp_de_aprovacao)
```

Antes de executar, o Hevy Write Agent verifica:
1. Existe uma operação com mesma key no histórico?
2. Qual foi o resultado anterior?
3. Se sucesso: não repetir, usar resultado anterior
4. Se erro: pode tentar novamente
5. Se desconhecido: consultar estado remoto antes de decidir
