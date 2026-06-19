import os
import sys
import json
import pandas as pd
import numpy as np
from tabulate import tabulate
import ccxt
import time

# ==============================================================================
# SUPERTREND V3.6 - GESTÃO DE CARTEIRA (BINANCE FUTURES)
# ==============================================================================

# Cores ANSI para Terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
BOLD = "\033[1m"
RESET = "\033[0m"

def load_assets():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "assets.json")
    if not os.path.exists(config_path): return ["BTCUSDT", "ETHUSDT"]
    try:
        with open(config_path, "r") as f:
            return json.load(f).get("assets", ["BTCUSDT"])
    except: return ["BTCUSDT"]

def load_portfolio():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "portfolio.json")
    if not os.path.exists(path): return {}
    try:
        with open(path, "r") as f: return json.load(f)
    except: return {}

def save_portfolio(portfolio):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "portfolio.json")
    with open(path, "w") as f: json.dump(portfolio, f, indent=4)

def fetch_ohlcv(exchange, symbol, timeframe='1h', limit=500):
    try:
        clean_symbol = symbol.replace("/", "").upper()
        ohlcv = exchange.fetch_ohlcv(clean_symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e: raise Exception(f"{e}")

def calculate_supertrend(df, period=15, multiplier=1.4):
    high, low, close = df['high'].values, df['low'].values, df['close'].values
    tr = np.zeros(len(df))
    tr[0] = high[0] - low[0]
    tr[1:] = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
    atr = np.zeros(len(df))
    alpha = 1 / period
    atr[0] = np.mean(tr[:period])
    for i in range(1, len(df)): atr[i] = (tr[i] * alpha) + (atr[i-1] * (1 - alpha))
    hl2 = (high + low) / 2
    basic_ub, basic_lb = hl2 + multiplier * atr, hl2 - multiplier * atr
    final_ub, final_lb = np.zeros(len(df)), np.zeros(len(df))
    for i in range(len(df)):
        if i == 0: final_ub[i], final_lb[i] = basic_ub[i], basic_lb[i]
        else:
            final_ub[i] = basic_ub[i] if basic_ub[i] < final_ub[i-1] or close[i-1] > final_ub[i-1] else final_ub[i-1]
            final_lb[i] = basic_lb[i] if basic_lb[i] > final_lb[i-1] or close[i-1] < final_lb[i-1] else final_lb[i-1]
    direction, st_line = np.ones(len(df)), np.zeros(len(df))
    for i in range(1, len(df)):
        if direction[i-1] == -1:
            if close[i] < final_lb[i]: direction[i], st_line[i] = 1, final_ub[i]
            else: direction[i], st_line[i] = -1, final_lb[i]
        else:
            if close[i] > final_ub[i]: direction[i], st_line[i] = -1, final_lb[i]
            else: direction[i], st_line[i] = 1, final_ub[i]
    return st_line, direction

def run_scanner():
    assets = load_assets()
    portfolio = load_portfolio()

    try:
        exchange = ccxt.binance({'options': {'defaultType': 'future'}})
        exchange.fetch_ohlcv('BTCUSDT', limit=1)
    except:
        exchange = ccxt.kraken()

    print(f"\n🚀 {BOLD}SCANNER SUPERTREND V3.6{RESET} - {exchange.id.upper()}")
    print(f"Monitorando {len(assets)} ativos... [Timeframe: 1h]\n")

    results = []
    start_time = time.time()

    for symbol in assets:
        sys.stdout.write(f"\r🔍 Analisando: {symbol:10} ")
        sys.stdout.flush()
        try:
            curr_sym = symbol
            if exchange.id == 'kraken' and not "/" in symbol: curr_sym = f"{symbol[:-4]}/{symbol[-4:]}"
            df = fetch_ohlcv(exchange, curr_sym)
            st, direction = calculate_supertrend(df)

            last_close = df['close'].iloc[-1]
            last_st = st[-1]
            last_dir = direction[-1]

            c_inercia = 0
            for k in range(1, 4):
                if st[-k] == st[-k-1]: c_inercia += 1
                else: break

            b_desde_sinal = 0
            for k in range(1, 20):
                if direction[-k] == direction[-k-1]: b_desde_sinal += 1
                else: break

            is_active = symbol in portfolio
            side = "LONG" if last_dir == -1 else "SHORT"

            # --- Lógica de Decisão ---
            acao = "AGUARDAR"
            semaforo = "AMARELO"
            st_display = f"{last_st:.4f}"
            pnl_display = "-"

            if is_active:
                pos = portfolio[symbol]
                # PnL calculado com base na entrada salva
                pnl = (last_close / pos['entry_price'] - 1) * 100 if pos['side'] == "LONG" else (pos['entry_price'] / last_close - 1) * 100
                pnl_color = GREEN if pnl > 0 else RED
                pnl_display = f"{pnl_color}{pnl:+.2f}%{RESET}"

                # Critérios de Fechamento: Flip de tendência ou Inércia
                if c_inercia >= 3 or side != pos['side']:
                    acao = f"{BOLD}{RED}FECHAR{RESET}"
                    semaforo = f"{ORANGE}LARANJA (INÉRCIA){RESET}"
                    st_display = f"{RED}{last_st:.4f}{RESET}"
                    portfolio.pop(symbol) # Removido da carteira
                else:
                    acao = f"{BOLD}{GREEN}MANTER{RESET}"
                    semaforo = f"{YELLOW}AMARELO{RESET}"

                    # Cor do ST: Verde se moveu a favor, Vermelho se contra
                    old_st = pos['last_st']
                    if (pos['side'] == "LONG" and last_st > old_st) or (pos['side'] == "SHORT" and last_st < old_st):
                        st_color = GREEN
                    elif (pos['side'] == "LONG" and last_st < old_st) or (pos['side'] == "SHORT" and last_st > old_st):
                        st_color = RED
                    else:
                        st_color = RESET

                    st_display = f"{st_color}{last_st:.4f}{RESET}"
                    pos['last_st'] = last_st # Atualiza para próxima rodada
            else:
                # Se não está ativo, verifica se há sinal fresco de entrada
                if b_desde_sinal <= 2:
                    acao = f"{BOLD}{GREEN}ENTRAR{RESET}"
                    semaforo = f"{GREEN}VERDE (ENTRADA){RESET}"
                    # Registra entrada no portfólio
                    portfolio[symbol] = {
                        "side": side,
                        "entry_price": last_close,
                        "last_st": last_st
                    }
                    st_display = f"{last_st:.4f}"

            # Filtra apenas o que é operacional (IGNORA AGUARDAR)
            if "AGUARDAR" not in acao:
                results.append([
                    symbol,
                    f"{GREEN if last_dir == -1 else RED}{'ALTA' if last_dir == -1 else 'BAIXA'}{RESET}",
                    semaforo, acao, f"{last_close:.4f}", st_display, pnl_display
                ])

        except Exception as e:
            # results.append([symbol, "ERRO", "-", "-", "-", "-", str(e)[:20]])
            pass

    save_portfolio(portfolio)
    sys.stdout.write("\r" + " " * 50 + "\r")

    headers = ["ATIVO", "TENDÊNCIA", "SEMÁFORO", "AÇÃO", "PREÇO ATUAL", "STOP LOSS (ST)", "PNL (%)"]
    if results:
        print(tabulate(results, headers=headers, tablefmt="grid"))
    else:
        print("\n☕ Sem ações operacionais. Todos os ativos estão em AGUARDAR.")

    print(f"\n✅ Concluído em {time.time() - start_time:.2f}s")

if __name__ == "__main__":
    run_scanner()
