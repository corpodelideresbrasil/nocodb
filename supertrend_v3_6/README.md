# Supertrend v3.6 - Portfolio Manager (4H Default)

Este projeto automatiza a análise do indicador **Supertrend v3.6** em contratos futuros perpetuos da Binance, com foco em gestão de carteira e sinais confirmados.

## Novidades desta Versão

- **Timeframe 4H**: O padrão de análise foi alterado para 4 horas, ideal para operações de swing trade em cripto.
- **Confirmação Manual**: Novas entradas (ENTRAR/VENDER) não são adicionadas automaticamente à carteira. O programa solicitará sua confirmação individual (`s/n`) ao final de cada análise.
- **Gestão de Carteira**: Ações de `MANTER` e `FECHAR` são recomendadas com base nas posições salvas em `portfolio.json`.
- **PnL em Tempo Real**: Exibe o lucro/prejuízo das operações abertas.
- **Feedback Visual**: Cores indicam a saúde da operação e a movimentação do Stop Loss.

## Como Configurar os Ativos

Edite o arquivo `assets.json` com os símbolos da Binance Futures (ex: `BTCUSDT`).

```json
{
    "assets": [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT"
    ]
}
```

## Como Iniciar

1. **Ativar o Ambiente Virtual**:
   - `source venv/bin/activate` (Mac/Linux) ou `.\venv\Scripts\Activate.ps1` (Windows)

2. **Instalar Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Executar o Scanner**:
   ```bash
   python main.py
   ```

## Fluxo de Operação
1. O scanner analisa os ativos no gráfico de 4H.
2. Exibe a tabela com recomendações operacionais.
3. Se houver novas entradas, o programa perguntará: `❓ Deseja confirmar entrada em XXXX? (s/n)`.
4. Respondendo `s`, o ativo é incluído no `portfolio.json` e passará a ser monitorado com PnL e Trailing Stop na próxima rodada.
