import pandas as pd
import numpy as np

def calculate_supertrend(df, period=15, multiplier=1.4):
    """
    Replicates ta.supertrend(multiplier, period) from Pine Script v5.
    df must have 'high', 'low', 'close' columns.
    """
    high = df['high']
    low = df['low']
    close = df['close']

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

    basic_ub_v = basic_ub.values
    basic_lb_v = basic_lb.values
    close_v = close.values

    for i in range(len(df)):
        if i == 0:
            final_ub[i] = basic_ub_v[i]
            final_lb[i] = basic_lb_v[i]
        else:
            if basic_ub_v[i] < final_ub[i-1] or close_v[i-1] > final_ub[i-1]:
                final_ub[i] = basic_ub_v[i]
            else:
                final_ub[i] = final_ub[i-1]

            if basic_lb_v[i] > final_lb[i-1] or close_v[i-1] < final_lb[i-1]:
                final_lb[i] = basic_lb_v[i]
            else:
                final_lb[i] = final_lb[i-1]

    direction = np.ones(len(df))
    supertrend = np.zeros(len(df))

    for i in range(1, len(df)):
        if direction[i-1] == -1:
            if close_v[i] < final_lb[i]:
                direction[i] = 1
                supertrend[i] = final_ub[i]
            else:
                direction[i] = -1
                supertrend[i] = final_lb[i]
        else:
            if close_v[i] > final_ub[i]:
                direction[i] = -1
                supertrend[i] = final_lb[i]
            else:
                direction[i] = 1
                supertrend[i] = final_ub[i]

    supertrend[:period] = np.nan
    direction[:period] = 0

    return pd.Series(supertrend, index=df.index), pd.Series(direction, index=df.index)

def generate_signals(df, supertrend, direction, max_inertia=3):
    """
    Generates signals based on Supertrend and Inertia logic.
    """
    df = df.copy()
    df['supertrend'] = supertrend
    df['direction'] = direction
    df['trend'] = df['direction'].apply(lambda x: 1 if x == -1 else -1)

    df['buy_signal'] = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    df['sell_signal'] = (df['trend'] == -1) & (df['trend'].shift(1) == 1)

    barras_desde_sinal = np.zeros(len(df))
    count = 100
    for i in range(len(df)):
        if df['buy_signal'].iloc[i] or df['sell_signal'].iloc[i]:
            count = 0
        else:
            count += 1
        barras_desde_sinal[i] = count
    df['barras_desde_sinal'] = barras_desde_sinal

    change_supertrend = df['supertrend'].diff()
    contagem_inercia = np.zeros(len(df))
    count_inercia = 0
    for i in range(len(df)):
        if change_supertrend.iloc[i] == 0:
            count_inercia += 1
        else:
            count_inercia = 0
        contagem_inercia[i] = count_inercia
    df['contagem_inercia'] = contagem_inercia

    def get_semaforo(row):
        if row['contagem_inercia'] >= max_inertia:
            return "LARANJA (INÉRCIA)"
        elif row['barras_desde_sinal'] <= 2:
            return "VERDE (ENTRADA VÁLIDA)"
        else:
            return "AMARELO (ATENÇÃO)"

    df['semaforo'] = df.apply(get_semaforo, axis=1)

    def get_action(row):
        if row['contagem_inercia'] >= max_inertia:
            return "FECHAR (INÉRCIA)"
        if row['barras_desde_sinal'] <= 2:
            return "ENTRAR" if row['trend'] == 1 else "VENDER"
        return "AGUARDAR"

    df['acao'] = df.apply(get_action, axis=1)

    return df
