# Manual do Usuário: Programa Python EFG - Crypto (MPRM V14.1)

Este programa é uma implementação em Python do modelo **Market Physics Regime Model (MPRM V14.1)**. Ele foi desenvolvido sob uma arquitetura amnésica (Markoviana), onde cada decisão é baseada exclusivamente no jogo de energias e forças do estado presente.

## 1. Lógica de Sinais: A Engenharia por Trás do Modelo

O MPRM trata o mercado como um sistema termodinâmico. Não operamos "preço", operamos **Energia**.

### A. O Critério de 35% (Relação Sinal-Ruído - SNR)
*   **O Racional Matemático:** Em um sistema com 4 estados possíveis (Bull, Bear, Comp, Exh), a probabilidade de "ruído puro" (aleatoriedade) para qualquer estado é de **25%**.
*   **O Gatilho Físico:** Para que um movimento seja considerado uma "Ignition" (Ignição), a energia direcional deve superar o ruído. Adotamos **35%** porque isso representa um **excesso de 40% de energia** sobre a base neutra (25% + 10%).
*   **Vantagem Financeira:** No tempo gráfico de 1D, esperar a força atingir 40% ou 45% frequentemente resulta em "comprar o topo do primeiro impulso". Os 35% capturam a **aceleração inicial** (o momento em que a força rompe a inércia do repouso), maximizando o lucro esperado.

### B. Redução de 30% (Afastamento > 1 ATR — "Limite Elástico")
*   **Por que 30%?** Com uma alavancagem média de 10x, um afastamento de 1 ATR do Stop Loss gera um lucro latente onde a realização de **30% da posição** cobre o risco total do capital inicialmente empenhado na operação. É o "Break-even Matemático".
*   **A Física:** Imagine o preço ligado ao stop por um elástico. Acima de 1 ATR, o sistema atingiu seu **Limite Elástico**. A energia potencial de reversão (contratendência) supera a energia cinética atual. Realizamos 30% para converter o "calor" do mercado em saldo, mantendo 70% para seguir a inércia se o elástico não romper.

### C. Redução de 50% (Stop FLAT por 3 barras — "Atrito Estático")
*   **Por que 50%?** Quando o Trailing Stop para de subir/descer (Velocidade = 0), a probabilidade de o próximo candle ser de continuidade ou reversão torna-se **Simétrica (50/50)**. Pela lógica de Markov, se o edge é nulo, a exposição deve ser reduzida à metade.
*   **A Física (O Racional das 3 Barras):** No domínio discreto do tempo, 1 ponto é posição, 2 pontos são uma direção. A **3ª barra** é o requisito mínimo para provar que o sistema não está apenas em um "ciclo de respiro", mas sim sofrendo **Atrito Estático** (resistência que anulou o momento). É a prova física de que a inércia direcional foi dissipada.

---

## 2. Mapeamento das Transições de Estado

| Transição | Significado Físico | Equivalente no Mercado | Ação Sugerida |
| :--- | :--- | :--- | :--- |
| **COMP -> BULL/BEAR** | Conversão de E. Potencial em Cinética. | **Ignition.** Rompimento com volume de corpo. | **ENTRAR** |
| **BULL/BEAR -> COMP** | Desaceleração / Aumento de Atrito. | **Acúmulo ou Distribuição.** O preço parou de andar. | **REDUZIR 50%** |
| **BULL/BEAR -> EXH** | Aumento crítico de Entropia (Caos). | **Exaustão de Tendência.** Pavios longos e briga. | **FECHAR** |
| **EXH -> COMP** | Equilíbrio Térmico. | O mercado cansou de brigar e entrou em repouso lateral. | **AGUARDAR** |
| **BULL <-> BEAR** | Inversão de Vetor de Força. | Mudança total de mão. A tese original morreu. | **FECHAR** |

---

## 3. Estrutura e Operação do Programa

### Modos de Uso:
*   **1. Rodada Oficial:** Execute uma vez ao dia. O programa perguntará o resultado (Lucro/Prejuízo) de cada saída e atualizará seu saldo de **$200.00** no `portfolio.json`.
*   **2. Acompanhamento:** Use para monitorar o **REGIME** e o **STOP LOSS** (Inertial Trail) em tempo real sem alterar dados.

### Gestão de Posições (portfolio.json):
*   **Trava de Margem:** O sistema limita o uso total a **25% ($50.00)**.
*   **Alavancagem:** Sugerida entre **1x e 15x** (inteiros), baseada no produto da força pela volatilidade para maximizar o retorno.

---
*EFG - Crypto Monitor | Engenharia de Sistemas Financeiros.*
