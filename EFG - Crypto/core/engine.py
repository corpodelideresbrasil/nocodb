import pandas as pd
import numpy as np

class MPRMEngine:
    """
    Motor de Sinais e Gestão de Posição do MPRM (V14.1).
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

        # Calcular idade do regime
        regime_change = df['regime'] != df['regime'].shift()
        df['regime_age'] = regime_change.cumsum().groupby(regime_change.cumsum()).cumcount()

        df['trail_stop'] = np.nan
        df['flat_count'] = 0
        current_trail, flat_counter = None, 0

        # Aumentado para 200 para estabilizar o ATR/EMA perfeitamente conforme TradingView
        start_idx = max(0, len(df) - 200)

        for i in range(start_idx, len(df)):
            row = df.iloc[i]
            regime = row['regime']
            low, high, atr = row['low'], row['high'], row['atr_sl']

            # Lógica de Ratcheting (Trailing Stop)
            if regime == 0: # BULL
                new_stop = low - (atr * self.sl_mult)
                current_trail = max(current_trail or 0, new_stop)
            elif regime == 1: # BEAR
                new_stop = high + (atr * self.sl_mult)
                current_trail = min(current_trail or 1e10, new_stop)
            else:
                current_trail = None

            # Contador de Flat (Stop horizontal)
            if i > 0 and current_trail == df.iloc[i-1].get('trail_stop'):
                flat_counter += 1
            else:
                flat_counter = 0

            df.at[df.index[i], 'trail_stop'] = current_trail
            df.at[df.index[i], 'flat_count'] = flat_counter

        last = df.iloc[-1]
        decision = {
            'ignition_long': last['regime'] == 0 and last['regime_age'] == 0,
            'ignition_short': last['regime'] == 1 and last['regime_age'] == 0,
            'regime_age': last['regime_age'],
            'signal_status': "FRESH" if last['regime_age'] <= 10 else "ALERT" if last['regime_age'] <= 20 else "EXPIRED",
            'trail_stop': last['trail_stop'],
            'flat_count': last['flat_count']
        }

        # Lógica de Saída (Se houver posição ativa)
        if self.active_position:
            price, atr, trail = last['close'], last['atr_sl'], last['trail_stop']

            # SAÍDA TOTAL: Instantânea se mudar regime (COMP/EXH) ou bater stop
            decision['exit_total'] = last['regime'] in [2, 3]

            if self.active_position['side'] == 'LONG':
                if (trail and price < trail) or last['regime'] == 1: # Stop ou Inversão p/ Bear
                    decision['exit_total'] = True
            elif self.active_position['side'] == 'SHORT':
                if (trail and price > trail) or last['regime'] == 0: # Stop ou Inversão p/ Bull
                    decision['exit_total'] = True

            # SAÍDAS PARCIAIS: Protegidas pela carência de 10 candles (bars_held)
            # Foco em capturar tendências de longo prazo evitando ruído inicial
            bars_held = self.active_position.get('bars_held', 0)
            if bars_held >= 10:
                decision['exit_50_flat'] = last['flat_count'] >= 3
                decision['exit_30_stretch'] = trail and abs(price - trail) > atr
            else:
                decision['exit_50_flat'] = False
                decision['exit_30_stretch'] = False

        return decision
