import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.provider import fetch_multiple_ohlcv
from core.calculator import calculate_supertrend
from core.engine import generate_signals
from config import settings
from tabulate import tabulate

def run_scanner():
    print("=== Supertrend v3.6 Scanner ===")
    print(f"Timeframe: {settings.TIMEFRAME}")
    print(f"ATR: {settings.ATR_PERIOD}, Mult: {settings.ATR_MULTIPLIER}, Max Inertia: {settings.MAX_INERTIA}")
    print("-" * 30)

    symbols = settings.SYMBOLS
    data = fetch_multiple_ohlcv(symbols, timeframe=settings.TIMEFRAME, limit=100)

    results = []

    for symbol, df in data.items():
        # Calculate Indicators
        df = calculate_supertrend(df, period=settings.ATR_PERIOD, multiplier=settings.ATR_MULTIPLIER)

        # Generate Signals
        df = generate_signals(df, max_inertia=settings.MAX_INERTIA)

        # Get last candle result
        last_row = df.iloc[-1]

        results.append([
            symbol,
            last_row['action'],
            last_row['color'],
            f"{last_row['close']:.4f}",
            f"{last_row['supertrend']:.4f}"
        ])

    headers = ["TICKER", "AÇÃO", "COR", "PREÇO", "SUPERTREND"]
    print(tabulate(results, headers=headers, tablefmt="grid"))

if __name__ == "__main__":
    run_scanner()
