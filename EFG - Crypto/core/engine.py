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

        # Identificação de Mudança de Regime e Transição
        df['prev_regime'] = df['regime'].shift()
        regime_change = df['regime'] != df['prev_regime']
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
        # Gatilhos de Ignição V14.2: Baseados na Transição e Força
        # Estados: 0: BULL, 1: BEAR, 2: COMP, 3: EXH
        f_res = last['f_bull_i'] if last['regime'] == 0 else last['f_bear_i'] if last['regime'] == 1 else 0.0
        over_noise = f_res > last['noise_floor']

        # Regras de Entrada (Transições Permitidas)
        # Permite Ignition se entrar em BULL/BEAR vindo de COMP ou se mantendo em BULL/BEAR (Inércia)
        # Bloqueia se vier de EXH ou estiver em EXH/COMP
        valid_transition = False
        if last['regime'] in [0, 1]:
            if last['prev_regime'] in [0, 1, 2] and last['prev_regime'] != 3:
                valid_transition = True

        # Cálculo do Índice de Convicção (Assertividade Esperada)
        # Produto da Força Markoviana pelo excesso de Força Física sobre o ruído
        strength = last['p_bull'] if last['regime'] == 0 else last['p_bear'] if last['regime'] == 1 else 0.25
        force_ratio = f_res / last['noise_floor'] if last['noise_floor'] > 0 else 1.0
        conviction = strength * min(2.0, force_ratio) # Limitamos o multiplicador de força para não distorcer

        decision = {
            'ignition_long': last['regime'] == 0 and valid_transition and over_noise and last['regime_age'] <= 10,
            'ignition_short': last['regime'] == 1 and valid_transition and over_noise and last['regime_age'] <= 10,
            'trail_stop': last['trail_stop'],
            'conviction': conviction,
            'flat_count': last['flat_count'],
            'regime_age': last['regime_age'],
            'signal_status': "FRESH" if last['regime_age'] <= 10 else "ALERT" if last['regime_age'] <= 20 else "EXPIRED"
        }

        # Lógica de Gestão de Posição (Transições V14.2)
        if self.active_position:
            price, atr, trail = last['close'], last['atr_sl'], last['trail_stop']
            side = self.active_position['side']

            # 1. Saída Total: Regime EXH ou Inversão Total (BULL <-> BEAR) ou Stop Loss
            decision['exit_total'] = (last['regime'] == 3) # EXH = Sair sempre

            if side == 'LONG':
                if last['regime'] == 1 or (trail and price < trail): decision['exit_total'] = True
            else: # SHORT
                if last['regime'] == 0 or (trail and price > trail): decision['exit_total'] = True

            # 2. Redução 50%: Transição para COMP ou Trail Flat
            # BULL -> COMP ou BEAR -> COMP = Desaceleração
            decision['exit_50_flat'] = (last['flat_count'] >= 3) or (last['regime'] == 2)

            # 3. Redução 30%: Preço Esticado (Requer afastamento > (Risco Inicial + 1 ATR))
            # Evita reduções imediatas na entrada.
            decision['exit_30_stretch'] = trail and abs(price - trail) > (atr * (self.sl_mult + 1.0))

        return decision
