import os
import sys
import json
import pandas as pd
import numpy as np
from tabulate import tabulate
import ccxt

# ==============================================================================
# SUPERTREND V3.6 - VERSÃO CONSOLIDADA COM CONFIGURAÇÃO JSON
# ==============================================================================

def load_assets():
    """ Carrega a lista de ativos do arquivo assets.json """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "assets.json")

    # Ativos padrão caso o arquivo não exista
    default_assets = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    if not os.path.exists(config_path):
        print(f"⚠️ Aviso: assets.json não encontrado. Usando ativos padrão: {default_assets}")
        return default_assets

    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            return data.get("assets", default_assets)
    except Exception as e:
        print(f"❌ Erro ao ler assets.json: {e}. Usando ativos padrão.")
        return default_assets

def fetch_ohlcv(symbol, timeframe='1h', limit=500):
    """ Busca dados da exchange Kraken """
    try:
        exchange = ccxt.kraken()
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        raise Exception(f"Erro ao buscar dados: {e}")

def calculate_supertrend(df, period=15, multiplier=1.4):
    """ Cálculo exato do Supertrend v5 (Pine Script) """
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([(high - low), (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    hl2 = (high + low) / 2
    basic_ub, basic_lb = hl2 + multiplier * atr, hl2 - multiplier * atr
    final_ub, final_lb = np.zeros(len(df)), np.zeros(len(df))
    for i in range(len(df)):
        if i == 0:
            final_ub[i], final_lb[i] = basic_ub.iloc[i], basic_lb.iloc[i]
        else:
            final_ub[i] = basic_ub.iloc[i] if basic_ub.iloc[i] < final_ub[i-1] or close.iloc[i-1] > final_ub[i-1] else final_ub[i-1]
            final_lb[i] = basic_lb.iloc[i] if basic_lb.iloc[i] > final_lb[i-1] or close.iloc[i-1] < final_lb[i-1] else final_lb[i-1]
    direction, supertrend = np.ones(len(df)), np.zeros(len(df))
    for i in range(1, len(df)):
        if direction[i-1] == -1:
            if close.iloc[i] < final_lb[i]: direction[i], supertrend[i] = 1, final_ub[i]
            else: direction[i], supertrend[i] = -1, final_lb[i]
        else:
            if close.iloc[i] > final_ub[i]: direction[i], supertrend[i] = -1, final_lb[i]
            else: direction[i], supertrend[i] = 1, final_ub[i]
    return pd.Series(supertrend, index=df.index), pd.Series(direction, index=df.index)

def generate_signals(df, st_line, direction, max_inertia=3):
    """ Lógica de Sinais e Inércia """
    df = df.copy()
    df['trend'] = direction.apply(lambda x: 1 if x == -1 else -1)
    df['buy_signal'] = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    df['sell_signal'] = (df['trend'] == -1) & (df['trend'].shift(1) == 1)
    barras, count = np.zeros(len(df)), 100
    for i in range(len(df)):
        if df['buy_signal'].iloc[i] or df['sell_signal'].iloc[i]: count = 0
        else: count += 1
        barras[i] = count
    df['barras_desde_sinal'] = barras
    change_st, inercia, count_i = st_line.diff(), np.zeros(len(df)), 0
    for i in range(len(df)):
        if change_st.iloc[i] == 0: count_i += 1
        else: count_i = 0
        inercia[i] = count_i
    df['contagem_inercia'] = inercia
    df['semaforo'] = df.apply(lambda r: "LARANJA (INÉRCIA)" if r['contagem_inercia'] >= max_inertia else ("VERDE (ENTRADA VÁLIDA)" if r['barras_desde_sinal'] <= 2 else "AMARELO (ATENÇÃO)"), axis=1)
    df['acao'] = df.apply(lambda r: "FECHAR (INÉRCIA)" if r['contagem_inercia'] >= max_inertia else (("ENTRAR" if r['trend'] == 1 else "VENDER") if r['barras_desde_sinal'] <= 2 else "AGUARDAR"), axis=1)
    return df

def run_scanner():
    assets = load_assets()
    print(f"\n🚀 Scanner Supertrend v3.6 - Monitorando {len(assets)} ativos")
    results = []
    for symbol in assets:
        try:
            df = fetch_ohlcv(symbol)
            st, dir = calculate_supertrend(df)
            df = generate_signals(df, st, dir)
            last = df.iloc[-1]
            results.append([symbol, "ALTA" if last['trend'] == 1 else "BAIXA", last['semaforo'], last['acao'], f"{last['close']:.2f}"])
        except Exception as e:
            results.append([symbol, "ERRO", "-", "-", str(e)])
    print(tabulate(results, headers=["ATIVO", "TENDÊNCIA", "SEMÁFORO", "AÇÃO", "PREÇO"], tablefmt="grid"))

if __name__ == "__main__":
    run_scanner()
