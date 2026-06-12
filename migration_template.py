import pandas as pd
import numpy as np

def calculate_raul_lateralidade(df, len_curta=9, len_longa=21, lookback=7,
                                thr_flat=1.1, thr_squeeze=0.5, thr_barcode=6,
                                hold_consolid=3):
    """
    Traduz a lógica do Pine Script 'Raul Lateralidade v3.4' para Python usando Pandas.
    """

    # 1. Cálculos de Médias e ATR
    # Nota: Em Python (Pandas), usamos window=len e min_periods para alinhar com o Pine Script
    df['sma_curta'] = df['close'].rolling(window=len_curta).mean()
    df['sma_longa'] = df['close'].rolling(window=len_longa).mean()

    # Cálculo do ATR simplificado (Wilder's Smoothing no Pine Script)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['atr'] = true_range.rolling(window=lookback).mean()

    # 2. Detecção de Lateralidade

    # 2.1 Horizontalidade (Slope da SMA Curta)
    # math.abs(smaCurta - smaCurta[5]) / atr
    df['sma_slope'] = np.abs(df['sma_curta'] - df['sma_curta'].shift(5)) / df['atr']
    df['is_flat_sma'] = df['sma_slope'] < (thr_flat / 4)

    # 2.2 Squeeze (Médias Próximas)
    # math.abs(smaCurta - smaLonga) / atr
    df['avg_dist'] = np.abs(df['sma_curta'] - df['sma_longa']) / df['atr']
    df['is_squeezed'] = df['avg_dist'] < (thr_squeeze / 2)

    # 2.3 Código de Barras (Trocas de Cor de Candle)
    # Replicamos o loop do Pine com operações vetorizadas
    df['candle_color'] = np.where(df['close'] > df['open'], 1, -1)
    # Detecta se a cor mudou em relação ao candle anterior
    df['color_change'] = (df['candle_color'] != df['candle_color'].shift()).astype(int)
    # Soma as trocas de cor no lookback
    df['color_change_count'] = df['color_change'].rolling(window=lookback).sum()
    df['is_barcode'] = df['color_change_count'] >= thr_barcode

    # 3. Lógica de Persistência (Histerese)
    df['is_consolid_instant'] = df['is_flat_sma'] | df['is_squeezed'] | df['is_barcode']

    # Simula o contador 'barsSinceConsolid'
    # Esta parte é imperativa no Pine, aqui usamos uma lógica de preenchimento para frente
    df['is_consolid'] = False
    for i in range(len(df)):
        if df.loc[df.index[i], 'is_consolid_instant']:
            # Se for consolidado, marca as próximas 'hold_consolid' barras também
            for j in range(0, hold_consolid + 1):
                if i + j < len(df):
                    df.loc[df.index[i+j], 'is_consolid'] = True

    # 4. Sinais de Entrada
    df['long_cond'] = (df['sma_curta'] > df['sma_longa']) & \
                      (df['close'] > df['sma_curta']) & \
                      (~df['is_consolid'])

    df['short_cond'] = (df['sma_curta'] < df['sma_longa']) & \
                       (df['close'] < df['sma_curta']) & \
                       (~df['is_consolid'])

    return df

if __name__ == "__main__":
    # Exemplo de criação de dados fictícios para teste de sintaxe
    data = {
        'open': np.random.random(50),
        'high': np.random.random(50) + 1,
        'low': np.random.random(50) - 1,
        'close': np.random.random(50)
    }
    df_test = pd.DataFrame(data)
    result = calculate_raul_lateralidade(df_test)
    print("Migração concluída. Colunas geradas:")
    print(result.columns)
    print("\nÚltimos 5 sinais de Long:")
    print(result['long_cond'].tail())
