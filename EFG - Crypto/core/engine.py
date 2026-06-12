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
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.ewm(alpha=1/length, min_periods=length, adjust=False).mean()

    def process_signals(self, df):
        df = df.copy()
        df['atr_sl'] = self._atr(df, 14)

        regime_change = df['regime'] != df['regime'].shift()
        df['regime_age'] = regime_change.cumsum().groupby(regime_change.cumsum()).cumcount()

        df['trail_stop'] = np.nan
        df['flat_count'] = 0
        current_trail, flat_counter = None, 0
        start_idx = max(0, len(df) - 50)

        for i in range(start_idx, len(df)):
            row = df.iloc[i]
            regime, low, high, atr = row['regime'], row['low'], row['high'], row['atr_sl']
            if regime == 0:
                new_stop = low - (atr * self.sl_mult)
                current_trail = max(current_trail or 0, new_stop)
            elif regime == 1:
                new_stop = high + (atr * self.sl_mult)
                current_trail = min(current_trail or 1e10, new_stop)
            else: current_trail = None

            if i > 0 and current_trail == df.iloc[i-1].get('trail_stop'): flat_counter += 1
            else: flat_counter = 0

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

        if self.active_position:
            price, atr, trail = last['close'], last['atr_sl'], last['trail_stop']
            # Saída total imediata se mudar regime ou bater stop
            decision['exit_total'] = last['regime'] in [2, 3]
            if self.active_position['side'] == 'LONG' and trail and price < trail: decision['exit_total'] = True
            elif self.active_position['side'] == 'SHORT' and trail and price > trail: decision['exit_total'] = True

            # FILTRO DE TENDÊNCIA: Usa a idade da POSIÇÃO (bars_held), não do regime.
            bars_held = self.active_position.get('bars_held', 0)
            if bars_held >= 10:
                decision['exit_50_flat'] = last['flat_count'] >= 3
                decision['exit_30_stretch'] = trail and abs(price - trail) > atr
            else:
                decision['exit_50_flat'] = False
                decision['exit_30_stretch'] = False

            # Adicional: Saída total se houver inversão de tendência (Long -> Bear ou Short -> Bull)
            if self.active_position['side'] == 'LONG' and last['regime'] == 1: decision['exit_total'] = True
            if self.active_position['side'] == 'SHORT' and last['regime'] == 0: decision['exit_total'] = True

        return decision
