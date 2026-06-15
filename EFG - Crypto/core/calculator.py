import pandas as pd
import numpy as np

class MPRMCalculator:
    """
    Calculadora matemática para o Market Physics Regime Model (V14.1).
    Responsável por traduzir a termodinâmica de preço e cadeias de Markov.
    Nativa: Não depende de pandas_ta para compatibilidade com Python 3.14+.
    """

    def __init__(self, markov_len=20):
        self.markov_len = markov_len

    def _ema(self, series, length):
        """Implementação nativa de EMA via Pandas EWM."""
        return series.ewm(span=length, adjust=False).mean()

    def _atr(self, df, length):
        """Implementação nativa de ATR (Wilder's Smoothing)."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.ewm(alpha=1/length, min_periods=length, adjust=False).mean()

    def calculate_physics(self, df):
        """
        Calcula as forças físicas baseadas em F=m.a (Módulo 1 - Refinado).
        - Massa (m) = Volume Normalizado
        - Aceleração (a) = Trabalho do Preço (Body Work)
        """
        # Massa (m): Volume relativo à média (Inércia)
        df['vol_ema'] = self._ema(df['volume'], self.markov_len)
        df['mass'] = (df['volume'] / df['vol_ema']).replace([np.inf, -np.inf], 1.0).fillna(1.0)

        # Trabalho/Aceleração (a)
        df['body_work'] = np.abs(df['close'] - df['open'])

        # Força Aplicada (F = m * a)
        # Se a massa for baixa (volume baixo), mesmo um movimento grande tem pouca força.
        # Se a massa for alta, pequenos movimentos carregam muita energia cinética.
        df['f_bull_i'] = np.where(df['close'] > df['open'], df['mass'] * df['body_work'], 0.0)
        df['f_bear_i'] = np.where(df['close'] < df['open'], df['mass'] * df['body_work'], 0.0)

        # Compressão (Referenciada ao ATR recente) - "Energia Potencial Elástica"
        df['atr_ref'] = self._atr(df, self.markov_len)
        df['f_comp_i'] = (df['atr_ref'] - (df['high'] - df['low'])).clip(lower=0.0)
        # Aplicamos massa à compressão: compressão com alto volume = mola muito tensionada
        df['f_comp_i'] = df['f_comp_i'] * df['mass']

        # Exaustão (Wicks vs Body)
        df['wicks'] = (df['high'] - df[['open', 'close']].max(axis=1)) + \
                      (df[['open', 'close']].min(axis=1) - df['low'])
        df['f_exh_i'] = np.where(df['wicks'] > (df['body_work'] * 2.0), df['wicks'], 0.0)

        # Normalização Instantânea (O "Agora")
        df['total_i'] = df['f_bull_i'] + df['f_bear_i'] + df['f_comp_i'] + df['f_exh_i']

        # Probabilidades Instantâneas
        for col in ['bull', 'bear', 'comp', 'exh']:
            df[f'p_{col}_i'] = np.where(df['total_i'] > 0, df[f'f_{col}_i'] / df['total_i'], 0.25)

        # Atrito Estático/Ruído: Média da volatilidade das energias
        # Define o nível de força necessária para "romper o ruído"
        df['noise_floor'] = self._ema(df['total_i'], self.markov_len) * 0.5

        return df

    def calculate_markov(self, df):
        """
        Suavização de Estados via Cadeia de Markov (Módulo 2 do Manual).
        """
        # Suavização via EMA
        for col in ['bull', 'bear', 'comp', 'exh']:
            df[f'p_{col}'] = self._ema(df[f'p_{col}_i'], self.markov_len)

        # Normalização Final da Cadeia
        df['sum_markov'] = df[['p_bull', 'p_bear', 'p_comp', 'p_exh']].sum(axis=1)

        for col in ['bull', 'bear', 'comp', 'exh']:
            df[f'p_{col}'] = np.where(df['sum_markov'] <= 0, 0.25, df[f'p_{col}'] / df['sum_markov'])

        return df

    def identify_regime(self, df):
        """
        Identifica o Regime e o Estado Dinâmico (Módulo 3 do Manual).
        """
        # Regime Dominante
        df['max_p'] = df[['p_bull', 'p_bear', 'p_comp', 'p_exh']].max(axis=1)

        conditions = [
            (df['max_p'] == df['p_bull']),
            (df['max_p'] == df['p_bear']),
            (df['max_p'] == df['p_comp']),
            (df['max_p'] == df['p_exh'])
        ]
        choices = [0, 1, 2, 3] # BULL, BEAR, COMP, EXH
        df['regime'] = np.select(conditions, choices, default=3)

        # Estado Dinâmico (Expansion, Contraction, Exhaustion)
        df['trend_energy'] = df['p_bull'] + df['p_bear']
        df['equilibrium_energy'] = df['p_comp'] + df['p_exh']

        dyn_conditions = [
            (df['trend_energy'] > df['equilibrium_energy']),
            (df['p_comp'] > df['p_exh'])
        ]
        dyn_choices = ["EXPANSION", "CONTRACTION"]
        df['dynamic_state'] = np.select(dyn_conditions, dyn_choices, default="EXHAUSTION")

        return df
