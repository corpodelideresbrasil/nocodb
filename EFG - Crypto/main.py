import os
import numpy as np
from core.data_provider import DataProvider
from core.calculator import MPRMCalculator
from core.engine import MPRMEngine
from core.portfolio import PortfolioManager

def load_assets(filepath):
    if not os.path.exists(filepath): return []
    symbols = []
    with open(filepath, 'r') as f:
        for line in f:
            clean = line.strip().replace(',', '').replace("'", "").replace('"', '')
            if clean and not clean.startswith('#'): symbols.append(clean)
    return symbols

def monitor_market():
    symbols = load_assets("assets.txt")
    provider = DataProvider()
    calc = MPRMCalculator()
    portfolio = PortfolioManager(balance=200.0)

    opportunities = [] # Para ranqueamento

    print(f"--- MPRM V14.1 Futures Monitor | Saldo: ${portfolio.balance} ---")
    print(f"Alavancagem Atual: {portfolio.get_current_leverage():.1f}X / 5.0X")
    print("-" * 50)

    for symbol in symbols:
        try:
            df = provider.fetch_ohlcv(symbol)
            if df is None or df.empty: continue

            # Cálculos de Regime
            df = calc.calculate_physics(df)
            df = calc.calculate_markov(df)
            df = calc.identify_regime(df)

            # Motor de Decisão
            active_pos = portfolio.positions.get(symbol)
            engine = MPRMEngine(sl_mult=1.5)
            decision = engine.process_signals(df, active_position=active_pos)

            last = df.iloc[-1]

            # 1. MONITORAMENTO DE POSIÇÕES ATIVAS
            if active_pos:
                print(f"[ATIVA] {symbol:10} | Lado: {active_pos['side']:5} | Stop: {decision['trail_stop']:.4f}")
                if decision.get('exit_total'):
                    print(f"   >>> ❌ SAÍDA TOTAL RECOMENDADA (Regime/Stop)")
                elif decision.get('exit_50_flat'):
                    print(f"   >>> ⚠️ REDUZIR 50% (Linha Trail Flat há {decision['flat_count']} candles)")
                elif decision.get('exit_30_stretch'):
                    print(f"   >>> 🚀 REDUZIR 30% (Preço Esticado > 1 ATR)")

            # 2. CAPTURA DE NOVAS OPORTUNIDADES
            else:
                # Só recomenda se for sinal fresco ou alerta (regra dos 20 candles)
                if decision['signal_status'] != "EXPIRED":
                    strength = last['p_bull'] if last['regime'] == 0 else last['p_bear']
                    side = "LONG" if last['regime'] == 0 else "SHORT"

                    if decision['ignition_long'] or decision['ignition_short'] or decision['signal_status'] == "ALERT":
                        opportunities.append({
                            'symbol': symbol,
                            'side': side,
                            'strength': strength,
                            'status': decision['signal_status'],
                            'age': decision['regime_age'],
                            'price': last['close']
                        })

        except Exception as e:
            print(f"Erro em {symbol}: {e}")

    # 3. RANKING DE OPORTUNIDADES
    if opportunities:
        print("\n" + "="*50)
        print("RANKING DE OPORTUNIDADES (TOP MARKOV STRENGTH)")
        print("="*50)

        # Ordena por força Markov
        opportunities.sort(key=lambda x: x['strength'], reverse=True)

        for op in opportunities:
            can_execute = portfolio.can_open_new()
            status_exec = "✅ DISPONÍVEL" if can_execute else "❌ LIMITE DE ALAVANCAGEM ATINGIDO"

            margin = portfolio.balance * portfolio.margin_per_asset_pct
            notional = margin * portfolio.max_total_leverage

            print(f"[{op['strength']*100:4.1f}%] {op['symbol']:10} | {op['side']:5} | Status: {op['status']} ({op['age']} candles)")
            print(f"       Ação: {status_exec}")
            print(f"       Estratégia: Usar ${margin:.2f} de Margem | Nocional: ${notional:.2f} (5X)")
            print("-" * 50)

if __name__ == "__main__":
    monitor_market()
