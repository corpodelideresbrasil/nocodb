import pandas as pd
import numpy as np

def calculate_supertrend(df, period=15, multiplier=1.4):
    """
    Replicates ta.supertrend(multiplier, period) from Pine Script v5.
    df must have 'high', 'low', 'close' columns.

    Returns:
    - supertrend (pd.Series)
    - direction (pd.Series): -1 for up trend, 1 for down trend
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # ATR calculation (RMA - Running Moving Average)
    # Pine Script ta.rma(tr, period) = alpha=1/period ewm
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)

    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

    hl2 = (high + low) / 2

    basic_ub = hl2 + multiplier * atr
    basic_lb = hl2 - multiplier * atr

    final_ub = np.zeros(len(df))
    final_lb = np.zeros(len(df))

    # Use values to avoid slow iloc if possible, but for simplicity:
    basic_ub_v = basic_ub.values
    basic_lb_v = basic_lb.values
    close_v = close.values

    for i in range(len(df)):
        if i == 0:
            final_ub[i] = basic_ub_v[i]
            final_lb[i] = basic_lb_v[i]
        else:
            # Final Upper Band
            if basic_ub_v[i] < final_ub[i-1] or close_v[i-1] > final_ub[i-1]:
                final_ub[i] = basic_ub_v[i]
            else:
                final_ub[i] = final_ub[i-1]

            # Final Lower Band
            if basic_lb_v[i] > final_lb[i-1] or close_v[i-1] < final_lb[i-1]:
                final_lb[i] = basic_lb_v[i]
            else:
                final_lb[i] = final_lb[i-1]

    # Direction and Supertrend
    direction = np.ones(len(df)) # 1 for down, -1 for up
    supertrend = np.zeros(len(df))

    for i in range(1, len(df)):
        if direction[i-1] == -1: # Up trend
            if close_v[i] < final_lb[i]:
                direction[i] = 1 # Switch to Down
                supertrend[i] = final_ub[i]
            else:
                direction[i] = -1 # Stay Up
                supertrend[i] = final_lb[i]
        else: # Down trend
            if close_v[i] > final_ub[i]:
                direction[i] = -1 # Switch to Up
                supertrend[i] = final_lb[i]
            else:
                direction[i] = 1 # Stay Down
                supertrend[i] = final_ub[i]

    # Handle initial values where ATR is not yet calculated
    supertrend[:period] = np.nan
    direction[:period] = 0

    return pd.Series(supertrend, index=df.index), pd.Series(direction, index=df.index)
