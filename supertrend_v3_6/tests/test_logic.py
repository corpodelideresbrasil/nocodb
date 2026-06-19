import pandas as pd
import numpy as np
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from core.calculator import calculate_supertrend
from core.engine import generate_signals

def create_mock_data():
    """
    Creates mock OHLCV data that simulates a trend change and then a flat supertrend.
    """
    data = {
        'high':  [10, 11, 12, 13, 14, 15, 16, 16, 16, 16, 16, 16, 16, 16, 16],
        'low':   [ 9, 10, 11, 12, 13, 14, 15, 15, 15, 15, 15, 15, 15, 15, 15],
        'close': [9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5, 15.5]
    }
    return pd.DataFrame(data)

def test_logic():
    print("Testing Supertrend and Signal Logic...")
    df = create_mock_data()

    # Calculate Supertrend
    df = calculate_supertrend(df, period=3, multiplier=1.0)

    # Manually force supertrend to be flat for testing inertia
    df.loc[10:, 'supertrend'] = df.loc[10, 'supertrend']

    # Generate Signals
    df = generate_signals(df, max_inertia=3)

    print("\nResults:")
    print(df[['close', 'supertrend', 'direction', 'action', 'color', 'consecutive_flat']])

    # Simple assertions
    assert 'action' in df.columns
    assert 'color' in df.columns

    # In this mock data, after some bars the Supertrend should become flat
    assert "LARANJA" in df['color'].values, "Expected LARANJA color to be present in the results"
    assert df['color'].iloc[-1] == "LARANJA"

    print("\nTests Passed!")

if __name__ == "__main__":
    test_logic()
