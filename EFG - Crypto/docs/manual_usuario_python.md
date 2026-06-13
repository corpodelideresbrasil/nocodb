# Manual do Usuário: Programa Python EFG - Crypto (MPRM V14.1)

Este programa é uma implementação em Python do modelo **Market Physics Regime Model (MPRM V14.1)**. Ele foi desenvolvido sob uma arquitetura amnésica (Markoviana), onde cada decisão é baseada exclusivamente no jogo de energias e forças do estado presente.

## 1. Estrutura e Operação

O sistema opera em dois modos distintos:
*   **1. Rodada Oficial:** Executada uma vez ao dia para atualizar o saldo real e as posições no arquivo `portfolio.json`.
*   **2. Acompanhamento:** Modo de leitura para consulta de regimes e níveis de Stop Loss (Inertial Trail) em tempo real.

## 2. Lógica de Sinais: A Física por Trás do Modelo

O MPRM não olha para o "gráfico", ele olha para a **termodinâmica do preço**.

### A. Critérios de Entrada (Gatilho ENTRAR)
Para garantir uma vantagem estatística sobre o ruído, o sistema utiliza o conceito de **Relação Sinal-Ruído (SNR)**:
1.  **Vencer a Neutralidade (>= 35%):** Em um sistema de 4 estados (Bull, Bear, Comp, Exh), a chance aleatória de cada um é 25%. Uma força de 35% representa um aumento de **40% sobre a base neutra**, confirmando que a energia direcional superou o ruído estatístico. O ajuste de 40% para 35% visa capturar o **início da aceleração** (Ignition), evitando entrar quando o movimento já está em velocidade terminal.
2.  **Momento Físico (Expansion):** O estado deve ser **EXPANSION**. Entrar em *Contraction* seria antecipar um movimento sem velocidade de corpo.
3.  **Amnésia:** A decisão é baseada na transição de estado *agora*.

### B. Saídas Parciais (Reduções de Risco)

*   **Redução de 30% (Afastamento > 1 ATR - "Limite Elástico"):**
    *   **Física:** O preço se afastou demais do seu centro de massa de inércia (`Inertial Trail`). Como uma mola esticada ao limite, a **Energia Potencial de Reversão** é máxima. O sistema está "sobrecarregado".
    *   **Financeiro:** Realiza-se lucro na euforia (esticada) para proteger a conta contra o retorno inevitável à média (Pullback). Mantém-se 70% para capturar a continuidade da inércia.
*   **Redução de 50% (Linha Trail FLAT por 3 barras - "Atrito Estático"):**
    *   **Física:** A `Inertial Trail` para de se mover se o preço não renova mínimas (Long) ou máximas (Short). Se isso persiste por 3 barras, a **Velocidade** do stop zerou. Três barras é o período mínimo para confirmar que o sistema não está apenas "respirando", mas sim sofrendo **Atrito** (resistência/oferta) que anulou seu momento.
    *   **Financeiro:** Eficiência de capital. Se a tendência parou de andar, sua margem está "presa" em um ativo sem momentum. Reduz-se 50% para liberar margem para novos ativos que acabaram de dar "Ignition".

### C. Saída Total (Gatilho FECHAR)
*   **Entropia (Exhaustion):** Se o regime mudar para **EXHAUSTION**, o sistema entrou em caos (pavios longos e indecisão). A tese física de ordem foi destruída pela entropia.
*   **Vetor Oposto (Stop Loss):** O preço cruzou a linha de inércia. A força contrária venceu a resistência do movimento.

## 3. Mapeamento das Transições de Estado

| Transição | Significado Físico | Equivalente Financeiro |
| :--- | :--- | :--- |
| **COMP -> BULL/BEAR** | Conversão de Energia Potencial em Cinética. | **Ignition (Entrada).** O rompimento com volume de corpo. |
| **BULL/BEAR -> COMP** | Perda de Momentum / Desaceleração. | **Acúmulo/Distribuição.** Hora de reduzir (50%) por perda de tração. |
| **BULL/BEAR -> EXH** | Aumento de Entropia (Caos). | **Exaustão de Tendência.** Saída total por alto risco de reversão. |
| **EXH -> COMP** | Resfriamento do Sistema. | O mercado parou de "brigar" e entrou em zona de equilíbrio. |

## 4. Gestão de Posições (portfolio.json)
O arquivo `portfolio.json` rastreia o saldo inicial de **$200.00** e aplica:
*   **Margem/Ativo:** 2% ($4.00).
*   **Teto de Margem:** 25% ($50.00).
*   **Alavancagem:** Inteira (1-15x) para maximizar o lucro esperado (produto da Força Markov pela Volatilidade).

---
*EFG - Crypto Monitor | Engenharia de Sistemas Financeiros.*
