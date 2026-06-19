import os
import sys
import json
import pandas as pd
import numpy as np
from tabulate import tabulate
import ccxt
import time

# ==============================================================================
# SUPERTREND V3.6 - VERSÃO GESTÃO ROBUSTA (ANTI-SOBREPOSIÇÃO)
# ==============================================================================

# Cores ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
BOLD = "\033[1m"
RESET = "\033[0m"

def normalize_symbol(symbol):
    """ Remove barras e coloca em maiúsculo para consistência no portfolio.json """
    return symbol.replace("/", "").upper()

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

    if not os.path.exists(path):
        return {"balance": 160.0, "positions": {}}

    try:
        with open(path, "r") as f:
            data = json.load(f)
            # Garantir que chaves essenciais existem sem resetar o arquivo
            if "balance" not in data: data["balance"] = 160.0
            if "positions" not in data: data["positions"] = {}
            return data
    except json.JSONDecodeError:
        print(f"❌ {RED}ERRO FATAL: O arquivo portfolio.json está corrompido!{RESET}")
        print("Para sua segurança, o programa será encerrado. Corrija o arquivo ou delete-o para iniciar um novo.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado ao carregar portfolio: {e}")
        sys.exit(1)

def save_portfolio(data):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "portfolio.json")
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"❌ {RED}ERRO AO SALVAR PORTFOLIO:{RESET} {e}")

def fetch_ohlcv(exchange, symbol, timeframe='4h', limit=500):
    try:
        clean_symbol = normalize_symbol(symbol)
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
            final_ub[i] = basic_ub[i] if basic_ub[i] < final_ub[i-1] - 1e-10 or close[i-1] > final_ub[i-1] + 1e-10 else final_ub[i-1]
            final_lb[i] = basic_lb[i] if basic_lb[i] > final_lb[i-1] + 1e-10 or close[i-1] < final_lb[i-1] - 1e-10 else final_lb[i-1]
    direction, st_line = np.ones(len(df)), np.zeros(len(df))
    for i in range(1, len(df)):
        if direction[i-1] == -1:
            if close[i] < final_lb[i] - 1e-10: direction[i], st_line[i] = 1, final_ub[i]
            else: direction[i], st_line[i] = -1, final_lb[i]
        else:
            if close[i] > final_ub[i] + 1e-10: direction[i], st_line[i] = -1, final_lb[i]
            else: direction[i], st_line[i] = 1, final_ub[i]
    return st_line, direction

def run_scanner():
    assets = load_assets()
    port_data = load_portfolio()
    positions = port_data["positions"]

    try:
        exchange = ccxt.binance({'options': {'defaultType': 'future'}})
        exchange.fetch_ohlcv('BTCUSDT', limit=1)
    except:
        exchange = ccxt.kraken()

    print(f"\n🚀 {BOLD}SUPERTREND V3.6{RESET} | SALDO ATUAL: {GREEN}${port_data['balance']:.2f}{RESET}")
    print(f"Monitorando {len(assets)} ativos... [Timeframe: 4h]\n")

    results = []
    pending_entries = []
    pending_exits = []
    start_time = time.time()

    for symbol in assets:
        norm_sym = normalize_symbol(symbol)
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

            # Inércia
            c_inercia = 0
            for k in range(1, 10):
                if abs(st[-k] - st[-k-1]) < 1e-10: c_inercia += 1
                else: break

            # Velas desde o flip
            b_desde_sinal = 0
            for k in range(1, 20):
                if direction[-k] == direction[-k-1]: b_desde_sinal += 1
                else: break

            is_active = norm_sym in positions
            side = "LONG" if last_dir == -1 else "SHORT"

            acao = "AGUARDAR"
            semaforo = "AMARELO"
            st_display = f"{last_st:.4f}"
            pnl_display = "-"

            if is_active:
                pos = positions[norm_sym]
                # PnL robusto
                pnl = (last_close / pos['entry_price'] - 1) * 100 if pos['side'] == "LONG" else (pos['entry_price'] / last_close - 1) * 100
                pnl_display = f"{GREEN if pnl > 0 else RED}{pnl:+.2f}%{RESET}"

                if c_inercia >= 3 or side != pos['side']:
                    acao = f"{BOLD}{RED}FECHAR{RESET}"
                    semaforo = f"{ORANGE}LARANJA (INÉRCIA){RESET}"
                    st_display = f"{RED}{last_st:.4f}{RESET}"
                    pending_exits.append(norm_sym)
                else:
                    acao = f"{BOLD}{GREEN}MANTER{RESET}"
                    semaforo = f"{YELLOW}AMARELO{RESET}"
                    old_st = pos['last_st']
                    st_color = GREEN if (pos['side'] == "LONG" and last_st > old_st + 1e-10) or (pos['side'] == "SHORT" and last_st < old_st - 1e-10) else (RED if abs(last_st - old_st) > 1e-10 else RESET)
                    st_display = f"{st_color}{last_st:.4f}{RESET}"
                    pos['last_st'] = last_st
            else:
                # Entrada: Apenas se NÃO está na carteira (norm_sym)
                if b_desde_sinal <= 2 and c_inercia < 3:
                    acao = f"{BOLD}{GREEN}ENTRAR{RESET}"
                    semaforo = f"{GREEN}VERDE (ENTRADA){RESET}"
                    pending_entries.append({"symbol": norm_sym, "side": side, "entry_price": last_close, "last_st": last_st})

            if "AGUARDAR" not in acao:
                results.append([symbol, f"{GREEN if last_dir == -1 else RED}{'ALTA' if last_dir == -1 else 'BAIXA'}{RESET}", semaforo, acao, f"{last_close:.4f}", st_display, pnl_display])

        except Exception: pass

    sys.stdout.write("\r" + " " * 50 + "\r")
    if results:
        print(tabulate(results, headers=["ATIVO", "TENDÊNCIA", "SEMÁFORO", "AÇÃO", "PREÇO ATUAL", "STOP LOSS (ST)", "PNL (%)"], tablefmt="grid"))
    else:
        print("☕ Sem ações operacionais no momento.")

    print(f"\n✅ Análise concluída em {time.time() - start_time:.2f}s")

    for symbol in pending_exits:
        print(f"\n🔔 Recomendação de Saída: {BOLD}{symbol}{RESET}")
        try:
            val = float(input(f"💰 Qual o valor de Lucro/Prejuízo realizado para {symbol} em USD? (Ex: 5.50 ou -2.10): "))
            port_data["balance"] += val
            positions.pop(symbol)
            print(f"✅ Saldo atualizado: {GREEN}${port_data['balance']:.2f}{RESET}")
        except ValueError:
            print("⚠️ Valor inválido. Posição mantida.")

    if pending_entries:
        print(f"\n💎 Novas Entradas Recomendadas:")
        for entry in pending_entries:
            choice = input(f"❓ Confirmar {BOLD}{entry['symbol']}{RESET} ({entry['side']}) a {entry['entry_price']:.4f}? (s/n): ").lower()
            if choice in ['s', 'y']:
                positions[entry['symbol']] = {"side": entry['side'], "entry_price": entry['entry_price'], "last_st": entry['last_st']}
                print(f"✅ {entry['symbol']} adicionado.")

    save_portfolio(port_data)

if __name__ == "__main__":
    run_scanner()
