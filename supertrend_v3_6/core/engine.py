import pandas as pd
import numpy as np

def generate_signals(df, max_inertia=3):
    """
    Determines signal states (Verde, Amarelo, Laranja) and inertia exits.

    Verde (ENTRADA VÁLIDA): Signal occurred <= 2 candles ago.
    Amarelo (ZONA DE ATENÇÃO): Trend is still valid, signal > 2 candles ago.
    Laranja (INÉRCIA): Supertrend sideways for max_inertia candles.
    """
    df = df.copy()

    direction = df['direction']
    supertrend = df['supertrend']

    # Identify trend change
    df['trend_change'] = direction != direction.shift()

    # Distance since trend change
    # We can use cumsum on trend_change to group bars and then count within group
    df['trend_group'] = df['trend_change'].cumsum()
    df['bars_since_change'] = df.groupby('trend_group').cumcount()

    # Identify inertia (Supertrend flat)
    df['is_flat'] = supertrend == supertrend.shift()

    # Count consecutive flat bars
    # Using a similar grouping logic for consecutive values
    df['flat_group'] = (supertrend != supertrend.shift()).cumsum()
    df['consecutive_flat'] = df.groupby('flat_group').cumcount()

    # Signal Logic
    df['action'] = "AGUARDAR"
    df['color'] = "CINZA" # Default

    for i in range(len(df)):
        if pd.isna(supertrend[i]) or direction[i] == 0:
            continue

        current_dir = "COMPRA" if direction[i] == 1 else "VENDA"

        # Check Inertia first
        if df['consecutive_flat'][i] >= max_inertia:
            df.at[i, 'action'] = "FECHAR (INÉRCIA)"
            df.at[i, 'color'] = "LARANJA"
            continue

        # Check Signal Age
        if df['bars_since_change'][i] <= 2:
            df.at[i, 'action'] = f"ENTRAR ({current_dir})"
            df.at[i, 'color'] = "VERDE"
        else:
            df.at[i, 'action'] = f"MANTER ({current_dir})"
            df.at[i, 'color'] = "AMARELO"

    return df
