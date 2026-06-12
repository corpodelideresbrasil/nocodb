# Blueprint de Automação: Estratégia Raul Lateralidade

Este documento consolida as informações necessárias para a migração da estratégia de trading do Pine Script para Python.

## 1. Endereço do Repositório e Localização
- **URL do Repositório:** `https://github.com/corpodelideresbrasil/nocodb`
- **Código Fonte do Indicador (Pine Script v6):** Arquivo `strategy_raul_lateralidade_v3_4.pine`
- **Branch de Desenvolvimento:** `improve-raul-lateralidade-strategy-5018352353769845846`

## 2. Conceitos Matemáticos e Regras de Negócio
A estratégia visa automatizar sinais de entrada e saída, filtrando períodos de baixa volatilidade (lateralidade).

### Parâmetros de Sensibilidade (Base: 1D)
- **Lookback:** 7 (período de observação).
- **Sensibilidade Inclinação (thrFlat):** 1.1 (detecta médias horizontais).
- **Sensibilidade Squeeze (thrSqueeze):** 0.5 (detecta médias curtas e longas próximas).
- **Sensibilidade Código de Barras (thrBarcode):** 6 (trocas excessivas de cor de candle).

### Lógica Anti-Ruído
- **Normalização por ATR:** Todos os cálculos de distância e inclinação são divididos pelo ATR para garantir que a estratégia funcione em qualquer ativo (ex: BTC vs DOGE) sem reajuste manual.
- **Histerese de Consolidação (holdConsolid):** Mantém o estado de "lateralidade" por um número de barras (padrão: 3) após a detecção, evitando sinais falsos.
- **Barra de Carência (minBarsBetweenTrades):** Cooldown após a saída de uma operação para evitar re-entradas imediatas em zonas de ruído.

### Regras de Operação
- **Long (Compra):** `smaCurta > smaLonga` AND `preço > smaCurta` AND NOT `isConsolid`.
- **Short (Venda):** `smaCurta < smaLonga` AND `preço < smaCurta` AND NOT `isConsolid`.
- **Saída "Sem Força":** Se o preço cruzar contra a `smaCurta`.
- **Saída "Breakeven/Loss":** Se o preço cair abaixo do preço médio de entrada (para Long).

## 3. Guia de Migração para Python
Para migrar o código, utilize o template `migration_template.py` fornecido. Ele utiliza a biblioteca `pandas` para replicar os cálculos vetoriais do Pine Script.

### Passos para Novo Projeto:
1. Crie uma pasta para o projeto: `mkdir automacao-sinais && cd automacao-sinais`.
2. Configure um ambiente virtual: `python -m venv venv && source venv/bin/activate`.
3. Instale dependências: `pip install pandas pandas_ta ccxt`.
4. Copie o arquivo `migration_template.py` para o novo diretório.
5. Copie este arquivo `blueprint_automacao.md` para a pasta `docs/` do seu novo projeto para manter o histórico de requisitos.
