import pandas as pd
import numpy as np

def calculate_atr(df, period=15):
    """
    Calculates the Average True Range (ATR) using RMA (Running Moving Average),
    which matches Pine Script's ta.atr behavior.
    """
    high = df['high']
    low = df['low']
    close = df['close']

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Pine Script ta.rma(tr, period) is equivalent to EMA with alpha=1/period
    atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    return atr

def calculate_supertrend(df, period=15, multiplier=1.4):
    """
    Calculates Supertrend matching Pine Script's ta.supertrend(multiplier, period).
    """
    df = df.copy()

    hl2 = (df['high'] + df['low']) / 2
    atr = calculate_atr(df, period)

    basic_ub = hl2 + multiplier * atr
    basic_lb = hl2 - multiplier * atr

    final_ub = np.zeros(len(df))
    final_lb = np.zeros(len(df))
    supertrend = np.zeros(len(df))
    direction = np.zeros(len(df)) # 1 for Up, -1 for Down

    for i in range(len(df)):
        if i == 0 or pd.isna(atr[i]):
            supertrend[i] = np.nan
            final_ub[i] = np.nan
            final_lb[i] = np.nan
            direction[i] = 0
            continue

        # Final Upper Band
        if pd.isna(final_ub[i-1]):
            final_ub[i] = basic_ub[i]
        elif basic_ub[i] < final_ub[i-1] or df['close'][i-1] > final_ub[i-1]:
            final_ub[i] = basic_ub[i]
        else:
            final_ub[i] = final_ub[i-1]

        # Final Lower Band
        if pd.isna(final_lb[i-1]):
            final_lb[i] = basic_lb[i]
        elif basic_lb[i] > final_lb[i-1] or df['close'][i-1] < final_lb[i-1]:
            final_lb[i] = basic_lb[i]
        else:
            final_lb[i] = final_lb[i-1]

        # Supertrend and Direction
        if i == 1 or pd.isna(supertrend[i-1]):
            # Initialization after ATR is available
            supertrend[i] = final_ub[i]
            direction[i] = -1
        elif supertrend[i-1] == final_ub[i-1]:
            if df['close'][i] > final_ub[i]:
                supertrend[i] = final_lb[i]
                direction[i] = 1
            else:
                supertrend[i] = final_ub[i]
                direction[i] = -1
        else: # supertrend[i-1] == final_lb[i-1]
            if df['close'][i] < final_lb[i]:
                supertrend[i] = final_ub[i]
                direction[i] = -1
            else:
                supertrend[i] = final_lb[i]
                direction[i] = 1

    df['supertrend'] = supertrend
    df['direction'] = direction
    return df
