# Manual do Usuário: Programa Python EFG - Crypto (MPRM V15.0 - Pure Physics)

Este programa é uma implementação em Python do modelo **Market Physics Regime Model (MPRM V15.0)**. Esta versão elimina completamente o uso de EMAs (médias móveis) nas probabilidades de estado para remover o lag temporal, focando na física pura do estado presente.

## 1. Lógica de Sinais: A Engenharia por Trás do Modelo

O MPRM trata o mercado como um sistema mecânico e termodinâmico. Não operamos "preço", operamos **Trabalho e Força**.

### A. A Segunda Lei de Newton (F = m.a)
Para que uma tendência tenha assertividade, não basta o preço se mover. É preciso que haja **Massa** sustentando o movimento.
*   **Massa (m):** No nosso modelo, a massa é o **Volume Normalizado**. Um volume acima da média (m > 1) aumenta a inércia do movimento.
*   **Aceleração (a):** É o **Trabalho do Preço** (corpo do candle).
*   **Força (F):** A força resultante é o produto do Volume pelo Deslocamento. Movimentos com baixo volume são considerados "sem massa" e, portanto, incapazes de vencer o atrito do mercado.

### B. O Critério de 35%, Piso de Ruído e Histerese
*   **O Racional Matemático:** Em um sistema com 4 estados possíveis, a probabilidade de "ruído puro" é de **25%**.
*   **O Gatilho Físico:** Adotamos **35%** porque representa um excesso de energia sobre a base neutra.
*   **Filtro de Atrito:** Exige que a **Força (F)** supere o **Piso de Ruído** (Atrito Estático).
*   **Histerese (V14.2):** Para evitar que o sistema mude de regime por variações mínimas (flickering), implementamos uma margem de **5%**. O novo estado deve vencer o atual por essa margem, ou o atual deve cair abaixo do nível de ruído (25%), para que a mudança ocorra. É o "termostato" do sistema.

### C. Redução de 30% (Afastamento > 1 ATR — "Limite Elástico")
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
    -   **Lógica:** Perda de energia por pavios (rejeição). Representa o caos.
    -   **Transição COMP -> EXH:** Significa a dissipação da energia potencial acumulada em briga desordenada (pavios) em vez de movimento direcional. É a "mola que quebrou".

### B. Cadeia de Markov e Inércia (V15.0 - Sem Lag)
Diferente de indicadores comuns, o MPRM V15.0 opera na proporção da energia instantânea:

1.  **Soma das Forças:** $Total = F_{bull} + F_{bear} + F_{comp} + F_{exh}$
2.  **Probabilidades do Agora ($P_i$):** Representam a distribuição de energia no candle atual.
3.  **Matriz de Transição:** As decisões não são baseadas em "médias do passado", mas na transição direta entre o estado anterior ($T-1$) e o atual ($T$). Isso permite capturar inversões e ignições no exato momento em que a física do mercado muda.

### C. Estágio 3: Identificação de Regime e Piso de Ruído
-   **Regime Dominante:** O estado com o maior percentual no vetor de Markov define o Regime (Bull, Bear, Comp ou Exh).
-   **Piso de Ruído (Atrito Estático):** Calculamos a média da energia total recente. Se a força Bull/Bear do candle atual não superar este piso, o sinal de ignição é bloqueado como "Ruído".

---

## 3. Mapeamento das Transições de Estado (V15.0)

O sistema analisa a transição do estado anterior ($T-1$) para o atual ($T$) para inferir a dinâmica futura:

| Transição | Contexto Físico | Decisão de Trade |
| :--- | :--- | :--- |
| **BULL -> BULL** | Continuidade de Fluxo. | **ENTRAR / MANTER** |
| **COMP -> BULL** | Rompimento de Compressão. | **ENTRAR** |
| **BULL -> COMP** | Perda de Momento (Acúmulo). | **REDUZIR 50%** |
| **ANY -> EXH** | Dissipação por Entropia. | **FECHAR (TOTAL)** |
| **EXH -> ANY** | Perda de Assertividade. | **FECHAR / SAIR** |
| **BULL <-> BEAR** | Inversão de Polaridade. | **FECHAR / REVERTER** |

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
