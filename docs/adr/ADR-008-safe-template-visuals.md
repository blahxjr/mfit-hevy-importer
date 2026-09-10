# ADR-008: Mídia visual local e segura para templates Hevy

## Status

Accepted

## Contexto

A revisão de mapeamentos MFIT → Hevy precisa mostrar uma prévia visual do template selecionado, mas o contrato Hevy validado não expõe uma imagem oficial do exercício. Isso torna qualquer tentativa de inventar URLs, de fazer scraping ou de assumir que a imagem do catálogo seja sempre disponível uma decisão de risco operacional e de integridade.

Além disso, a interface serve como camada de revisão e confirmação humana; ela não deve confirmar o template, alterar o catálogo Hevy ou introduzir qualquer comportamento de escrita em APIs externas.

## Decisão

Implementar uma camada local, auditable e segura para mídia visual de templates:

1. O sistema prioriza: imagem oficial do Hevy se estiver disponível no contrato; imagem local validada e carregada manualmente; fallback visual gerado localmente via ícone/etiqueta.
2. O sistema aceita apenas uploads locais de imagem em formatos seguros e com validações de MIME, tamanho e caminho.
3. O sistema mantém uma tabela `exercise_template_media` para registrar origem, arquivo local, URL opcional, texto alternativo, atribuição e verificação.
4. A interface de revisão usa essa estrutura para mostrar visual, sem transformar a revisão em uma ação de escrita no Hevy.
5. Quando não há imagem, o fallback usa uma representação semântica (ícone de movimento, tipo de equipamento e músculo), nunca uma imagem inventada.

## Regras de segurança

- Nenhuma chamada HTTP de scraping para imagens do Hevy.
- Nenhum endpoint de escrita do Hevy é usado para criar, atualizar ou anexar mídia.
- Nenhuma URL remota é inferida a partir de regras heurísticas sem validação explícita.
- Uploads são descartados se forem inválidos por tamanho, extensão, MIME ou path traversal.
- O arquivo local é servido somente pelo app local e nunca por um domínio externo.
- O texto alternativo e a atribuição são armazenados para auditoria e acessibilidade.

## Consequências

- A página de review permanece confiável e segura.
- O usuário pode revisar o template visualmente mesmo sem mídia oficial.
- A UI expressa claramente a origem da imagem, evitando a falsa impressão de que a imagem oficial foi confirmada.
- O sistema é auditável: a mídia local pode ser rastreada por template, data e origem.

## Alternativas rejeitadas

- Scraping de imagens do Hevy: rejeitado por risco de instabilidade, abuso e problemas de licença/privacidade.
- Inventar `image_url` com base em nomes de exercícios: rejeitado porque esconde a ausência real de dados e produz artefatos falsos.
- Copiar automaticamente mídia externa sem validação: rejeitado por risco de segurança e auditoria.
- Usar apenas texto sem fallback visual: rejeitado por piorar a experiência de revisão em templates com pouca semântica textual.

## Observação de arquitetura

Esta camada é auxiliar à revisão humana. Ela reforça a clareza, a acessibilidade e a confiança do fluxo de importação sem criar qualquer operação de escrita em sistemas externos.