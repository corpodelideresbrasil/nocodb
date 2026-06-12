import pandas as pd
import numpy as np

class MPRMEngine:
    """
    Motor de Sinais e Gestão de Posição do MPRM (V14.1).
    Gerencia Ignition, Trailing Stop, N-Candles e Saídas Parciais.
    Nativa: Não depende de pandas_ta para compatibilidade com Python 3.14+.
    """

    def __init__(self, sl_mult=1.5):
        self.sl_mult = sl_mult
        self.pos_state = 0 # 0: None, 1: Long, -1: Short
        self.trail_sl = None
        self.ignition_price = None
        self.bars_since_ignition = 0
        self.flat_count = 0

    def _atr(self, df, length):
        """Implementação nativa de ATR (Wilder's Smoothing)."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.ewm(alpha=1/length, min_periods=length, adjust=False).mean()

    def process_signals(self, df):
        """
        Gera gatilhos de entrada e saída baseados no regime e Trail.
        """
        # Preparação
        df['atr_sl'] = self._atr(df, 14)
        df['ignition_long'] = False
        df['ignition_short'] = False
        df['exit_signal'] = False
        df['partial_exit_50'] = False
        df['partial_exit_30'] = False
        df['signal_validity'] = "NONE" # FRESH, ALERT, EXPIRED
        df['trail_stop_val'] = np.nan

        for i in range(1, len(df)):
            row = df.iloc[i]
            regime = row['regime']
            close = row['close']
            low = row['low']
            high = row['high']
            atr = row['atr_sl']

            # --- 1. GATILHOS DE IGNIÇÃO ---
            if regime == 0 and self.pos_state != 1:
                df.at[df.index[i], 'ignition_long'] = True
                self.pos_state = 1
                self.trail_sl = low - (atr * self.sl_mult)
                self.ignition_price = close
                self.bars_since_ignition = 0
                self.flat_count = 0

            elif regime == 1 and self.pos_state != -1:
                df.at[df.index[i], 'ignition_short'] = True
                self.pos_state = -1
                self.trail_sl = high + (atr * self.sl_mult)
                self.ignition_price = close
                self.bars_since_ignition = 0
                self.flat_count = 0

            # --- 2. VALIDADE DO SINAL (Regra dos N-Candles) ---
            if self.pos_state != 0:
                if self.bars_since_ignition <= 10:
                    df.at[df.index[i], 'signal_validity'] = "FRESH"
                elif self.bars_since_ignition <= 20:
                    df.at[df.index[i], 'signal_validity'] = "ALERT"
                else:
                    df.at[df.index[i], 'signal_validity'] = "EXPIRED"

            # --- 3. GESTÃO DE SAÍDA POR REGIME (Break) ---
            elif (regime == 2 or regime == 3) and self.pos_state != 0:
                df.at[df.index[i], 'exit_signal'] = True
                self._reset_state()

            # --- 4. TRAILING STOP E SAÍDAS PARCIAIS ---
            if self.pos_state != 0:
                prev_trail = self.trail_sl

                # Ratcheting
                if self.pos_state == 1:
                    current_sl = low - (atr * self.sl_mult)
                    self.trail_sl = max(self.trail_sl or 0, current_sl)
                    if close < self.trail_sl:
                        df.at[df.index[i], 'exit_signal'] = True
                        self._reset_state()
                else: # Short
                    current_sl = high + (atr * self.sl_mult)
                    self.trail_sl = min(self.trail_sl or 1e10, current_sl)
                    if close > self.trail_sl:
                        df.at[df.index[i], 'exit_signal'] = True
                        self._reset_state()

                # Verificação de Linha Flat (Saída 50%)
                if self.pos_state != 0: # Checa se ainda está posicionado após o Trail
                    if self.trail_sl == prev_trail:
                        self.flat_count += 1
                    else:
                        self.flat_count = 0

                    if self.flat_count >= 3:
                        df.at[df.index[i], 'partial_exit_50'] = True

                    # Verificação de Afastamento Excessivo (Saída 30%)
                    dist = abs(close - self.trail_sl) if self.trail_sl else 0
                    if dist > atr:
                        df.at[df.index[i], 'partial_exit_30'] = True

            df.at[df.index[i], 'trail_stop_val'] = self.trail_sl
            self.bars_since_ignition += 1

        return df

    def _reset_state(self):
        self.pos_state = 0
        self.trail_sl = None
        self.ignition_price = None
        self.bars_since_ignition = 0
        self.flat_count = 0

    def check_trade_validity(self, spread, slippage, atr):
        """
        Regra de Gestão de Risco: Spread + Slippage <= 20% ATR.
        """
        return (spread + slippage) <= (0.20 * atr)
