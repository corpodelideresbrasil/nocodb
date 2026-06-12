import pandas as pd
import numpy as np
import pandas_ta as ta

class MPRMCalculator:
    """
    Calculadora matemática para o Market Physics Regime Model (V14.1).
    Responsável por traduzir a termodinâmica de preço e cadeias de Markov.
    """

    def __init__(self, markov_len=20):
        self.markov_len = markov_len

    def calculate_physics(self, df):
        """
        Calcula as forças físicas instantâneas (Módulo 1 do Manual).
        """
        # Trabalho do Corpo (Body Work)
        df['body_work'] = np.abs(df['close'] - df['open'])

        # Forças Bull e Bear
        df['f_bull_i'] = np.where(df['close'] > df['open'], df['body_work'], 0.0)
        df['f_bear_i'] = np.where(df['close'] < df['open'], df['body_work'], 0.0)

        # Compressão (Referenciada ao ATR recente)
        df['atr_ref'] = ta.atr(df['high'], df['low'], df['close'], length=self.markov_len)
        df['f_comp_i'] = (df['atr_ref'] - (df['high'] - df['low'])).clip(lower=0.0)

        # Exaustão (Wicks vs Body)
        df['wicks'] = (df['high'] - df[['open', 'close']].max(axis=1)) + \
                      (df[['open', 'close']].min(axis=1) - df['low'])
        df['f_exh_i'] = np.where(df['wicks'] > (df['body_work'] * 2.0), df['wicks'], 0.0)

        # Normalização Instantânea (O "Agora")
        df['total_i'] = df['f_bull_i'] + df['f_bear_i'] + df['f_comp_i'] + df['f_exh_i']

        # Probabilidades Instantâneas
        for col in ['bull', 'bear', 'comp', 'exh']:
            df[f'p_{col}_i'] = np.where(df['total_i'] > 0, df[f'f_{col}_i'] / df['total_i'], 0.25)

        return df

    def calculate_markov(self, df):
        """
        Suavização de Estados via Cadeia de Markov (Módulo 2 do Manual).
        """
        # Suavização via EMA
        for col in ['bull', 'bear', 'comp', 'exh']:
            df[f'p_{col}'] = ta.ema(df[f'p_{col}_i'], length=self.markov_len)

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
