import os
import sys
import json
import pandas as pd
import numpy as np
from tabulate import tabulate
import ccxt
import time

# ==============================================================================
# SUPERTREND V3.6 - VERSÃO FINAL OTIMIZADA (BINANCE FUTURES)
# ==============================================================================

def load_assets():
    """ Carrega a lista de ativos do arquivo assets.json """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "assets.json")
    default_assets = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

    if not os.path.exists(config_path):
        return default_assets
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            return data.get("assets", default_assets)
    except Exception:
        return default_assets

def fetch_ohlcv(exchange, symbol, timeframe='1h', limit=500):
    """ Busca dados OHLCV """
    try:
        clean_symbol = symbol.replace("/", "").upper()
        ohlcv = exchange.fetch_ohlcv(clean_symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        raise Exception(f"{e}")

def calculate_supertrend(df, period=15, multiplier=1.4):
    """ Cálculo otimizado do Supertrend v5 """
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values

    # 1. True Range (TR)
    tr = np.zeros(len(df))
    tr[0] = high[0] - low[0]
    tr[1:] = np.maximum(high[1:] - low[1:],
                        np.maximum(np.abs(high[1:] - close[:-1]),
                                   np.abs(low[1:] - close[:-1])))

    # 2. ATR usando RMA (Running Moving Average)
    atr = np.zeros(len(df))
    alpha = 1 / period
    atr[0] = np.mean(tr[:period]) # Inicialização comum para RMA
    for i in range(1, len(df)):
        atr[i] = (tr[i] * alpha) + (atr[i-1] * (1 - alpha))

    # 3. Upper e Lower Bands
    hl2 = (high + low) / 2
    basic_ub = hl2 + multiplier * atr
    basic_lb = hl2 - multiplier * atr

    final_ub = np.zeros(len(df))
    final_lb = np.zeros(len(df))

    for i in range(len(df)):
        if i == 0:
            final_ub[i], final_lb[i] = basic_ub[i], basic_lb[i]
        else:
            final_ub[i] = basic_ub[i] if basic_ub[i] < final_ub[i-1] or close[i-1] > final_ub[i-1] else final_ub[i-1]
            final_lb[i] = basic_lb[i] if basic_lb[i] > final_lb[i-1] or close[i-1] < final_lb[i-1] else final_lb[i-1]

    # 4. Supertrend Line e Direção
    direction = np.ones(len(df)) # 1 para Baixa, -1 para Alta
    st_line = np.zeros(len(df))

    for i in range(1, len(df)):
        if direction[i-1] == -1: # Tendência de Alta
            if close[i] < final_lb[i]:
                direction[i], st_line[i] = 1, final_ub[i]
            else:
                direction[i], st_line[i] = -1, final_lb[i]
        else: # Tendência de Baixa
            if close[i] > final_ub[i]:
                direction[i], st_line[i] = -1, final_lb[i]
            else:
                direction[i], st_line[i] = 1, final_ub[i]

    return st_line, direction

def run_scanner():
    assets = load_assets()

    # Configuração da Exchange (Prioridade Binance Futures)
    try:
        exchange = ccxt.binance({'options': {'defaultType': 'future'}})
        # Teste de conexão/restrição
        exchange.fetch_ohlcv('BTCUSDT', limit=1)
    except:
        print("⚠️ Binance Futures restrita ou inacessível. Tentando Kraken...")
        exchange = ccxt.kraken()

    print(f"\n🚀 SCANNER SUPERTREND V3.6 - {exchange.id.upper()}")
    print(f"Monitorando {len(assets)} ativos... [Timeframe: 1h]\n")

    results = []
    start_time = time.time()

    for symbol in assets:
        # Mensagem de progresso para não parecer travado
        sys.stdout.write(f"\r🔍 Analisando: {symbol:10} ")
        sys.stdout.flush()

        try:
            # Símbolo para Kraken (fallback) se necessário
            curr_sym = symbol
            if exchange.id == 'kraken' and not "/" in symbol:
                curr_sym = f"{symbol[:-4]}/{symbol[-4:]}"

            df = fetch_ohlcv(exchange, curr_sym)
            st, direction = calculate_supertrend(df)

            # --- Lógica de Sinais (Paridade com Pine Script) ---
            # contagemInercia: st constante por 3 velas
            c_inercia = 0
            for k in range(1, 4):
                if st[-k] == st[-k-1]: c_inercia += 1
                else: break

            # barrasDesdeSinal: velas desde o flip de tendência
            b_desde_sinal = 0
            for k in range(1, 20):
                if direction[-k] == direction[-k-1]: b_desde_sinal += 1
                else: break

            # Semáforo e Ação
            if c_inercia >= 3: # Inércia (3 velas parado)
                semaforo, acao = "LARANJA (INÉRCIA)", "FECHAR"
            elif b_desde_sinal <= 2: # Entrada Válida (até 2 velas do sinal)
                semaforo, acao = "VERDE (ENTRADA)", "ENTRAR" if direction[-1] == -1 else "VENDER"
            else:
                semaforo, acao = "AMARELO (ATENÇÃO)", "AGUARDAR"

            results.append([
                symbol,
                "ALTA (BUY)" if direction[-1] == -1 else "BAIXA (SELL)",
                semaforo,
                acao,
                f"{df['close'].iloc[-1]:.4f}",
                f"{st[-1]:.4f}"
            ])
        except Exception as e:
            results.append([symbol, "ERRO", "-", "-", "-", str(e)[:35]])

    # Limpa a linha de progresso
    sys.stdout.write("\r" + " " * 40 + "\r")
    sys.stdout.flush()

    headers = ["ATIVO", "TENDÊNCIA", "SEMÁFORO", "AÇÃO", "PREÇO ATUAL", "STOP LOSS (ST)"]
    print(tabulate(results, headers=headers, tablefmt="grid"))

    end_time = time.time()
    print(f"\n✅ Concluído em {end_time - start_time:.2f}s")

if __name__ == "__main__":
    run_scanner()
