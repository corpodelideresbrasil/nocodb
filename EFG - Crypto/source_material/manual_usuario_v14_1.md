# Manual do Usuário: Market Physics Regime Model (MPRM V14.1)

O **MPRM V14.1** é um decodificador de estados físicos do mercado. Ele ignora o ruído histórico e foca na termodinâmica do preço no exato momento da formação do candle.

## 1. O Painel de Controle (HUD)

* **Coluna "AGORA":** A energia bruta do candle atual.
* **Coluna "MARKOV":** A probabilidade suavizada (com base no `markov_len = 20`). **Decisões de entrada baseiam-se exclusivamente nesta coluna.**
* **Campo "STATE":**
* **EXPANSION:** Fluxo direcional. O ambiente ideal para o trade.
* **CONTRACTION:** Acúmulo. Prepare-se, a "mola" está carregando.
* **EXHAUSTION:** Caos (pavios longos). **Zona de exclusão de operações.**

## 2. A Regra dos "N" Candles (Validade do Sinal)

O sinal de *Ignition* (⚡ para compra, 🔥 para venda) tem um prazo de validade estrito baseado na inércia configurada (`markov_len = 20`).

* **Sinal Fresco (0 a 10 candles):** O sinal está em sua zona de máxima eficiência. Entre a mercado.
* **Sinal de Alerta (11 a 20 candles):** O sinal está perdendo inércia. Entre apenas se o preço realizar um *pullback* (retorno) para a zona de preço original da ignição.
* **Sinal Expirado (> 20 candles):** A inércia markoviana foi dissipada. **Não execute.** O sinal deve ser descartado, mesmo que a cor da barra ainda favoreça a direção.

## 3. Inertial Trail: Gestão da Inércia

A linha de *Trailing Stop* é o limite físico onde a tese de movimento se invalida.

* **Linha com Inclinação (Ascendente/Descendente):** Tendência saudável. **Mantenha a posição.**
* **Linha Flat (Horizontal):** O mercado perdeu momento direcional.
* *Ação:* Se a linha permanecer *flat* por 3 candles consecutivos, encerre **50% da posição** (realização parcial) para proteger capital.

* **Preço se afasta da linha:** Define-se "afastamento excessivo" quando o preço se distancia mais de **1.0 ATR** da `Inertial Trail`.
* *Ação:* Quando o preço atinge essa distância, ele está "esticado". Realize **30% da posição** para garantir lucro e suba o stop dos 70% restantes para o preço de entrada (ou para a própria linha de trail).

## 4. Gestão de Risco: Spread e Slippage

Como especialista em lançamentos, você sabe que a execução é tão importante quanto a análise.

* **O que são:**
* *Spread:* A diferença entre o preço de compra e venda.
* *Slippage:* A diferença entre o preço que você deseja e o que o mercado executa, causada pela falta de liquidez imediata.

* **Quando agir:**
* Se o `Spread` + `Slippage` estimado for maior que **20% do ATR atual**, a operação é inviável. O custo transacional consumirá sua vantagem estatística.
* *Ação:* Em ativos de baixa liquidez, coloque ordens limitadas um tick acima/abaixo do gatilho (Ignition), nunca a mercado. Se o mercado se mover rápido demais (notícias), não persiga o preço.

## 5. Resumo Operacional (Painel de Bordo)

| Elemento | Condição Ideal | Ação em Caso de Desvio |
| --- | --- | --- |
| **Markov (HUD)** | > 40% de força | < 25%: Não entre. |
| **STATE** | Expansion/Contraction | Se Exhaustion: Fique de fora. |
| **Inertial Trail** | Inclinada | Flat por 3 barras: Saída parcial (50%). |
| **Afastamento** | < 1.0 ATR | > 1.0 ATR: Saída parcial (30%). |
| **N-Candles** | < 20 barras | > 20 barras: Sinal expirado. |

---

**Nota Técnica:** O MPRM V14.1 não prevê o futuro, ele gerencia o risco do presente. Mantenha a disciplina técnica. O tempo e os juros compostos trabalham melhor quando o operacional é simples e repetível.
