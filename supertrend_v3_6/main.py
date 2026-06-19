import os
import sys
import json
import pandas as pd
import numpy as np
from tabulate import tabulate
import ccxt
import time

# ==============================================================================
# SUPERTREND V3.6 - VERSÃO GESTÃO INTERATIVA E FINANCEIRA (CORREÇÃO FINAL)
# ==============================================================================

# Cores ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def normalize_symbol(symbol):
    if not symbol: return ""
    return symbol.replace("/", "").replace("-", "").replace("_", "").upper().strip()

def get_portfolio_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "portfolio.json")

def load_portfolio():
    path = get_portfolio_path()
    default_data = {"balance": 160.0, "positions": {}}
    if not os.path.exists(path): return default_data
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "balance" not in data: data["balance"] = 160.0
            if "positions" not in data: data["positions"] = {}
            clean_pos = {normalize_symbol(k): v for k, v in data["positions"].items()}
            data["positions"] = clean_pos
            return data
    except: return default_data

def save_portfolio(data):
    path = get_portfolio_path()
    try:
        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
    except Exception as e: print(f"❌ Erro ao salvar portfolio: {e}")

def fetch_ohlcv(exchange, symbol, timeframe='4h', limit=1000):
    try:
        clean_symbol = normalize_symbol(symbol)
        ohlcv = exchange.fetch_ohlcv(clean_symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df.iloc[:-1]
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

def format_pnl(val):
    if val == "-": return "-"
    color = GREEN if val >= 0 else RED
    return f"{color}{val:+.2f}%{RESET}"

def run_scanner():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "assets.json")
    if not os.path.exists(config_path):
        print("❌ assets.json não encontrado.")
        return
    with open(config_path, "r") as f: assets = json.load(f).get("assets", [])

    port_data = load_portfolio()
    positions = port_data["positions"]

    try:
        exchange = ccxt.binance({'options': {'defaultType': 'future'}})
        exchange.fetch_ohlcv('BTCUSDT', limit=1)
    except:
        exchange = ccxt.kraken()

    print(f"\n🚀 {BOLD}SUPERTREND V3.6{RESET} | SALDO: {GREEN}${port_data['balance']:.2f}{RESET}")
    print(f"Fonte: {exchange.id.upper()} | Timeframe: 4h\n")

    analysis_results = []
    pending_entries = []
    pending_exits = []
    current_prices = {}
    start_time = time.time()

    idx = 1
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
            current_prices[norm_sym] = last_close

            c_inercia = 0
            for k in range(1, 10):
                if abs(st[-k] - st[-k-1]) < 1e-10: c_inercia += 1
                else: break

            b_desde_sinal = 0
            for k in range(1, 20):
                if direction[-k] == direction[-k-1]: b_desde_sinal += 1
                else: break

            is_active = norm_sym in positions
            acao, semaforo, pnl_val = "AGUARDAR", "AMARELO", "-"
            st_display = f"{last_st:.4f}"

            if is_active:
                pos = positions[norm_sym]
                pnl_val = (last_close/pos['entry_price'] - 1)*100 if pos['side']=="LONG" else (1 - last_close/pos['entry_price'])*100

                if c_inercia >= 3 or (last_dir == -1 and pos['side'] == "SHORT") or (last_dir == 1 and pos['side'] == "LONG"):
                    acao, semaforo = f"{BOLD}{RED}FECHAR{RESET}", f"{ORANGE}LARANJA (INÉRCIA){RESET}"
                    st_display = f"{RED}{last_st:.4f}{RESET}"
                    pending_exits.append(norm_sym)
                else:
                    acao, semaforo = f"{BOLD}{GREEN}MANTER{RESET}", f"{YELLOW}AMARELO{RESET}"
                    old_st = pos.get('last_st', last_st)
                    st_color = GREEN if (pos['side']=="LONG" and last_st > old_st+1e-10) or (pos['side']=="SHORT" and last_st < old_st-1e-10) else (RED if abs(last_st-old_st)>1e-10 else RESET)
                    st_display = f"{st_color}{last_st:.4f}{RESET}"
                    pos['last_st'] = last_st
            else:
                if c_inercia < 3:
                    if b_desde_sinal <= 2:
                        acao, semaforo = f"{BOLD}{GREEN}ENTRAR{RESET}", f"{GREEN}VERDE{RESET}"
                        type_str = "RECOMENDADO"
                    else:
                        acao, semaforo = f"{BOLD}{YELLOW}ENTRAR (OPCIONAL){RESET}", f"{YELLOW}AMARELO{RESET}"
                        type_str = "OPCIONAL"

                    st_display = f"{last_st:.4f}"
                    pending_entries.append({"symbol": norm_sym, "side": "LONG" if last_dir == -1 else "SHORT", "entry_price": last_close, "last_st": last_st, "type": type_str, "display_name": symbol})

            if "AGUARDAR" not in acao:
                analysis_results.append([idx, symbol, f"{GREEN if last_dir == -1 else RED}{'ALTA' if last_dir == -1 else 'BAIXA'}{RESET}", semaforo, acao, f"{last_close:.4f}", st_display, format_pnl(pnl_val)])
                idx += 1
        except Exception: pass

    sys.stdout.write("\r" + " " * 50 + "\r")
    headers = ["#", "ATIVO", "TENDÊNCIA", "SEMÁFORO", "AÇÃO", "PREÇO ATUAL", "STOP LOSS (ST)", "PNL %"]
    print(f"--- {BOLD}AÇÕES RECOMENDADAS{RESET} ---")
    if analysis_results:
        print(tabulate(analysis_results, headers=headers, tablefmt="grid"))
    else:
        print("☕ Nenhuma ação operacional recomendada no momento.")

    print(f"\n✅ Análise concluída em {time.time() - start_time:.2f}s")

    # --- SAÍDAS ---
    for symbol in pending_exits:
        print(f"\n🔔 Recomendação de Saída: {BOLD}{symbol}{RESET}")
        try:
            val_in = input(f"💰 Lucro/Prejuízo para {symbol} em USD [Enter p/ pular]: ")
            if val_in.strip():
                port_data["balance"] += float(val_in)
                if symbol in positions: del positions[symbol]
                print(f"✅ {symbol} removido.")
        except: pass

    # --- ENTRADAS (NUMERADO) ---
    if pending_entries:
        entry_map = {str(row[0]): normalize_symbol(row[1]) for row in analysis_results if "ENTRAR" in row[4]}
        if entry_map:
            print(f"\n💎 {BOLD}Confirmar Novas Entradas:{RESET}")
            print("Digite os números das linhas separados por espaço e pressione Enter. '0' para sair.")
            try:
                line = input("👉 Números: ").strip()
                if line and line != "0":
                    for c in line.split():
                        if c in entry_map:
                            asset_norm = entry_map[c]
                            e = next((item for item in pending_entries if item['symbol'] == asset_norm), None)
                            if e:
                                confirm = input(f"   Confirmar {BOLD}{e['display_name']}{RESET} ({e['side']})? (s/n): ").lower()
                                if confirm in ['s', 'y']:
                                    positions[e['symbol']] = {"side": e['side'], "entry_price": e['entry_price'], "last_st": e['last_st'], "is_new": True}
                                    print(f"   ✅ {e['display_name']} adicionado.")
            except: pass

    save_portfolio(port_data)

    # --- REPUBLICAÇÃO ---
    print("\n" + "="*85)
    print(f"💼 {BOLD}ESTADO ATUALIZADO DA CARTEIRA{RESET} | SALDO ATUAL: {GREEN}${port_data['balance']:.2f}{RESET}")
    final_rows = []
    # Recarrega para limpar flags
    final_state = load_portfolio()
    for sym, pos in final_state["positions"].items():
        price = current_prices.get(sym, pos['entry_price'])
        pnl = (price/pos['entry_price'] - 1)*100 if pos['side']=="LONG" else (1 - price/pos['entry_price'])*100
        status_label = f"{BOLD}{GREEN}NOVA ENTRADA{RESET}" if pos.get('is_new') else f"{BOLD}{CYAN}MANTIDA{RESET}"
        final_rows.append([sym, pos['side'], "-", status_label, f"{price:.4f}", f"{pos['last_st']:.4f}", format_pnl(pnl)])

    if final_rows:
        print(tabulate(final_rows, headers=headers[1:], tablefmt="grid"))

    # Limpeza SEGURA da flag is_new (sem mudar tamanho do dict no loop do scanner)
    for sym in list(port_data["positions"].keys()):
        if "is_new" in port_data["positions"][sym]:
            del port_data["positions"][sym]["is_new"]
    save_portfolio(port_data)
    print("="*85 + "\n")

if __name__ == "__main__":
    run_scanner()
