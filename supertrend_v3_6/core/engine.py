import pandas as pd
import numpy as np

def generate_signals(df, supertrend, direction, max_inertia=3):
    """
    Generates signals based on Supertrend and Inertia logic.
    """
    df = df.copy()
    df['supertrend'] = supertrend
    df['direction'] = direction # -1 for Up, 1 for Down

    # trend = direction < 0 ? 1 : -1 (Pine Script)
    # So trend = 1 for Up, -1 for Down
    df['trend'] = df['direction'].apply(lambda x: 1 if x == -1 else -1)

    # barrasDesdeSinal
    df['buy_signal'] = (df['trend'] == 1) & (df['trend'].shift(1) == -1)
    df['sell_signal'] = (df['trend'] == -1) & (df['trend'].shift(1) == 1)

    barras_desde_sinal = np.zeros(len(df))
    count = 100 # start with large number
    for i in range(len(df)):
        if df['buy_signal'].iloc[i] or df['sell_signal'].iloc[i]:
            count = 0
        else:
            count += 1
        barras_desde_sinal[i] = count
    df['barras_desde_sinal'] = barras_desde_sinal

    # Lógica de Inércia
    # contagemInercia := (ta.change(supertrend) == 0) ? contagemInercia + 1 : 0
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

    # Semáforo
    # semaforo = (contagemInercia >= maxInertia) ? 3 : (barrasDesdeSinal <= 2) ? 1 : ((trend == 1 or trend == -1) ? 2 : 0)
    def get_semaforo(row):
        if row['contagem_inercia'] >= max_inertia:
            return "LARANJA (INÉRCIA)"
        elif row['barras_desde_sinal'] <= 2:
            return "VERDE (ENTRADA VÁLIDA)"
        else:
            return "AMARELO (ATENÇÃO)"

    df['semaforo'] = df.apply(get_semaforo, axis=1)

    # Ação
    def get_action(row):
        if row['contagem_inercia'] >= max_inertia:
            return "FECHAR (INÉRCIA)"
        if row['barras_desde_sinal'] <= 2:
            return "ENTRAR" if row['trend'] == 1 else "VENDER"
        return "AGUARDAR"

    df['acao'] = df.apply(get_action, axis=1)

    return df
