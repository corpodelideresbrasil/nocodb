# Supertrend v3.6 - Portfolio Manager (Flexível)

Este projeto automatiza a análise do indicador **Supertrend v3.6** em contratos futuros perpétuos da Binance, com foco em gestão de carteira e sinais confirmados.

## Novidades desta Versão

- **Entradas Opcionais (Amarelo)**: Sinais em estado Amarelo não são mais ocultados. Eles aparecem como `ENTRAR (OPCIONAL)`, permitindo que você decida se deseja entrar na operação mesmo após o sinal inicial.
- **Timeframe 4H**: O padrão de análise é 4 horas (velas fechadas para estabilidade).
- **Confirmação Manual**: Novas entradas (Verde ou Amarelo) solicitarão confirmação (`s/n`) antes de serem salvas.
- **Gestão de Carteira**: Ações de `MANTER` e `FECHAR` são recomendadas com base nas posições em `portfolio.json`.
- **PnL em Tempo Real**: Exibe o lucro/prejuízo das operações abertas.

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
1. O scanner analisa os ativos no gráfico de 4H (apenas velas fechadas).
2. Exibe a tabela com recomendações: `ENTRAR` (Verde), `ENTRAR (OPCIONAL)` (Amarelo), `MANTER` ou `FECHAR`.
3. Para cada nova entrada (Verde ou Amarelo), o programa perguntará: `❓ Confirmar entrada em XXXX? (s/n)`.
4. Ao fechar uma operação, o programa solicitará o lucro/prejuízo realizado para atualizar seu saldo financeiro (início: $160).
5. Após as interações, uma tabela resumo da carteira atualizada é exibida.
