# Manual do Usuário: Programa Python EFG - Crypto (MPRM V14.1)

Este programa é uma implementação em Python do modelo **Market Physics Regime Model (MPRM V14.1)**, projetado para monitorar múltiplos ativos simultaneamente e identificar regimes de mercado baseados em física de preços e cadeias de Markov.

## 1. Estrutura do Programa

O programa automatiza os cálculos que anteriormente eram manuais ou limitados ao TradingView:

*   **Calculator (`core/calculator.py`):** Realiza toda a matemática pesada (Normalização ATR, Forças Bull/Bear, EMA de Markov).
*   **Engine (`core/engine.py`):** Gere as regras de negócio, sinais de ignição e o trailing stop dinâmico.
*   **Portfolio Manager (`core/portfolio.py`):** Controla as posições abertas e aplica as regras de risco (Saldo 200 USD, 2% margem, 5X alavancagem).
*   **Data Provider (`core/data_provider.py`):** Conecta-se a exchanges (padrão: Binance Futures) para coletar dados OHLCV em tempo real.

## 2. Gestão de Posições (portfolio.json)

O programa utiliza um arquivo chamado `portfolio.json` localizado na raiz da pasta do projeto para rastrear quais ativos você está operando.
*   **Criação:** O arquivo é criado automaticamente na primeira vez que uma posição é aberta.
*   **Uso:** Sinais de **saída parcial (50%/30%)** e **saída total** só serão exibidos para ativos que constam neste arquivo.
*   **Importante:** Você pode editar este arquivo manualmente se quiser adicionar posições que já possui.

## 3. Interpretação de Sinais em Python

Diferente do HUD visual do TradingView, o programa Python opera com gatilhos de dados:

### Gatilhos de Ignição (Ignition)
*   **⚡ LONG:** Gerado quando o regime transiciona para Bull (0) e não há posição aberta.
*   **🔥 SHORT:** Gerado quando o regime transiciona para Bear (1) e não há posição aberta.

### Critérios de Entrada (Gatilho ENTRAR)
Para um ativo receber a recomendação `ENTRAR`, ele deve satisfazer:
1.  **Regime:** Deve estar em Regime 0 (BULL) ou 1 (BEAR).
2.  **Idade (N-Candles):** O sinal deve ter idade entre 0 e 20 candles (FRESH ou ALERT). Sinais EXPIRED são descartados.
3.  **Ranqueamento:** O ativo deve ter força de Markov suficiente para estar entre os top-ranked.
4.  **Limite de Margem:** Deve haver espaço no orçamento de 20% da margem total da carteira ($40.00 para um saldo de $200.00). Caso o limite seja atingido, ativos com sinais válidos mas menor prioridade serão marcados como `LIMITE OFF`.

## 4. Gestão de Risco Automatizada

O módulo `Engine` inclui a verificação de viabilidade operacional:
*   **Custo Transacional:** O programa calcula se `Spread + Slippage` excede **20% do ATR**. Caso exceda, o sinal é marcado como "Inviável" no console.

## 4. Como Executar

1.  Certifique-se de ter as dependências instaladas:
    ```bash
    python3 -m pip install -r requirements.txt
    ```
2.  Para monitorar os ativos, edite a lista no arquivo `main.py` e execute:
    ```bash
    python3 main.py
    ```

## 5. Saídas Parciais e Trailing Stop

O programa monitora o `trail_stop_val` a cada novo candle:
*   **Afastamento Excessivo:** Se o preço atual se distanciar > 1 ATR da linha de trail, o sistema emitirá um alerta de **Realização Parcial (30%)**.
*   **Linha Flat:** O sistema detecta se a linha de Trail não mudou de valor por 3 candles, sugerindo **Realização Parcial (50%)**.

---
*MPRM V14.1 Python Edition - Focado na Termodinâmica do Presente.*
