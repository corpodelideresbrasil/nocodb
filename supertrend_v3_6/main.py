import os
import sys
import pandas as pd
import numpy as np
from tabulate import tabulate
import ccxt

# ==============================================================================
# SUPERTREND V3.6 - VERSÃO ROBUSTA (SINGLE FILE)
# ==============================================================================
# Este script contém toda a lógica necessária para rodar o scanner sem erros
# de importação de módulos.
# ==============================================================================

def fetch_ohlcv(symbol, timeframe='1h', limit=500):
    """ Busca dados da exchange Kraken (mais estável para diversas regiões) """
    try:
        exchange = ccxt.kraken()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        raise Exception(f"Erro ao buscar dados de {symbol}: {e}")

def calculate_supertrend(df, period=15, multiplier=1.4):
    """
    Cálculo exato do Supertrend v5 (Pine Script).
    Usa RMA (Running Moving Average) para o ATR.
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # Cálculo do True Range
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)

    # ATR usando RMA (alpha = 1/period)
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    hl2 = (high + low) / 2
    basic_ub = hl2 + multiplier * atr
    basic_lb = hl2 - multiplier * atr

    final_ub = np.zeros(len(df))
    final_lb = np.zeros(len(df))

    # Loop para Bands (Inércia de Banda)
    for i in range(len(df)):
        if i == 0:
            final_ub[i] = basic_ub.iloc[i]
            final_lb[i] = basic_lb.iloc[i]
        else:
            # Upper Band
            if basic_ub.iloc[i] < final_ub[i-1] or close.iloc[i-1] > final_ub[i-1]:
                final_ub[i] = basic_ub.iloc[i]
            else:
                final_ub[i] = final_ub[i-1]

            # Lower Band
            if basic_lb.iloc[i] > final_lb[i-1] or close.iloc[i-1] < final_lb[i-1]:
                final_lb[i] = basic_lb.iloc[i]
            else:
                final_lb[i] = final_lb[i-1]

    # Determinação da Direção e Linha Final
    direction = np.ones(len(df)) # 1 para Down, -1 para Up
    supertrend = np.zeros(len(df))

    close_v = close.values
    for i in range(1, len(df)):
        if direction[i-1] == -1: # Tendência de Alta
            if close_v[i] < final_lb[i]:
                direction[i] = 1 # Virou Baixa
                supertrend[i] = final_ub[i]
            else:
                direction[i] = -1 # Continua Alta
                supertrend[i] = final_lb[i]
        else: # Tendência de Baixa
            if close_v[i] > final_ub[i]:
                direction[i] = -1 # Virou Alta
                supertrend[i] = final_lb[i]
            else:
                direction[i] = 1 # Continua Baixa
                supertrend[i] = final_ub[i]

    return pd.Series(supertrend, index=df.index), pd.Series(direction, index=df.index)

def generate_signals(df, supertrend, direction, max_inertia=3):
    """ Lógica de Sinais, Semáforo e Inércia """
    df = df.copy()
    df['supertrend'] = supertrend
    df['direction'] = direction
    df['trend'] = df['direction'].apply(lambda x: 1 if x == -1 else -1)

    # Detecção de novos sinais
    df['buy_signal'] = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    df['sell_signal'] = (df['trend'] == -1) & (df['trend'].shift(1) == 1)

    # Contador de velas desde o sinal
    barras_desde_sinal = np.zeros(len(df))
    count = 100
    for i in range(len(df)):
        if df['buy_signal'].iloc[i] or df['sell_signal'].iloc[i]:
            count = 0
        else:
            count += 1
        barras_desde_sinal[i] = count
    df['barras_desde_sinal'] = barras_desde_sinal

    # Contador de Inércia (Supertrend lateralizado)
    change_st = df['supertrend'].diff()
    contagem_inercia = np.zeros(len(df))
    count_i = 0
    for i in range(len(df)):
        if change_st.iloc[i] == 0:
            count_i += 1
        else:
            count_i = 0
        contagem_inercia[i] = count_i
    df['contagem_inercia'] = contagem_inercia

    # Lógica de Semáforo
    def get_status(row):
        if row['contagem_inercia'] >= max_inertia:
            return "LARANJA (INÉRCIA)", "FECHAR (INÉRCIA)"
        elif row['barras_desde_sinal'] <= 2:
            return "VERDE (ENTRADA VÁLIDA)", ("ENTRAR" if row['trend'] == 1 else "VENDER")
        else:
            return "AMARELO (ATENÇÃO)", "AGUARDAR"

    status_data = df.apply(get_status, axis=1)
    df['semaforo'] = [x[0] for x in status_data]
    df['acao'] = [x[1] for x in status_data]

    return df

def run_scanner(symbols, timeframe='1h'):
    results = []
    print(f"\n🚀 Iniciando Scanner Supertrend v3.6")
    print(f"Ativos: {len(symbols)} | Timeframe: {timeframe}\n")

    for symbol in symbols:
        try:
            df = fetch_ohlcv(symbol, timeframe=timeframe)
            st, direction = calculate_supertrend(df)
            df_signals = generate_signals(df, st, direction)

            last = df_signals.iloc[-1]
            results.append([
                symbol,
                "ALTA (BUY)" if last['trend'] == 1 else "BAIXA (SELL)",
                last['semaforo'],
                last['acao'],
                f"{last['close']:.2f}"
            ])
        except Exception as e:
            print(f"❌ Erro em {symbol}: {e}")
            results.append([symbol, "ERROR", "-", "-", "-"])

    print(tabulate(results, headers=["ATIVO", "TENDÊNCIA", "SEMÁFORO", "AÇÃO", "PREÇO"], tablefmt="grid"))

if __name__ == "__main__":
    # Lista de Ativos
    assets = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "ADA/USDT", "DOT/USDT", "XRP/USDT"]
    run_scanner(assets)
