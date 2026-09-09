# ADR-004: Canonicalização com IA Externa

## Status

Accepted

## Contexto

Os nomes de exercícios extraídos do MFIT estão principalmente em português, enquanto o catálogo do Hevy usa predominantemente nomes em inglês. O matching baseado apenas em similaridade textual pode, portanto, produzir baixa confiança, falsos positivos ou ausência de correspondência.

O MVP precisa melhorar os termos de busca sem introduzir uma integração automática com provedores de IA, sem exigir uma chave adicional e sem permitir que uma sugestão externa escreva dados no Hevy.

## Decisão

Adotar, no MVP, um fluxo manual assistido e sem integração de API:

```text
PDF MFIT
→ parser/normalização local
→ exportar prompt + contexto JSON
→ usuário utiliza IA externa manualmente
→ IA devolve JSON
→ sistema importa/valida localmente
→ matching melhorado
→ revisão humana
→ escrita somente em fase posterior e controlada
```

A Etapa 1 define somente a documentação e os contratos JSON. O contexto exportado não contém IDs do Hevy, credenciais, dados de autenticação ou instruções de escrita. A resposta externa contém apenas sugestões de nomes, aliases, padrões e dicas de equipamento/músculo, sempre sujeitas à validação local e à revisão humana.

## Alternativas consideradas

- **Integração direta com API de IA:** rejeitada no MVP para evitar dependência de provedor, custo, chave adicional e envio automático de dados.
- **Apenas RapidFuzz:** rejeitada como solução única porque similaridade textual não resolve suficientemente diferenças de idioma e variações técnicas.
- **Criação automática de exercícios customizados:** rejeitada por aumentar o risco de duplicidade, erro semântico e escrita indevida.
- **Scraping de nomes ou imagens do Hevy:** rejeitado por riscos operacionais, legais, de estabilidade e de privacidade.

## Consequências positivas

- Não exige chave API de IA.
- Permite comparar diferentes IAs.
- Reduz custo e lock-in.
- Preserva o controle do usuário.
- Mantém auditoria do contexto, do prompt e da resposta validada.
- Mantém a IA externa fora do caminho de escrita do Hevy.

## Riscos

- JSON inválido.
- Alucinação de nomes ou atributos.
- IA alterar dados proibidos.
- Inconsistência de nomes entre diferentes provedores.
- Exposição acidental de dados no prompt.

## Mitigações

- JSON Schema Draft 2020-12 estrito para contexto e resposta.
- Validação local antes de qualquer uso da resposta.
- Ausência de IDs do Hevy no contexto.
- Nenhum mapeamento confirmado automaticamente.
- Revisão humana obrigatória.
- `needs_review` permanece verdadeiro por padrão.
- Nenhuma escrita no Hevy nessa funcionalidade.

## Segurança

- Nenhuma API key no export.
- Nenhum endpoint `/write` é chamado.
- Nenhum POST, PUT, PATCH ou DELETE é enviado à API Hevy por esta funcionalidade.
- Nenhum template ID é aceito na resposta da IA.
- Nenhum dado original do MFIT pode ser alterado.
- Séries, repetições, cargas, percentuais, descansos, observações, técnicas e `group_id` permanecem fora da transformação de canonicalização.
- O usuário deve revisar o contexto antes de colá-lo em uma IA externa.
