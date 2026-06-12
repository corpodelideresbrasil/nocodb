import pandas as pd
import numpy as np

class MPRMEngine:
    """
    Motor de Sinais e Gestão de Posição do MPRM (V14.1).
    Foco no AGORA: Markoviano, sem olhar para o passado temporal.
    """

    def __init__(self, sl_mult=1.5, active_position=None):
        self.sl_mult = sl_mult
        self.active_position = active_position

    def _atr(self, df, length=14):
        """Cálculo nativo do ATR (Wilder's Smoothing)."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.ewm(alpha=1/length, min_periods=length, adjust=False).mean()

    def process_signals(self, df):
        """
        Calcula o estado atual dos sinais, trailing stop e saídas parciais.
        """
        df = df.copy()
        df['atr_sl'] = self._atr(df, 14)

        # Identificação de Mudança de Regime
        regime_change = df['regime'] != df['regime'].shift()
        df['regime_age'] = regime_change.cumsum().groupby(regime_change.cumsum()).cumcount()

        df['trail_stop'] = np.nan
        df['flat_count'] = 0
        current_trail, flat_counter = None, 0

        # Lookback amnésico (apenas o necessário para estabilizar o trail stop dinâmico)
        # 50 barras é o ponto de equilíbrio para convergência do ATR/EMA sem peso histórico excessivo.
        start_idx = max(0, len(df) - 50)

        for i in range(start_idx, len(df)):
            row = df.iloc[i]
            regime, low, high, atr = row['regime'], row['low'], row['high'], row['atr_sl']

            # Lógica de Ratcheting (Amnésia de Direção)
            if regime == 0: # BULL
                new_stop = low - (atr * self.sl_mult)
                current_trail = max(current_trail or 0, new_stop)
            elif regime == 1: # BEAR
                new_stop = high + (atr * self.sl_mult)
                current_trail = min(current_trail or 1e10, new_stop)
            else:
                current_trail = None # Extinção do rastro em regimes Blue/Orange

            # Contador de Flat (Inércia de Tendência)
            if i > 0 and current_trail == df.iloc[i-1].get('trail_stop'):
                flat_counter += 1
            else:
                flat_counter = 0

            df.at[df.index[i], 'trail_stop'] = current_trail
            df.at[df.index[i], 'flat_count'] = flat_counter

        last = df.iloc[-1]
        # Gatilhos de Ignição: Baseados puramente na mudança de estado (regime_age == 0)
        decision = {
            'ignition_long': last['regime'] == 0 and last['regime_age'] == 0,
            'ignition_short': last['regime'] == 1 and last['regime_age'] == 0,
            'trail_stop': last['trail_stop'],
            'flat_count': last['flat_count'],
            'regime_age': last['regime_age'],
            'signal_status': "FRESH" if last['regime_age'] <= 10 else "ALERT" if last['regime_age'] <= 20 else "EXPIRED"
        }

        # Lógica de Saída Amestral (Sem olhar para data de abertura da posição)
        if self.active_position:
            price, atr, trail = last['close'], last['atr_sl'], last['trail_stop']

            # 1. Saída Total (Regime desfavorável ou Stop Loss atingido)
            decision['exit_total'] = last['regime'] in [2, 3]

            if self.active_position['side'] == 'LONG':
                if (trail and price < trail) or last['regime'] == 1:
                    decision['exit_total'] = True
            elif self.active_position['side'] == 'SHORT':
                if (trail and price > trail) or last['regime'] == 0:
                    decision['exit_total'] = True

            # 2. Saídas Parciais (Baseadas puramente na energia e rastro atual)
            # Regra: Flat Trail por 3 barras ou Distância > 1 ATR
            decision['exit_50_flat'] = last['flat_count'] >= 3
            decision['exit_30_stretch'] = trail and abs(price - trail) > atr

        return decision
