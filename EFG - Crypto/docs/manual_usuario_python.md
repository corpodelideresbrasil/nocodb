# Manual do Usuário: Programa Python EFG - Crypto (MPRM V14.1)

Este programa é uma implementação em Python do modelo **Market Physics Regime Model (MPRM V14.1)**. Ele foi desenvolvido sob uma arquitetura amnésica (Markoviana), onde cada decisão é baseada exclusivamente no jogo de energias e forças do estado presente.

## 1. Estrutura e Operação

O sistema opera em dois modos distintos, selecionáveis ao iniciar:

*   **1. Rodada Oficial:** Deve ser executada uma vez ao dia (ex: pela manhã). Este modo é interativo e permite confirmar entradas e saídas, atualizando o saldo real e as posições no arquivo `portfolio.json`.
*   **2. Acompanhamento:** Modo de leitura para monitoramento intraday. Não altera dados e serve para consultar regimes e níveis de Stop Loss em tempo real.

## 2. Gestão de Posições (portfolio.json)

O arquivo `portfolio.json` é o "livro de ordens" do programa.
*   **Persistência:** Ele salva o saldo (iniciando em $200.00) e os detalhes de cada contrato aberto (Margem, Alavancagem, Lado).
*   **Sincronização:** Alertas de saída (Total ou Parcial) só são gerados para ativos que constam neste arquivo, evitando sinais irrelevantes.

## 3. Lógica de Sinais e Tomada de Decisão

### A. Critérios de Entrada (Gatilho ENTRAR)
Para garantir uma vantagem estatística sobre o ruído (que é de 25% em 4 estados), o sistema exige:
1.  **Vencer a Neutralidade:** A Força de Markov do regime dominante (Bull ou Bear) deve ser **>= 35%**.
2.  **Momento Físico (Expansion):** O estado dinâmico deve ser **EXPANSION**. Entrar em *Contraction* é evitado, pois o movimento ainda não tem velocidade.
3.  **Margem Disponível:** A nova posição deve caber no teto de **25% de margem total** da carteira ($50.00 de um capital de $200.00).
4.  **Validade:** Sinais com mais de 20 candles de idade (EXPIRED) são descartados por perda de inércia original.

### B. Critérios de Saída Total (Gatilho FECHAR)
O encerramento imediato da posição ocorre se:
1.  **Inversão de Regime:** O mercado muda para um estado desfavorável (ex: estava em BULL e foi para COMP, EXH ou BEAR).
2.  **Stop Loss Atingido:** O preço cruza o valor da `Inertial Trail` (coluna STOP LOSS da tabela).

### C. Lógica das Saídas Parciais (Reduções)
As reduções visam assegurar lucros e minimizar a exposição em momentos de exaustão ou perda de impulso, sem encerrar a tese principal:

*   **Redução de 50% (Linha Trail FLAT):**
    *   *Gatilho:* O Trailing Stop (`Inertial Trail`) permanece no mesmo valor por **3 candles consecutivos**.
    *   *Fundamento:* Indica que o preço não está mais renovando mínimas (em Long) ou máximas (em Short). O movimento perdeu impulso direcional.
*   **Redução de 30% (Preço Esticado):**
    *   *Gatilho:* A distância entre o preço atual e a linha de Stop Loss é **maior que 1.0 ATR**.
    *   *Fundamento:* O preço se afastou demais da sua base de inércia (sistema sobrecarregado). Realiza-se lucro parcial para proteção contra pullbacks violentos.

*Nota:* Diferente de versões anteriores, não há "tempo de carência". Se o modelo físico detectar perda de energia no candle seguinte à entrada, a redução será sugerida imediatamente para preservar o capital.

## 4. Mapeamento Físico (Termodinâmica)

*   **Velocidade (`body_work`):** Deslocamento líquido do preço.
*   **Energia Cinética (`f_bull`, `f_bear`):** Impulso direcional.
*   **Energia Potencial (`f_comp`):** Acúmulo/Compressão da mola (Range < ATR).
*   **Entropia / Atrito (`f_exh`):** Caos e pavios excessivos (Exaustão).
*   **Inércia (Markov EMA):** Resistência à mudança de estado.
*   **Vetor de Movimento (`Inertial Trail`):** O ponto de Stop Loss que segue a força dominante.

## 5. Gestão de Risco Estrita

*   **Margem por Ativo:** 2% do saldo nominal ($4.00 para capital de $200).
*   **Margem Total:** Máximo de 25% ($50.00) comprometidos simultaneamente.
*   **Alavancagem:** Sugerida entre **1x e 15x** (inteiros), calculada para maximizar o lucro com base na força de Markov.
*   **Alavancagem do Portfólio:** Monitorada para não exceder **5.0X** do capital total.

---
*EFG - Crypto Monitor | Física de Mercado Aplicada.*
