# Supertrend v3.6 - Python implementation (Binance Futures)

Este projeto é uma implementação de alta performance em Python do indicador **Supertrend v3.6**, otimizado para monitorar múltiplos ativos em contratos futuros perpétuos da Binance.

## Novidades da Versão Otimizada

- **Binance Futures**: O sistema agora se conecta diretamente aos contratos perpétuos da Binance (ex: BTCUSDT, ETHUSDT).
- **Coluna Stop Loss**: Agora exibe o valor exato do Supertrend (Stop Loss) na tabela de resultados.
- **Feedback em Tempo Real**: O terminal exibe qual ativo está sendo analisado no momento para garantir que o processo está ativo.
- **Performance**: Algoritmo otimizado com NumPy para processamento ultrarápido de múltiplos ativos.

## Estrutura do Projeto

- `main.py`: Script consolidado com lógica otimizada.
- `assets.json`: Arquivo de configuração para listar os ativos (ex: `BTCUSDT`, `ADAUSDT`).
- `requirements.txt`: Dependências.

## Como Configurar os Ativos

Edite o arquivo `assets.json` na raiz da pasta. Adicione os símbolos no padrão Binance Futures (sem barra):

```json
{
    "assets": [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "TONUSDT"
    ]
}
```

## Como Iniciar

1. **Ativar o Ambiente Virtual**:
   - `source venv/bin/activate` (Mac/Linux) ou `.\venv\Scripts\Activate.ps1` (Windows)

2. **Instalar as Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Executar o Scanner**:
   ```bash
   python main.py
   ```

## Observações
O script detecta automaticamente se a Binance está disponível. Caso haja restrições regionais (como em alguns ambientes de teste), ele tentará usar a Kraken como alternativa de demonstração.
