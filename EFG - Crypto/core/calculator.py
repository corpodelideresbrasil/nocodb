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

        # Exaustão (Wicks vs Body) - Elevado multiplicador e filtro de significância (0.5 ATR)
        df['wicks'] = (df['high'] - df[['open', 'close']].max(axis=1)) + \
                      (df[['open', 'close']].min(axis=1) - df['low'])
        # Só ativa exaustão se o pavio for 4x maior que o corpo E maior que 50% do ATR médio
        df['f_exh_i'] = np.where((df['wicks'] > (df['body_work'] * 4.0)) & (df['wicks'] > (df['atr_ref'] * 0.5)), df['wicks'], 0.0)

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
        Calcula as probabilidades amnésicas (V15.0 - Sem Lag).
        Remove as EMAs para focar puramente nas forças do estado presente.
        """
        # Usamos as probabilidades instantâneas diretamente para evitar lag temporal
        for col in ['bull', 'bear', 'comp', 'exh']:
            df[f'p_{col}'] = df[f'p_{col}_i']

        return df

    def identify_regime(self, df, h_threshold=0.25):
        """
        Identifica o Regime com Histerese e o Estado Dinâmico (V14.2).
        Histerese: Evita 'flickering' de estados quando as probabilidades estão próximas.
        Adicionado: Barreira de Energia (Atrito Estático) para evitar mudanças bruscas.
        """
        regimes = []
        # Inicializa com o estado de maior probabilidade no primeiro candle
        first_probs = df[['p_bull', 'p_bear', 'p_comp', 'p_exh']].iloc[0].values
        current_regime = np.argmax(first_probs)

        p_cols = ['p_bull', 'p_bear', 'p_comp', 'p_exh']
        f_cols = ['f_bull_i', 'f_bear_i', 'f_comp_i', 'f_exh_i']
        probs_matrix = df[p_cols].values
        forces_matrix = df[f_cols].values
        noise_matrix = df['noise_floor'].values

        for i in range(len(df)):
            probs = probs_matrix[i]
            forces = forces_matrix[i]
            noise = noise_matrix[i]

            p_curr = probs[current_regime]
            max_idx = np.argmax(probs)
            p_max = probs[max_idx]
            f_target = forces[max_idx]

            # Barreira de Energia (Atrito Estático):
            # Para mudar de estado, a força do novo estado deve vencer o ruído médio.
            # EXH (3) requer 3.0x o ruído (blow-off). Trend (0,1) requer 1.5x (ignição real).
            mult = 3.0 if max_idx == 3 else 1.5 if max_idx in [0, 1] else 1.0
            energy_barrier = noise * mult
            has_energy = f_target > energy_barrier

            # Lógica de Histerese + Barreira de Energia:
            # Só muda se (Histerese vencida E tem energia suficiente) OU se o estado atual colapsar.
            if (p_max > p_curr + h_threshold and has_energy) or (p_curr < 0.10):
                current_regime = max_idx

            regimes.append(current_regime)

        df['regime'] = regimes

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
