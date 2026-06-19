import sys
import os

# Add the script's directory to the search path explicitly at the beginning
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import pandas as pd
from tabulate import tabulate

try:
    from data.provider import fetch_ohlcv
    from core.calculator import calculate_supertrend
    from core.engine import generate_signals
except ImportError as e:
    print(f"Erro de importação: {e}")
    print(f"Path atual: {sys.path}")
    print(f"Diretório do script: {script_dir}")
    print("Tentando alternativa...")
    # Tentativa de fallback caso seja executado de fora da pasta
    sys.path.append(os.path.join(script_dir, '..'))
    from supertrend_v3_6.data.provider import fetch_ohlcv
    from supertrend_v3_6.core.calculator import calculate_supertrend
    from supertrend_v3_6.core.engine import generate_signals

def run_scanner(symbols, timeframe='1h'):
    results = []

    print(f"Scanning {len(symbols)} assets on {timeframe} timeframe...")

    for symbol in symbols:
        try:
            # Fetch data
            df = fetch_ohlcv(symbol, timeframe=timeframe)

            # Calculate Supertrend
            supertrend, direction = calculate_supertrend(df)

            # Generate Signals
            df_signals = generate_signals(df, supertrend, direction)

            # Get last row for current status
            last_row = df_signals.iloc[-1]

            results.append([
                symbol,
                "COMPRA" if last_row['trend'] == 1 else "VENDA",
                last_row['semaforo'],
                last_row['acao'],
                f"{last_row['close']:.2f}"
            ])
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            results.append([symbol, "ERROR", "-", "-", "-"])

    headers = ["ATIVO", "TENDÊNCIA", "SEMÁFORO", "AÇÃO", "PREÇO ATUAL"]
    print("\n" + tabulate(results, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    # Example assets
    assets = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "ADA/USDT"]
    run_scanner(assets)
