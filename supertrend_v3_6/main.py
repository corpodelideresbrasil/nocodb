import os
import sys
import json
import pandas as pd
import numpy as np
from tabulate import tabulate
import ccxt
import time

# ==============================================================================
# SUPERTREND V3.6 - VERSÃO GESTÃO ROBUSTA E PERSISTENTE (FINAL)
# ==============================================================================

# Cores ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
ORANGE = "\033[38;5;208m"
BOLD = "\033[1m"
RESET = "\033[0m"

def normalize_symbol(symbol):
    """ Remove barras e padroniza para uppercase """
    if not symbol: return ""
    return symbol.replace("/", "").replace("-", "").replace("_", "").upper().strip()

def get_portfolio_path():
    """ Retorna o caminho absoluto do portfolio.json """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "portfolio.json")

def load_portfolio():
    path = get_portfolio_path()
    default_data = {"balance": 160.0, "positions": {}}

    if not os.path.exists(path):
        print(f"ℹ️ Criando novo arquivo de portfolio em: {path}")
        return default_data

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw: return default_data
            data = json.loads(raw)

            # Garantir campos obrigatórios
            if "balance" not in data: data["balance"] = 160.0
            if "positions" not in data: data["positions"] = {}

            # Normalização de chaves para evitar duplicidade
            clean_positions = {}
            for k, v in data["positions"].items():
                clean_positions[normalize_symbol(k)] = v
            data["positions"] = clean_positions

            print(f"✅ Portfolio carregado com sucesso ({len(clean_positions)} ativos).")
            return data
    except Exception as e:
        print(f"⚠️ Erro ao ler portfolio.json: {e}")
        return default_data

def save_portfolio(data):
    """ Gravação atômica para evitar perda de dados """
    path = get_portfolio_path()
    try:
        # Normalização de segurança antes de gravar
        clean_positions = {}
        for k, v in data["positions"].items():
            clean_positions[normalize_symbol(k)] = v
        data["positions"] = clean_positions

        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
    except Exception as e:
        print(f"❌ {RED}ERRO CRÍTICO AO SALVAR PORTFOLIO:{RESET} {e}")

def fetch_ohlcv(exchange, symbol, timeframe='4h', limit=500):
    try:
        clean_symbol = normalize_symbol(symbol)
        ohlcv = exchange.fetch_ohlcv(clean_symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        # ESTABILIDADE: Ignora a vela atual (que ainda está mudando)
        return df.iloc[:-1]
    except Exception as e: raise Exception(f"{e}")

def calculate_supertrend(df, period=15, multiplier=1.4):
    """ Cálculo do Supertrend (Paridade Pine Script v5) """
    high, low, close = df['high'].values, df['low'].values, df['close'].values
    tr = np.zeros(len(df))
    tr[0] = high[0] - low[0]
    tr[1:] = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))

    atr = np.zeros(len(df))
    alpha = 1 / period
    atr[0] = np.mean(tr[:period])
    for i in range(1, len(df)):
        atr[i] = (tr[i] * alpha) + (atr[i-1] * (1 - alpha))

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

def print_table(results, title="RESULTADOS"):
    headers = ["ATIVO", "TENDÊNCIA", "SEMÁFORO", "AÇÃO", "PREÇO ATUAL", "STOP LOSS (ST)", "PNL (%)"]
    print(f"\n--- {BOLD}{title}{RESET} ---")
    if results:
        print(tabulate(results, headers=headers, tablefmt="grid"))
    else:
        print("Nenhuma ação recomendada.")

def run_scanner():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "assets.json")
    if not os.path.exists(config_path):
        print(f"❌ Erro: assets.json não encontrado.")
        return

    with open(config_path, "r") as f:
        assets = json.load(f).get("assets", [])

    port_data = load_portfolio()

    try:
        exchange = ccxt.binance({'options': {'defaultType': 'future'}})
        exchange.fetch_ohlcv('BTCUSDT', limit=1)
    except:
        exchange = ccxt.kraken()

    print(f"\n🚀 {BOLD}SUPERTREND V3.6{RESET} | SALDO: {GREEN}${port_data['balance']:.2f}{RESET}")
    print(f"Fonte: {exchange.id.upper()} | Timeframe: 4h (Estabilidade Total)\n")

    analysis_results = []
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
            side = "LONG" if last_dir == -1 else "SHORT"

            # Inércia: exatos 3 períodos flat
            c_inercia = 0
            for k in range(1, 5):
                if abs(st[-k] - st[-k-1]) < 1e-10: c_inercia += 1
                else: break

            # Fresh Signal
            b_desde_sinal = 0
            for k in range(1, 20):
                if direction[-k] == direction[-k-1]: b_desde_sinal += 1
                else: break

            is_active = norm_sym in port_data["positions"]
            acao, semaforo, pnl_display = "AGUARDAR", "AMARELO", "-"
            st_display = f"{last_st:.4f}"

            if is_active:
                pos = port_data["positions"][norm_sym]
                pnl = (last_close/pos['entry_price'] - 1)*100 if pos['side']=="LONG" else (pos['entry_price']/last_close - 1)*100
                pnl_display = f"{GREEN if pnl > 0 else RED}{pnl:+.2f}%{RESET}"

                if c_inercia >= 3 or side != pos['side']:
                    acao, semaforo = f"{BOLD}{RED}FECHAR{RESET}", f"{ORANGE}LARANJA (INÉRCIA){RESET}"
                    st_display = f"{RED}{last_st:.4f}{RESET}"
                    pending_exits.append(norm_sym)
                else:
                    acao, semaforo = f"{BOLD}{GREEN}MANTER{RESET}", f"{YELLOW}AMARELO{RESET}"
                    old_st = pos['last_st']
                    st_color = GREEN if (pos['side']=="LONG" and last_st > old_st+1e-10) or (pos['side']=="SHORT" and last_st < old_st-1e-10) else (RED if abs(last_st-old_st)>1e-10 else RESET)
                    st_display = f"{st_color}{last_st:.4f}{RESET}"
                    pos['last_st'] = last_st # Update memory
            else:
                if c_inercia < 3:
                    if b_desde_sinal <= 2:
                        acao, semaforo = f"{BOLD}{GREEN}ENTRAR{RESET}", f"{GREEN}VERDE{RESET}"
                        type_str = "RECOMENDADO"
                    else:
                        acao, semaforo = f"{BOLD}{YELLOW}ENTRAR (OPCIONAL){RESET}", f"{YELLOW}AMARELO{RESET}"
                        type_str = "OPCIONAL"

                    st_display = f"{last_st:.4f}"
                    pending_entries.append({"symbol": norm_sym, "side": side, "entry_price": last_close, "last_st": last_st, "type": type_str})

            if "AGUARDAR" not in acao:
                analysis_results.append([symbol, f"{GREEN if last_dir == -1 else RED}{'ALTA' if last_dir == -1 else 'BAIXA'}{RESET}", semaforo, acao, f"{last_close:.4f}", st_display, pnl_display])
        except Exception: pass

    sys.stdout.write("\r" + " " * 50 + "\r")
    print_table(analysis_results, "AÇÕES RECOMENDADAS")
    print(f"\n✅ Análise concluída em {time.time() - start_time:.2f}s")

    # --- PROCESSAMENTO ---
    for symbol in pending_exits:
        print(f"\n🔔 Recomendação de Saída: {BOLD}{symbol}{RESET}")
        try:
            val_in = input(f"💰 Lucro/Prejuízo realizado para {symbol} em USD (Ex: 5.5 ou -2.1) [Enter p/ pular]: ")
            if val_in.strip():
                port_data["balance"] += float(val_in)
                if symbol in port_data["positions"]: del port_data["positions"][symbol]
                save_portfolio(port_data) # Salva agora
                print(f"✅ {symbol} removido.")
            else: print("⚠️ Posição mantida.")
        except: print("⚠️ Valor inválido.")

    if pending_entries:
        print(f"\n💎 Novas Oportunidades:")
        for entry in pending_entries:
            choice = input(f"❓ Confirmar entrada em {BOLD}{entry['symbol']}{RESET} [{entry['type']}] ({entry['side']})? (s/n): ").lower()
            if choice in ['s', 'y']:
                port_data["positions"][entry['symbol']] = {
                    "side": entry['side'],
                    "entry_price": entry['entry_price'],
                    "last_st": entry['last_st']
                }
                save_portfolio(port_data) # Salva agora
                print(f"✅ {entry['symbol']} adicionado.")

    # SalvaTrailing Stops das posições que ficaram
    save_portfolio(port_data)

    # REPUBLICAÇÃO DA TABELA FINAL
    print("\n" + "="*70)
    print(f"💼 {BOLD}ESTADO FINAL DA CARTEIRA{RESET} | SALDO ATUALIZADO: {GREEN}${port_data['balance']:.2f}{RESET}")
    final_view = []
    # Recarrega para prova real
    final_data = load_portfolio()
    for sym, pos in final_data["positions"].items():
        final_view.append([sym, f"{GREEN if pos['side']=='LONG' else RED}{pos['side']}{RESET}", "-", f"{BOLD}{GREEN}POSIÇÃO ATIVA{RESET}", f"{pos['entry_price']:.4f}", f"{pos['last_st']:.4f}", "-"])

    if final_view:
        print_table(final_view, "CARTEIRA ATUALIZADA")
    else:
        print("\n📭 Nenhuma posição aberta.")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_scanner()
