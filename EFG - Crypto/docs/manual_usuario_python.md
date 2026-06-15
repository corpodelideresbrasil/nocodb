# Manual do Usuário: Programa Python EFG - Crypto (MPRM V14.1 - Refinado)

Este programa é uma implementação em Python do modelo **Market Physics Regime Model (MPRM V14.1)**, agora refinado para incorporar as leis de Newton (**F = m.a**) no cálculo de energias. Ele foi desenvolvido sob uma arquitetura amnésica (Markoviana), onde cada decisão é baseada exclusivamente no jogo de energias e forças do estado presente.

## 1. Lógica de Sinais: A Engenharia por Trás do Modelo

O MPRM trata o mercado como um sistema mecânico e termodinâmico. Não operamos "preço", operamos **Trabalho e Força**.

### A. A Segunda Lei de Newton (F = m.a)
Para que uma tendência tenha assertividade, não basta o preço se mover. É preciso que haja **Massa** sustentando o movimento.
*   **Massa (m):** No nosso modelo, a massa é o **Volume Normalizado**. Um volume acima da média (m > 1) aumenta a inércia do movimento.
*   **Aceleração (a):** É o **Trabalho do Preço** (corpo do candle).
*   **Força (F):** A força resultante é o produto do Volume pelo Deslocamento. Movimentos com baixo volume são considerados "sem massa" e, portanto, incapazes de vencer o atrito do mercado.

### B. O Critério de 35% e o Piso de Ruído (Atrito Estático)
*   **O Racional Matemático:** Em um sistema com 4 estados possíveis (Bull, Bear, Comp, Exh), a probabilidade de "ruído puro" (aleatoriedade) para qualquer estado é de **25%**.
*   **O Gatilho Físico:** Para que um movimento seja considerado uma "Ignition" (Ignição), a energia direcional deve superar o ruído. Adotamos **35%** porque isso representa um **excesso de 40% de energia** sobre a base neutra (25% + 10%).
*   **Filtro de Atrito:** Além dos 35%, o sistema agora exige que a **Força (F)** seja superior ao **Piso de Ruído** (média das energias recentes). Isso filtra ativos que estão "andando de lado" ou sem volatilidade, garantindo que só entramos quando há energia real para romper a inércia.
*   **Vantagem Financeira:** No tempo gráfico de 1D, esperar a força atingir 40% ou 45% frequentemente resulta em "comprar o topo do primeiro impulso". Os 35% capturam a **aceleração inicial** (o momento em que a força rompe a inércia do repouso), maximizando o lucro esperado.

### B. Redução de 30% (Afastamento > 1 ATR — "Limite Elástico")
*   **Por que 30%?** Com uma alavancagem média de 10x, um afastamento de 1 ATR do Stop Loss gera um lucro latente onde a realização de **30% da posição** cobre o risco total do capital inicialmente empenhado na operação. É o "Break-even Matemático".
*   **A Física:** Imagine o preço ligado ao stop por um elástico. Acima de 1 ATR, o sistema atingiu seu **Limite Elástico**. A energia potencial de reversão (contratendência) supera a energia cinética atual. Realizamos 30% para converter o "calor" do mercado em saldo, mantendo 70% para seguir a inércia se o elástico não romper.

### D. Redução de 50% (Stop FLAT por 3 barras — "Atrito Cinético")
*   **Por que 50%?** Quando o Trailing Stop para de subir/descer (Velocidade = 0), a probabilidade de o próximo candle ser de continuidade ou reversão torna-se **Simétrica (50/50)**. Pela lógica de Markov, se o edge é nulo, a exposição deve ser reduzida à metade.
*   **A Física (O Racional das 3 Barras):** No domínio discreto do tempo, 1 ponto é posição, 2 pontos são uma direção. A **3ª barra** é o requisito mínimo para provar que o sistema não está apenas em um "ciclo de respiro", mas sim sofrendo **Atrito Cinético** (resistência que anulou o momento). É a prova física de que a inércia direcional foi dissipada.

---

## 2. O Núcleo Matemático: Como os Estados são Calculados

O modelo processa os dados em três estágios: Física Instantânea, Normalização de Markov e Identificação de Regime.

### A. Estágio 1: Física Instantânea (O "Agora")
Para cada candle, isolamos quatro vetores de força independentes:

1.  **BULL & BEAR (Força Cinética):**
    -   **Fórmula:** $F = m \cdot a$
    -   **Massa ($m$):** Volume Normalizado ($Volume / EMA(Volume)$). Representa a inércia financeira.
    -   **Aceleração ($a$):** Trabalho do preço ($|Fechamento - Abertura|$).
    -   *Se Fechamento > Abertura, a força é Bull. Se for menor, é Bear.*

2.  **COMP (Energia Potencial de Compressão):**
    -   **Lógica:** Mede a "energia da mola" acumulada em ranges estreitos com volume alto.
    -   **Fórmula:** $(ATR_{ref} - (Máxima - Mínima)) \cdot Massa$.
    -   Se o preço não se move, mas o volume (massa) é alto, a pressão de compressão aumenta drasticamente.

3.  **EXH (Entropia/Exaustão):**
    -   **Lógica:** Perda de energia por pavios (rejeição).
    -   **Fórmula:** Soma dos pavios superior e inferior.
    -   *Só é ativada se os pavios forem > 2x o tamanho do corpo do candle.*

### B. Estágio 2: Cadeia de Markov (A Inércia Probabilística)
Diferente de indicadores comuns, o MPRM não olha apenas o valor absoluto, mas a **proporção da energia total**:

1.  **Soma das Forças:** $Total = F_{bull} + F_{bear} + F_{comp} + F_{exh}$
2.  **Vetor de Probabilidade Instantânea ($P_i$):** Cada estado recebe uma fatia: $P_{estado\_i} = F_{estado} / Total$.
3.  **Suavização de Markov:** Aplicamos uma EMA de 20 períodos nesses percentuais: $P_{markov} = EMA(P_{estado\_i}, 20)$.
    -   **Influência do Passado:** A Cadeia de Markov garante que o próximo estado dependa do atual. O candle anterior influencia o presente através da "Inércia Probabilística" carregada pela EMA.

### C. Estágio 3: Identificação de Regime e Piso de Ruído
-   **Regime Dominante:** O estado com o maior percentual no vetor de Markov define o Regime (Bull, Bear, Comp ou Exh).
-   **Piso de Ruído (Atrito Estático):** Calculamos a média da energia total recente. Se a força Bull/Bear do candle atual não superar este piso, o sinal de ignição é bloqueado como "Ruído".

---

## 3. Mapeamento das Transições de Estado

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
